from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from visual_memory import VisualMemoryConfig
from visual_memory.deposit_config import load_deposit_config
from visual_memory.models import StockSearchResult
from visual_memory.ops import (
    DepositphotosOperationLog,
    DepositphotosOperationState,
    match_orientation,
    merge_notes,
)
from visual_memory.seo import embed_image_metadata, seo_fields_for
from visual_memory.stock import DepositphotosClient, StockProviderError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Resume-safe Depositphotos workflow runner")
    parser.add_argument("--query", required=True)
    parser.add_argument("--orientation", required=True, choices=("landscape", "portrait", "square", "vertical", "horizontal"))
    parser.add_argument("--mode", default="preview_export", choices=("preview_export", "licensed_export", "search_only"))
    parser.add_argument("--operation", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--limit", type=int, default=15)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--embed-metadata", action="store_true")
    parser.add_argument("--slot-label", default="Depositphotos")
    parser.add_argument("--target-description", default="")
    parser.add_argument("--healthcheck-only", action="store_true")
    parser.add_argument("--format", default="webp", choices=("webp", "jpg", "png"))
    return parser


def normalize_orientation(value: str) -> str:
    if value == "vertical":
        return "portrait"
    if value == "horizontal":
        return "landscape"
    return value


def build_client() -> DepositphotosClient:
    settings = load_deposit_config()
    config = VisualMemoryConfig(database_path=PROJECT_ROOT / "data" / "visual_memory.db")
    config.depositphotos_search_url = settings.get("search_url")
    config.depositphotos_api_key = settings.get("api_key")
    config.depositphotos_api_secret = settings.get("api_secret")
    config.depositphotos_affiliate_id = settings.get("affiliate_id")
    return DepositphotosClient(config)


def api_key_for_download() -> str:
    settings = load_deposit_config()
    for candidate in (settings.get("api_secret"), settings.get("api_key")):
        if isinstance(candidate, str) and len(candidate.strip()) >= 24:
            return candidate.strip()
    raise StockProviderError("Depositphotos API key is missing for licensed download")


def login_session_id(api_key: str) -> str:
    settings = load_deposit_config()
    login_user = settings.get("account") or settings.get("api_key")
    login_password = os.environ.get("DP_LOGIN_PASSWORD", "").strip() or settings.get("password")
    if not login_user or not login_password:
        raise StockProviderError("Depositphotos login credentials are missing")

    payload = {
        "dp_command": "login",
        "dp_apikey": api_key,
        "dp_login_user": login_user,
        "dp_login_password": login_password,
    }
    request = Request(
        "https://api.depositphotos.com/",
        data=urlencode(payload).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    context = None
    if os.environ.get("PHOTO_AI_INSECURE_SSL", "").strip() in {"1", "true", "TRUE", "yes", "YES"}:
        import ssl

        context = ssl._create_unverified_context()
    with urlopen(request, context=context, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("type") != "success" or not payload.get("sessionid"):
        raise StockProviderError("Depositphotos login failed for licensed download")
    return str(payload["sessionid"])


def licensed_download_link(api_key: str, session_id: str, asset_id: str, option: str = "xl", license_name: str = "standard") -> tuple[str, str | None]:
    payload = {
        "dp_command": "getMedia",
        "dp_apikey": api_key,
        "dp_session_id": session_id,
        "dp_media_id": asset_id,
        "dp_media_option": option,
        "dp_media_license": license_name,
    }
    request = Request(
        "https://api.depositphotos.com/",
        data=urlencode(payload).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    context = None
    if os.environ.get("PHOTO_AI_INSECURE_SSL", "").strip() in {"1", "true", "TRUE", "yes", "YES"}:
        import ssl

        context = ssl._create_unverified_context()
    with urlopen(request, context=context, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("type") != "success" or not payload.get("downloadLink"):
        message = ""
        error = payload.get("error")
        if isinstance(error, dict):
            message = str(error.get("errormsg") or "")
        raise StockProviderError(message or "Depositphotos licensed download failed")
    return str(payload["downloadLink"]), payload.get("licenseId")


def ensure_wp_fields(slot_label: str, target_description: str) -> None:
    fields = seo_fields_for(slot_label, target_description)
    required = {
        "alt": fields.alt,
        "title": fields.title,
        "caption": fields.caption,
        "description": fields.description,
        "keywords": ",".join(fields.keywords),
        "credit": fields.credit,
    }
    missing = [key for key, value in required.items() if not value.strip()]
    if missing:
        raise StockProviderError("Missing required WordPress fields: " + ", ".join(missing))


def _tokenize(value: str) -> list[str]:
    return [part for part in re.split(r"[^a-z0-9]+", value.lower()) if part]


def semantic_score(item: StockSearchResult, query: str, orientation: str) -> float:
    haystack = " ".join(
        value for value in [
            item.title or "",
            " ".join(item.keywords),
            item.landing_url or "",
        ] if value
    ).lower()
    tokens = _tokenize(query)
    score = 0.0

    strong_positive = ("piazza", "barberini", "triton", "fountain", "rome")
    strong_negative = ("hotel", "building", "exterior", "facade", "bristol")

    for token in tokens:
        if token in haystack:
            score += 1.8
    for token in strong_positive:
        if token in haystack:
            score += 2.5
    for token in strong_negative:
        if token in haystack:
            score -= 3.5

    if "piazza barberini" in haystack:
        score += 7.0
    if "triton fountain" in haystack:
        score += 5.0
    if "triton fountain at piazza barberini" in haystack:
        score += 8.0
    if "piazza del tritone" in haystack:
        score -= 4.0

    if item.width and item.height and match_orientation(item.width, item.height, orientation):
        score += 2.0

    if item.width and item.height:
        score += min(2.0, (item.width * item.height) / 12_000_000)

    return score


def choose_best_result(results: list[StockSearchResult], query: str, orientation: str) -> StockSearchResult | None:
    scored = sorted(
        results,
        key=lambda item: semantic_score(item, query, orientation),
        reverse=True,
    )
    return scored[0] if scored else None


def download_preview(preview_url: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    request = Request(preview_url, method="GET")
    context = None
    if os.environ.get("PHOTO_AI_INSECURE_SSL", "").strip() in {"1", "true", "TRUE", "yes", "YES"}:
        import ssl

        context = ssl._create_unverified_context()
    with urlopen(request, context=context, timeout=30) as response:
        output_path.write_bytes(response.read())


def standard_dimensions(orientation: str) -> tuple[int, int]:
    if orientation == "portrait":
        return (1200, 1500)
    if orientation == "square":
        return (1200, 1200)
    return (1600, 1000)


def ensure_output_path(output_path: Path, target_format: str) -> Path:
    suffix = f".{target_format}"
    if output_path.suffix.lower() == suffix:
        return output_path
    return output_path.with_suffix(suffix)


def postprocess_image(source_path: Path, output_path: Path, orientation: str) -> Path:
    from PIL import Image, ImageOps

    width, height = standard_dimensions(orientation)
    final_path = ensure_output_path(output_path, output_path.suffix.lstrip(".") or "webp")
    final_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source_path) as image:
        converted = image.convert("RGB")
        fitted = ImageOps.fit(converted, (width, height), method=Image.Resampling.LANCZOS)
        save_kwargs = {"quality": 92}
        if final_path.suffix.lower() == ".webp":
            save_kwargs["format"] = "WEBP"
        elif final_path.suffix.lower() in {".jpg", ".jpeg"}:
            save_kwargs["format"] = "JPEG"
            save_kwargs["optimize"] = True
        elif final_path.suffix.lower() == ".png":
            save_kwargs["format"] = "PNG"
        fitted.save(final_path, **save_kwargs)
    if source_path != final_path and source_path.exists():
        source_path.unlink()
    return final_path


def main() -> None:
    args = build_parser().parse_args()
    orientation = normalize_orientation(args.orientation)
    log_store = DepositphotosOperationLog(PROJECT_ROOT / "ops_logs")
    state = log_store.load(args.operation) if args.resume else None

    if state is None:
        state = DepositphotosOperationState(
            operation=args.operation,
            search_query=args.query,
            orientation=orientation,
            mode=args.mode,
            output=str(ensure_output_path(args.output.expanduser(), args.format)) if args.output else None,
        )
        state.notes = merge_notes(state.notes, "resume-safe workflow state file created")
        log_store.save(state)

    client = build_client()
    health = client.validate_connection()
    log_store.write_health_report(
        provider=health.provider,
        connected=health.connected,
        search_enabled=health.search_enabled,
        endpoint=health.endpoint,
        auth_mode=health.auth_mode,
        message=health.message,
    )

    try:
        ensure_wp_fields(args.slot_label, args.target_description or args.query)

        if args.healthcheck_only:
            state.status = "completed" if health.connected else "failed"
            state.metadata_embed = "skipped"
            state.notes = merge_notes(
                state.notes,
                f"healthcheck connected={health.connected}",
                f"healthcheck search_enabled={health.search_enabled}",
                health.message or "",
            )
            if not health.connected:
                state.failure_stage = "api_connect"
                state.failure_reason = health.message
                state.next_action = "verify credentials or SSL settings"
            log_store.save(state)
            print(f"connected={health.connected}")
            print(f"search_enabled={health.search_enabled}")
            return

        if not health.connected:
            state.status = "failed"
            state.failure_stage = "api_connect"
            state.failure_reason = health.message or "Depositphotos connection failed"
            state.next_action = "verify credentials or SSL settings"
            log_store.save(state)
            raise SystemExit(1)

        if not health.search_enabled:
            state.status = "failed"
            state.failure_stage = "api_search"
            state.failure_reason = health.message or "Depositphotos search is not enabled"
            state.next_action = "verify account permissions or the correct API search section"
            state.notes = merge_notes(
                state.notes,
                "connection established but search capability is unavailable",
            )
            log_store.save(state)
            raise SystemExit(1)

        if not state.selected_asset_id:
            results = client.search(state.search_query, limit=args.limit, page=1)
            state.status = "api_search_done"
            state.notes = merge_notes(state.notes, f"api returned {len(results)} results")
            orientation_matches = [item for item in results if match_orientation(item.width, item.height, state.orientation)]
            selected = choose_best_result(orientation_matches or results, state.search_query, state.orientation)
            if selected is None:
                state.status = "failed"
                state.failure_stage = "asset_select"
                state.failure_reason = f"no {state.orientation} result found"
                state.next_action = "try broader query or different orientation"
                log_store.save(state)
                raise SystemExit(1)
            state.selected_asset_id = selected.asset_id
            state.selected_item_url = selected.landing_url
            state.selected_preview_url = selected.preview_url
            state.status = "asset_selected"
            state.notes = merge_notes(
                state.notes,
                f"selected asset {selected.asset_id}",
                f"selected title: {selected.title or 'untitled'}",
            )
            log_store.save(state)

        if state.mode == "search_only":
            state.status = "completed"
            state.metadata_embed = "skipped"
            state.notes = merge_notes(state.notes, "search-only mode, no download performed")
            log_store.save(state)
            print(f"selected_asset_id={state.selected_asset_id}")
            return

        if not state.output:
            state.status = "failed"
            state.failure_stage = "preview_export"
            state.failure_reason = "output path is required for export modes"
            state.next_action = "rerun with --output"
            log_store.save(state)
            raise SystemExit(1)

        output_path = Path(state.output).expanduser()
        if not output_path.exists():
            if not state.selected_preview_url:
                if state.mode != "licensed_export":
                    state.status = "failed"
                    state.failure_stage = "preview_export"
                    state.failure_reason = "selected asset has no preview URL"
                    state.next_action = "choose a different asset or use licensed flow"
                    log_store.save(state)
                    raise SystemExit(1)
            temp_path = output_path.with_suffix(".download")
            if state.mode == "licensed_export":
                api_key = api_key_for_download()
                session_id = login_session_id(api_key)
                download_link, license_id = licensed_download_link(api_key, session_id, state.selected_asset_id or "")
                state.license_id = str(license_id or "")
                download_preview(download_link, temp_path)
            else:
                download_preview(state.selected_preview_url, temp_path)
            final_path = postprocess_image(temp_path, output_path, state.orientation)
            state.output = str(final_path)
            state.status = "preview_export_done" if state.mode == "preview_export" else "licensed_export_done"
            state.notes = merge_notes(
                state.notes,
                "licensed original downloaded to output path" if state.mode == "licensed_export" else "preview downloaded to output path",
                f"postprocess applied to {state.orientation} standard",
            )
            log_store.save(state)

        if args.embed_metadata and state.metadata_embed != "done":
            fields = seo_fields_for(args.slot_label, args.target_description or args.query)
            embed_image_metadata(str(output_path), fields)
            state.metadata_embed = "done"
            state.status = "metadata_embedded"
            state.notes = merge_notes(state.notes, "metadata embed attempted via exiftool")
            log_store.save(state)
        elif not args.embed_metadata:
            state.metadata_embed = "skipped"
            log_store.save(state)

        state.status = "completed"
        log_store.save(state)
        print(f"selected_asset_id={state.selected_asset_id}")
        print(f"output={state.output}")
    except StockProviderError as exc:
        state.status = "failed"
        state.failure_stage = "api_search"
        state.failure_reason = str(exc)
        state.next_action = "verify endpoint, credentials, or SSL settings"
        log_store.save(state)
        raise


if __name__ == "__main__":
    main()

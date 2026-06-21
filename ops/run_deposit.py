#!/usr/bin/env python3
"""Depositphotos quick flow: connect, search, crop, save WebP to Downloads."""
from __future__ import annotations

import argparse
import json
import os
import re
import ssl
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from PIL import Image, ImageOps

from src.utils.config import load_project_env
from src.core.database import VisualMemoryComponent, VisualMemoryConfig
from src.visual_memory.deposit_config import load_deposit_config
from src.visual_memory.models import StockConnectionStatus, StockSearchResult

load_project_env()


def connection_message(status: StockConnectionStatus) -> str:
    if status.connected:
        return (
            f"connected=true auth={status.auth_mode or 'unknown'} "
            f"endpoint={status.endpoint or 'unknown'}"
        )
    return (
        "connected=false "
        f"search_enabled={status.search_enabled} "
        f"message={status.message or 'no message'}"
    )


def print_results(results: list[StockSearchResult]) -> None:
    if not results:
        print("No results")
        return
    for idx, result in enumerate(results, start=1):
        print(
            f"{idx:>2}: {result.asset_id} - {result.title or ''}\n"
            f"    preview: {result.preview_url or '-'}\n"
            f"    landing: {result.landing_url or '-'}\n"
        )


BRANDED_TITLE_FRAGMENTS = (
    "hotel",
    "resort",
    "spa island",
    "gellert",
    "blue lagoon",
    "pam thermal",
)

PEOPLE_TITLE_FRAGMENTS = (
    "young woman",
    "woman",
    "female",
    "man",
    "tourists",
    "patients",
    "bikini",
)

GENERIC_POSITIVE_FRAGMENTS = (
    "thermal",
    "hot spring",
    "mineral",
    "pool",
    "water",
    "steam",
    "close up",
    "close-up",
    "detail",
    "scene",
)


def score_result_for_generic_use(result: StockSearchResult) -> int:
    title = (result.title or "").lower()
    score = 0
    for frag in GENERIC_POSITIVE_FRAGMENTS:
        if frag in title:
            score += 8
    for frag in PEOPLE_TITLE_FRAGMENTS:
        if frag in title:
            score -= 18
    for frag in BRANDED_TITLE_FRAGMENTS:
        if frag in title:
            score -= 60
    if result.landing_url and "/editorial/" in result.landing_url:
        score -= 6
    return score


def choose_preferred_result(results: list[StockSearchResult]) -> StockSearchResult:
    if not results:
        raise RuntimeError("No Depositphotos result to choose from")
    return max(results, key=score_result_for_generic_use)


def build_component(credentials_path: Path | None) -> VisualMemoryComponent:
    database = Path.cwd() / "data" / "visual_memory.db"
    config = VisualMemoryConfig(database_path=database)
    return VisualMemoryComponent(config, deposit_config_path=credentials_path)


def slugify(value: str) -> str:
    lowered = value.strip().lower()
    ascii_only = re.sub(r"[^a-z0-9]+", "-", lowered)
    cleaned = ascii_only.strip("-")
    return cleaned or "depositphotos"


def infer_extension(url: str) -> str:
    lower = url.lower()
    if ".png" in lower:
        return ".png"
    if ".webp" in lower:
        return ".webp"
    return ".jpg"


def ssl_context() -> ssl.SSLContext | None:
    if os.environ.get("PHOTO_AI_INSECURE_SSL", "").strip() in {"1", "true", "TRUE", "yes", "YES"}:
        return ssl._create_unverified_context()
    return None


def download_url(url: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, method="GET")
    with urlopen(request, timeout=30, context=ssl_context()) as response:
        output_path.write_bytes(response.read())
    return output_path


def normalize_orientation(value: str) -> str:
    lowered = value.lower()
    if lowered in {"vertical", "portrait"}:
        return "portrait"
    if lowered == "square":
        return "square"
    return "landscape"


def infer_orientation_from_query(query: str) -> str:
    lowered = query.lower()
    if "square" in lowered:
        return "square"
    if "portrait" in lowered or "vertical" in lowered:
        return "portrait"
    return "landscape"


def normalize_query_for_search(raw_query: str) -> str:
    normalized = raw_query.lower()
    normalized = normalized.replace("fotoğraf", "fotograf")
    normalized = normalized.replace("görsel", "gorsel")
    tokens = re.split(r"[^a-z0-9]+", normalized)
    stopwords = {
        "foto",
        "fotograf",
        "resim",
        "gorsel",
        "getir",
        "indir",
        "de",
        "dan",
        "den",
        "bir",
        "bana",
        "lutfen",
        "lütfen",
        "dp",
        "depositphotos",
        "dpden",
        "dpyi",
    }
    filtered = [token for token in tokens if token and token not in stopwords]
    cleaned = " ".join(filtered).strip()
    return cleaned or raw_query.strip()


def standard_dimensions(orientation: str) -> tuple[int, int]:
    if orientation == "portrait":
        return (1200, 1500)
    if orientation == "square":
        return (1200, 1200)
    return (1200, 750)


def api_key_for_download(settings: dict[str, str]) -> str:
    for candidate in (settings.get("api_secret"), settings.get("api_key")):
        if isinstance(candidate, str) and len(candidate.strip()) >= 24:
            return candidate.strip()
    raise RuntimeError("Depositphotos API key is missing for licensed download")


def login_user_for_download(settings: dict[str, str]) -> str:
    env_user = os.environ.get("DP_LOGIN_USER", "").strip()
    if env_user:
        return env_user
    for candidate in (settings.get("account"), settings.get("api_key")):
        if isinstance(candidate, str) and candidate.strip() and len(candidate.strip()) < 24:
            return candidate.strip()
    raise RuntimeError("Depositphotos login user is missing")


def login_password_for_download(settings: dict[str, str]) -> str:
    env_password = os.environ.get("DP_LOGIN_PASSWORD", "").strip()
    if env_password:
        return env_password
    password = settings.get("password")
    if isinstance(password, str) and password.strip():
        return password.strip()
    raise RuntimeError("Depositphotos login password is missing")


def login_session_id(api_key: str, login_user: str, login_password: str) -> str:
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
    with urlopen(request, timeout=30, context=ssl_context()) as response:
        data = json.loads(response.read().decode("utf-8"))
    if data.get("type") != "success" or not data.get("sessionid"):
        raise RuntimeError("Depositphotos login failed")
    return str(data["sessionid"])


def licensed_download_link(api_key: str, session_id: str, asset_id: str) -> str:
    payload = {
        "dp_command": "getMedia",
        "dp_apikey": api_key,
        "dp_session_id": session_id,
        "dp_media_id": asset_id,
        "dp_media_option": "xl",
        "dp_media_license": "standard",
    }
    request = Request(
        "https://api.depositphotos.com/",
        data=urlencode(payload).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urlopen(request, timeout=30, context=ssl_context()) as response:
        data = json.loads(response.read().decode("utf-8"))
    if data.get("type") != "success" or not data.get("downloadLink"):
        error = data.get("error")
        detail = ""
        if isinstance(error, dict):
            detail = str(error.get("errormsg") or "").strip()
        raise RuntimeError(detail or "Depositphotos licensed download failed")
    return str(data["downloadLink"])


def target_output_path(query: str, asset_id: str, orientation: str, custom_output: Path | None) -> Path:
    if custom_output is not None:
        return custom_output.expanduser().with_suffix(".webp")
    downloads = Path.home() / "Downloads"
    filename = f"{slugify(query)}-{orientation}-{asset_id}.webp"
    return downloads / filename


def crop_and_convert_webp(source_path: Path, final_path: Path, orientation: str) -> Path:
    width, height = standard_dimensions(orientation)
    final_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source_path) as image:
        converted = image.convert("RGB")
        fitted = ImageOps.fit(converted, (width, height), method=Image.Resampling.LANCZOS)
        fitted.save(final_path, format="WEBP", quality=92)
    if source_path.exists():
        source_path.unlink()
    return final_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Depositphotos quick runner")
    parser.add_argument("prompt", nargs="?", help="free-form prompt text, e.g. 'cordoba panoramic'")
    parser.add_argument("--query", "-q", default=None, help="search query")
    parser.add_argument("--limit", type=int, default=5, help="max result count")
    parser.add_argument("--page", type=int, default=1, help="result page")
    parser.add_argument("--credentials", type=Path, help="path to credentials json")
    parser.add_argument("--validate-only", action="store_true", help="only validate API connection")
    parser.add_argument("--no-download", action="store_true", help="skip preview download")
    parser.add_argument("--preview-only", action="store_true", help="download watermarked preview instead of licensed")
    parser.add_argument("--output", type=Path, help="output path; .webp extension is enforced")
    parser.add_argument(
        "--orientation",
        choices=("landscape", "portrait", "square", "horizontal", "vertical"),
        default=None,
        help="crop orientation (default: inferred from query)",
    )
    parser.add_argument("--verbose", action="store_true", help="print extra details")
    parser.add_argument("--asset-id", default=None, help="skip search, download this specific asset ID")
    args = parser.parse_args()
    query = normalize_query_for_search((args.query or args.prompt or "cordoba panoramic").strip())
    orientation = normalize_orientation(args.orientation) if args.orientation else infer_orientation_from_query(query)

    # Default this so the workflow works across sessions in this environment.
    os.environ.setdefault("PHOTO_AI_INSECURE_SSL", "1")

    component = build_component(args.credentials)
    status = component.validate_depositphotos_connection()
    print(f"Depositphotos connection: {connection_message(status)}")
    if args.verbose and status.message:
        print("message:", status.message)
    if not status.connected:
        raise SystemExit(1)

    if args.validate_only:
        return

    results = component.search_depositphotos(query, limit=args.limit, page=args.page)
    print_results(results)
    if not results or args.no_download:
        return

    if args.asset_id:
        first = next((r for r in results if str(r.asset_id) == str(args.asset_id)), None)
        if not first:
            # asset not in results, build a minimal stub
            from src.visual_memory.models import StockSearchResult
            first = StockSearchResult(
                provider="depositphotos",
                asset_id=str(args.asset_id),
                title=None,
                preview_url=None,
                landing_url=None,
            )
    else:
        first = choose_preferred_result(results)
    if not first.preview_url and not args.asset_id:
        print("First result has no preview URL; download skipped")
        return

    settings = load_deposit_config(args.credentials)
    temp_path: Path | None = None
    mode = "licensed"
    if args.preview_only:
        mode = "preview"
        extension = infer_extension(first.preview_url)
        temp_download = Path("tmp") / f"{slugify(query)}-{first.asset_id}{extension}"
        temp_path = download_url(first.preview_url, temp_download)
    else:
        try:
            api_key = api_key_for_download(settings)
            login_user = login_user_for_download(settings)
            login_password = login_password_for_download(settings)
            session_id = login_session_id(api_key, login_user, login_password)
            media_url = licensed_download_link(api_key, session_id, first.asset_id)
            extension = infer_extension(media_url)
            temp_download = Path("tmp") / f"{slugify(query)}-{first.asset_id}{extension}"
            temp_path = download_url(media_url, temp_download)
        except Exception as exc:
            mode = "preview-fallback"
            print(f"Licensed download failed, fallback to preview: {exc}")
            extension = infer_extension(first.preview_url)
            temp_download = Path("tmp") / f"{slugify(query)}-{first.asset_id}{extension}"
            temp_path = download_url(first.preview_url, temp_download)

    final_output = target_output_path(query, first.asset_id, orientation, args.output)
    saved = crop_and_convert_webp(temp_path, final_output, orientation)
    print(f"Downloaded and processed ({mode}): {saved.resolve()}")


if __name__ == "__main__":
    main()

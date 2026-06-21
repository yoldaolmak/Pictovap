#!/usr/bin/env python3
"""
YO OS WordPress Uploader — REST API media upload and attachment
"""

import requests
import json
import os
import re
import html
from pathlib import Path
from typing import Dict, List, Optional
import base64

from src.core.settings import env_str, load_project_env

load_project_env()

AUTO_MEDIA_START = "<!-- yo:auto-media:start -->"
AUTO_MEDIA_END = "<!-- yo:auto-media:end -->"


class YOWordPressUploader:
    """Upload processed images to WordPress via REST API"""

    SITE_ENDPOINTS = {
        "yoldaolmak": {
            "url": env_str("WP_URL", "https://yoldaolmak.com"),
            "user": env_str("WP_USER", "hamal"),
            "password": env_str("WP_APP_PASSWORD"),
        },
        "gezievreni": {
            "url": env_str("GEZIEVRENI_URL", "https://gezievreni.com"),
            "user": env_str("GEZIEVRENI_USER", "hamal"),
            "password": env_str("GEZIEVRENI_PASS"),
        },
        "gezgindunyasi": {
            "url": env_str("GEZGINDUNYASI_URL", "https://gezgindunyasi.com"),
            "user": env_str("GEZGINDUNYASI_USER", "clawdbot"),
            "password": env_str("GEZGINDUNYASI_PASS"),
        },
    }

    def __init__(self, site: str = "yoldaolmak"):
        if site not in self.SITE_ENDPOINTS:
            raise ValueError(f"Unknown site: {site}")

        config = self.SITE_ENDPOINTS[site]
        self.site = site
        self.base_url = config["url"]
        self.user = config["user"]
        self.password = config["password"]
        if not self.base_url or not self.user or not self.password:
            raise ValueError(f"Missing WordPress credentials for site: {site}")
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create authenticated session"""
        session = requests.Session()
        session.auth = (self.user, self.password)
        session.headers.update({
            "User-Agent": "YO-OS-Media-Uploader/1.0",
        })
        return session


    def upload_media(
        self,
        file_path: str,
        title: str,
        alt_text: str,
        description: str = "",
        caption: str = "",
    ) -> Dict:
        """Upload single image to WordPress media library.
        Aynı slug'lı eski media varsa önce siler (slug çakışması / -1 -2 sorunu).

        Returns:
            dict with media_id and details
        """
        file_p = Path(file_path)
        if not file_p.exists():
            return {"success": False, "error": f"File not found: {file_path}"}

        endpoint = f"{self.base_url}/wp-json/wp/v2/media"

        # Read file
        with open(file_path, "rb") as f:
            file_data = f.read()

        # Upload
        headers = {
            "Content-Disposition": f'attachment; filename="{file_p.name}"',
            "Content-Type": "image/webp",
        }

        try:
            resp = self.session.post(
                endpoint,
                data=file_data,
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()

            media = resp.json()
            media_id = media["id"]

            # Update media metadata
            update_data = {
                "title": title,
                "description": description,
                "caption": caption,
                "alt_text": alt_text,
            }

            update_endpoint = f"{self.base_url}/wp-json/wp/v2/media/{media_id}"
            update_resp = self.session.post(
                update_endpoint,
                json=update_data,
                timeout=30,
            )
            update_resp.raise_for_status()

            return {
                "success": True,
                "media_id": media_id,
                "url": media.get("source_url", ""),
                "title": title,
                "alt_text": alt_text,
                "file": file_p.name,
            }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "file": file_p.name,
            }

    def attach_to_post(
        self,
        media_id: int,
        post_id: int,
    ) -> Dict:
        """Attach media to post (not as featured image)

        Args:
            media_id: WordPress media ID
            post_id: WordPress post ID

        Returns:
            dict with success status
        """
        endpoint = f"{self.base_url}/wp-json/wp/v2/media/{media_id}"

        try:
            resp = self.session.post(
                endpoint,
                json={"post": post_id},
                timeout=30,
            )
            resp.raise_for_status()

            return {
                "success": True,
                "media_id": media_id,
                "post_id": post_id,
            }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "media_id": media_id,
            }

    def fetch_post_context(self, post_id: int) -> Dict:
        endpoint = f"{self.base_url}/wp-json/wp/v2/posts/{post_id}?context=edit"
        try:
            resp = self.session.get(endpoint, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            excerpt_raw = _extract_post_field(data.get("excerpt", {}), prefer="raw")
            content_raw = _extract_post_field(data.get("content", {}), prefer="raw")
            return {
                "id": post_id,
                "title": html.unescape(data.get("title", {}).get("rendered", "")).strip(),
                "slug": str(data.get("slug", "")).strip(),
                "excerpt": _strip_html(excerpt_raw),
                "content": _strip_html(content_raw)[:2500],
                "content_raw": content_raw,
            }
        except requests.exceptions.RequestException:
            return {}

    def append_media_to_post_content(self, post_id: int, media_items: List[Dict]) -> Dict:
        post = self.fetch_post_context(post_id)
        if not post:
            return {"success": False, "error": "Post context could not be loaded"}

        current_content = post.get("content_raw", "") or ""
        original_content = current_content
        current_content, removed_broken = self._remove_broken_local_image_blocks(current_content)
        current_content = _remove_auto_media_region(current_content)
        auto_blocks: list[str] = []
        inserted = 0

        for item in media_items:
            media_id = item.get("media_id")
            url = item.get("url", "")
            if not media_id or not url:
                continue

            marker = f"wp-image-{media_id}"
            if marker in current_content or url in current_content:
                continue

            alt_text = _escape_attr(item.get("alt", ""))
            caption = _escape_html(item.get("caption", ""))
            block = (
                f'<!-- wp:image {{"id":{media_id},"sizeSlug":"full","linkDestination":"none"}} -->\n'
                f'<figure class="wp-block-image size-full"><img src="{url}" alt="{alt_text}" '
                f'class="wp-image-{media_id}"/>'
            )
            if caption:
                block += f'<figcaption class="wp-element-caption">{caption}</figcaption>'
            block += "</figure>\n<!-- /wp:image -->"
            heading_text = str(item.get("heading", "") or "").strip()
            heading_level = int(item.get("heading_level", 0) or 0)

            if heading_text:
                updated_content = _insert_block_after_heading(
                    current_content,
                    heading_text=heading_text,
                    block_html=block,
                    heading_level=heading_level or None,
                )
                if updated_content != current_content:
                    current_content = updated_content
                    inserted += 1
                    continue

            auto_blocks.append(block)
            inserted += 1

        if not auto_blocks:
            if current_content != original_content or removed_broken:
                endpoint = f"{self.base_url}/wp-json/wp/v2/posts/{post_id}"
                try:
                    resp = self.session.post(
                        endpoint,
                        json={"content": current_content},
                        timeout=30,
                    )
                    resp.raise_for_status()
                    return {"success": True, "updated": True, "inserted": inserted, "removed_broken": removed_broken}
                except requests.exceptions.RequestException as e:
                    return {"success": False, "error": str(e)}
            return {"success": True, "updated": False, "inserted": 0}

        combined_blocks = AUTO_MEDIA_START + "\n" + "\n\n".join(auto_blocks) + "\n" + AUTO_MEDIA_END
        new_content = _insert_before_first_h2(current_content, combined_blocks)
        endpoint = f"{self.base_url}/wp-json/wp/v2/posts/{post_id}"

        try:
            resp = self.session.post(
                endpoint,
                json={"content": new_content},
                timeout=30,
            )
            resp.raise_for_status()
            return {"success": True, "updated": True, "inserted": inserted, "removed_broken": removed_broken}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    def cleanup_broken_media_from_post(self, post_id: int) -> Dict:
        post = self.fetch_post_context(post_id)
        if not post:
            return {"success": False, "error": "Post context could not be loaded"}
        current_content = post.get("content_raw", "") or ""
        cleaned_content, removed_broken = self._remove_broken_local_image_blocks(current_content)
        cleaned_content = _remove_auto_media_region(cleaned_content)
        if removed_broken == 0 and cleaned_content == current_content:
            return {"success": True, "updated": False, "removed_broken": 0}
        endpoint = f"{self.base_url}/wp-json/wp/v2/posts/{post_id}"
        try:
            resp = self.session.post(
                endpoint,
                json={"content": cleaned_content},
                timeout=30,
            )
            resp.raise_for_status()
            return {"success": True, "updated": True, "removed_broken": removed_broken}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}

    def _remove_broken_local_image_blocks(self, content: str) -> tuple[str, int]:
        removed = 0

        def replace_block(match: re.Match[str]) -> str:
            nonlocal removed
            block = match.group(0)
            src_match = re.search(r'<img[^>]+src="([^"]+)"', block, flags=re.I)
            if not src_match:
                return block
            src = src_match.group(1)
            if not src.startswith(self.base_url + "/wp-content/uploads/"):
                return block
            try:
                resp = self.session.get(src, timeout=15, allow_redirects=True)
                if resp.status_code == 404:
                    removed += 1
                    return ""
            except requests.exceptions.RequestException:
                return block
            return block

        cleaned = re.sub(
            r"<!-- wp:image\b.*?<!-- /wp:image -->\s*",
            replace_block,
            content,
            flags=re.S,
        )
        return cleaned.strip() + ("\n" if cleaned.strip() else ""), removed


def _strip_html(value: str) -> str:
    text = re.sub(r"<style[^>]*>.*?</style>", " ", value, flags=re.S | re.I)
    text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def fetch_post_context(post_id: int, site: str = "yoldaolmak") -> Dict:
    uploader = YOWordPressUploader(site=site)
    return uploader.fetch_post_context(post_id)


def _extract_post_field(value: object, *, prefer: str = "rendered") -> str:
    if isinstance(value, dict):
        preferred = value.get(prefer)
        if isinstance(preferred, str):
            return preferred
        rendered = value.get("rendered")
        if isinstance(rendered, str):
            return rendered
    return str(value or "")


def _escape_attr(value: str) -> str:
    return html.escape(str(value or ""), quote=True)


def _escape_html(value: str) -> str:
    return html.escape(str(value or ""))


def _insert_before_first_h2(content: str, block_html: str) -> str:
    match = re.search(r"<h2\b[^>]*>", content, flags=re.I)
    if not match:
        return content.rstrip() + "\n\n" + block_html + "\n"
    insert_at = match.start()
    prefix = content[:insert_at].rstrip()
    suffix = content[insert_at:].lstrip()
    return prefix + "\n\n" + block_html + "\n\n" + suffix


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(_strip_html(value))).strip().lower()


def _insert_block_after_heading(
    content: str,
    *,
    heading_text: str,
    block_html: str,
    heading_level: Optional[int] = None,
) -> str:
    def _inside_code_like_block(full: str, start: int, end: int) -> bool:
        containers = [
            re.compile(r"<!-- wp:code(?:\s+\{.*?\})? -->.*?<!-- /wp:code -->", flags=re.S | re.I),
            re.compile(r"<!-- wp:preformatted(?:\s+\{.*?\})? -->.*?<!-- /wp:preformatted -->", flags=re.S | re.I),
            re.compile(r"<!-- wp:html(?:\s+\{.*?\})? -->.*?<!-- /wp:html -->", flags=re.S | re.I),
            re.compile(r"<pre\b[^>]*>.*?</pre>", flags=re.S | re.I),
        ]
        for container in containers:
            for block in container.finditer(full):
                if start >= block.start() and end <= block.end():
                    return True
        return False

    pattern = re.compile(
        r"<!-- wp:heading(?:\s+\{.*?\})? -->\s*<h(?P<level>[1-6])\b[^>]*>.*?</h(?P=level)>\s*<!-- /wp:heading -->",
        flags=re.S | re.I,
    )
    target = _normalize_text(heading_text)

    for match in pattern.finditer(content):
        level = int(match.group("level"))
        if heading_level and level != heading_level:
            continue

        heading_block = match.group(0)
        if target not in _normalize_text(heading_block):
            continue
        if _inside_code_like_block(content, match.start(), match.end()):
            continue

        # Guardrail: skip insertion when an image already exists directly
        # above/below the heading, or with only one paragraph gap.
        before = content[: match.start()]
        after = content[match.end() :]
        has_nearby_image_before = re.search(
            r"<!-- wp:image\b.*?<!-- /wp:image -->\s*(?:<!-- wp:paragraph(?:\s+\{.*?\})? -->.*?<!-- /wp:paragraph -->\s*)?$",
            before,
            flags=re.S | re.I,
        )
        has_nearby_image_after = re.match(
            r"\s*(?:<!-- wp:paragraph(?:\s+\{.*?\})? -->.*?<!-- /wp:paragraph -->\s*)?<!-- wp:image\b",
            after,
            flags=re.S | re.I,
        )
        if has_nearby_image_before or has_nearby_image_after:
            continue

        insert_at = match.end()
        prefix = content[:insert_at].rstrip()
        suffix = content[insert_at:].lstrip()
        return prefix + "\n\n" + block_html + "\n\n" + suffix

    return content


def _remove_auto_media_region(content: str) -> str:
    cleaned = re.sub(
        re.escape(AUTO_MEDIA_START) + r".*?" + re.escape(AUTO_MEDIA_END) + r"\s*",
        "",
        content,
        flags=re.S,
    )
    return cleaned.strip() + ("\n" if cleaned.strip() else "")


def upload_images_batch(
    image_files: List[str],
    metadata_dict: Dict,  # filepath → {alt, title, caption, description}
    post_id: int,
    site: str = "yoldaolmak",
) -> Dict:
    """Upload multiple processed images and attach to post

    Args:
        image_files: list of WebP file paths
        metadata_dict: metadata per file
        post_id: target WordPress post ID
        site: site name (yoldaolmak, gezievreni, etc)

    Returns:
        dict with results
    """
    uploader = YOWordPressUploader(site=site)
    results = {
        "site": site,
        "post_id": post_id,
        "uploaded": [],
        "failed": [],
    }

    for i, file_path in enumerate(image_files, 1):
        print(f"\n[{i}/{len(image_files)}] Uploading: {Path(file_path).name}")

        meta = metadata_dict.get(file_path, {})
        if not meta:
            print(f"  ✗ No metadata found")
            results["failed"].append({
                "file": file_path,
                "error": "No metadata",
            })
            continue

        # Upload media
        upload_result = uploader.upload_media(
            file_path=file_path,
            title=meta.get("title", "Image"),
            alt_text=meta.get("alt", ""),
            description=meta.get("description", ""),
            caption=meta.get("caption", ""),
        )

        if not upload_result["success"]:
            print(f"  ✗ Upload failed: {upload_result['error']}")
            results["failed"].append({
                "file": file_path,
                "error": upload_result["error"],
            })
            continue

        media_id = upload_result["media_id"]
        print(f"  ✓ Uploaded: ID {media_id}")

        # Attach to post
        attach_result = uploader.attach_to_post(
            media_id=media_id,
            post_id=post_id,
        )

        if attach_result["success"]:
            print(f"  ✓ Attached to post {post_id}")
            results["uploaded"].append({
                "file": Path(file_path).name,
                "media_id": media_id,
                "post_id": post_id,
                "title": meta.get("title"),
                "alt": meta.get("alt"),
                "caption": meta.get("caption"),
                "heading": meta.get("heading"),
                "heading_level": meta.get("heading_level"),
                "url": upload_result.get("url", ""),
            })
        else:
            print(f"  ⚠️  Upload OK but attach failed: {attach_result['error']}")
            results["uploaded"].append({
                "file": Path(file_path).name,
                "media_id": media_id,
                "attach_error": attach_result["error"],
                "caption": meta.get("caption"),
                "title": meta.get("title"),
                "alt": meta.get("alt"),
                "heading": meta.get("heading"),
                "heading_level": meta.get("heading_level"),
                "url": upload_result.get("url", ""),
            })

    content_result = uploader.append_media_to_post_content(post_id, results["uploaded"])
    results["content_update"] = content_result
    if content_result.get("success") and content_result.get("updated"):
        print(f"\n✓ Post content updated: {content_result.get('inserted', 0)} image block added")
    elif not content_result.get("success"):
        print(f"\n⚠️  Post content update failed: {content_result.get('error', 'unknown error')}")

    return results


if __name__ == "__main__":
    # Test auth
    uploader = YOWordPressUploader(site="yoldaolmak")
    print(f"✓ Connected to {uploader.base_url}")
    print(f"  User: {uploader.user}")
    print("\nReady for image uploads")

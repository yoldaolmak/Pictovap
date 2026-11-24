"""CMS upload type remains correct on minimal systems without MIME tables."""

from unittest.mock import patch

from pictovap.utils.media_type import upload_content_type


def test_webp_without_system_mime_database():
    with patch("pictovap.utils.media_type.mimetypes.guess_type", return_value=(None, None)):
        assert upload_content_type("picture.webp") == "image/webp"
        assert upload_content_type("PICTURE.WEBP") == "image/webp"
        assert upload_content_type("unknown.bin") == "application/octet-stream"

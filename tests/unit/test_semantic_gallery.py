import pytest
import json
from unittest.mock import MagicMock, patch
from pictova.main import search_semantic_assets
from pictova.services.wordpress import YOWordPressUploader

@patch('sqlite3.connect')
@patch('pictova.main.get_visual_memory_db_path')
def test_dynamic_sql_filters_portrait_person(mock_get_db_path, mock_connect):
    conn_mock = MagicMock()
    mock_connect.return_value = conn_mock
    mock_db_path = MagicMock()
    mock_db_path.exists.return_value = True
    mock_get_db_path.return_value = mock_db_path
    
    search_semantic_assets("Akyaka", count=2, content_filter="dikey, kemal kaya")
    
    execute_calls = conn_mock.execute.call_args_list
    assert len(execute_calls) > 0
    
    # Check the first query (FTS)
    sql, params = execute_calls[0][0]
    assert "a.orientation = 'portrait'" in sql
    assert "(a.ai_keywords_json LIKE ? OR a.description LIKE ? OR a.people_json LIKE ?)" in sql
    assert "%kemal kaya%" in params

@patch('pictova.utils.config.load_project_env')
@patch.object(YOWordPressUploader, 'fetch_post_context')
@patch('requests.Session.post')
def test_append_media_to_post_content_creates_gallery(
    mock_post,
    mock_fetch,
    mock_env,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("PICTOVA_POST_MANIFEST_DIR", str(tmp_path / "manifests"))
    wp = YOWordPressUploader()

    base_post = {
        "content_raw": "<h2>Akyaka Nerede</h2>\n<p>Some text</p>"
    }

    def fetch_after_write(*_args, **_kwargs):
        if mock_post.call_args:
            return {
                "content_raw": mock_post.call_args.kwargs["json"]["content"],
                "modified": "2026-06-28T16:00:00",
            }
        return base_post

    mock_fetch.side_effect = fetch_after_write
    
    media_items = [
        {"media_id": 1, "url": "http://example.com/url1.jpg", "heading": "Akyaka Nerede", "heading_level": 2},
        {"media_id": 2, "url": "http://example.com/url2.jpg", "heading": "Akyaka Nerede", "heading_level": 2},
    ]
    
    mock_post.return_value.raise_for_status = MagicMock()
    
    result = wp.append_media_to_post_content(123, media_items)
    
    assert result["success"] is True
    post_call = mock_post.call_args
    assert post_call is not None
    
    new_content = post_call.kwargs.get("json", {}).get("content", "")
    
    assert "<!-- wp:gallery" in new_content
    assert "wp-image-1" in new_content
    assert "wp-image-2" in new_content
    assert "<!-- /wp:gallery -->" in new_content
    assert "<!-- wp:image" in new_content
    with open(result["manifest_path"], "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["expected_media_ids"] == [1, 2]

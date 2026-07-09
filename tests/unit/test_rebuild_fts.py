from scripts.rebuild_fts import _build_doc


def test_build_doc_indexes_apple_ml_labels():
    row = {
        "city": "",
        "state_province": "İzmir",
        "sub_admin_area": "",
        "country": "Türkiye",
        "location": "",
        "scene": "",
        "activity": "",
        "summary": "",
        "title": "",
        "description": "",
        "ai_keywords_json": "[]",
        "metadata_keywords_json": "[]",
        "apple_labels_json": '["Lighthouse", "Village"]',
    }

    document = _build_doc(row)

    assert "Lighthouse" in document
    assert "Village" in document

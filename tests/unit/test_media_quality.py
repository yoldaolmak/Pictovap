from pictovap.core.media_quality import validate_metadata


def _metadata(source: str):
    return {
        "title": "Harbor at sunrise",
        "alt": "Fishing boats at sunrise",
        "caption": "Fishing boats rest in the harbor at sunrise.",
        "description": "Fishing boats rest in a quiet harbor at sunrise.",
        "_source": source,
        "embedded": True,
        "_confidence": 0.9,
        "_evidence": ["boats in harbor"],
        "_warnings": [],
    }


def test_semantic_model_source_is_provider_neutral():
    errors = validate_metadata(_metadata("semantic-model"), {})

    assert "metadata source is not semantic model output" not in errors


def test_unrecognized_metadata_source_is_rejected():
    errors = validate_metadata(_metadata("fallback"), {})

    assert "metadata source is not semantic model output" in errors

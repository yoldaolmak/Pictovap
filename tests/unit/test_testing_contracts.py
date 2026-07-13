from __future__ import annotations

import pytest
from PIL import Image

from pictovap.providers.local import LocalFolderSource
from pictovap.testing import (
    ContractViolation,
    assert_cms_adapter_contract,
    assert_image_source_contract,
    sample_placement,
    validate_candidates,
    validate_placement_result,
)


def _candidate():
    return {
        "id": "one",
        "filename": "one.jpg",
        "provider": "fixture",
        "source_type": "api",
        "local_path": None,
        "source_url": "https://images.example/one.jpg",
        "license": "cc0",
        "attribution": None,
        "keywords": ["fixture"],
        "width": 1600,
        "height": 1000,
    }


class FixtureProvider:
    def search_candidates(self, query, count):
        return [_candidate()]


class FixtureCMS:
    def place(self, placement):
        return {"placed": [placement.article_id], "failed": [], "warnings": []}


def test_image_source_contract_returns_validated_candidates():
    candidates = assert_image_source_contract(FixtureProvider(), count=1)
    assert candidates[0]["provider"] == "fixture"


def test_contract_kit_accepts_real_local_provider(tmp_path):
    Image.new("RGB", (1600, 1000), color="blue").save(tmp_path / "harbor.jpg")

    candidates = assert_image_source_contract(
        LocalFolderSource(directory=str(tmp_path)),
        query="harbor",
        count=1,
    )

    assert candidates[0]["provider"] == "local"


def test_candidate_validation_reports_exact_missing_fields():
    candidate = _candidate()
    del candidate["license"]

    with pytest.raises(ContractViolation, match="license"):
        validate_candidates([candidate])


def test_candidate_validation_enforces_requested_maximum():
    with pytest.raises(ContractViolation, match="more than 1"):
        validate_candidates([_candidate(), _candidate()], maximum=1)


def test_candidate_validation_requires_json_safe_metadata():
    candidate = _candidate()
    candidate["metadata"] = object()

    with pytest.raises(ContractViolation, match="JSON-serializable"):
        validate_candidates([candidate])


def test_image_source_contract_rejects_negative_count():
    with pytest.raises(ContractViolation, match="non-negative"):
        assert_image_source_contract(FixtureProvider(), count=-1)


def test_cms_contract_uses_sample_placement():
    result = assert_cms_adapter_contract(FixtureCMS())
    assert result["placed"] == ["contract-test"]


def test_sample_placement_is_minimal_but_complete():
    placement = sample_placement()
    assert placement.article_id == "contract-test"
    assert placement.placements[0].slot_id == "featured"


@pytest.mark.parametrize("field", ["placed", "failed", "warnings"])
def test_placement_validation_requires_list_fields(field):
    result = {"placed": [], "failed": [], "warnings": []}
    result[field] = "wrong"

    with pytest.raises(ContractViolation, match=field):
        validate_placement_result(result)


def test_contract_helpers_reject_objects_without_protocol_methods():
    with pytest.raises(ContractViolation, match="ImageSourceAdapter"):
        assert_image_source_contract(object())
    with pytest.raises(ContractViolation, match="CMSAdapter"):
        assert_cms_adapter_contract(object())

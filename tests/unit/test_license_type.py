import pytest

from pictovap.core.primitives import LicenseType, ProvenancePack


def test_common_license_aliases_are_normalized():
    assert LicenseType.from_string("CC0 1.0") is LicenseType.CC0
    assert LicenseType.from_string("CC-BY-SA-4.0") is LicenseType.CC_BY_SA
    assert LicenseType.from_string("unexpected") is LicenseType.UNKNOWN


def test_provider_license_values_are_preserved():
    assert LicenseType.from_string("owned") is LicenseType.OWNED
    assert LicenseType.from_string("pexels") is LicenseType.PEXELS


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        ("by", LicenseType.CC_BY),
        ("by-sa", LicenseType.CC_BY_SA),
        ("by-nc", LicenseType.CC_BY_NC),
        ("by-nc-sa", LicenseType.CC_BY_NC_SA),
        ("by-nd", LicenseType.CC_BY_ND),
        ("by-nc-nd", LicenseType.CC_BY_NC_ND),
        ("cc0", LicenseType.CC0),
        ("pdm", LicenseType.PDM),
        ("sampling+", LicenseType.SAMPLING_PLUS),
        ("nc-sampling+", LicenseType.NC_SAMPLING_PLUS),
    ],
)
def test_openverse_license_values_are_preserved(raw_value, expected):
    assert LicenseType.from_string(raw_value) is expected


def test_provenance_pack_serializes_license_enum_value():
    pack = ProvenancePack(image_id="image", license_status="unsplash")
    assert pack.license_status is LicenseType.UNSPLASH
    assert pack.to_dict()["license_status"] == "unsplash"

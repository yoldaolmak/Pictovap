from pictovap.core.primitives import LicenseType, ProvenancePack


def test_common_license_aliases_are_normalized():
    assert LicenseType.from_string("CC0 1.0") is LicenseType.CC0
    assert LicenseType.from_string("CC-BY-SA-4.0") is LicenseType.CC_BY_SA
    assert LicenseType.from_string("unexpected") is LicenseType.UNKNOWN


def test_provenance_pack_serializes_license_enum_value():
    pack = ProvenancePack(image_id="image", license_status="unsplash")
    assert pack.license_status is LicenseType.UNSPLASH
    assert pack.to_dict()["license_status"] == "unsplash"
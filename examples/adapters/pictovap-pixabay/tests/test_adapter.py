from pictovap_pixabay import PixabaySource
from pictovap.testing import assert_image_source_contract


def test_adapter_contract_without_credentials():
    adapter = PixabaySource()
    assert assert_image_source_contract(adapter) == []

from pictovap_wikimedia import WikimediaSource
from pictovap.testing import assert_image_source_contract


def test_adapter_contract_without_credentials():
    adapter = WikimediaSource()
    assert assert_image_source_contract(adapter) == []

import pytest
import respx

from datalab_api import DatalabClient


def test_redirect_url(mocked_api, mocked_ui, fake_api_url, fake_ui_url):
    with pytest.warns(
        UserWarning,
        match="^Found API URL https://api.datalab.industries in HTML meta tag. Creating client with this URL instead.$",
    ):
        client = DatalabClient(fake_ui_url)

    assert mocked_ui["ui-redirect"].called
    assert mocked_api["info"].called
    assert mocked_api["info-blocks"].called
    assert client.datalab_api_url == fake_api_url


def test_sample_list(mocked_api, fake_api_url):
    with DatalabClient(fake_api_url) as client:
        assert mocked_api["api"].called
        assert mocked_api["info"].called
        assert mocked_api["info-blocks"].called

        samples = client.get_items(display=True)
        assert mocked_api["samples"].called
        assert len(samples)
        assert samples[0]["item_id"] == "test"

        sample = client.get_item("KUVEKJ", display=True)
        assert mocked_api["sample-KUVEKJ"].called
        assert sample["item_id"] == "KUVEKJ"


@respx.mock
def test_collection_get(fake_api_url, mocked_api):
    with DatalabClient("https://api.datalab.industries") as client:
        assert mocked_api["api"].called
        assert mocked_api["info"].called
        assert mocked_api["info-blocks"].called

        collection, children = client.get_collection("test_collection", display=True)
        assert mocked_api["collection-test_collection"].called

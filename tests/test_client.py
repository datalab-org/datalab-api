import pytest
import respx

from datalab_api import DatalabClient
from datalab_api._base import DatalabAPIError


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


def test_sample_operations(mocked_api, fake_api_url):
    with DatalabClient(fake_api_url) as client:
        assert mocked_api["api"].called
        assert mocked_api["info"].called
        assert mocked_api["info-blocks"].called

        client.authenticate()
        assert mocked_api["current_user"].called

        samples = client.get_items(display=True)
        assert mocked_api["samples"].called
        assert len(samples)
        assert samples[0]["item_id"] == "test"

        sample = client.get_item("KUVEKJ", display=True)
        assert mocked_api["sample-KUVEKJ"].called
        assert sample["item_id"] == "KUVEKJ"

        # Check that the full server error message is shown for a missing item
        with pytest.raises(
            DatalabAPIError,
            match="No matching items for match={'item_id': 'TEST'} with current authorization",
        ):
            client.get_item("TEST", display=True)
        assert mocked_api["sample-missing-TEST"].called

        with pytest.raises(DatalabAPIError, match="KeyError"):
            client.update_item(item_id="TEST", item_data={"name": "test"})
        assert mocked_api["bad-save"].called


@respx.mock
def test_collection_get(fake_api_url, mocked_api):
    with DatalabClient("https://api.datalab.industries") as client:
        assert mocked_api["api"].called
        assert mocked_api["info"].called
        assert mocked_api["info-blocks"].called

        collection, children = client.get_collection("test_collection", display=True)
        assert mocked_api["collection-test_collection"].called

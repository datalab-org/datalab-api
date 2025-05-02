import pytest
import respx
from httpx import Response

from datalab_api import DatalabClient


@respx.mock
def test_redirect_url(fake_ui_html, fake_info_json, fake_block_info_json):
    fake_ui = respx.get("https://ui.datalab.industries").mock(
        return_value=Response(200, content=fake_ui_html)
    )
    fake_info_api = respx.get("https://api.datalab.industries/info").mock(
        return_value=Response(200, json=fake_info_json)
    )
    fake_block_info_api = respx.get("https://api.datalab.industries/info/blocks").mock(
        return_value=Response(200, json=fake_block_info_json)
    )
    with pytest.warns(
        UserWarning,
        match="^Found API URL https://api.datalab.industries in HTML meta tag. Creating client with this URL instead.$",
    ):
        client = DatalabClient("https://ui.datalab.industries")
    assert fake_ui.called
    assert fake_info_api.called
    assert fake_block_info_api.called
    assert client.datalab_api_url == "https://api.datalab.industries"


@respx.mock
def test_sample_list(fake_samples_json, fake_info_json, fake_sample_json, fake_block_info_json):
    fake_api = respx.get("https://api.datalab.industries/").mock(
        return_value=Response(200, content="<!doctype html></html>")
    )
    fake_samples_api = respx.get("https://api.datalab.industries/samples").mock(
        return_value=Response(200, json=fake_samples_json)
    )
    fake_info_api = respx.get("https://api.datalab.industries/info").mock(
        return_value=Response(200, json=fake_info_json)
    )
    fake_block_info_api = respx.get("https://api.datalab.industries/info/blocks").mock(
        return_value=Response(200, json=fake_block_info_json)
    )
    fake_item_api = respx.get("https://api.datalab.industries/get-item-data/KUVEKJ").mock(
        return_value=Response(200, json=fake_sample_json)
    )
    with DatalabClient("https://api.datalab.industries") as client:
        samples = client.get_items(display=True)
        assert fake_samples_api.called
        assert fake_api.called
        assert fake_info_api.called
        assert fake_block_info_api.called
        assert len(samples)
        assert samples[0]["item_id"] == "test"
        sample = client.get_item("KUVEKJ", display=True)
        assert fake_item_api.called
        assert sample["item_id"] == "KUVEKJ"


@respx.mock
def test_collection_get(fake_info_json, fake_block_info_json, fake_collection_json):
    fake_api = respx.get("https://api.datalab.industries/").mock(
        return_value=Response(200, content="<!doctype html></html>")
    )
    fake_info_api = respx.get("https://api.datalab.industries/info").mock(
        return_value=Response(200, json=fake_info_json)
    )
    fake_block_info_api = respx.get("https://api.datalab.industries/info/blocks").mock(
        return_value=Response(200, json=fake_block_info_json)
    )

    fake_collection_api = respx.get(
        "https://api.datalab.industries/collections/test_collection"
    ).mock(return_value=Response(200, json=fake_collection_json))

    with DatalabClient("https://api.datalab.industries") as client:
        collection, children = client.get_collection("test_collection")
        assert fake_api.called
        assert fake_info_api.called
        assert fake_block_info_api.called
        assert fake_collection_api.called

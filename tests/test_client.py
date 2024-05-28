import pytest
import respx
from datalab_api import DatalabClient
from httpx import Response


@respx.mock
def test_redirect_url(fake_ui_html, fake_info_json):
    fake_ui = respx.get("https://ui.datalab.industries").mock(
        return_value=Response(200, content=fake_ui_html)
    )
    fake_api = respx.get("https://api.datalab.industries/info").mock(
        return_value=Response(200, json=fake_info_json)
    )
    with pytest.warns(
        UserWarning,
        match="^Found API URL https://api.datalab.industries in HTML meta tag. Creating client with this URL instead.$",
    ):
        client = DatalabClient("https://ui.datalab.industries")
    assert fake_ui.called
    assert fake_api.called
    assert client.datalab_api_url == "https://api.datalab.industries"

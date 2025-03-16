import json
import os

from pytest import fixture


@fixture
def fake_samples_json():
    """Returns a mocked JSON response for the API /samples endpoint."""
    return json.loads(
        '{"status": "success", "samples": [{"chemform": "NaCoO2", "collections": [], "creators": [{"contact_email": null, "display_name": "A. Nother"}], "date": "2025-02-25T14:33:00", "item_id": "test", "name": "", "nblocks": 0, "refcode": "demo:test", "type": "samples"}]}'
    )


@fixture
def fake_ui_html():
    """Returns a mocked HTML response from the Datalab UI that includes a metadata tag for a fake API URL."""
    return """<!doctype html>
<html lang="">
  <head>
    <meta charset="utf-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width,initial-scale=1.0" />
    <link rel="icon" href="/favicon.ico" />
    <title>datalab</title>
    <script
      type="text/javascript"
      src="https://cdn.bokeh.org/bokeh/release/bokeh-2.4.3.min.js"
      crossorigin="anonymous"
    ></script>
    <script
      type="text/javascript"
      src="https://cdn.bokeh.org/bokeh/release/bokeh-widgets-2.4.3.min.js"
      crossorigin="anonymous"
    ></script>
  <meta name="x_datalab_api_url" content="https://api.datalab.industries"><script defer src="/js/chunk-vendors.js"></script><script defer src="/js/app.js"></script></head>
  <body>
    <noscript>
      <strong
        >We're sorry but datalab doesn't work properly without
        JavaScript enabled. Please enable it to continue.</strong
      >
    </noscript>
    <div id="app"></div>
    <!-- built files will be auto injected -->
  </body>
</html>"""


@fixture
def fake_info_json():
    """Returns a mocked JSON response for the API /info endpoint."""

    return json.loads(
        '{"data":{"attributes":{"api_version":"0.1.0","available_api_versions":["0.1.0"],"datamodel_version":"0.3.2","homepage":null,"identifier_prefix":"test","issue_tracker":null,"maintainer":null,"query":"","server_version":"0.3.2","source_repository":null,"timestamp":"2024-05-28T10:13:26.898213"},"id":"/","type":"info"},"links":{"self":"http://localhost:5001/info"},"meta":{"api_version":"0.1.0","available_api_versions":["0.1.0"],"datamodel_version":"0.3.2","query":"","server_version":"0.3.2","timestamp":"2024-05-28T10:13:26.898346"}}'
    )


@fixture
def fake_block_info_json():
    """Returns a mocked JSON response for the API /info endpoint."""

    return json.loads(
        '{"data":[{"attributes":{"accepted_file_extensions": [], "description":"Add a rich text comment to the document","name": "Comment", "version": "0.1.0"}, "id": "comment", "type": "block_type"}]}'
    )


@fixture(scope="session")
def fake_api_key():
    """Returns a fake API key."""
    return 24 * "0"


@fixture(scope="session", autouse=True)
def set_fake_api_key(fake_api_key):
    """Sets a fake API key in the env, expecting a datalab instance with identifier prefix 'test'.

    Will reset the old env var if present on clean exit.

    """
    old_value = os.environ.get("TEST_DATALAB_API_KEY")
    try:
        os.environ["TEST_DATALAB_API_KEY"] = fake_api_key
        yield

    finally:
        if old_value:
            os.environ["TEST_DATALAB_API_KEY"] = old_value
        else:
            del os.environ["TEST_DATALAB_API_KEY"]

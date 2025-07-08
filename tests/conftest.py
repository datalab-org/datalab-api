import json
import os

import respx
from httpx import Response
from pytest import fixture


@fixture
def fake_api_url():
    return "https://api.datalab.industries"


@fixture
def fake_ui_url():
    return "https://ui.datalab.industries"


@fixture
def mocked_api(
    fake_api_url,
    fake_user_json,
    fake_info_json,
    fake_block_info_json,
    fake_samples_json,
    fake_sample_json,
    fake_collection_json,
):
    with respx.mock(base_url=fake_api_url, assert_all_called=False) as respx_mock:
        fake_api = respx_mock.get("/", name="api")
        fake_api.return_value = Response(200, content="<!doctype html></html>")

        fake_authentication = respx_mock.get("/get-current-user", name="current_user")
        fake_authentication.return_value = Response(200, json=fake_user_json)

        fake_info_api = respx_mock.get("/info", name="info")
        fake_info_api.return_value = Response(200, json=fake_info_json)

        fake_block_info_api = respx_mock.get("/info/blocks", name="info-blocks")
        fake_block_info_api.return_value = Response(200, json=fake_block_info_json)

        fake_samples_api = respx_mock.get("/samples", name="samples")
        fake_samples_api.return_value = Response(200, json=fake_samples_json)

        fake_item_api = respx_mock.get("/get-item-data/KUVEKJ", name="sample-KUVEKJ")
        fake_item_api.return_value = Response(200, json=fake_sample_json)

        fake_collection_api = respx_mock.get(
            "/collections/test_collection", name="collection-test_collection"
        )
        fake_collection_api.return_value = Response(200, json=fake_collection_json)

        yield respx_mock


@fixture
def mocked_ui(fake_ui_url, fake_ui_html):
    with respx.mock(base_url=fake_ui_url, assert_all_called=False) as respx_mock:
        fake_ui = respx_mock.get("/", name="ui-redirect")
        fake_ui.return_value = Response(200, content=fake_ui_html)

        yield respx_mock


@fixture
def fake_samples_json():
    """Returns a mocked JSON response for the API /samples endpoint."""
    return json.loads(
        '{"status": "success", "samples": [{"chemform": "NaCoO2", "collections": [], "creators": [{"contact_email": null, "display_name": "A. Nother"}], "date": "2025-02-25T14:33:00", "item_id": "test", "name": "", "nblocks": 0, "refcode": "demo:test", "type": "samples"}]}'
    )


@fixture
def fake_collection_json():
    """Returns a mocked JSON response for the API /samples endpoint."""
    return json.loads(
        '{"child_items":[{"chemform":null,"creators":[{"display_name":"Matthew Evans"}],"date":"2024-11-28T13:01:00","item_id":"KRMBTQ","name":"","nblocks":0,"nfiles":0,"refcode":"test:KRMBTQ","type":"samples"},{"chemform":null,"creators":[{"display_name":"Matthew Evans"},{"display_name":"Greymon (bot)"}],"date":"2024-11-06T13:46:00","item_id":"RCLPGC","name":"","nblocks":0,"nfiles":0,"refcode":"test:RCLPGC","type":"samples"}],"collection_id":"test","data":{"blocks_obj":{},"collection_id":"test","creator_ids":["6659fe2a7024bf196a90c933"],"creators":[{"display_name":"Matthew Evans","immutable_id":"6659fe2a7024bf196a90c933"}],"description":null,"display_order":[],"immutable_id":"672be2ddb2dcbefd7f9b4342","last_modified":"2024-11-06T21:42:53.974000+00:00","num_items":2,"relationships":null,"title":null,"type":"collections"},"status":"success"}'
    )


@fixture
def fake_sample_json():
    """Returns a mocked JSON response for the API /get-item-data/<sample_id> endpoint."""
    return json.loads("""
            {
  "child_items": [],
  "files_data": {
    "6808d81e9e49c952b04da54e": {
      "blocks": [],
      "creator_ids": [
        "6574f788aabb227db8d1b14e"
      ],
      "creators": null,
      "extension": ".asc",
      "immutable_id": "6808d81e9e49c952b04da54e",
      "is_live": false,
      "item_ids": [
        "KUVEKJ"
      ],
      "last_modified": "2025-04-23T12:07:58.652000+00:00",
      "last_modified_remote": null,
      "location": "/app/files/6808d81e9e49c952b04da54e/20230426_143716_Scan_5s_1to110.asc",
      "metadata": {},
      "name": "20230426_143716_Scan_5s_1to110.asc",
      "original_name": "20230426 143716 Scan 5s 1to110.asc",
      "relationships": null,
      "representation": null,
      "revision": 1,
      "revisions": null,
      "size": 5777461,
      "source": "uploaded",
      "source_path": null,
      "source_server_name": null,
      "time_added": "2025-04-23T12:07:58.652000+00:00",
      "type": "files",
      "url_path": null
    }
  },
  "item_data": {
    "blocks_obj": {
      "otsvedqi7d0bzaf": {
        "block_id": "otsvedqi7d0bzaf",
        "blocktype": "ms",
        "collection_id": null,
        "file_id": "6808d81e9e49c952b04da54e",
        "item_id": "KUVEKJ",
        "title": "Mass spectrometry"
      }
    },
    "chemform": null,
    "collections": [],
    "creator_ids": [
      "6574f788aabb227db8d1b14e"
    ],
    "creators": [
      {
        "contact_email": null,
        "display_name": "Matthew Evans",
        "immutable_id": "6574f788aabb227db8d1b14e"
      }
    ],
    "date": "2025-04-23T12:07:00+00:00",
    "description": null,
    "display_order": [
      "otsvedqi7d0bzaf"
    ],
    "file_ObjectIds": [
      "6808d81e9e49c952b04da54e"
    ],
    "files": [
      {
        "blocks": [],
        "creator_ids": [
          "6574f788aabb227db8d1b14e"
        ],
        "creators": null,
        "extension": ".asc",
        "immutable_id": "6808d81e9e49c952b04da54e",
        "is_live": false,
        "item_ids": [
          "KUVEKJ"
        ],
        "last_modified": "2025-04-23T12:07:58.652000+00:00",
        "last_modified_remote": null,
        "location": "/app/files/6808d81e9e49c952b04da54e/20230426_143716_Scan_5s_1to110.asc",
        "metadata": {},
        "name": "20230426_143716_Scan_5s_1to110.asc",
        "original_name": "20230426 143716 Scan 5s 1to110.asc",
        "relationships": null,
        "representation": null,
        "revision": 1,
        "revisions": null,
        "size": 5777461,
        "source": "uploaded",
        "source_path": null,
        "source_server_name": null,
        "time_added": "2025-04-23T12:07:58.652000+00:00",
        "type": "files",
        "url_path": null
      }
    ],
    "immutable_id": "6808d7fb47ccfd57b44da54e",
    "item_id": "KUVEKJ",
    "last_modified": null,
    "name": "",
    "refcode": "demo:KUVEKJ",
    "relationships": [],
    "revision": 1,
    "revisions": null,
    "synthesis_constituents": [],
    "synthesis_description": null,
    "type": "samples"
  },
  "item_id": "KUVEKJ",
  "parent_items": [],
  "status": "success"
}
""")


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


@fixture
def fake_user_json():
    """Returns a mocked JSON response from the /get-current-user endpoint."""

    return json.loads(
        """
{
  "account_status": "active",
  "contact_email": null,
  "display_name": "Jane Doe",
  "identities": [
    {
      "display_name": "Jane Doe",
      "identifier": "1111111",
      "identity_type": "github",
      "name": "jane-doe",
      "verified": true
    }
  ],
  "immutable_id": "6574f788aabb227db8d1b14e",
  "last_modified": null,
  "managers": null,
  "relationships": null,
  "role": "user",
  "type": "people"
}"""
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

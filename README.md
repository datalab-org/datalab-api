# *datalab* Python API

A simple Python API that can interact with [datalab](https://github.com/the-grey-group/datalab) instances.

The idea here is to provide a set of utility functions and models for manipulating samples, cells, users and metadata associated with datalab entries.

This API may not expose all the functionality available in a given datalab instance, and the idea would be that this package can support multiple versions of the underlying [datalab REST API](https://the-datalab.readthedocs.io/en/latest/rest_api/).
This means that the API is primarily *functional* in nature, as opposed to object-oriented, since datalab instances are free to use their own custom data models.
The available schemas are reported as instance metadata and in the future object-oriented models may be able to be genereated directly in the client (so e.g., the returned data would be Python objects like `Sample` rather than JSON data).

## Installation

The API can be used by installing this repository with `pip`, ideally in a fresh Python environment (created using e.g., conda, virtualenv or other related tools -- if you're not sure about this, ask).

```shell
pip install git+https://github.com/ml-evs/datalab-python-api
```

## Usage

This package implemented some basic functionality for displaying and manipulating entries:

```python
from pydatalab.api import DatalabClient

with DatalabClient("https://api.public.odbx.science", api_key=<MY_API_KEY>) as client:
    item = client.get_items(item_id="test", show=True)

    item_refcode = item["refcode"]
    file_id, response = client.upload_file(path="my_echem_data.mpr", refcode=item_refcode)

    block_id, response = client.create_block(blocktype="echem", item=item_refcode, file=file_id)

    # With the Bokeh optional dependency installed:
    block, response = client.get_block(block_id)
    block.show()
```

### Authentication

Currently the only supported authentication method is via an API key.
You can generate one for your account for a given datalab instance by visiting the `/get-api-key` endpoint of your chosen instance, or, if using a recent version of datalab, by visiting your account settings in the browser.

This API key can then be passed directly to the API client, or can be set via the environment variable `DATALAB_API_KEY`.
To suport the use case of needing to interact with multiple datalab instances, the client will also check prefixed environment variables that use the [`IDENTIFIER_PREFIX` of the chosen datalab instance](https://the-datalab.readthedocs.io/en/latest/config/#mandatory-settings), e.g., `GREY_DATALAB_API_KEY` or `PUBLIC_DATALAB_API_KEY`.
Only keys that match will be read (e.g., other environment variables starting with `PUBLIC_` will be ignored, when connecting to the [public demo datalab](https://public.datalab.odbx.science).

<!-- This file was edited with the assistance of an AI model and requires human review from the contributor. -->
# <div align="center"><i>datalab</i> Python API</div>

<div align="center">
<a href="https://pypi.org/datalab-api"><img src="https://img.shields.io/pypi/v/datalab-api?logo=pypi&label=PyPI" /></a>
<a href="https://github.com/datalab-org/datalab-api?tab=MIT-1-ov-file#MIT-1-ov-file"><img src="https://img.shields.io/github/license/datalab-org/datalab-api" /></a>
</div>

<div align="center">
<a href="https://datalab-python-api.readthedocs.io/en/stable/?badge=stable"><img src="https://img.shields.io/readthedocs/datalab-python-api?logo=readthedocs" /></a>
<a href="https://pypi.org/datalab-api"><img src="https://img.shields.io/pypi/pyversions/datalab-api?logo=python&label=Python%20versions" /></a>
</div>

A simple Python API that can interact with [*datalab*](https://github.com/datalab-org/datalab) instances.

The idea here is to provide a set of utility functions and models for manipulating samples, cells, inventory, files, users and metadata associated with *datalab* entries in an automated way.

This API may not expose all the functionality available in a given *datalab* instance, and the idea would be that this package can support multiple versions of the underlying [*datalab* REST API](https://docs.datalab-org.io).
By default, the API is *functional* in nature, returning JSON data as Python dictionaries, since *datalab* instances are free to use their own custom data models.
Optionally, the client can also generate object-oriented [pydantic](https://docs.pydantic.dev) models directly from the schemas reported by an instance (including any custom item types), so that the returned data are Python objects like `Sample` (see [Object-oriented models](#object-oriented-models) below).

The issue tracker here will be used to track development of features, as well as bug reports.
If you have any suggestions or feedback, please post it there.

## Installation

The API can be used by installing this repository with `pip`, ideally in a fresh Python 3.11+ environment (created using e.g., conda, virtualenv or other related tools -- if you're not sure about this, ask).

Either from PyPI, for the latest released version:

```shell
pip install datalab-api
```

or for the latest development version from GitHub:

```shell
git clone git@github.com:datalab-org/datalab-api
cd datalab-api
pip install .
```

## Usage

Example usage as a Jupyter notebook can be found in the `examples` directory or
in the [online documentation](https://api-docs.datalab-org.io), as
well as the full [API
documentation](https://api-docs.datalab-org.io/en/stable/reference/).

### Authentication

Currently the only supported authentication method is via an API key.
You can generate one for your account for a given *datalab* instance by visiting the `/get-api-key` endpoint of your chosen instance, or, if using a recent version of *datalab*, by visiting your account settings in the browser.

This API key can be set via the environment variable `DATALAB_API_KEY`.
To suport the use case of needing to interact with multiple datalab instances, the client will also check prefixed environment variables that use the [`IDENTIFIER_PREFIX` of the chosen datalab instance](https://docs.datalab-org.io/en/stable/config/#mandatory-settings), e.g., `GREY_DATALAB_API_KEY` or `PUBLIC_DATALAB_API_KEY`.
Only keys that match will be read (e.g., other environment variables starting with `PUBLIC_` will be ignored, when connecting to the [public demo datalab](https://demo.datalab-org.io)).

### Python API

This package implements basic functionality for displaying and manipulating entries:

```python
from datalab_api import DatalabClient

with DatalabClient("https://demo-api.datalab-org.io") as client:
    # List all items of a given type
    items = client.get_items()

    # Get more info on a particular item
    item = client.get_item(item_id="test")

    # Upload a file to an item
    file_response = client.upload_file(filepath="my_echem_data.mpr", item_id="test")
```

### Object-oriented models

Each *datalab* instance reports the JSON schemas of its item types at its `/info/types` endpoint.
Since *datalab* v0.8.0, these include any **custom item types** registered by the deployment, which are namespaced with a leading underscore (e.g., `_my_samples`).
The client can build [pydantic](https://docs.pydantic.dev) models from these schemas, which are fetched on first access to `client.models`:

```python
from datalab_api import DatalabClient

with DatalabClient("https://demo-api.datalab-org.io") as client:
    print(client.models)
    # ItemModels('samples': Sample, 'cells': Cell, ..., '_my_samples': MySample)

    Sample = client.models.Sample  # or client.models["samples"]
    MySample = client.models["_my_samples"]  # or client.models.MySample, from the schema title

    # Validated locally, e.g., against the field types, enums and ID patterns of the schema
    sample = MySample(name="My sample", chemform="NaCl", drying_time=2.5)

    # Create it on the server (with a generated ID, as no `item_id` was given)
    sample.create(collection_ids=["my-collection"])
    print(sample.item_id, sample.refcode)

    # Modify the item and send *only* the changed fields back to the server
    sample.synthesis_constituents.append({"item": {"name": "NaCl"}, "quantity": 1.0})
    sample.description = "Dried at 80 °C"
    sample.save()

    # Reload from the server, or attach files and blocks
    sample.refresh()
    sample.upload_file("my_xrd_data.xy")
    sample.add_block("xrd", file_ids=sample.files[0].immutable_id)
```

Custom types subclass the built-in model that they extend (so `isinstance(sample, Sample)` holds for a `Sample`-derived custom type), and every item model subclasses `datalab_api.models.DatalabItem`.
The metadata served for each type are available as class attributes (`item_type`, `base_type`, `hidden_fields`, `ui_color`), and the original schema as `datalab_schema`.
Any fields returned by the server that are not in the schema (e.g., `nblocks` in item summaries) are retained, and fields can also be accessed by key (`sample["item_id"]`) for compatibility with the dictionary-based API.

To have the existing item methods (`get_item`, `get_items`, `search_items` and `create_item`) return model instances instead of dictionaries, pass `use_models=True` to the client, or `as_model=True` to an individual call:

```python
with DatalabClient("https://demo-api.datalab-org.io", use_models=True) as client:
    sample = client.get_item("my-sample")
    sample.name = "A new name"
    sample.save()

    # Summaries are also returned as models, but not all fields are populated
    samples = client.get_items()
```

Models can also be built without a client, e.g., from a saved copy of an `/info/types` response:

```python
import json
from datalab_api.models import build_item_models

models = build_item_models(json.load(open("info_types.json")))
```

Note that the generated models are a client-side convenience: the server remains the source of truth and performs its own validation on create and save.
Validation of data returned by the server is lenient (optional fields may be `null`), and if an entry does not validate at all (e.g., legacy data) a warning is raised and the model is constructed without validation.

### Elevated (admin) permissions

By default a client can only see items its account owns or has been shared on.
Admins can opt in to datalab's super-user mode to read items belonging to other users, by passing `elevate_permissions`:

```python
with DatalabClient("https://demo-api.datalab-org.io", elevate_permissions=True) as client:
    # Finds the item even if it belongs to another user
    item = client.get_item(item_id="someone-elses-sample")
```

This sends datalab's `sudo=1` flag on read requests.
It requires the API key in use to belong to an **admin** account; for any other account the server ignores
it and normal permissions apply.

The attribute can also be toggled at any point in the client's lifetime:

```python
client.elevate_permissions = True
```

Note that objects created while elevated (e.g. uploaded files) are still recorded as belonging to the admin's own account, not the item owner's.

### Command-line interface (CLI)

There is also an EXPERIMENTAL CLI, exposed via the `datalab` command.
This CLI has many subcommands, which can be listed with `datalab help` or by entering the shell with just `datalab`.
For now, the CLI does not expose all of the functionality of the underlying API, and is mostly oriented on GET-focused operations.

```shell
$ datalab

╭──────────────────────────────────────────────────────────────────────────────────────────╮
│                                                                                          │
│               oooo              o8              o888             oooo                    │
│            ooooo888    ooooooo o888oo  ooooooo    888   ooooooo    888ooooo              │
│          888    888    ooooo888 888    ooooo888   888   ooooo888   888    888            │
│          888    888  888    888 888  888    888   888 888    888   888    888            │
│            88ooo888o  88ooo88 8o 888o 88ooo88 8o o888o 88ooo88 8o o888ooo88              │
│                                                                                          │
╰─ Copyright (c) 2020-2024 Matthew Evans, Joshua Bocarsly & the Datalab Development Team. ─╯

datalab > help

Documented commands (type help <topic>):
========================================
authenticate  get  info

Undocumented commands:
======================
exit  help  quit

datalab > help get

 Usage: [INSTANCE_URL] get [OPTIONS] ITEM_TYPE [INSTANCE_URL]

 Get a table of items of the given type.

╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────────────╮
│ *    item_type         TEXT            [default: None] [required]                                   │
│      instance_url      [INSTANCE_URL]  [default: None]                                              │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────╮
│ --page-limit        INTEGER  [default: 10]                                                          │
│ --api-key           TEXT     [default: None]                                                        │
│ --log-level         TEXT     [default: WARNING]                                                     │
│ --help                       Show this message and exit.                                            │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────╯

datalab > get samples demo-api.datalab-org.io --page-limit 2
                                                    /samples/
┏━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ type ┃ ID              ┃ refcode     ┃ name                           ┃ nblocks ┃ collections ┃ creators      ┃
┡━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│  C   │ test_api        │ grey:WHQFXG │                                │       0 │             │ Matthew Evans │
├──────┼─────────────────┼─────────────┼────────────────────────────────┼─────────┼─────────────┼───────────────┤
│  S   │ test12331231312 │ grey:GFSUQM │                                │       1 │             │ Matthew Evans │
└──────┴─────────────────┴─────────────┴────────────────────────────────┴─────────┴─────────────┴───────────────┘
```

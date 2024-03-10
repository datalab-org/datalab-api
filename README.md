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

### Authentication

Currently the only supported authentication method is via an API key.
You can generate one for your account for a given datalab instance by visiting the `/get-api-key` endpoint of your chosen instance, or, if using a recent version of datalab, by visiting your account settings in the browser.

This API key can then be passed directly to the API client, or can be set via the environment variable `DATALAB_API_KEY`.
To suport the use case of needing to interact with multiple datalab instances, the client will also check prefixed environment variables that use the [`IDENTIFIER_PREFIX` of the chosen datalab instance](https://the-datalab.readthedocs.io/en/latest/config/#mandatory-settings), e.g., `GREY_DATALAB_API_KEY` or `PUBLIC_DATALAB_API_KEY`.
Only keys that match will be read (e.g., other environment variables starting with `PUBLIC_` will be ignored, when connecting to the [public demo datalab](https://public.datalab.odbx.science).

### Python API

This package implemented some basic functionality for displaying and manipulating entries:

```python
from datalab_api import DatalabClient

with DatalabClient("https://api.public.odbx.science", api_key=<MY_API_KEY>) as client:
    
    # List all items of a given type
    items = client.get_items()

    # Get more info on a particular item
    item = client.get_item(item_id="test")

    # Upload a file to an item
    file_response = client.upload_file(path="my_echem_data.mpr", item_id="test")

```

### Command-line interface (CLI)

There is also a CLI, exposed via the `datalab` command.
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

datalab > get samples api.odbx.science --page-limit 2
                                                    /samples/
┏━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ type ┃ ID              ┃ refcode     ┃ name                           ┃ nblocks ┃ collections ┃ creators      ┃
┡━━━━━━╇━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│  C   │ test_api        │ grey:WHQFXG │                                │       0 │             │ Matthew Evans │
├──────┼─────────────────┼─────────────┼────────────────────────────────┼─────────┼─────────────┼───────────────┤
│  S   │ test12331231312 │ grey:GFSUQM │                                │       1 │             │ Matthew Evans │
└──────┴─────────────────┴─────────────┴────────────────────────────────┴─────────┴─────────────┴───────────────┘
```

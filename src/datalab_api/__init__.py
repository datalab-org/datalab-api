import os
from importlib.metadata import version
from typing import Any
from pathlib import Path
import logging

import httpx
from rich.logging import RichHandler

__version__ = version("datalab-api")

__all__ = ("__version__", "DatalabClient")

BAD_SERVER_VERSIONS = ((0, 2, 0),)
BAD_API_VERSIONS = ((0, 0, 0),)
MIN_API_VERSION = (0, 1, 0)


class DatalabClient:
    """A client for the Datalab API.

    The client will keep an HTTP session open for the duration of its life and thus is
    amenable for use as a context manager, e.g.,

    ```python
    with DatalabClient("https://public.api.odbx.science", api_key="my-api-key") as client:
        client.get_items()
    ```

    """

    def __init__(
        self, datalab_api_url: str, api_key: str | None = None, log_level: str = "WARNING"
    ):
        """Creates an authenticated client.

        Parameters:
            datalab_api_url: The URL of the Datalab API.
                TODO: If the URL of a datalab *UI* is provided, a request will be made to attempt to resolve the underlying API URL
                (e.g., `https://public.datalab.odbx.science` will 'redirect' to `https://public.api.odbx.science`).
            api_key: The API key to authenticate requests. If no key is provided, the client will attempt to load it from a series of environment variables.
            log_level: The logging level to use for the client. Defaults to "WARNING".

        """

        self.datalab_api_url = datalab_api_url
        if not self.datalab_api_url:
            raise ValueError("No Datalab API URL provided.")
        if not self.datalab_api_url.startswith("http"):
            self.datalab_api_url = f"https://{self.datalab_api_url}"
        self._api_key = api_key
        logging.basicConfig(level=log_level, handlers=[RichHandler()])
        self.log = logging.getLogger(__name__)

        self._http_client = httpx.Client
        self._headers: dict[str, str] = {}
        self._headers["User-Agent"] = f"Datalab Python API/{__version__}"

        info_json = self.get_info()

        self._datalab_api_versions: list[str] = info_json["data"]["attributes"][
            "available_api_versions"
        ]
        self._datalab_server_version: str = info_json["data"]["attributes"]["server_version"]
        self._datalab_instance_prefix: str | None = info_json["data"]["attributes"].get(
            "identifier_prefix"
        )

        self._set_api_key()

    def get_info(self) -> dict[str, Any]:
        """Fetch metadata associated with this datalab instance.

        Returns:
            dict: The JSON response from the `/info` endpoint of the Datalab API.

        """
        with self._http_client(headers=self._headers) as session:
            info_url = f"{self.datalab_api_url}/info"
            info_resp = session.get(info_url, follow_redirects=True, headers=self._headers)
        return info_resp.json()

    def _version_negotiation(self):
        """Check whether this client is expected to work with this instance.

        Raises:
            RuntimeError: If the server version is not supported or if no supported API versions are found.

        """

        for available_api_version in sorted(self._datalab_api_versions):
            major, minor, _ = (int(_) for _ in available_api_version.split("."))
            if major == MIN_API_VERSION[0] and minor == MIN_API_VERSION[1]:
                self._selected_api_version = available_api_version
                break
        else:
            raise RuntimeError(f"No supported API versions found in {self._datalab_api_versions=}")

        if self._datalab_server_version in BAD_SERVER_VERSIONS:
            raise RuntimeError(
                f"Server version {self._datalab_server_version} is not supported by this client."
            )

    @property
    def api_key(self) -> str | None:
        """The API key used to authenticate requests to the Datalab API, passed
        as the `DATALAB-API-KEY` HTTP header.

        This can be retrieved by an authenticated user with the `/get-api-key`
        endpoint of a Datalab API.

        """
        return self._api_key

    def _set_api_key(self):
        """If not provided explicitly, attempts to load the API key from environment variables and
        set the `api_key` attribute."""

        if self._api_key is not None:
            return

        key_env_var = "DATALAB_API_KEY"

        # probe the prefixed environment variable first
        if self._datalab_instance_prefix is not None:
            self._api_key = os.getenv(f"{self._datalab_instance_prefix.upper()}_{key_env_var}")

        if self._api_key is None:
            self._api_key = os.getenv("DATALAB_API_KEY")

        if self._api_key is None:
            raise ValueError(
                f"No API key provided explicitly and no key found in environment variables {key_env_var}/<prefix>_{key_env_var}."
            )

        self._headers["DATALAB-API-KEY"] = self._api_key

    def authenticate(self):
        """Tests authentication of the client with the Datalab API."""
        with self._http_client(headers=self._headers) as session:
            user_url = f"{self.datalab_api_url}/get-current-user"
            user_resp = session.get(user_url, follow_redirects=True, headers=self._headers)
        if user_resp.status_code != 200:
            raise RuntimeError(
                f"Failed to authenticate to {self.datalab_api_url!r}: {user_resp.status_code=} from {self._headers}. Please check your API key."
            )
        return user_resp.json()

    def get_items(self, item_type: str | None = "samples") -> list[dict[str, Any]]:
        """List items of the given type available to the authenticated user.

        Parameters:
            item_type: The type of item to list. Defaults to "samples". Other
            choices will trigger a call to the `/<item_type>` endpoint of the API.

        Returns:
            A list of items of the given type.

        """
        if item_type is None:
            item_type = "samples"
        with self._http_client(headers=self._headers) as session:
            items_url = f"{self.datalab_api_url}/{item_type}"
            items_resp = session.get(items_url, follow_redirects=True, headers=self._headers)
        if items_resp.status_code != 200:
            raise RuntimeError(
                f"Failed to list items with {item_type=} at {items_url}: {items_resp.status_code=}. Check the item type is correct."
            )
        items = items_resp.json()
        if items["status"] != "success":
            raise RuntimeError(f"Failed to list items at {items_url}: {items['status']!r}.")
        return items[item_type]

    def search_items(
        self, query: str, item_types: list[str] | str = ["samples", "cells"]
    ) -> list[dict[str, Any]]:
        """Search for items of the given types that match the query.

        Parameters:
            query: Free-text query to search for.
            item_types: The types of items to search for. Defaults to ["samples", "cells"].

        Returns:
            An ordered list of items of the given types that match the query.

        """
        if isinstance(item_types, str):
            item_types = [item_types]

        with self._http_client(headers=self._headers) as session:
            search_items_url = (
                f"{self.datalab_api_url}/search-items?query={query}&types={','.join(item_types)}"
            )
            items_resp = session.get(search_items_url, follow_redirects=True, headers=self._headers)
        if items_resp.status_code != 200:
            raise RuntimeError(
                f"Failed to search items with {item_types=} at {search_items_url}: {items_resp.status_code=}"
            )
        items = items_resp.json()
        if items["status"] != "success":
            raise RuntimeError(f"Failed to list items at {search_items_url}: {items['status']!r}.")

        return items["items"]

    def create_item(self, item_id: str, item_type: str, item_data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Create an item with a given ID and item data.

        Parameters:
            item_id: The ID of the item to create.
            item_type: The type of item to create, e.g., 'samples', 'cells'.
            item_data: The data for the item.

        """
        new_item = {}
        if item_data is not None:
            new_item = item_data
        new_item.update(**{"item_id": item_id, "type": item_type})

        with self._http_client(headers=self._headers) as session:
            create_item_url = f"{self.datalab_api_url}/new-sample/"
            create_item_resp = session.post(
                create_item_url,
                json=new_item,
                follow_redirects=True,
                headers=self._headers,
            )
        try:
            created_item = create_item_resp.json()
            if created_item["status"] != "success":
                raise RuntimeError(f"Failed to create item at {create_item_url}: {created_item['status']!r}.")
            return created_item["sample_list_entry"]

        except Exception:
            raise RuntimeError(
                f"Failed to create item {item_id=} with data {item_data=} at {create_item_url}: {create_item_resp.status_code=}. Check the item information is correct."
            )

    def update_item(self, item_id: str, item_data: dict[str, Any]) -> dict[str, Any]:
        """Update an item with the given item data.

        Parameters:
            item_id: The ID of the item to update.
            item_data: The new data for the item.

        Returns:
            A dictionary of the updated item data.

        """
        update_item_data = {"item_id": item_id, "data": item_data}
        with self._http_client(headers=self._headers) as session:
            update_item_url = f"{self.datalab_api_url}/save-item/"
            update_item_resp = session.post(
                update_item_url,
                json=update_item_data,
                follow_redirects=True,
                headers=self._headers,
            )
        if update_item_resp.status_code != 200:
            raise RuntimeError(
                f"Failed to update item {item_id=} at {update_item_url}: {update_item_resp.status_code=}. Check the item information is correct."
            )
        updated_item = update_item_resp.json()
        if updated_item["status"] != "success":
            raise RuntimeError(f"Failed to update item at {update_item_url}: {updated_item['status']!r}.")
        return updated_item

    def get_item(
        self, item_id: str | None = None, refcode: str | None = None, load_blocks: bool = False
    ) -> dict[str, Any]:
        """Get an item with a given ID or refcode.

        Parameters:
            item_id: The ID of the item to search for.
            refcode: The refcode of the item to search fork
            load_blocks: Whether to load the blocks associated with the item.

        Returns:
            A dictionary of item data for the item with the given ID or refcode.

        """

        if item_id is None and refcode is None:
            raise ValueError("Must provide one of `item_id` or `refcode`.")
        if item_id is not None and refcode is not None:
            raise ValueError("Must provide only one of `item_id` or `refcode`.")

        if refcode is not None:
            raise NotImplementedError("Searching by `refcode` is not yet implemented.")

        with self._http_client(headers=self._headers) as session:
            item_url = f"{self.datalab_api_url}/get-item-data/{item_id}"
            item_resp = session.get(item_url, follow_redirects=True, headers=self._headers)

        if item_resp.status_code != 200:
            raise RuntimeError(
                f"Failed to find item {item_id=}, {refcode=} {item_url}: {item_resp.status_code=}. Check the item information is correct."
            )

        item = item_resp.json()
        if item["status"] != "success":
            raise RuntimeError(f"Failed to get item at {item_url}: {item['status']!r}.")

        # Filter out any deleted blocks
        item["item_data"]["blocks_obj"] = {
            block_id: block
            for block_id, block in item["item_data"]["blocks_obj"].items()
            if block_id in item["item_data"]["display_order"]
        }

        # Make a call to `/update-block` which will parse/create plots and return as JSON
        if load_blocks:
            ret_item_id = item["item_data"]["item_id"]
            for block_id, block in item["item_data"]["blocks_obj"].items():
                block_data = self.get_block(
                    item_id=ret_item_id, block_id=block_id, block_data=block
                )
                item["item_data"]["blocks_obj"][block_id] = block_data

        return item["item_data"]

    def get_block(self, item_id: str, block_id: str, block_data: dict[str, Any]) -> dict[str, Any]:
        """Get a block with a given ID and block data.
        Should be used in conjunction with `get_item` to load an existing block.

        Parameters:
            item_id: The ID of the item to search for.
            block_id: The ID of the block to search for.
            block_data: Any other block data required by the request.

        Returns:
            A dictionary of block data for the block with the given ID.

        """
        with self._http_client(headers=self._headers) as session:
            block_url = f"{self.datalab_api_url}/update-block/"
            block_request = {
                "block_data": block_data,
                "item_id": item_id,
                "block_id": block_id,
                "save_to_db": False,
            }
            block_resp = session.post(
                block_url, json=block_request, follow_redirects=True, headers=self._headers
            )
        if block_resp.status_code != 200:
            raise RuntimeError(
                f"Failed to find block {block_id=} for item {item_id=} at {block_url}: {block_resp.status_code=}. Check the block information is correct."
            )

        block = block_resp.json()
        if block["status"] != "success":
            raise RuntimeError(f"Failed to get block at {block_url}: {block['status']!r}.")
        return block["new_block_data"]

    def upload_file_to_item(self, item_id: str, file_path: Path | str) -> dict[str, Any]:
        """Upload a file to an item with a given ID.

        Parameters:
            item_id: The ID of the item to upload the file to.
            file_path: The path to the file to upload.

        Returns:
            A dictionary of the uploaded file data.

        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path=} does not exist.")

        with self._http_client(headers=self._headers) as session:
            upload_url = f"{self.datalab_api_url}/upload-file/"
            with open(file_path, "rb") as file:
                files = {"file": (file_path.name, file)}
                upload_resp = session.post(
                    upload_url,
                    files=files,
                    data={"item_id": item_id, "replace_file": None},
                    follow_redirects=True,
                    headers=self._headers,
                )
        if upload_resp.status_code != 201:
            raise RuntimeError(
                f"Failed to upload file {file_path=} to item {item_id=} at {upload_url}: {upload_resp.status_code=}. Check the file information is correct."
            )

        upload = upload_resp.json()
        if upload["status"] != "success":
            raise RuntimeError(f"Failed to upload file at {upload_url}: {upload['status']!r}.")

        return upload

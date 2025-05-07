from __future__ import annotations

import warnings
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Optional, Union

from ._base import BaseDatalabClient, __version__

__all__ = ("DatalabClient", "__version__")


class DuplicateItemError(ValueError):
    """Raised when the API operation would create a duplicate item."""


class DatalabClient(BaseDatalabClient):
    """A client for the Datalab API.

    The client will keep an HTTP session open for the duration of its life and thus is
    amenable for use as a context manager, e.g.,

    ```python
    with DatalabClient("https://demo-api.datalab-org.io") as client:
        client.get_items()
    ```

    """

    def get_info(self) -> dict[str, Any]:
        """Fetch metadata associated with this datalab instance.

        The server information is stored on the client and can be accessed
        by the `info` attribute.

        Returns:
            dict: The JSON response from the `/info` endpoint of the Datalab API.

        """
        info_url = f"{self.datalab_api_url}/info"
        info_resp = self.session.get(info_url, follow_redirects=True)
        self.info = info_resp.json()["data"]
        return self.info

    def authenticate(self):
        """Tests authentication of the client with the Datalab API."""
        user_url = f"{self.datalab_api_url}/get-current-user"
        user_resp = self.session.get(user_url, follow_redirects=True)
        if user_resp.status_code != 200:
            raise RuntimeError(
                f"Failed to authenticate to {self.datalab_api_url!r}: {user_resp.status_code=} from {self._headers}. Please check your API key."
            )
        return user_resp.json()

    def get_block_info(self) -> list[dict[str, Any]]:
        """Return the list of available data blocks types for this instance,
        including some details and descriptions of their usage.

        The block information is stored on the client and can be accessed
        by the `block_info` attribute.

        Returns:
            A list of dictionary of block types.

        """
        block_info_url = f"{self.datalab_api_url}/info/blocks"
        block_info_resp = self.session.get(block_info_url, follow_redirects=True)
        if block_info_resp.status_code != 200:
            raise RuntimeError(
                f"Failed to list block information at {block_info_url}: {block_info_resp.status_code=}."
            )
        self.block_info = block_info_resp.json()["data"]
        return self.block_info

    def get_items(self, item_type: str | None = "samples") -> list[dict[str, Any]]:
        """List items of the given type available to the authenticated user.

        Parameters:
            item_type: The type of item to list. Defaults to "samples". Other
            choices will trigger a call to the `/<item_type>` endpoint of the API.

        Returns:
            A list of items of the given type.

        """
        endpoint_type_map = {
            "cells": "samples",
            "samples": "samples",
            "starting_materials": "starting-materials",
            "equipment": "equipment",
        }

        if item_type is None:
            item_type = "samples"

        items_url = f"{self.datalab_api_url}/{endpoint_type_map.get(item_type, item_type.replace('_', '-'))}"
        items_resp = self.session.get(items_url, follow_redirects=True)
        if items_resp.status_code != 200:
            raise RuntimeError(
                f"Failed to list items with {item_type=} at {items_url}: {items_resp.status_code=}. Check the item type is correct."
            )
        items = items_resp.json()
        if items["status"] != "success":
            raise RuntimeError(f"Failed to list items at {items_url}: {items['status']!r}.")

        if item_type in items:
            # Old approach
            return items[item_type]
        if "items" in items:
            return items["items"]

        else:
            return items

    def search_items(
        self, query: str, item_types: Iterable[str] | str = ("samples", "cells")
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

        search_items_url = (
            f"{self.datalab_api_url}/search-items?query={query}&types={','.join(item_types)}"
        )
        items_resp = self.session.get(search_items_url, follow_redirects=True)
        if items_resp.status_code != 200:
            raise RuntimeError(
                f"Failed to search items with {item_types=} at {search_items_url}: {items_resp.status_code=}"
            )
        items = items_resp.json()
        if items["status"] != "success":
            raise RuntimeError(f"Failed to list items at {search_items_url}: {items['status']!r}.")

        return items["items"]

    def create_item(
        self,
        item_id: str | None = None,
        item_type: str = "samples",
        item_data: dict[str, Any] | None = None,
        collection_id: str | None = None,
    ) -> dict[str, Any]:
        """Create an item with a given ID and item data.

        Parameters:
            item_id: The ID of the item to create, if set to `None`, the server will generate one.
            item_type: The type of item to create, e.g., 'samples', 'cells'.
            item_data: The data for the item.
            collection_id: The ID of the collection to add the item to (optional).
                If such a collection does not exist, one will be made.

        """
        new_item = {}
        if item_data is not None:
            new_item = item_data
        new_item.update({"item_id": item_id, "type": item_type})

        if new_item["item_id"] is None:
            new_item.pop("item_id")

        if collection_id is not None:
            try:
                collection_immutable_id = self.get_collection(collection_id)[0]["immutable_id"]
            except RuntimeError:
                self.create_collection(collection_id)
                collection_immutable_id = self.get_collection(collection_id)[0]["immutable_id"]
            new_item["collections"] = new_item.get("collections", [])
            new_item["collections"].append({"immutable_id": collection_immutable_id})

        create_item_url = f"{self.datalab_api_url}/new-sample/"
        create_item_resp = self.session.post(
            create_item_url,
            json={"new_sample_data": new_item, "generate_id_automatically": item_id is None},
            follow_redirects=True,
        )
        try:
            created_item = create_item_resp.json()
            if create_item_resp.status_code == 409:
                raise DuplicateItemError(
                    f"Item {item_id=} already exists at {create_item_url}: {created_item['status']!r}."
                )
            if created_item["status"] != "success":
                if "DuplicateKeyError" in created_item["message"]:
                    raise DuplicateItemError(
                        f"Item {item_id=} already exists at {create_item_url}: {created_item['status']!r}."
                    )
                raise RuntimeError(f"Failed to create item at {create_item_url}: {created_item}.")
            return created_item["sample_list_entry"]

        except Exception as exc:
            raise exc.__class__(
                f"Failed to create item {item_id=} with data {item_data=} at {create_item_url}: {create_item_resp.status_code=}, {create_item_resp.content}. Check the item information is correct."
            ) from exc

    def update_item(self, item_id: str, item_data: dict[str, Any]) -> dict[str, Any]:
        """Update an item with the given item data.

        Parameters:
            item_id: The ID of the item to update.
            item_data: The new data for the item.

        Returns:
            A dictionary of the updated item data.

        """
        update_item_data = {"item_id": item_id, "data": item_data}
        update_item_url = f"{self.datalab_api_url}/save-item/"
        update_item_resp = self.session.post(
            update_item_url,
            json=update_item_data,
            follow_redirects=True,
        )
        if update_item_resp.status_code != 200:
            raise RuntimeError(
                f"Failed to update item {item_id=} at {update_item_url}: {update_item_resp.status_code=}. Check the item information is correct."
            )
        updated_item = update_item_resp.json()
        if updated_item["status"] != "success":
            raise RuntimeError(
                f"Failed to update item at {update_item_url}: {updated_item['status']!r}."
            )
        return updated_item

    def get_item(
        self,
        item_id: str | None = None,
        refcode: str | None = None,
        load_blocks: bool = False,
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

        item_url = f"{self.datalab_api_url}/get-item-data/{item_id}"
        item_resp = self.session.get(item_url, follow_redirects=True)

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

    def get_item_files(self, item_id: str) -> None:
        """Download all the files for a given item and save them locally
        in the current working directory.

        Parameters:
            item_id: The ID of the item to search for.

        """

        item_data = self.get_item(item_id)
        for f in item_data.get("files", []):
            url = f"{self.datalab_api_url}/files/{f['immutable_id']}/{f['name']}"
            if Path(f["name"]).exists():
                warnings.warn(f"Will not overwrite existing file {f['name']}")
                continue
            with open(f["name"], "wb") as file:
                with self.session.stream("GET", url, follow_redirects=True) as response:
                    for chunk in response.iter_bytes(chunk_size=1024):
                        file.write(chunk)

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
        block_url = f"{self.datalab_api_url}/update-block/"
        block_request = {
            "block_data": block_data,
            "item_id": item_id,
            "block_id": block_id,
            "save_to_db": False,
        }
        block_resp = self.session.post(block_url, json=block_request, follow_redirects=True)
        if block_resp.status_code != 200:
            raise RuntimeError(
                f"Failed to find block {block_id=} for item {item_id=} at {block_url}: {block_resp.status_code=}. Check the block information is correct."
            )

        block = block_resp.json()
        if block["status"] != "success":
            raise RuntimeError(f"Failed to get block at {block_url}: {block['status']!r}.")
        return block["new_block_data"]

    def upload_file(self, item_id: str, file_path: Path | str) -> dict[str, Any]:
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

        upload_url = f"{self.datalab_api_url}/upload-file/"
        with open(file_path, "rb") as file:
            files = {"file": (file_path.name, file)}
            upload_resp = self.session.post(
                upload_url,
                files=files,
                data={"item_id": item_id, "replace_file": None},
                follow_redirects=True,
            )
        if upload_resp.status_code != 201:
            raise RuntimeError(
                f"Failed to upload file {file_path=} to item {item_id=} at {upload_url}: {upload_resp.status_code=}. Check the file information is correct."
            )

        upload = upload_resp.json()
        if upload["status"] != "success":
            raise RuntimeError(f"Failed to upload file at {upload_url}: {upload['status']!r}.")

        return upload

    def create_data_block(
        self,
        item_id: str,
        block_type: str,
        file_ids: str | list[str] | None = None,
        file_paths: Path | list[Path] | None = None,
    ) -> dict[str, Any]:
        """Creates a data block for an item with the given block type and file ID.

        Parameters:
            item_id: The ID of the item to create the block for.
            block_type: The type of block to create.
            file_ids: The ID of the file to attach to the block, must already
                be uploaded to the item.
            file_paths: A path, or set of paths, to files to upload and attach to the
                item. Conflicts with `file_id`, only one can be provided.

        Returns:
            The created block data.

        """

        blocks_url = f"{self.datalab_api_url}/add-data-block/"

        # TODO: future validation of block types based on server response
        payload = {
            "item_id": item_id,
            "block_type": block_type,
            "index": None,
        }

        if file_paths:
            raise NotImplementedError(
                "Simultaneously uploading files and creating blocks is not yet supported."
            )

        if file_ids:
            if isinstance(file_ids, str):
                file_ids = [file_ids]
            # check that the file is attached to the item
            item = self.get_item(item_id=item_id, load_blocks=False)
            attached_file_ids = set(item["file_ObjectIds"])
            if not set(file_ids).issubset(attached_file_ids):
                raise RuntimeError(
                    f"Not all IDs {file_ids=} are attached to item {item_id=}: {attached_file_ids=}"
                )

        block_resp = self.session.post(blocks_url, json=payload, follow_redirects=True)
        if block_resp.status_code != 200:
            raise RuntimeError(
                f"Failed to create block {block_type=} for item {item_id=}:\n{block_resp.text}"
            )
        block_data = block_resp.json()["new_block_obj"]

        if file_ids:
            block_data = self._update_data_block(
                block_type=block_type, block_data=block_data, file_ids=file_ids
            )

        return block_data

    def update_data_block(
        self, item_id: str, block_id: str, block_type: str, block_data: dict
    ) -> dict[str, Any]:
        """Attempts to update a block with the given payload of data,
        returning the updated block.

        Parameters:
            item_id: The ID of the item that the block is attached to.
            block_id: The ID of existing block.
            block_type: The type of block to update.
            block_data: The payload of block data to update; will be used to selectively update
                any fields present, with validation performed by the remote block code itself.

        Returns:
            If successful, the updated block data.

        Raises:
            RuntimeError: If the block update fails.

        """
        payload = {k: v for k, v in block_data.items()}
        payload["block_id"] = block_id
        payload["blocktype"] = block_type
        payload["item_id"] = item_id

        return self._update_data_block(block_type=block_type, block_data=payload)

    def _update_data_block(
        self, block_type: str, block_data: dict, file_ids: str | list[str] | None = None
    ) -> dict[str, Any]:
        """Attaches files to blocks: should only be used via wrapper methods."""
        if file_ids and isinstance(file_ids, str):
            file_ids = [file_ids]

        if file_ids:
            if len(file_ids) > 1:
                raise RuntimeError(
                    "API does not currently support attaching multiple files in a block."
                )
            block_data["file_id"] = file_ids[0]

        blocks_url = f"{self.datalab_api_url}/update-block/"
        payload = {
            "block_data": block_data,
            "block_type": block_type,
            "save_to_db": True,
        }

        resp = self.session.post(blocks_url, json=payload, follow_redirects=True)
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to update block {block_type=}:\n{resp.text}")

        return resp.json()["new_block_data"]

    def get_collection(self, collection_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Get a collection with a given ID.

        Parameters:
            collection_id: The ID of the collection to search for.

        Returns:
            A dictionary of collection data for the collection with the given ID,
            and a list of the member items.

        """
        collection_url = f"{self.datalab_api_url}/collections/{collection_id}"
        collection_resp = self.session.get(collection_url, follow_redirects=True)
        if collection_resp.status_code != 200:
            raise RuntimeError(
                f"Failed to find collection {collection_id=} at {collection_url}: {collection_resp.status_code=}. Check the collection ID is correct."
            )
        collection = collection_resp.json()
        if collection["status"] != "success":
            raise RuntimeError(
                f"Failed to get collection at {collection_url}: {collection['status']!r}."
            )
        return collection["data"], collection["child_items"]

    def create_collection(
        self, collection_id: str, collection_data: dict | None = None
    ) -> dict[str, Any]:
        """Create a collection with a given ID and collection data.

        Parameters:
            collection_id: The ID of the collection to create.
            collection_data: The data for the collection.

        """
        collection_url = f"{self.datalab_api_url}/collections"

        new_collection = {}
        if collection_data is not None:
            new_collection = collection_data
        new_collection.update({"collection_id": collection_id, "type": "collections"})

        collection_resp = self.session.put(
            collection_url,
            json={"data": new_collection},
            follow_redirects=True,
        )

        if collection_resp.status_code != 201 or collection_resp.json()["status"] != "success":
            raise RuntimeError(
                f"Failed to create collection {collection_id=} at {collection_url}: {collection_resp.status_code=}. Check the collection information is correct: {collection_resp.content}"
            )

        created_collection = collection_resp.json()["data"]
        return created_collection

import warnings
from pathlib import Path
from typing import Any, Optional, Union

from ._base import BaseDatalabClient, __version__

__all__ = ("__version__", "DatalabClient")


class DatalabClient(BaseDatalabClient):
    """A client for the Datalab API.

    The client will keep an HTTP session open for the duration of its life and thus is
    amenable for use as a context manager, e.g.,

    ```python
    with DatalabClient("https://public.api.odbx.science") as client:
        client.get_items()
    ```

    """

    def get_info(self) -> dict[str, Any]:
        """Fetch metadata associated with this datalab instance.

        Returns:
            dict: The JSON response from the `/info` endpoint of the Datalab API.

        """
        info_url = f"{self.datalab_api_url}/info"
        info_resp = self.session.get(info_url, follow_redirects=True)
        return info_resp.json()

    def authenticate(self):
        """Tests authentication of the client with the Datalab API."""
        user_url = f"{self.datalab_api_url}/get-current-user"
        user_resp = self.session.get(user_url, follow_redirects=True)
        if user_resp.status_code != 200:
            raise RuntimeError(
                f"Failed to authenticate to {self.datalab_api_url!r}: {user_resp.status_code=} from {self._headers}. Please check your API key."
            )
        return user_resp.json()

    def get_items(self, item_type: Optional[str] = "samples") -> list[dict[str, Any]]:
        """List items of the given type available to the authenticated user.

        Parameters:
            item_type: The type of item to list. Defaults to "samples". Other
            choices will trigger a call to the `/<item_type>` endpoint of the API.

        Returns:
            A list of items of the given type.

        """
        if item_type is None:
            item_type = "samples"
        items_url = f"{self.datalab_api_url}/{item_type}"
        items_resp = self.session.get(items_url, follow_redirects=True)
        if items_resp.status_code != 200:
            raise RuntimeError(
                f"Failed to list items with {item_type=} at {items_url}: {items_resp.status_code=}. Check the item type is correct."
            )
        items = items_resp.json()
        if items["status"] != "success":
            raise RuntimeError(f"Failed to list items at {items_url}: {items['status']!r}.")
        return items[item_type]

    def search_items(
        self, query: str, item_types: Union[list[str], str] = ["samples", "cells"]
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
        self, item_id: str, item_type: str, item_data: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
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

        create_item_url = f"{self.datalab_api_url}/new-sample/"
        create_item_resp = self.session.post(
            create_item_url,
            json=new_item,
            follow_redirects=True,
        )
        try:
            created_item = create_item_resp.json()
            if created_item["status"] != "success":
                raise RuntimeError(
                    f"Failed to create item at {create_item_url}: {created_item['status']!r}."
                )
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
        item_id: Optional[str] = None,
        refcode: Optional[str] = None,
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
            file_location = f["location"]
            url = file_location.replace("/app", self.datalab_api_url)
            if Path(f["name"]).exists():
                warnings.warn(f"Will not overwrite existing file {f['name']}")
                continue
            with open(f["name"], "wb") as file:
                response = self.session.get(url, follow_redirects=True)
                file.write(response.content)

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

    def upload_file(self, item_id: str, file_path: Union[Path, str]) -> dict[str, Any]:
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
        file_ids: Optional[Union[str, list[str]]] = None,
        file_paths: Optional[Union[Path, list[Path]]] = None,
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

    def _update_data_block(
        self, block_type: str, block_data: dict, file_ids: Optional[Union[str, list[str]]] = None
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

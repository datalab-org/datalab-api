import os
from importlib.metadata import version
from typing import Any
import httpx
import logging
from rich.logging import RichHandler

__version__ = version("datalab-api")

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
        """Authenticates the client with the Datalab API."""
        with self._http_client(headers=self._headers) as session:
            user_url = f"{self.datalab_api_url}/get-current-user"
            user_resp = session.get(user_url, follow_redirects=True, headers=self._headers)
        if user_resp.status_code != 200:
            raise RuntimeError(f"Failed to authenticate to {self.datalab_api_url!r}: {user_resp.status_code=} from {self._headers}. Please check your API key.")
        return user_resp.json()

    def get_items(self, data_type: str = "samples"):
        """List items available to the authenticated user."""
        with self._http_client(headers=self._headers) as session:
            items_url = f"{self.datalab_api_url}/{data_type}"
            items_resp = session.get(items_url, follow_redirects=True, headers=self._headers)
        if items_resp.status_code != 200:
            raise RuntimeError(f"Failed to list items at {self.datalab_api_url!r}: {items_resp.status_code=} from {self._headers}.")
        items = items_resp.json()
        if items["status"] != "success":
            raise RuntimeError(f"Failed to list items at {self.datalab_api_url!r}: {items['status']!r}.")
        return items["samples"]


__all__ = ("__version__", "DatalabClient")

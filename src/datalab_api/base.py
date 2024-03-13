import logging
from importlib.metadata import version
import os
from typing import Any

import httpx
from rich.logging import RichHandler

BAD_SERVER_VERSIONS = ((0, 2, 0),)
BAD_API_VERSIONS = ((0, 0, 0),)
MIN_API_VERSION = (0, 1, 0)

__version__ = version("datalab-api")

__all__ = ("__version__", "BaseDatalabClient")


class BaseDatalabClient:
    """A base class that implements some of the shared/logistical functionality
    (hopefully) common to all Datalab clients.

    Mainly used to keep the namespace of the 'real' client classes clean and
    readable by users.
    """

    _api_key: str | None = None
    _session: httpx.Client | None = None
    _headers: dict[str, str] = {}

    def __init__(self, datalab_api_url: str, log_level: str = "WARNING"):
        """Creates an authenticated client.

        An API key is required to authenticate requests. The client will attempt to load it from a
        series of environment variables, `DATALAB_API_KEY` and prefixed versions for the given
        requested instance (e.g., `PUBLIC_DATALAB_API_KEY` for the public deployment
        which has prefix `public`).

        Parameters:
            datalab_api_url: The URL of the Datalab API.
                TODO: If the URL of a datalab *UI* is provided, a request will be made to attempt
                to resolve the underlying API URL (e.g., `https://public.datalab.odbx.science`
                will 'redirect' to `https://public.api.odbx.science`).
            log_level: The logging level to use for the client. Defaults to "WARNING".


        """

        self.datalab_api_url = datalab_api_url
        if not self.datalab_api_url:
            raise ValueError("No Datalab API URL provided.")
        if not self.datalab_api_url.startswith("http"):
            self.datalab_api_url = f"https://{self.datalab_api_url}"
        logging.basicConfig(level=log_level, handlers=[RichHandler()])
        self.log = logging.getLogger(__name__)

        self._http_client = httpx.Client
        self._headers["User-Agent"] = f"Datalab Python API/{__version__}"

        info_json = self.get_info()

        self._datalab_api_versions: list[str] = info_json["data"]["attributes"][
            "available_api_versions"
        ]
        self._datalab_server_version: str = info_json["data"]["attributes"]["server_version"]
        self._datalab_instance_prefix: str | None = info_json["data"]["attributes"].get(
            "identifier_prefix"
        )

        self._find_api_key()

    def get_info(self) -> dict[str, Any]:
        raise NotImplementedError

    @property
    def session(self) -> httpx.Client:
        if self._session is None:
            return self._http_client(headers=self.headers)
        return self._session

    @property
    def headers(self):
        return self._headers

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
    def api_key(self) -> str:
        """The API key used to authenticate requests to the Datalab API, passed
        as the `DATALAB-API-KEY` HTTP header.

        This can be retrieved by an authenticated user with the `/get-api-key`
        endpoint of a Datalab API.

        """
        if self._api_key is not None:
            return self._api_key
        return self._find_api_key()

    def _find_api_key(self) -> str:
        """Checks various environment variables for an API key and sets the value in the 
        session headers.
        """
        if self._api_key is None:
            key_env_var = "DATALAB_API_KEY"

            api_key: str | None = None

            # probe the prefixed environment variable first
            if self._datalab_instance_prefix is not None:
                api_key = os.getenv(f"{self._datalab_instance_prefix.upper()}_{key_env_var}")

            if api_key is None:
                api_key = os.getenv("DATALAB_API_KEY")

            if api_key is None:
                raise ValueError(
                    f"No API key found in environment variables {key_env_var}/<prefix>_{key_env_var}."
                )

            self._api_key = api_key

            # Reset session as we are now updating the headers
            if self._session is not None:
                try:
                    self._session.close()
                except Exception:
                    pass
                finally:
                    self._session = None
            self._headers["DATALAB-API-KEY"] = self.api_key

        return self.api_key

    def __enter__(self) -> "BaseDatalabClient":
        return self

    def __exit__(self, *_):
        if self._session is not None:
            self._session.close()

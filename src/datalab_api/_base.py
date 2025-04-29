import functools
import logging
import os
import re
import warnings
from importlib.metadata import version
from typing import Any, Optional

import httpx
from rich.console import Console
from rich.logging import RichHandler
from rich.pretty import pprint
from rich.table import Table

__version__ = version("datalab-api")

__all__ = ("BaseDatalabClient", "__version__")


def pretty_displayer(method):
    """A decorator which wraps a method with a 'display' kwarg, which will
    either pretty print a JSON response, or display a Rich table.

    """

    @functools.wraps(method)
    def rich_wrapper(self, *args, **kwargs):
        display = kwargs.pop("display", False)
        page_limit = kwargs.pop("page_limit", 10)
        result = method(self, *args, **kwargs)
        if display:
            blocks = None
            if isinstance(result, dict):
                if "blocks_obj" in result:
                    blocks = result["blocks_obj"]
                elif "blocktype" in result:
                    blocks = {result["block_id"]: result}
                    result = None
                if blocks:
                    for block in blocks.values():
                        if "bokeh_plot_data" in block:
                            bokeh_from_json(block)
                if result:
                    pprint(result, max_length=None, max_string=100, max_depth=3)
            elif isinstance(result, list):
                try:
                    table = Table(show_lines=True)
                    table.add_column("type", overflow="crop", justify="center")
                    table.add_column("ID", style="cyan", no_wrap=True)
                    table.add_column("refcode", style="magenta", no_wrap=True)
                    table.add_column("name", width=30, overflow="ellipsis", no_wrap=True)
                    for item in result[:page_limit]:
                        table.add_row(
                            item["type"][0].upper(),
                            item["item_id"],
                            item["refcode"],
                            item["name"],
                            end_section=True,
                        )
                    console = Console()
                    console.print(table)
                except Exception:
                    pprint(result, max_length=None, max_string=100, max_depth=3)

        return result

    return rich_wrapper


class AutoPrettyPrint(type):
    def __new__(cls, name, bases, dct):
        for attr, value in dct.items():
            if callable(value) and not attr.startswith("__"):
                dct[attr] = pretty_displayer(value)
        return super().__new__(cls, name, bases, dct)


def bokeh_from_json(block_data, show=True):
    from bokeh.io import curdoc
    from bokeh.plotting import show as bokeh_show

    bokeh_plot_data = block_data.get("bokeh_plot_data", block_data)
    curdoc().replace_with_json(bokeh_plot_data["doc"])
    if show:
        bokeh_show(curdoc().roots[0])

    return curdoc()


class BaseDatalabClient(metaclass=AutoPrettyPrint):
    """A base class that implements some of the shared/logistical functionality
    (hopefully) common to all Datalab clients.

    Mainly used to keep the namespace of the 'real' client classes clean and
    readable by users.
    """

    _api_key: Optional[str] = None
    _session: Optional[httpx.Client] = None
    _headers: dict[str, str] = {}
    _timeout: httpx.Timeout = httpx.Timeout(10.0, read=60.0)

    info: dict[str, Any] = {}
    """The `data` response from the `/info` endpoint of the Datalab API."""

    block_info: list[dict[str, Any]] = []
    """The `data` response from the `/info/blocks` endpoint of the Datalab API."""

    bad_server_versions: Optional[tuple[tuple[int, int, int]]] = ((0, 2, 0),)
    """Any known server versions that are not supported by this client."""

    min_server_version: tuple[int, int, int] = (0, 1, 0)
    """The minimum supported server version that this client supports."""

    def __init__(self, datalab_api_url: str, log_level: str = "WARNING"):
        """Creates an authenticated client.

        An API key is required to authenticate requests. The client will attempt to load it from a
        series of environment variables, `DATALAB_API_KEY` and prefixed versions for the given
        requested instance (e.g., `PUBLIC_DATALAB_API_KEY` for the public deployment
        which has prefix `public`).

        Parameters:
            datalab_api_url: The URL of the Datalab API.
                TODO: If the URL of a datalab *UI* is provided, a request will be made to attempt
                to resolve the underlying API URL (e.g., `https://demo-api.datalab-org.io`
                will 'redirect' to `https://demo-api.datalab-org.io`).
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

        self._detect_api_url()

        self.get_info()
        self.get_block_info()

        self._datalab_api_versions: list[str] = self.info["attributes"]["available_api_versions"]
        self._datalab_server_version: str = self.info["attributes"]["server_version"]
        self._datalab_instance_prefix: Optional[str] = self.info["attributes"].get(
            "identifier_prefix"
        )

        self._find_api_key()

    def _detect_api_url(self) -> None:
        """Perform a handshake with the chosen URL to ascertain the correct API URL.

        If a datalab UI URL is passed, the client will attempt to resolve the API URL by
        inspecting the HTML meta tags.

        Do not use the session for this, so we are not passing the API key to arbitrary URLs.

        """
        response = httpx.get(self.datalab_api_url)
        match = re.search(
            r'<meta name="x_datalab_api_url" content="(.*?)">',
            response.text,
            re.IGNORECASE,
        )
        if match:
            self.datalab_api_url = match.group(1)
            warnings.warn(
                f"Found API URL {self.datalab_api_url} in HTML meta tag. Creating client with this URL instead."
            )

    def get_info(self) -> dict[str, Any]:
        raise NotImplementedError

    def get_block_info(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    @property
    def session(self) -> httpx.Client:
        if self._session is None:
            return self._http_client(headers=self.headers, timeout=self.timeout)
        return self._session

    @property
    def headers(self) -> dict[str, str]:
        """Any headers to send with each request to the datalab API."""
        return self._headers

    @property
    def timeout(self) -> httpx.Timeout:
        """A timeout object to use for the datalab API session."""
        return self._timeout

    def _version_negotiation(self):
        """Check whether this client is expected to work with this instance.

        Raises:
            RuntimeError: If the server version is not supported or if no supported API versions are found.

        """

        for available_api_version in sorted(self._datalab_api_versions):
            major, minor, _ = (int(_) for _ in available_api_version.split("."))
            if major == self.min_api_version[0] and minor == self.min_api_version[1]:
                self._selected_api_version = available_api_version
                break
        else:
            raise RuntimeError(f"No supported API versions found in {self._datalab_api_versions=}")

        if self._datalab_server_version in self.bad_server_versions:
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

            api_key: Optional[str] = None

            # probe the prefixed environment variable first
            if self._datalab_instance_prefix is not None:
                api_key = os.getenv(f"{self._datalab_instance_prefix.upper()}_{key_env_var}")

            if api_key is None:
                api_key = os.getenv("DATALAB_API_KEY")

            # Remove single and double quotes around API key if present
            if api_key is not None:
                api_key = api_key.strip("'").strip('"')

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

    def __enter__(self):
        return self

    def __exit__(self, *_):
        if self._session is not None:
            self._session.close()

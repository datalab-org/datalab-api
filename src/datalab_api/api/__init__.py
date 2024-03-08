from importlib.metadata import version
import httpx

__version__ = version("datalab-api")

BAD_SERVER_VERSIONS = ("0.2.0", )
BAD_API_VERSIONS = ("0.0.0", )
MIN_API_VERSION = ("0.1.0", )


class DatalabClient:
    """A client for the Datalab API.

    The client will keep an HTTP session open for the duration of its life and thus is 
    amenable for use as a context manager, e.g.,

    ```python
    with DatalabClient("https://public.api.odbx.science", api_key="my-api-key") as client:
        client.get_items()
    ```
    """

    def __init__(self, datalab_api_url: str, api_key: str | None = None):
        """Creates an authenticated client.

        Parameters:
            datalab_api_url: The URL of the Datalab API.
                If the URL of a datalab *UI* is provided, a request will be made to attempt to resolve the underlying API URL (e.g., `https://public.datalab.odbx.science` will 'redirect' to `https://public.api.odbx.science`).
            api_key: The API key to authenticate requests. If no key is provided, the client will attempt to load it from a series of environment variables.

        """

        self.datalab_api_url = datalab_api_url
        self.api_key = api_key

        self._session = httpx.AsyncClient()
        self._headers: dict[str, str] = {}
        self._headers["User-Agent"] = "Datalab Python API/{__version__}"

        info_url = f"{self.datalab_api_url}/info"
        info_resp = self._session.get(info_url)
        if info_resp.status_code != 200:
            raise RuntimeError("Unable to conncet to `/info` endpoint of Datalab API. Please check URL: {url!r}")

        info_json = info_resp.json()
        self._datalab_api_versions = info_json["data"]["available_api_versions"]
        self._datalab_server_version = info_json["data"]["server_version"]

    def _version_negotiation(self):

        for available_api_version in sorted(self._datalab_api_versions):
            major, minor, patch = (int(_) for _ in available_api_version.split("."))
            if major == MIN_API_VERSION[0] and minor == MIN_API_VERSION[1]:
                self._selected_api_version = available_api_version
                break
        else:
            raise RuntimeError(f"No supported API versions found in {self._datalab_api_versions=}")

        if self._datalab_server_version in BAD_SERVER_VERSIONS:
            raise RuntimeError(f"Server version {self._datalab_server_version} is not supported by this client.")




__all__ = ("__version__", "DatalClient")


import socket
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .models import DownloadResult


class DownloadError(RuntimeError):
    """Raised when a URL cannot be downloaded for measurement."""


class UrlDownloader:
    def __init__(self, user_agent: str = "speedmeter/0.1.0") -> None:
        self._user_agent = user_agent

    def download(self, url: str, timeout: float, chunk_size: int) -> DownloadResult:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")

        request = Request(url, headers={"User-Agent": self._user_agent})
        total_bytes = 0
        started_at = perf_counter()

        try:
            with urlopen(request, timeout=timeout) as response:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    total_bytes += len(chunk)
        except HTTPError as exc:
            raise DownloadError(f"HTTP {exc.code}: {exc.reason}") from exc
        except (URLError, TimeoutError, socket.timeout, OSError, ValueError) as exc:
            raise DownloadError(_format_network_error(exc)) from exc

        elapsed_seconds = perf_counter() - started_at
        if total_bytes == 0:
            raise DownloadError("response body is empty")

        return DownloadResult(
            bytes_downloaded=total_bytes,
            elapsed_seconds=elapsed_seconds,
        )


def _format_network_error(exc: BaseException) -> str:
    if isinstance(exc, URLError) and exc.reason:
        return f"network error: {exc.reason}"
    return f"network error: {exc}"

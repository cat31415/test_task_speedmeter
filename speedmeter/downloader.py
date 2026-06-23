import socket
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .models import DownloadProgress, DownloadResult, ProgressCallback


class DownloadError(RuntimeError):
    """Raised when a URL cannot be downloaded for measurement."""


class UrlDownloader:
    def __init__(self, user_agent: str = "speedmeter/0.1.0") -> None:
        self._user_agent = user_agent

    def download(
        self,
        url: str,
        timeout: float,
        chunk_size: int,
        progress_callback: ProgressCallback | None = None,
    ) -> DownloadResult:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")

        request = Request(url, headers={"User-Agent": self._user_agent})
        total_bytes = 0
        started_at = perf_counter()

        try:
            with urlopen(request, timeout=timeout) as response:
                total_size = _content_length(response)
                if total_size is not None:
                    _notify_progress(
                        progress_callback,
                        bytes_downloaded=0,
                        total_bytes=total_size,
                        elapsed_seconds=0.0,
                    )

                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    total_bytes += len(chunk)
                    _notify_progress(
                        progress_callback,
                        bytes_downloaded=total_bytes,
                        total_bytes=total_size,
                        elapsed_seconds=perf_counter() - started_at,
                    )
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


def _content_length(response: object) -> int | None:
    value = response.headers.get("Content-Length")
    if value is None:
        return None

    try:
        parsed = int(value)
    except ValueError:
        return None

    if parsed <= 0:
        return None
    return parsed


def _notify_progress(
    progress_callback: ProgressCallback | None,
    bytes_downloaded: int,
    total_bytes: int | None,
    elapsed_seconds: float,
) -> None:
    if progress_callback is None:
        return

    progress_callback(
        DownloadProgress(
            bytes_downloaded=bytes_downloaded,
            total_bytes=total_bytes,
            elapsed_seconds=elapsed_seconds,
        )
    )

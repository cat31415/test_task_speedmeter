from collections.abc import Callable
from typing import Protocol

from .models import (
    DownloadProgress,
    DownloadResult,
    MeasurementReport,
    ProgressCallback,
)


MeasurementProgressCallback = Callable[[int, int, DownloadProgress], None]


class Downloader(Protocol):
    def download(
        self,
        url: str,
        timeout: float,
        chunk_size: int,
        progress_callback: ProgressCallback | None = None,
    ) -> DownloadResult:
        raise NotImplementedError


class SpeedMeter:
    def __init__(self, downloader: Downloader) -> None:
        self._downloader = downloader

    def measure(
        self,
        url: str,
        request_count: int = 10,
        timeout: float = 30.0,
        chunk_size: int = 64 * 1024,
        progress_callback: MeasurementProgressCallback | None = None,
    ) -> MeasurementReport:
        if request_count <= 0:
            raise ValueError("request_count must be greater than zero")
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")

        total_bytes = 0
        total_time_seconds = 0.0

        for request_number in range(1, request_count + 1):
            if progress_callback is not None:
                progress_callback(
                    request_number,
                    request_count,
                    DownloadProgress(
                        bytes_downloaded=0,
                        total_bytes=None,
                        elapsed_seconds=0.0,
                    ),
                )

            request_progress_callback = None
            if progress_callback is not None:
                request_progress_callback = _bind_request_progress(
                    progress_callback,
                    request_number,
                    request_count,
                )

            result = self._downloader.download(
                url=url,
                timeout=timeout,
                chunk_size=chunk_size,
                progress_callback=request_progress_callback,
            )
            total_bytes += result.bytes_downloaded
            total_time_seconds += result.elapsed_seconds

        if total_time_seconds <= 0:
            raise ValueError("total download time must be greater than zero")

        return MeasurementReport(
            request_count=request_count,
            total_bytes=total_bytes,
            total_time_seconds=total_time_seconds,
            average_request_time_seconds=total_time_seconds / request_count,
            speed_mbps=(total_bytes / 1_000_000) / total_time_seconds,
        )


def _bind_request_progress(
    progress_callback: MeasurementProgressCallback,
    request_number: int,
    request_count: int,
) -> ProgressCallback:
    def handle_progress(progress: DownloadProgress) -> None:
        progress_callback(request_number, request_count, progress)

    return handle_progress

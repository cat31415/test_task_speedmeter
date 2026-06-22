from typing import Protocol

from .models import DownloadResult, MeasurementReport


class Downloader(Protocol):
    def download(self, url: str, timeout: float, chunk_size: int) -> DownloadResult:
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
    ) -> MeasurementReport:
        if request_count <= 0:
            raise ValueError("request_count must be greater than zero")
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")

        total_bytes = 0
        total_time_seconds = 0.0

        for _ in range(request_count):
            result = self._downloader.download(
                url=url,
                timeout=timeout,
                chunk_size=chunk_size,
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

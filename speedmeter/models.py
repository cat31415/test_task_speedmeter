from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class DownloadResult:
    bytes_downloaded: int
    elapsed_seconds: float


@dataclass(frozen=True)
class DownloadProgress:
    bytes_downloaded: int
    total_bytes: int | None
    elapsed_seconds: float


ProgressCallback = Callable[[DownloadProgress], None]


@dataclass(frozen=True)
class MeasurementReport:
    request_count: int
    total_bytes: int
    total_time_seconds: float
    average_request_time_seconds: float
    speed_mbps: float

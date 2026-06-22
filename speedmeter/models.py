from dataclasses import dataclass


@dataclass(frozen=True)
class DownloadResult:
    bytes_downloaded: int
    elapsed_seconds: float


@dataclass(frozen=True)
class MeasurementReport:
    request_count: int
    total_bytes: int
    total_time_seconds: float
    average_request_time_seconds: float
    speed_mbps: float

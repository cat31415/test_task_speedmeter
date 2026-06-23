import argparse
import sys
from collections.abc import Sequence
from time import monotonic
from typing import TextIO

from .downloader import DownloadError, UrlDownloader
from .measurement import SpeedMeter
from .models import DownloadProgress, MeasurementReport


DEFAULT_REQUESTS = 10
DEFAULT_TIMEOUT = 30.0
DEFAULT_CHUNK_SIZE = 64 * 1024


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    meter = SpeedMeter(UrlDownloader())
    progress = ProgressRenderer(sys.stderr)
    try:
        report = meter.measure(
            url=args.url,
            request_count=args.requests,
            timeout=args.timeout,
            chunk_size=args.chunk_size,
            progress_callback=progress.update,
        )
    except (DownloadError, ValueError) as exc:
        progress.finish()
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        progress.finish()
        print("Interrupted.", file=sys.stderr)
        return 130

    progress.finish()
    print(format_report(report))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="speedmeter",
        description=(
            "Measure download speed by sequentially fetching a URL several times."
        ),
    )
    parser.add_argument(
        "url",
        help="URL to download, preferably a large image or file.",
    )
    parser.add_argument(
        "-n",
        "--requests",
        type=_positive_int,
        default=DEFAULT_REQUESTS,
        help=f"number of sequential requests to run (default: {DEFAULT_REQUESTS})",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=_positive_float,
        default=DEFAULT_TIMEOUT,
        help=f"timeout for each request in seconds (default: {DEFAULT_TIMEOUT:g})",
    )
    parser.add_argument(
        "-c",
        "--chunk-size",
        type=_positive_int,
        default=DEFAULT_CHUNK_SIZE,
        help=(
            "read buffer size in bytes "
            f"(default: {DEFAULT_CHUNK_SIZE})"
        ),
    )
    return parser


def format_report(report: MeasurementReport) -> str:
    downloaded_mb = report.total_bytes / 1_000_000
    return "\n".join(
        (
            f"Requests: {report.request_count}",
            f"Average request time: {report.average_request_time_seconds:.3f} s",
            f"Total downloaded: {downloaded_mb:.3f} MB ({report.total_bytes} bytes)",
            f"Total time: {report.total_time_seconds:.3f} s",
            f"Download speed: {report.speed_mbps:.3f} MB/s",
        )
    )


class ProgressRenderer:
    def __init__(self, stream: TextIO, bar_width: int = 24) -> None:
        self._stream = stream
        self._bar_width = bar_width
        self._last_line_length = 0
        self._last_rendered_at = 0.0
        self._last_request_number: int | None = None

    def update(
        self,
        request_number: int,
        request_count: int,
        progress: DownloadProgress,
    ) -> None:
        if request_number != self._last_request_number:
            self._last_request_number = request_number
            self._last_rendered_at = 0.0

        now = monotonic()
        is_complete = (
            progress.total_bytes is not None
            and progress.bytes_downloaded >= progress.total_bytes
        )
        if not is_complete and now - self._last_rendered_at < 0.1:
            return

        self._last_rendered_at = now
        self._write_line(
            _format_progress_line(
                request_number=request_number,
                request_count=request_count,
                progress=progress,
                bar_width=self._bar_width,
            )
        )

    def finish(self) -> None:
        if self._last_line_length == 0:
            return

        print(file=self._stream, flush=True)
        self._last_line_length = 0

    def _write_line(self, line: str) -> None:
        padding = " " * max(0, self._last_line_length - len(line))
        print(f"\r{line}{padding}", end="", file=self._stream, flush=True)
        self._last_line_length = len(line)


def _format_progress_line(
    request_number: int,
    request_count: int,
    progress: DownloadProgress,
    bar_width: int,
) -> str:
    prefix = f"Request {request_number}/{request_count}"

    if progress.bytes_downloaded == 0 and progress.total_bytes is None:
        return f"{prefix} waiting for response..."

    speed_mbps = _speed_mbps(progress)
    downloaded = _format_mb(progress.bytes_downloaded)

    if progress.total_bytes is None:
        return f"{prefix} downloaded {downloaded} at {speed_mbps:.2f} MB/s"

    percent = min(100.0, progress.bytes_downloaded / progress.total_bytes * 100)
    total = _format_mb(progress.total_bytes)
    bar = _progress_bar(percent, bar_width)
    return (
        f"{prefix} {bar} {percent:5.1f}% "
        f"{downloaded}/{total} at {speed_mbps:.2f} MB/s"
    )


def _progress_bar(percent: float, width: int) -> str:
    filled = round(width * percent / 100)
    empty = width - filled
    return f"[{'#' * filled}{'-' * empty}]"


def _format_mb(bytes_count: int) -> str:
    return f"{bytes_count / 1_000_000:.2f} MB"


def _speed_mbps(progress: DownloadProgress) -> float:
    if progress.elapsed_seconds <= 0:
        return 0.0
    return progress.bytes_downloaded / 1_000_000 / progress.elapsed_seconds


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc

    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def _positive_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc

    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed

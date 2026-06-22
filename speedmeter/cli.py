import argparse
import sys
from collections.abc import Sequence

from .downloader import DownloadError, UrlDownloader
from .measurement import SpeedMeter
from .models import MeasurementReport


DEFAULT_REQUESTS = 10
DEFAULT_TIMEOUT = 30.0
DEFAULT_CHUNK_SIZE = 64 * 1024


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    meter = SpeedMeter(UrlDownloader())
    try:
        report = meter.measure(
            url=args.url,
            request_count=args.requests,
            timeout=args.timeout,
            chunk_size=args.chunk_size,
        )
    except (DownloadError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130

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

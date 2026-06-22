import unittest

from speedmeter.measurement import SpeedMeter
from speedmeter.models import DownloadResult


class FakeDownloader:
    def __init__(self, results: list[DownloadResult]) -> None:
        self._results = list(results)
        self.calls: list[tuple[str, float, int]] = []

    def download(self, url: str, timeout: float, chunk_size: int) -> DownloadResult:
        self.calls.append((url, timeout, chunk_size))
        return self._results.pop(0)


class SpeedMeterTests(unittest.TestCase):
    def test_measure_aggregates_download_results(self) -> None:
        downloader = FakeDownloader(
            [
                DownloadResult(bytes_downloaded=2_000_000, elapsed_seconds=1.0),
                DownloadResult(bytes_downloaded=3_000_000, elapsed_seconds=2.0),
            ]
        )

        report = SpeedMeter(downloader).measure(
            url="https://example.com/image.jpg",
            request_count=2,
            timeout=7,
            chunk_size=1024,
        )

        self.assertEqual(report.request_count, 2)
        self.assertEqual(report.total_bytes, 5_000_000)
        self.assertEqual(report.total_time_seconds, 3.0)
        self.assertEqual(report.average_request_time_seconds, 1.5)
        self.assertAlmostEqual(report.speed_mbps, 5 / 3)
        self.assertEqual(
            downloader.calls,
            [
                ("https://example.com/image.jpg", 7, 1024),
                ("https://example.com/image.jpg", 7, 1024),
            ],
        )

    def test_measure_validates_request_count(self) -> None:
        downloader = FakeDownloader([])

        with self.assertRaisesRegex(ValueError, "request_count"):
            SpeedMeter(downloader).measure(
                url="https://example.com/file",
                request_count=0,
            )


if __name__ == "__main__":
    unittest.main()

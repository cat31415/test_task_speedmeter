import unittest

from speedmeter.measurement import SpeedMeter
from speedmeter.models import DownloadProgress, DownloadResult, ProgressCallback


class FakeDownloader:
    def __init__(self, results: list[DownloadResult]) -> None:
        self._results = list(results)
        self.calls: list[tuple[str, float, int]] = []

    def download(
        self,
        url: str,
        timeout: float,
        chunk_size: int,
        progress_callback: ProgressCallback | None = None,
    ) -> DownloadResult:
        self.calls.append((url, timeout, chunk_size))
        result = self._results.pop(0)
        if progress_callback is not None:
            progress_callback(
                DownloadProgress(
                    bytes_downloaded=result.bytes_downloaded,
                    total_bytes=result.bytes_downloaded,
                    elapsed_seconds=result.elapsed_seconds,
                )
            )
        return result


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

    def test_measure_reports_request_progress(self) -> None:
        downloader = FakeDownloader(
            [
                DownloadResult(bytes_downloaded=10, elapsed_seconds=1.0),
                DownloadResult(bytes_downloaded=20, elapsed_seconds=1.0),
            ]
        )
        updates: list[tuple[int, int, DownloadProgress]] = []

        SpeedMeter(downloader).measure(
            url="https://example.com/file",
            request_count=2,
            progress_callback=lambda request_number, request_count, progress: (
                updates.append((request_number, request_count, progress))
            ),
        )

        self.assertEqual(updates[0][0], 1)
        self.assertEqual(updates[0][1], 2)
        self.assertEqual(updates[0][2].bytes_downloaded, 0)
        self.assertEqual(updates[-1][0], 2)
        self.assertEqual(updates[-1][1], 2)
        self.assertEqual(updates[-1][2].bytes_downloaded, 20)


if __name__ == "__main__":
    unittest.main()

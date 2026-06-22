import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from speedmeter.downloader import DownloadError, UrlDownloader


class PayloadHandler(BaseHTTPRequestHandler):
    payload = b"download-test-data" * 128

    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Length", str(len(self.payload)))
        self.end_headers()
        self.wfile.write(self.payload)

    def log_message(self, format: str, *args: object) -> None:
        return


class EmptyPayloadHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        return


class UrlDownloaderTests(unittest.TestCase):
    def test_download_reads_response_body_in_chunks(self) -> None:
        with no_proxy_for_localhost(), running_server(PayloadHandler) as url:
            result = UrlDownloader().download(url, timeout=5, chunk_size=17)

        self.assertEqual(result.bytes_downloaded, len(PayloadHandler.payload))
        self.assertGreater(result.elapsed_seconds, 0)

    def test_download_rejects_empty_body(self) -> None:
        with no_proxy_for_localhost(), running_server(EmptyPayloadHandler) as url:
            with self.assertRaisesRegex(DownloadError, "empty"):
                UrlDownloader().download(url, timeout=5, chunk_size=64)


def no_proxy_for_localhost():
    return patch.dict(
        "os.environ",
        {
            "NO_PROXY": "127.0.0.1,localhost",
            "no_proxy": "127.0.0.1,localhost",
        },
    )


class running_server:
    def __init__(self, handler_class: type[BaseHTTPRequestHandler]) -> None:
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), handler_class)
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            daemon=True,
        )

    def __enter__(self) -> str:
        self._thread.start()
        host, port = self._server.server_address
        return f"http://{host}:{port}/file"

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()

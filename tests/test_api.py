import http.server
import json
import os
import threading
import unittest
from unittest.mock import MagicMock, patch

from resqui.api import APIClient, DEFAULT_ENDPOINT


class _RecordingHandler(http.server.BaseHTTPRequestHandler):
    """Records every POST it receives and answers with a configurable status."""

    response_status = 201

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        self.server.requests.append(
            {
                "path": self.path,
                "headers": dict(self.headers),
                "body": self.rfile.read(length).decode("utf-8"),
            }
        )
        self.send_response(self.server.response_status)
        self.end_headers()
        self.wfile.write(b"[]")

    def log_message(self, *args):
        pass


class _LocalServer:
    """A real HTTP server on 127.0.0.1, standing in for a self-hosted PostgREST."""

    def __init__(self, response_status=201):
        self.httpd = http.server.HTTPServer(("127.0.0.1", 0), _RecordingHandler)
        self.httpd.requests = []
        self.httpd.response_status = response_status
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    @property
    def url(self):
        host, port = self.httpd.server_address
        return f"http://{host}:{port}"

    @property
    def requests(self):
        return self.httpd.requests

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.httpd.shutdown()
        self.httpd.server_close()


class TestAPIClientEndpoint(unittest.TestCase):
    def setUp(self):
        env = patch.dict(os.environ, {}, clear=False)
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("DASHVERSE_ENDPOINT", None)

    def test_default_endpoint_is_public_dashverse_over_https(self):
        self.assertEqual(DEFAULT_ENDPOINT, "https://api.dashverse.cloud")
        with patch("resqui.api.http.client.HTTPSConnection") as MockHTTPS:
            conn = MockHTTPS.return_value
            conn.getresponse.return_value = MagicMock(status=201, reason="Created")
            conn.getresponse.return_value.read.return_value = b"[]"
            APIClient("tok").post("{}")
        MockHTTPS.assert_called_once_with("api.dashverse.cloud", None)
        method, path = conn.request.call_args[0][:2]
        self.assertEqual((method, path), ("POST", "/assessment"))

    def test_http_endpoint_posts_to_self_hosted_server(self):
        with _LocalServer() as server:
            APIClient("tok", endpoint=server.url).post('{"a": 1}')
        self.assertEqual(len(server.requests), 1)
        req = server.requests[0]
        self.assertEqual(req["path"], "/assessment")
        self.assertEqual(req["headers"]["Authorization"], "Bearer tok")
        self.assertEqual(json.loads(req["body"]), {"a": 1})

    def test_endpoint_from_environment_variable(self):
        with _LocalServer() as server:
            with patch.dict(os.environ, {"DASHVERSE_ENDPOINT": server.url}):
                APIClient("tok").post("{}")
        self.assertEqual(len(server.requests), 1)

    def test_explicit_endpoint_overrides_environment_variable(self):
        with _LocalServer() as server:
            env = {"DASHVERSE_ENDPOINT": "http://127.0.0.1:1"}
            with patch.dict(os.environ, env):
                APIClient("tok", endpoint=server.url).post("{}")
        self.assertEqual(len(server.requests), 1)

    def test_empty_environment_variable_falls_back_to_default(self):
        with patch.dict(os.environ, {"DASHVERSE_ENDPOINT": ""}):
            client = APIClient("tok")
        self.assertEqual(client.endpoint, DEFAULT_ENDPOINT)

    def test_base_path_is_prefixed_to_assessment_route(self):
        with _LocalServer() as server:
            APIClient("tok", endpoint=server.url + "/postgrest/").post("{}")
        self.assertEqual(server.requests[0]["path"], "/postgrest/assessment")

    def test_endpoint_without_scheme_defaults_to_https(self):
        with patch("resqui.api.http.client.HTTPSConnection") as MockHTTPS:
            conn = MockHTTPS.return_value
            conn.getresponse.return_value = MagicMock(status=201, reason="Created")
            conn.getresponse.return_value.read.return_value = b"[]"
            APIClient("tok", endpoint="dashverse.example.org:8443").post("{}")
        MockHTTPS.assert_called_once_with("dashverse.example.org", 8443)

    def test_unsupported_scheme_raises_value_error(self):
        with self.assertRaises(ValueError):
            APIClient("tok", endpoint="ftp://dashverse.example.org")

    def test_non_2xx_response_raises_runtime_error(self):
        with _LocalServer(response_status=401) as server:
            client = APIClient("tok", endpoint=server.url)
            with self.assertRaises(RuntimeError) as ctx:
                client.post("{}")
        self.assertIn("401", str(ctx.exception))

    def test_missing_token_still_raises_value_error(self):
        with patch.dict(os.environ, {"DASHVERSE_TOKEN": ""}):
            with self.assertRaises(ValueError):
                APIClient(endpoint="http://127.0.0.1:1")


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3

import http.client
import os
from urllib.parse import urlsplit
from resqui.version import version

DEFAULT_ENDPOINT = "https://api.dashverse.cloud"


class APIClient:
    """
    Client for the DashVERSE (PostgREST) API.

    The endpoint is taken from the `endpoint` argument, then the
    `DASHVERSE_ENDPOINT` environment variable, then `DEFAULT_ENDPOINT`.
    It may include a scheme (http/https, default https), a port and a
    base path, e.g. `http://192.168.1.10:3000` or `https://example.org/api`.
    """

    def __init__(self, bearer_token=None, endpoint=None):
        if bearer_token is None:
            bearer_token = os.environ.get("DASHVERSE_TOKEN")
        if bearer_token is None or bearer_token == "":
            raise ValueError("Missing authentication token")
        if not endpoint:
            endpoint = os.environ.get("DASHVERSE_ENDPOINT") or DEFAULT_ENDPOINT
        if "://" not in endpoint:
            endpoint = f"https://{endpoint}"
        url = urlsplit(endpoint)
        if url.scheme not in ("http", "https") or not url.hostname:
            raise ValueError(f"Invalid DashVERSE endpoint: {endpoint}")
        self.endpoint = endpoint
        self._scheme = url.scheme
        self._host = url.hostname
        self._port = url.port
        self._path = url.path.rstrip("/") + "/assessment"
        self.headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
            # TODO: turn this into minimal in production
            "Prefer": "return=representation",
            "User-Agent": f"resqui/{version}",
        }

    def post(self, payload):
        if self._scheme == "https":
            conn = http.client.HTTPSConnection(self._host, self._port)
        else:
            conn = http.client.HTTPConnection(self._host, self._port)
        conn.request("POST", self._path, payload, self.headers)
        res = conn.getresponse()
        status = res.status
        reason = res.reason
        data = res.read().decode("utf-8")
        if not (200 <= status < 300):
            raise RuntimeError(f"Request failed with {status} {reason}: {data}")

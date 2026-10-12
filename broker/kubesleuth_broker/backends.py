"""HTTP clients for the observability stack.

Base URLs come from the broker's own configuration, never from the model, so a
tool call cannot be turned into a request to an arbitrary host (no SSRF).
"""
from __future__ import annotations

import json
import time
from typing import Protocol

import httpx

TIMEOUT = httpx.Timeout(10.0, connect=3.0)


class BackendUnavailable(Exception):
    pass


class _Http:
    def __init__(self, base_url: str, name: str):
        self.base = base_url.rstrip("/")
        self.name = name
        self._c = httpx.Client(timeout=TIMEOUT, follow_redirects=False)

    def get(self, path: str, params: dict) -> dict | list:
        if not self.base:
            raise BackendUnavailable(f"{self.name} is not configured")
        try:
            r = self._c.get(self.base + path, params=params)
        except httpx.HTTPError as exc:
            raise BackendUnavailable(f"{self.name} unreachable: {type(exc).__name__}") from exc
        if r.status_code >= 400:
            raise BackendUnavailable(f"{self.name} returned HTTP {r.status_code}: {r.text[:300]}")
        return r.json()


# ---------------------------------------------------------------- protocols
class Metrics(Protocol):
    def query_range(self, promql: str, start: float, end: float, step: int) -> list[dict]: ...


class Logs(Protocol):
    def query_range(self, logql: str, start: float, end: float, limit: int) -> list[tuple[str, str, dict]]: ...


class Traces(Protocol):
    def find_traces(self, service: str, start: float, end: float, limit: int, errors_only: bool) -> list[dict]: ...
    def dependencies(self, end: float, lookback_s: int) -> list[dict]: ...


class Alerts(Protocol):
    def active(self) -> list[dict]: ...


# ---------------------------------------------------------------- live
class Prometheus(_Http):
    def __init__(self, base_url: str):
        super().__init__(base_url, "prometheus")

    def query_range(self, promql, start, end, step):
        doc = self.get("/api/v1/query_range", {"query": promql, "start": start, "end": end, "step": step,
                                                "timeout": "8s"})
        if doc.get("status") != "success":
            raise BackendUnavailable(f"prometheus error: {doc.get('error')}")
        return doc["data"]["result"]


class Loki(_Http):
    def __init__(self, base_url: str):
        super().__init__(base_url, "loki")

    def query_range(self, logql, start, end, limit):
        doc = self.get("/loki/api/v1/query_range", {
            "query": logql, "start": int(start * 1e9), "end": int(end * 1e9), "limit": limit,
            "direction": "backward"})
        out = []
        for stream in doc.get("data", {}).get("result", []):
            labels = stream.get("stream", {})
            for ts_ns, line in stream.get("values", []):
                out.append((ts_ns, line, labels))
        out.sort(key=lambda x: x[0])
        return out


class Jaeger(_Http):
    def __init__(self, base_url: str):
        super().__init__(base_url, "jaeger")

    def find_traces(self, service, start, end, limit, errors_only):
        params = {"service": service, "start": int(start * 1e6), "end": int(end * 1e6), "limit": limit}
        if errors_only:
            params["tags"] = json.dumps({"error": "true"})
        return self.get("/api/traces", params).get("data") or []

    def dependencies(self, end, lookback_s):
        return self.get("/api/dependencies", {"endTs": int(end * 1000), "lookback": lookback_s * 1000}).get("data") or []


class Alertmanager(_Http):
    def __init__(self, base_url: str):
        super().__init__(base_url, "alertmanager")

    def active(self):
        return self.get("/api/v2/alerts", {"active": "true", "silenced": "false", "inhibited": "false"})


def now() -> float:
    return time.time()

"""HTTP transport with Requests as the fast path and urllib as a fallback."""

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from .context import render_value

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None


def build_url(base_url: str, path: str, params: dict[str, Any] | None) -> str:
    if path.startswith(("http://", "https://")):
        url = path
    else:
        url = base_url.rstrip("/") + "/" + path.lstrip("/")
    if params:
        query = urllib.parse.urlencode(params, doseq=True)
        url += ("&" if "?" in url else "?") + query
    return url


class HttpTransport:
    """Execute one HTTP case and return the runner's normalized response shape."""

    def request(
        self,
        case: dict[str, Any],
        base_url: str,
        context: dict[str, Any],
        timeout: int | float,
    ) -> dict[str, Any]:
        method = case.get("method", "GET").upper()
        headers = render_value(case.get("headers", {}), context)
        params = render_value(case.get("params", {}), context)
        body = render_value(case.get("json"), context)
        path = render_value(case.get("path", ""), context)
        url = build_url(base_url, path, params)
        if requests is not None:
            return self._request_with_requests(method, url, headers, body, timeout)
        return self._request_with_urllib(method, url, headers, body, timeout)

    @staticmethod
    def _normalize(
        url: str,
        method: str,
        status_code: int | None,
        elapsed_ms: float,
        raw_text: str,
        error: str | None,
    ) -> dict[str, Any]:
        try:
            json_body = json.loads(raw_text) if raw_text else None
        except (TypeError, ValueError):
            json_body = None
        return {
            "url": url, "method": method, "status_code": status_code,
            "elapsed_ms": elapsed_ms, "text": raw_text, "json": json_body,
            "error": error,
        }

    def _request_with_requests(self, method, url, headers, body, timeout):
        started = time.perf_counter()
        status_code, raw_text, error = None, "", None
        try:
            response = requests.request(
                method=method, url=url, headers=headers, json=body, timeout=timeout
            )
            status_code, raw_text = response.status_code, response.text
        except Exception as exc:
            error = str(exc)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        return self._normalize(url, method, status_code, elapsed_ms, raw_text, error)

    def _request_with_urllib(self, method, url, headers, body, timeout):
        data = None
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            headers.setdefault("Content-Type", "application/json; charset=utf-8")
        request = urllib.request.Request(url=url, data=data, headers=headers, method=method)
        started = time.perf_counter()
        status_code, raw_text, error = None, "", None
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                status_code = response.getcode()
                raw_text = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            status_code = exc.code
            raw_text = exc.read().decode("utf-8", errors="replace")
            error = str(exc)
        except Exception as exc:  # pragma: no cover
            error = str(exc)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        return self._normalize(url, method, status_code, elapsed_ms, raw_text, error)


_DEFAULT_TRANSPORT = HttpTransport()


def request(case, base_url, context, timeout):
    """Backward-compatible function wrapper around HttpTransport."""
    return _DEFAULT_TRANSPORT.request(case, base_url, context, timeout)

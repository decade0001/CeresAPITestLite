"""Assertion registry and built-in response checks."""

from collections.abc import Callable
from typing import Any

from .context import get_by_path, render_value

AssertionHandler = Callable[[dict[str, Any], dict[str, Any]], tuple[bool, str]]
_ASSERTIONS: dict[str, AssertionHandler] = {}


def register_assertion(name: str, handler: AssertionHandler) -> None:
    _ASSERTIONS[name] = handler


def _status_code(assertion, response):
    expected = assertion.get("equals")
    return response["status_code"] == expected, f"status_code == {expected}"


def _response_time(assertion, response):
    threshold = assertion.get("ms")
    return response["elapsed_ms"] < threshold, f"elapsed_ms < {threshold}"


def _contains(assertion, response):
    value = assertion.get("value", "")
    return value in response.get("text", ""), f"response contains {value}"


def _json_field_exists(assertion, response):
    path = assertion.get("path")
    get_by_path(response["json"], path)
    return True, f"json field exists: {path}"


def _json_field_equals(assertion, response):
    path = assertion.get("path")
    expected = assertion.get("equals")
    actual = get_by_path(response["json"], path)
    return actual == expected, f"json {path} == {expected}, actual={actual}"


def _json_field_not_empty(assertion, response):
    path = assertion.get("path")
    actual = get_by_path(response["json"], path)
    return actual not in (None, "", [], {}), f"json {path} is not empty"


register_assertion("status_code", _status_code)
register_assertion("response_time_less_than", _response_time)
register_assertion("contains", _contains)
register_assertion("json_field_exists", _json_field_exists)
register_assertion("json_field_equals", _json_field_equals)
register_assertion("json_field_not_empty", _json_field_not_empty)


def check_assertion(assertion, response, context):
    rendered = render_value(assertion, context)
    kind = rendered.get("type")
    handler = _ASSERTIONS.get(kind)
    if handler is None:
        return False, f"unknown assertion type: {kind}"
    try:
        return handler(rendered, response)
    except Exception as exc:
        return False, f"{kind} failed: {exc}"

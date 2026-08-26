"""Response value extraction for passing data between cases."""

from typing import Any

from .context import get_by_path, set_context_value


def extract_values(
    extract_rules: dict[str, str] | None,
    response: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    extracted: dict[str, Any] = {}
    for name, path in (extract_rules or {}).items():
        try:
            value = get_by_path(response["json"], path)
            set_context_value(context, name, value)
            extracted[name] = value
        except Exception as exc:
            extracted[name] = f"<extract failed: {exc}>"
    return extracted

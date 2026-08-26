"""Variable context and dotted-path utilities used by test cases."""

from typing import Any


def get_by_path(data: Any, path: str | None) -> Any:
    """Read nested dictionaries/lists using paths such as data.list.0.name."""
    if path in ("", None):
        return data
    current = data
    for part in str(path).split("."):
        if isinstance(current, list):
            current = current[int(part)]
        elif isinstance(current, dict):
            current = current[part]
        else:
            raise KeyError(path)
    return current


def set_context_value(context: dict[str, Any], name: str, value: Any) -> None:
    context[name] = value


def render_value(value: Any, context: dict[str, Any]) -> Any:
    """Recursively replace ${variable} placeholders without mutating input."""
    if isinstance(value, str):
        rendered = value
        for key, item in context.items():
            rendered = rendered.replace("${" + key + "}", str(item))
        return rendered
    if isinstance(value, dict):
        return {key: render_value(item, context) for key, item in value.items()}
    if isinstance(value, list):
        return [render_value(item, context) for item in value]
    return value

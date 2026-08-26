"""JSON and HTML report generation."""

import html
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import dump_json

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:  # pragma: no cover
    Environment = None


def render_html(summary: dict[str, Any]) -> str:
    template_dir = Path(__file__).resolve().parent.parent / "templates"
    template_path = template_dir / "report.html.j2"
    if Environment is not None and template_path.exists():
        environment = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )
        return environment.get_template("report.html.j2").render(summary=summary)

    rows = []
    for item in summary["results"]:
        response = item.get("response", {})
        status = "PASS" if item["passed"] else "FAIL"
        css_class = "pass" if item["passed"] else "fail"
        assertions = "<br>".join(
            ("PASS " if check["passed"] else "FAIL ")
            + html.escape(check["message"])
            for check in item.get("assertions", [])
        )
        rows.append(
            "<tr>"
            f"<td>{item['index']}</td><td>{html.escape(item['name'])}</td>"
            f"<td class='{css_class}'>{status}</td>"
            f"<td>{html.escape(str(response.get('method', '')))}</td>"
            f"<td>{html.escape(str(response.get('status_code', '')))}</td>"
            f"<td>{html.escape(str(response.get('elapsed_ms', '')))}</td>"
            f"<td>{html.escape(str(response.get('url', '')))}</td><td>{assertions}</td></tr>"
        )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{html.escape(summary['suite'])}</title>
<style>body{{font-family:Arial,sans-serif;margin:24px;color:#1f2937}}table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{border:1px solid #e5e7eb;padding:8px;vertical-align:top}}th{{background:#f3f4f6;text-align:left}}.pass{{color:#047857;font-weight:700}}.fail{{color:#b91c1c;font-weight:700}}</style>
</head><body><h1>{html.escape(summary['suite'])}</h1>
<p>Total: {summary['total']} | Passed: {summary['passed']} | Failed: {summary['failed']}</p>
<table><thead><tr><th>#</th><th>Case</th><th>Status</th><th>Method</th><th>HTTP</th><th>ms</th><th>URL</th><th>Assertions</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></body></html>"""


def write_reports(summary: dict[str, Any], report_dir: str | Path) -> None:
    output_dir = Path(report_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"api_report_{stamp}.json"
    html_path = output_dir / f"api_report_{stamp}.html"
    dump_json(json_path, summary)
    html_path.write_text(render_html(summary), encoding="utf-8")
    summary["json_report"] = str(json_path)
    summary["html_report"] = str(html_path)

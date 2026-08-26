"""Suite orchestration: load, render, execute, extract, assert, summarize."""

import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from .assertions import check_assertion
from .config import load_json
from .extractors import extract_values
from .reporting import write_reports
from .transport import request


def run_suite(
    case_path: str | Path,
    override_base_url: str | None = None,
    report_dir: str | Path = "reports",
    timeout: int | float = 8,
    stop_on_fail: bool = False,
) -> dict[str, Any]:
    """Run cases sequentially so extracted values can feed later requests."""
    suite = load_json(case_path)
    base_url = override_base_url or suite.get("base_url", "")
    context = dict(suite.get("variables", {}))
    global_headers = suite.get("global_headers", {})
    results = []

    for index, case in enumerate(suite.get("cases", []), start=1):
        merged = dict(case)
        merged["headers"] = {**global_headers, **case.get("headers", {})}
        result = {
            "index": index,
            "name": case.get("name", f"case-{index}"),
            "passed": False,
            "assertions": [],
            "extracted": {},
        }
        try:
            response = request(merged, base_url, context, timeout)
            result["response"] = response
            result["extracted"] = extract_values(case.get("extract"), response, context)
            result["assertions"] = [
                {"passed": passed, "message": message}
                for assertion in case.get("assertions", [])
                for passed, message in [check_assertion(assertion, response, context)]
            ]
            result["passed"] = bool(result["assertions"]) and all(
                item["passed"] for item in result["assertions"]
            )
        except Exception:
            result["response"] = {
                "error": traceback.format_exc(),
                "status_code": None,
                "elapsed_ms": None,
                "text": "",
            }
            result["assertions"] = [{"passed": False, "message": "case execution error"}]
        results.append(result)
        if stop_on_fail and not result["passed"]:
            break

    summary = {
        "suite": suite.get("name", Path(case_path).stem),
        "base_url": base_url,
        "total": len(results),
        "passed": sum(1 for item in results if item["passed"]),
        "failed": sum(1 for item in results if not item["passed"]),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "results": results,
    }
    write_reports(summary, report_dir)
    return summary

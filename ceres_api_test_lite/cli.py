"""Command-line entry point for the modular runner."""

import argparse
import sys

from .runner import run_suite


def main() -> None:
    parser = argparse.ArgumentParser(description="CeresAPITestLite - generic API test runner")
    parser.add_argument("--case", default="cases/demo_cases.json", help="case json file")
    parser.add_argument("--base-url", default=None, help="override base url")
    parser.add_argument("--report-dir", default="reports", help="report output directory")
    parser.add_argument("--timeout", type=int, default=8, help="request timeout seconds")
    parser.add_argument("--stop-on-fail", action="store_true", help="stop after first failed case")
    args = parser.parse_args()
    summary = run_suite(args.case, args.base_url, args.report_dir, args.timeout, args.stop_on_fail)
    print(f"total={summary['total']} passed={summary['passed']} failed={summary['failed']}")
    print(f"html_report={summary['html_report']}")
    sys.exit(0 if summary["failed"] == 0 else 1)

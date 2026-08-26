#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Backward-compatible CLI and import facade for CeresAPITestLite."""

from ceres_api_test_lite.assertions import check_assertion, register_assertion
from ceres_api_test_lite.config import dump_json, load_json
from ceres_api_test_lite.context import get_by_path, render_value, set_context_value
from ceres_api_test_lite.extractors import extract_values
from ceres_api_test_lite.reporting import render_html, write_reports
from ceres_api_test_lite.runner import run_suite
from ceres_api_test_lite.transport import HttpTransport, build_url, request
from ceres_api_test_lite.cli import main

__all__ = [
    "HttpTransport", "build_url", "check_assertion", "dump_json",
    "extract_values", "get_by_path", "load_json", "register_assertion",
    "render_html", "render_value", "request", "run_suite",
    "set_context_value", "write_reports",
]


if __name__ == "__main__":
    main()

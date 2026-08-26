import unittest

from ceres_api_test_lite.assertions import check_assertion
from ceres_api_test_lite.context import get_by_path, render_value
from ceres_api_test_lite.transport import build_url


class CoreTests(unittest.TestCase):
    def test_get_by_path_supports_dicts_and_lists(self):
        data = {"data": {"items": [{"id": 7}]}}
        self.assertEqual(get_by_path(data, "data.items.0.id"), 7)

    def test_render_value_replaces_nested_placeholders(self):
        self.assertEqual(
            render_value({"headers": {"Authorization": "Bearer ${token}"}}, {"token": "abc"}),
            {"headers": {"Authorization": "Bearer abc"}},
        )

    def test_json_field_assertion(self):
        passed, _ = check_assertion(
            {"type": "json_field_equals", "path": "code", "equals": 200},
            {"json": {"code": 200}},
            {},
        )
        self.assertTrue(passed)

    def test_build_url_encodes_query_parameters(self):
        self.assertEqual(
            build_url("http://localhost:8080/", "/products", {"q": "red shoes"}),
            "http://localhost:8080/products?q=red+shoes",
        )


if __name__ == "__main__":
    unittest.main()

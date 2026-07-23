from __future__ import annotations

import unittest

from specs.tooling.strict_json import StrictJSONError, loads_strict


class StrictJSONTests(unittest.TestCase):
    def test_accepts_object(self) -> None:
        self.assertEqual(loads_strict('{"value": 1}'), {"value": 1})

    def test_rejects_duplicate_keys(self) -> None:
        with self.assertRaisesRegex(StrictJSONError, "duplicate object key"):
            loads_strict('{"value": 1, "value": 2}')

    def test_rejects_non_standard_constants(self) -> None:
        with self.assertRaisesRegex(StrictJSONError, "non-standard JSON constant"):
            loads_strict('{"value": NaN}')

    def test_rejects_non_object_top_level(self) -> None:
        with self.assertRaisesRegex(StrictJSONError, "top-level"):
            loads_strict("[]")


if __name__ == "__main__":
    unittest.main()

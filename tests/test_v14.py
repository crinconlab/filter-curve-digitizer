"""Basic regression tests for version comparison and calibration mapping."""
import unittest
from Filter_Curve_Digitizer import APP_VERSION, Digitizer, parse_version


class VersionTests(unittest.TestCase):
    def test_current_version(self):
        self.assertEqual(parse_version(APP_VERSION), parse_version("v1.4.0"))

    def test_older_versions(self):
        self.assertLess(parse_version("v1.3b"), parse_version("v1.4.0"))
        self.assertLess(parse_version("v1.3"), parse_version("v1.3b"))
        self.assertLess(parse_version("v1.4a"), parse_version("v1.4"))

    def test_invalid_versions(self):
        self.assertIsNone(parse_version("latest"))
        self.assertIsNone(parse_version("v1.4.0-rc1"))

    def test_axis_mapping_unchanged(self):
        lo, hi, xs = Digitizer.coordinates(400, 700, 100, 400, 60, 450, 1)
        self.assertAlmostEqual(lo, 360)
        self.assertAlmostEqual(hi, 750)
        self.assertAlmostEqual(xs[0], 360)
        self.assertAlmostEqual(xs[-1], 750)


if __name__ == "__main__":
    unittest.main()

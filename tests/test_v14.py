"""Regression tests for calibration and offline-simulated GitHub update checks."""
import io
import json
import queue
import ssl
import unittest
import urllib.error
from unittest.mock import Mock, patch
from Filter_Curve_Digitizer import (
    APP_VERSION, RELEASES_URL, LATEST_RELEASE_API, Digitizer, parse_version, github_ssl_context
)


class VersionTests(unittest.TestCase):
    def test_current_version(self):
        self.assertEqual(parse_version(APP_VERSION), parse_version("v1.4.0"))

    def test_older_versions(self):
        self.assertLess(parse_version("v1.3b"), parse_version("v1.4.0"))
        self.assertLess(parse_version("v1.3b"), parse_version("v1.3"))
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


class ImmediateThread:
    """Execute the real worker synchronously, so no network or timing dependence."""
    def __init__(self, target, daemon=False):
        self.target = target

    def start(self):
        self.target()


class MockResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class UpdateSimulationTests(unittest.TestCase):
    def setUp(self):
        # No Tk window required: test the real update-check methods with UI mocks.
        self.app = object.__new__(Digitizer)
        self.app.settings = {}
        self.app.update_queue = queue.Queue()
        self.app.update_running = False
        self.app.root = Mock()
        # Run the UI callback immediately; worker is also synchronous in this test.
        self.app.root.after.side_effect = lambda _delay, callback: callback()

    def run_simulation(self, release_tag=None, error=None, manual=True, accept=False):
        if error:
            response = Mock(side_effect=error)
        else:
            response = Mock(return_value=MockResponse(
                json.dumps({"tag_name": release_tag}).encode("utf-8")
            ))
        with (
            patch("Filter_Curve_Digitizer.threading.Thread", ImmediateThread),
            patch("Filter_Curve_Digitizer.urllib.request.urlopen", response),
            patch("Filter_Curve_Digitizer.messagebox.askyesno", return_value=accept) as ask,
            patch("Filter_Curve_Digitizer.messagebox.showinfo") as info,
            patch("Filter_Curve_Digitizer.messagebox.showwarning") as warning,
            patch("Filter_Curve_Digitizer.webbrowser.open") as browser,
            patch("Filter_Curve_Digitizer.save_settings"),
        ):
            self.app.check_for_updates(manual=manual)
            self.assertFalse(self.app.update_running)
            return ask.call_args_list, info.call_args_list, warning.call_args_list, browser.call_args_list, response.call_args_list

    def test_ssl_context_preserves_certificate_verification(self):
        context = github_ssl_context()
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(context.check_hostname)

    def test_update_request_explicitly_uses_verified_context(self):
        _, _, _, _, requests = self.run_simulation("v1.4.0")
        self.assertIn("context", requests[0].kwargs)
        context = requests[0].kwargs["context"]
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(context.check_hostname)

    def test_preview_menu_simulation_shows_labelled_prompt_without_network(self):
        with (
            patch("Filter_Curve_Digitizer.messagebox.askyesno", return_value=True) as ask,
            patch("Filter_Curve_Digitizer.webbrowser.open") as browser,
            patch("Filter_Curve_Digitizer.urllib.request.urlopen") as network,
        ):
            self.app.simulate_update_notification()
            network.assert_not_called()
            self.assertEqual(len(ask.call_args_list), 1)
            self.assertIn("TEST ONLY", ask.call_args.args[0])
            self.assertIn("NOT published", ask.call_args.args[1])
            self.assertIn("v1.5.0", ask.call_args.args[1])
            browser.assert_called_once_with(RELEASES_URL)

    def test_newer_release_prompts_and_opens_real_releases_page_if_accepted(self):
        asks, infos, warnings, browsers, requests = self.run_simulation("v1.5.0", accept=True)
        self.assertEqual(len(asks), 1)
        self.assertIn("1.5.0", str(asks[0]))
        self.assertEqual(browsers[0].args[0], RELEASES_URL)
        self.assertEqual(len(browsers), 1)
        self.assertFalse(infos or warnings)
        self.assertEqual(requests[0].args[0].full_url, LATEST_RELEASE_API)

    def test_user_can_decline_update(self):
        asks, infos, warnings, browsers, _ = self.run_simulation("v1.5.0", accept=False)
        self.assertEqual(len(asks), 1)
        self.assertFalse(browsers or infos or warnings)

    def test_current_version_does_not_prompt(self):
        asks, infos, warnings, browsers, _ = self.run_simulation("v1.4.0")
        self.assertFalse(asks or warnings or browsers)
        self.assertEqual(len(infos), 1)

    def test_older_version_does_not_prompt(self):
        asks, infos, warnings, browsers, _ = self.run_simulation("v1.3b", manual=False)
        self.assertFalse(asks or infos or warnings or browsers)

    def test_network_failure_is_silent_for_automatic_checks(self):
        asks, infos, warnings, browsers, _ = self.run_simulation(
            error=OSError("offline"), manual=False
        )
        self.assertFalse(asks or infos or warnings or browsers)

    def test_no_stable_release_is_informational_not_an_error(self):
        missing = urllib.error.HTTPError(
            LATEST_RELEASE_API, 404, "Not Found", {}, None
        )
        asks, infos, warnings, browsers, _ = self.run_simulation(error=missing)
        self.assertFalse(asks or warnings or browsers)
        self.assertEqual(len(infos), 1)
        self.assertIn("No stable release", str(infos[0]))

    def test_manual_network_failure_displays_warning(self):
        asks, infos, warnings, browsers, _ = self.run_simulation(
            error=OSError("offline"), manual=True
        )
        self.assertEqual(len(warnings), 1)
        self.assertFalse(asks or infos or browsers)

    def test_unsupported_tag_is_not_treated_as_newer(self):
        asks, infos, warnings, browsers, _ = self.run_simulation("v1.5.0-rc1")
        self.assertEqual(len(warnings), 1)
        self.assertFalse(asks or infos or browsers)

    def test_automatic_check_respects_user_opt_out(self):
        self.app.settings["auto_check_updates"] = False
        with patch.object(self.app, "check_for_updates") as check:
            self.app._check_updates_on_start()
            check.assert_not_called()

    def test_automatic_check_respects_24_hour_interval(self):
        with patch("Filter_Curve_Digitizer.time.time", return_value=500000):
            self.app.settings["last_update_check"] = 500000 - 3600
            with patch.object(self.app, "check_for_updates") as check:
                self.app._check_updates_on_start()
                check.assert_not_called()


if __name__ == "__main__":
    unittest.main()

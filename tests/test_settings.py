# Copyright (C) 2026 EQQX2. SPDX-License-Identifier: GPL-3.0-or-later
"""Settings: start with Windows, close button, automatic rescan."""
import importlib
import time
import unittest
from unittest import mock

importlib.import_module("sdk_stub")
import app_stub
from test_app import StopLoop, bare_app, sleeps_then_stops

m = app_stub.load()
import startup


class StartupCommandTest(unittest.TestCase):
    def test_tray_mode_adds_the_flag(self):
        self.assertTrue(startup.command("tray", "C:\\EqRGB").endswith('rgb_app.pyw" --tray'))

    def test_window_mode_has_no_flag(self):
        self.assertTrue(startup.command("window", "C:\\EqRGB").endswith('rgb_app.pyw"'))


class SettingsApiTest(unittest.TestCase):
    def setUp(self):
        self.a = bare_app()
        self.api = m.Api(self.a)
        p = mock.patch.object(m.rgb, "save_state")
        p.start()
        self.addCleanup(p.stop)

    def test_close_action(self):
        self.api.set_close_action("quit")
        self.assertEqual(self.a.state["close_action"], "quit")
        self.api.set_close_action("whatever")
        self.assertEqual(self.a.state["close_action"], "tray")

    def test_rescan_every_validates(self):
        self.assertIn("error", self.api.set_rescan_every("abc"))
        self.assertIn("error", self.api.set_rescan_every(-1))
        self.assertIn("error", self.api.set_rescan_every(5000))
        self.api.set_rescan_every("15")
        self.assertEqual(self.a.state["rescan_every_min"], 15)

    def test_startup_writes_entry_with_mode(self):
        with mock.patch.object(m.startup, "set_enabled") as se, \
                mock.patch.object(m.startup, "is_enabled", return_value=True), \
                mock.patch.object(m.startup, "current_mode", return_value="window"):
            self.api.set_startup(True, "window")
        se.assert_called_once_with(True, "window", m.HERE)
        self.assertEqual(self.a.state["start_mode"], "window")


class ClosingTest(unittest.TestCase):
    def make(self, action):
        a = bare_app(close_action=action)
        a.quitting, a.test_color, a.jobs = False, None, mock.Mock()
        a.window, a.quit = mock.Mock(), mock.Mock()
        return a

    def test_tray_hides(self):
        a = self.make("tray")
        self.assertFalse(a.on_closing())
        a.window.hide.assert_called_once()

    def test_quit_quits(self):
        a = self.make("quit")
        with mock.patch.object(m.threading, "Thread") as th:
            self.assertFalse(a.on_closing())
        a.window.hide.assert_not_called()
        th.assert_called_once()
        self.assertEqual(th.call_args.kwargs["target"], a.quit)


class RescanWatchTest(unittest.TestCase):
    def run_loop(self, **state):
        a = bare_app(**state)
        a.client = object()
        a.periodic_at = time.time() - 3600
        with mock.patch.object(m.time, "sleep", sleeps_then_stops(1)), \
                mock.patch.object(m.icue, "running", return_value=False):
            try:
                a.rescan_watch()
            except StopLoop:
                pass
        return a

    def test_off_never_rescans(self):
        self.run_loop(rescan_every_min=0).rescan.assert_not_called()

    def test_due_rescans(self):
        self.run_loop(rescan_every_min=10).rescan.assert_called_once()

    def test_original_mode_skips(self):
        self.run_loop(rescan_every_min=10, mode="original").rescan.assert_not_called()


if __name__ == "__main__":
    unittest.main()

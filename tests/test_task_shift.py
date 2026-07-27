from __future__ import annotations

from datetime import datetime
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest
from unittest import mock


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PROJECT_DIR = Path(__file__).resolve().parents[1]
LOADER = importlib.machinery.SourceFileLoader(
    "task_shift", str(PROJECT_DIR / "task-shift")
)
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
task_shift = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = task_shift
LOADER.exec_module(task_shift)


class TimerParsingTests(unittest.TestCase):
    def test_schedule_loaded_state_and_files_are_merged(self) -> None:
        schedule = json.dumps(
            [
                {
                    "unit": "backup.timer",
                    "activates": "backup.service",
                    "next": 1_700_000_000_000_000,
                    "last": 1_699_000_000_000_000,
                }
            ]
        )
        units = json.dumps(
            [
                {
                    "unit": "backup.timer",
                    "active": "active",
                    "sub": "waiting",
                }
            ]
        )
        files = json.dumps(
            [
                {"unit_file": "backup.timer", "state": "enabled"},
                {"unit_file": "quiet.timer", "state": "disabled"},
                {"unit_file": "template@.timer", "state": "disabled"},
            ]
        )
        timers = task_shift.parse_timers(schedule, units, files)
        self.assertEqual([item.name for item in timers], ["backup.timer", "quiet.timer"])
        self.assertEqual(timers[0].activates, "backup.service")
        self.assertEqual(timers[0].state_label, "Active (waiting)")
        self.assertEqual(timers[0].unit_file_state, "enabled")
        self.assertEqual(timers[1].state_label, "Inactive")

    def test_unknown_json_is_rejected(self) -> None:
        with self.assertRaises(task_shift.TaskShiftError):
            task_shift.parse_timers("{}", "[]", "[]")

    def test_unit_validation_blocks_option_and_shell_injection(self) -> None:
        self.assertEqual(task_shift.validate_timer_name("backup.timer"), "backup.timer")
        for value in ("--all.timer", "bad name.timer", "name;id.timer", "x.service"):
            with self.subTest(value=value), self.assertRaises(task_shift.TaskShiftError):
                task_shift.validate_timer_name(value)

    def test_timestamp_formatting_handles_missing_and_real_values(self) -> None:
        self.assertEqual(task_shift.format_timestamp(0), "—")
        value = int(datetime(2024, 1, 2, 12, 0).timestamp() * 1_000_000)
        self.assertTrue(task_shift.format_timestamp(value).startswith("2024-01-02"))


class CommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.timer = task_shift.TimerUnit(
            "backup.timer",
            "backup.service",
            0,
            0,
            "active",
            "waiting",
            "enabled",
        )

    def test_scope_is_an_explicit_fixed_argument(self) -> None:
        self.assertEqual(
            task_shift.systemctl_arguments("user", "status", "backup.timer"),
            [task_shift.SYSTEMCTL, "--user", "status", "backup.timer"],
        )

    @mock.patch.object(task_shift, "run_systemctl", return_value="")
    def test_run_now_starts_only_the_reported_service(self, run_systemctl: mock.Mock) -> None:
        task_shift.perform_action("system", self.timer, "run-now")
        run_systemctl.assert_called_once_with("system", "start", "backup.service")

    @mock.patch.object(task_shift, "run_systemctl", return_value="")
    def test_timer_actions_are_allowlisted(self, run_systemctl: mock.Mock) -> None:
        task_shift.perform_action("system", self.timer, "disable")
        run_systemctl.assert_called_once_with("system", "disable", "backup.timer")
        with self.assertRaises(task_shift.TaskShiftError):
            task_shift.perform_action("system", self.timer, "edit")

    def test_equivalent_command_uses_normal_systemctl_syntax(self) -> None:
        self.assertEqual(
            task_shift.action_command("user", self.timer, "run-now"),
            "systemctl --user start backup.service",
        )


class UserInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = task_shift.qt_application()

    def test_layout_uses_separate_cards_and_clear_preview_scope(self) -> None:
        window = task_shift.TaskWindow(autoload=False)
        self.assertEqual(window.find_group.title(), "Find scheduled tasks")
        self.assertEqual(window.timers_group.title(), "Scheduled tasks")
        self.assertEqual(window.details_group.title(), "Selected scheduled task")
        self.assertGreaterEqual(window.minimumWidth(), 980)
        margins = window.main_layout.contentsMargins()
        self.assertEqual(
            (margins.left(), margins.top(), margins.right(), margins.bottom()),
            (20, 18, 20, 16),
        )
        window.close()

    def test_selection_shows_timer_and_command(self) -> None:
        window = task_shift.TaskWindow(autoload=False)
        timer = task_shift.TimerUnit(
            "backup.timer", "backup.service", 0, 0, "active", "waiting", "enabled"
        )
        window.timers_loaded([timer])
        window.table.selectRow(0)
        self.assertEqual(window.selected_timer.text(), "backup.timer")
        self.assertEqual(window.selected_target.text(), "backup.service")
        self.assertEqual(window.command_preview.text(), "systemctl status backup.timer")
        self.assertTrue(window.run_button.isEnabled())
        window.close()

    def test_run_now_is_disabled_without_an_activated_service(self) -> None:
        window = task_shift.TaskWindow(autoload=False)
        timer = task_shift.TimerUnit(
            "quiet.timer", "", 0, 0, "inactive", "dead", "disabled"
        )
        window.timers_loaded([timer])
        window.table.selectRow(0)
        self.assertFalse(window.run_button.isEnabled())
        window.close()


if __name__ == "__main__":
    unittest.main()

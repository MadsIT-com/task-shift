from __future__ import annotations

from datetime import datetime
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
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

    def test_schedule_editor_uses_pkexec_only_for_system_scope(self) -> None:
        self.assertEqual(
            task_shift.systemctl_edit_arguments("system", "backup.timer"),
            [
                task_shift.PKEXEC,
                task_shift.SYSTEMCTL,
                "edit",
                f"--drop-in={task_shift.TASKSHIFT_DROP_IN}",
                "--stdin",
                "backup.timer",
            ],
        )
        self.assertEqual(
            task_shift.systemctl_edit_arguments("user", "backup.timer"),
            [
                task_shift.SYSTEMCTL,
                "--user",
                "edit",
                f"--drop-in={task_shift.TASKSHIFT_DROP_IN}",
                "--stdin",
                "backup.timer",
            ],
        )

    @mock.patch.object(task_shift.subprocess, "run")
    def test_drop_in_is_passed_on_stdin_without_a_shell(self, run: mock.Mock) -> None:
        run.return_value = mock.Mock(returncode=0, stdout="", stderr="")
        contents = "# Managed by TaskShift: restored\n[Timer]\n"
        task_shift.write_schedule_drop_in("system", "backup.timer", contents)
        self.assertEqual(
            run.call_args.args[0],
            task_shift.systemctl_edit_arguments("system", "backup.timer"),
        )
        self.assertEqual(run.call_args.kwargs["input"], contents)
        self.assertNotIn("shell", run.call_args.kwargs)


class ScheduleTests(unittest.TestCase):
    def test_calendar_schedule_resets_existing_triggers_and_can_be_exact(self) -> None:
        drop_in = task_shift.schedule_drop_in(
            task_shift.ScheduleSpec(
                "OnCalendar", "Mon..Fri *-*-* 09:00:00", True, True
            )
        )
        self.assertIn("OnCalendar=\n", drop_in)
        self.assertIn("OnCalendar=Mon..Fri *-*-* 09:00:00", drop_in)
        self.assertIn("Persistent=yes", drop_in)
        self.assertIn("RandomizedDelaySec=0", drop_in)
        self.assertIn("AccuracySec=1s", drop_in)

    def test_interval_schedule_uses_only_generated_numeric_duration(self) -> None:
        drop_in = task_shift.schedule_drop_in(
            task_shift.ScheduleSpec("OnUnitActiveSec", "45min")
        )
        self.assertIn("OnActiveSec=45min", drop_in)
        self.assertIn("OnUnitActiveSec=45min", drop_in)
        with self.assertRaises(task_shift.TaskShiftError):
            task_shift.schedule_drop_in(
                task_shift.ScheduleSpec("OnUnitActiveSec", "5min\nExecStart=/bin/sh")
            )

    def test_calendar_input_rejects_newline_injection(self) -> None:
        with self.assertRaises(task_shift.TaskShiftError):
            task_shift.validate_calendar("daily\nExecStart=/bin/sh")

    @mock.patch.object(task_shift, "run_systemctl")
    def test_details_detect_only_an_active_taskshift_drop_in(
        self, run_systemctl: mock.Mock
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / task_shift.TASKSHIFT_DROP_IN
            path.write_text(
                "# Managed by TaskShift: active\n[Timer]\nOnCalendar=\nOnCalendar=daily\n",
                encoding="utf-8",
            )
            run_systemctl.return_value = (
                "TimersCalendar={ OnCalendar=daily ; next_elapse=tomorrow }\n"
                "TimersMonotonic=\nPersistent=yes\nRandomizedDelayUSec=0\n"
                f"AccuracyUSec=1s\nDropInPaths={path}\n"
            )
            details = task_shift.load_timer_details("system", "backup.timer")
        self.assertTrue(details.taskshift_override)
        self.assertTrue(details.persistent)
        self.assertIn("OnCalendar=daily", details.calendar)


class UserInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = task_shift.qt_application()

    def test_layout_uses_separate_cards_and_clear_preview_scope(self) -> None:
        window = task_shift.TaskWindow(autoload=False)
        self.assertEqual(window.find_group.title(), "Find scheduled tasks")
        self.assertEqual(window.timers_group.title(), "Scheduled tasks")
        self.assertEqual(window.details_group.title(), "Selected scheduled task")
        group_titles = {
            group.title() for group in window.findChildren(task_shift.QGroupBox)
        }
        self.assertTrue(
            {"Current session", "Automatic startup", "Schedule"}.issubset(group_titles)
        )
        self.assertGreaterEqual(window.minimumWidth(), 980)
        margins = window.main_layout.contentsMargins()
        self.assertEqual(
            (margins.left(), margins.top(), margins.right(), margins.bottom()),
            (20, 18, 20, 16),
        )
        window.close()

    @mock.patch.object(
        task_shift,
        "validate_calendar",
        side_effect=lambda value: (value.strip(), "Three validated future runs"),
    )
    def test_schedule_dialog_builds_familiar_weekly_schedule(
        self, validate_calendar: mock.Mock
    ) -> None:
        timer = task_shift.TimerUnit(
            "backup.timer", "backup.service", 0, 0, "active", "waiting", "enabled"
        )
        details = task_shift.TimerDetails(
            "OnCalendar=daily", "", True, "12h", "1min", False
        )
        parent = task_shift.TaskWindow(autoload=False)
        dialog = task_shift.ScheduleDialog(timer, details, parent)
        dialog.schedule_type.setCurrentIndex(1)
        dialog.weekday.setCurrentIndex(4)
        dialog.weekly_time.setTime(task_shift.QTime(17, 30))
        specification = dialog.values()
        self.assertEqual(specification.directive, "OnCalendar")
        self.assertEqual(specification.value, "Fri *-*-* 17:30:00")
        self.assertTrue(specification.persistent)
        dialog.close()
        parent.close()

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

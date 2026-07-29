# Contributing

TaskShift is intentionally small. Keep changes focused on a dependable Task
Scheduler-style landing point for existing systemd timers.

Before submitting a change:

1. Run `python3 -m unittest discover -s tests -v`.
2. Run `python3 -m py_compile task-shift`.
3. Run `shellcheck install.sh uninstall.sh`.
4. Run `desktop-file-validate` against the installed launcher.
5. Confirm no machine-specific timer data, logs, credentials, or test secrets
   entered the repository.
6. Keep systemctl actions allowlisted, shell-free, and subject to PolicyKit.
7. Keep schedule writes limited to `50-task-shift.conf`, validate custom
   calendars with `systemd-analyze`, and preserve an explicit rollback path.

Systemd must remain the scheduler. Complete task creation, arbitrary unit-file
editing, and arbitrary command execution are outside the current scope.

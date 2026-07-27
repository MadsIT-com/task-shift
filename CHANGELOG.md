# Changelog

## 0.2.0 - 2026-07-28

- Added Daily, Weekly, Monthly, interval, and custom calendar schedule editing.
- Added systemd calendar validation and a three-run preview.
- Added explicit controls for missed-run persistence and near-exact timing.
- Added a named TaskShift drop-in that preserves vendor files and unrelated
  administrator overrides.
- Added Restore original behavior that neutralizes only TaskShift's schedule.
- Added PolicyKit-backed system timer editing and unprivileged user timer
  editing through systemd's native `edit --stdin` interface.
- Grouped current-session, startup, and schedule actions into separate cards.
- Expanded schedule-injection, privilege-boundary, rollback, and interface
  tests.

## 0.1.0 - 2026-07-27

- Added a native Qt 6/KDE scheduled-task overview for system and user timers.
- Added search and state filtering with next run, last run, startup, and target
  service columns.
- Added Start, Stop, Enable, Disable, and explicitly confirmed Run task now
  actions.
- Added shell-free systemctl execution with scope, action, timer, and target
  service validation.
- Added visible progress, error reporting, and terminal command teaching.
- Added documentation, installation scripts, and automated tests.

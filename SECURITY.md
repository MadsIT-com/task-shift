# Security policy

## Reporting a vulnerability

While this repository is private, report suspected vulnerabilities directly to
the repository owner. Do not place credentials, private timer data, or
machine-specific logs in an issue. Private vulnerability reporting will be
enabled before the repository becomes public.

## Security model

TaskShift is a graphical client for the system `systemctl` command. It does not
implement systemd timers, scheduling, PolicyKit, service execution, privilege
elevation, or unit-file parsing.

All systemctl arguments are constructed as an argument vector and executed
without a shell. Scope, action, timer names, and activated service names are
validated against fixed allowlists. TaskShift never inserts `sudo`, never asks
for an administrator password, and never attempts to bypass PolicyKit.

Stop, Disable, and Run task now require an explicit confirmation showing the
equivalent command. TaskShift runs only the service name systemd reported for
the selected timer. It does not accept an arbitrary command or service name
from the user.

TaskShift stores no settings or history. Closing it discards search text,
scope, selection, timer data, and action status.

## Important limitations

- “Run task now” can immediately perform updates, cleanup, deletion, backups,
  network access, or any other behavior implemented by the activated service.
- Stopping a timer prevents scheduled activation only while it remains stopped;
  disabling changes future startup but does not necessarily stop it now.
- Systemd and PolicyKit remain responsible for authorization and execution.
- A compromised same-user process can inspect visible UI state and query most
  of the same timer metadata directly.
- Timer and service names plus systemd errors are displayed as text and never
  interpreted as commands.
- This preview does not create, edit, delete, reload, or validate unit files and
  does not run arbitrary commands.

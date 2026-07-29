# Security policy

## Reporting a vulnerability

Use GitHub's private vulnerability reporting for suspected security issues.
Do not place credentials, private timer data, or machine-specific logs in a
public issue.

## Security model

TaskShift is a graphical client for the system `systemctl` and
`systemd-analyze` commands. It does not implement systemd timers, calendar
parsing, PolicyKit, service execution, or general unit-file editing.

All command arguments are constructed as an argument vector and executed
without a shell. Scope, action, timer names, activated service names, schedule
types, intervals, and generated directives are validated against fixed
allowlists. Custom calendar expressions reject control characters and are
accepted only after Debian's `systemd-analyze calendar` validates them.

System schedule changes invoke exactly `/usr/bin/pkexec /usr/bin/systemctl
edit --drop-in=50-task-shift.conf --stdin TIMER`. Generated content is passed
on standard input, never through a shell or command argument. User schedules
use the equivalent `systemctl --user edit` command without elevation. TaskShift
never asks for an administrator password; PolicyKit and KDE own that prompt.

Stop, Disable, and Run task now require an explicit confirmation showing the
equivalent command. TaskShift runs only the service name systemd reported for
the selected timer. It does not accept an arbitrary command or service name
from the user.

TaskShift stores no application settings or history. Closing it discards search
text, scope, selection, timer data, and action status. A schedule explicitly
applied by the user remains as system configuration in the named TaskShift
drop-in.

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
- Applying a new schedule intentionally resets all existing monotonic and
  calendar trigger expressions for that timer. Restore original neutralizes
  TaskShift's drop-in, allowing the vendor file and unrelated drop-ins to take
  effect again.
- Existing randomized delay and accuracy settings remain unless the user
  explicitly selects near-exact timing. Distribution timers may therefore run
  later than the selected wall-clock time by design.
- The `pkexec` package is a setuid PolicyKit component. It is used because
  unprivileged `systemctl edit` cannot write system timer configuration.
- TaskShift does not create or delete complete tasks and does not accept or
  run arbitrary commands.

# TaskShift

**Shift from Task Scheduler to Debian systemd timers without beginning at a
blank terminal.**

TaskShift is a focused KDE interface for inspecting and controlling existing
systemd timers. It gives Windows administrators a familiar scheduled-task
overview while leaving scheduling, execution, and authorization with Debian's
native systemd packages.

**Current release: 0.2.0**

## The Shift suite

| Tool | Familiar starting point | Debian engine |
| --- | --- | --- |
| [RDPShift](https://github.com/MadsIT-com/rdp-shift) | An `mstsc`-style “enter a computer and connect” workflow | [FreeRDP](https://www.freerdp.com/) |
| [SSHShift](https://github.com/MadsIT-com/ssh-shift) | `Windows key → PuTTY → Enter → host → Enter`, made native to KDE | [OpenSSH](https://www.openssh.com/) + Konsole |
| [MapShift](https://github.com/MadsIT-com/map-shift) | A familiar “map network drive” path into KDE applications | KDE KIO SMB + KIO-FUSE |
| [ServiceShift](https://github.com/MadsIT-com/service-shift) | A `services.msc`-style overview with familiar service controls | systemd + PolicyKit |
| [TaskShift](https://github.com/MadsIT-com/task-shift) | A Task Scheduler-style overview with safe schedule editing | systemd timers + PolicyKit |

## Behavior

- Shows system or per-user timers, including installed inactive timers.
- Shows the next run, previous run, startup state, and activated service.
- Filters by timer name, activated service, and state.
- Starts or stops a timer and enables or disables its automatic startup.
- Runs the service reported by systemd only after an explicit confirmation.
- Changes schedules with familiar Daily, Weekly, Monthly, and Repeat controls,
  plus a custom systemd calendar option for experienced users.
- Validates calendar expressions with `systemd-analyze` and previews the next
  three runs before anything is written.
- Stores schedule changes in a named TaskShift drop-in without rewriting the
  package-provided timer file or unrelated administrator drop-ins.
- Restores original scheduling semantics by neutralizing only TaskShift's
  named drop-in.
- Uses allowlisted `systemctl` arguments without invoking a shell.
- Lets KDE and PolicyKit handle administrator authentication. TaskShift never
  asks for or handles an administrator password.
- Saves no timer inventory, search history, selected unit, or action history.

TaskShift changes when an existing timer runs, but deliberately does not
create or delete timer and service units. Creating a complete task still needs
a design that explains the two-unit model, file ownership, command execution,
validation, and rollback before it writes anything.

## Editing schedules safely

TaskShift never edits the original timer beneath `/usr/lib/systemd/system` or
an administrator's unrelated drop-in. It uses systemd's native
`systemctl edit --stdin --drop-in=50-task-shift.conf` workflow.

For system timers, Debian's `pkexec` package asks PolicyKit to show KDE's normal
administrator-authentication dialog. User timers are edited without elevation.
Generated drop-in content resets the timer's prior trigger expressions and adds
the selected replacement schedule; systemd reloads its configuration and the
active timer is restarted so its next run updates immediately.

Existing `RandomizedDelaySec` and `AccuracySec` settings remain in effect by
default. This is important for distribution timers that deliberately spread
network or disk work over a time window. Selecting **Run as close as possible**
explicitly overrides those values with zero randomized delay and one-second
accuracy. Calendar schedules can also choose whether one missed occurrence is
run after the machine starts again.

## Installation on Debian 13

```sh
sudo apt install git pkexec python3-pyqt6 systemd
git clone https://github.com/MadsIT-com/task-shift.git
cd task-shift
./install.sh
```

The application appears as **TaskShift** in Plasma's application menu. To
remove the wrapper:

```sh
./uninstall.sh
```

Uninstalling TaskShift does not change timers, services, or systemd settings.
Any active TaskShift schedule overrides therefore remain effective. Use
**Restore original** before uninstalling when an override is no longer wanted.

## Updates stay with Debian

TaskShift uses Debian's systemd package rather than bundling a scheduling
engine. Normal `apt` upgrades deliver systemd security and bug fixes through
the same trusted path as the operating system.

## Testing

```sh
python3 -m unittest discover -s tests -v
python3 -m py_compile task-shift
shellcheck install.sh uninstall.sh
```

## Security boundary

Timer names and schedules are machine configuration rather than credentials,
but TaskShift still avoids creating another inventory or action history. An
intentional schedule override is persistent system configuration. Actions are
limited to units returned by systemd and authorization remains with systemd
and PolicyKit. “Run task now” starts the activated service immediately and can
therefore perform updates, cleanup, or other work. See
[SECURITY.md](SECURITY.md) for the complete boundary.

## License

MIT. See [LICENSE](LICENSE).

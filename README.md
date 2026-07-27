# TaskShift

**Shift from Task Scheduler to Debian systemd timers without beginning at a
blank terminal.**

TaskShift is a focused KDE interface for inspecting and controlling existing
systemd timers. It gives Windows administrators a familiar scheduled-task
overview while leaving scheduling, execution, and authorization with Debian's
native systemd packages.

**Current private preview: 0.1.0**

## Behavior

- Shows system or per-user timers, including installed inactive timers.
- Shows the next run, previous run, startup state, and activated service.
- Filters by timer name, activated service, and state.
- Starts or stops a timer and enables or disables its automatic startup.
- Runs the service reported by systemd only after an explicit confirmation.
- Uses allowlisted `systemctl` arguments without invoking a shell.
- Lets KDE and PolicyKit handle administrator authentication. TaskShift never
  asks for or handles an administrator password.
- Saves no timer inventory, search history, selected unit, or action history.

This preview deliberately does not create, edit, or delete timers and service
units. A responsible task editor must explain the two-unit model, file
ownership, calendar syntax, daemon reloads, validation, and rollback before it
writes anything.

## Installation on Debian 13

```sh
sudo apt install git python3-pyqt6 systemd
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
but TaskShift still avoids creating another persistent inventory. Actions are
limited to units returned by systemd and authorization remains with systemd
and PolicyKit. “Run task now” starts the activated service immediately and can
therefore perform updates, cleanup, or other work. See
[SECURITY.md](SECURITY.md) for the complete boundary.

## License

MIT. See [LICENSE](LICENSE).

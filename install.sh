#!/bin/sh

set -eu

PROJECT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
INSTALL_PREFIX=${PREFIX:-"$HOME/.local"}
BIN_DIR="$INSTALL_PREFIX/bin"
DATA_ROOT=${XDG_DATA_HOME:-"$HOME/.local/share"}
APPLICATIONS_DIR="$DATA_ROOT/applications"
LAUNCHER_PATH="$BIN_DIR/task-shift"
DESKTOP_PATH="$APPLICATIONS_DIR/task-shift.desktop"
DESKTOP_TEMP=$(mktemp "${TMPDIR:-/tmp}/task-shift.desktop.XXXXXX")
trap 'rm -f "$DESKTOP_TEMP"' EXIT HUP INT TERM

missing=""
for command_name in python3 systemctl; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
        missing="$missing $command_name"
    fi
done
if ! /usr/bin/python3 -c 'import PyQt6' >/dev/null 2>&1; then
    missing="$missing python3-pyqt6"
fi
if [ -n "$missing" ]; then
    printf 'Missing dependencies:%s\n' "$missing" >&2
    printf '%s\n' 'On Debian 13: sudo apt install python3-pyqt6 systemd' >&2
    exit 1
fi

install -d -m 755 "$BIN_DIR" "$APPLICATIONS_DIR"
install -m 755 "$PROJECT_DIR/task-shift" "$LAUNCHER_PATH"

/usr/bin/python3 - "$PROJECT_DIR/task-shift.desktop.in" "$DESKTOP_TEMP" "$LAUNCHER_PATH" <<'PY'
from pathlib import Path
import sys

template = Path(sys.argv[1]).read_text(encoding="utf-8")
launcher = sys.argv[3]
escaped = launcher.replace("\\", "\\\\").replace('"', '\\"').replace("`", "\\`").replace("$", "\\$")
Path(sys.argv[2]).write_text(
    template.replace("@TASK_SHIFT_EXEC@", f'"{escaped}"'),
    encoding="utf-8",
)
PY

install -m 644 "$DESKTOP_TEMP" "$DESKTOP_PATH"
if command -v desktop-file-validate >/dev/null 2>&1; then
    desktop-file-validate "$DESKTOP_PATH"
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPLICATIONS_DIR"
fi
if command -v kbuildsycoca6 >/dev/null 2>&1; then
    kbuildsycoca6 --noincremental >/dev/null 2>&1 || true
fi
printf 'Installed TaskShift to %s\n' "$LAUNCHER_PATH"

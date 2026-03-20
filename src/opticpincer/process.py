"""Process management: launch, kill, wait-for, rebuild-and-launch.

All state (PID files, log files) lives under ``~/.opticpincer/``.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from opticpincer.core import find_window

user32 = ctypes.windll.user32  # type: ignore[attr-defined]

# ---------------------------------------------------------------------------
# Directories
# ---------------------------------------------------------------------------

_BASE_DIR = Path.home() / ".opticpincer"
_PIDS_DIR = _BASE_DIR / "pids"
_LOGS_DIR = _BASE_DIR / "logs"


def _ensure_dirs() -> None:
    _PIDS_DIR.mkdir(parents=True, exist_ok=True)
    _LOGS_DIR.mkdir(parents=True, exist_ok=True)


def _sanitize(name: str) -> str:
    """Turn an arbitrary command string into a safe filename stem."""
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", name)[:80]


# ---------------------------------------------------------------------------
# launch
# ---------------------------------------------------------------------------

# Windows process creation flags
CREATE_NEW_PROCESS_GROUP = 0x00000200
DETACHED_PROCESS = 0x00000008


def launch(command: str, *, cwd: str | None = None) -> int:
    """Start *command* in the background and return its PID.

    stdout/stderr are redirected to a timestamped log file under
    ``~/.opticpincer/logs/``.  The PID is persisted to
    ``~/.opticpincer/pids/<sanitized>.pid`` for later :func:`kill_by_title`.
    """
    _ensure_dirs()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    log_path = _LOGS_DIR / f"{ts}.log"

    log_fh = open(log_path, "w", encoding="utf-8")  # noqa: SIM115

    flags = CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS
    proc = subprocess.Popen(
        command,
        shell=True,
        cwd=cwd,
        stdout=log_fh,
        stderr=subprocess.STDOUT,
        creationflags=flags,
    )

    pid = proc.pid

    # Persist PID
    pid_path = _PIDS_DIR / f"{_sanitize(command)}.pid"
    pid_path.write_text(str(pid), encoding="utf-8")

    return pid


# ---------------------------------------------------------------------------
# kill
# ---------------------------------------------------------------------------

def kill_by_title(title_match: str) -> bool:
    """Find the window matching *title_match*, get its PID, and kill the process tree.

    Returns *True* if the process was killed.
    """
    hwnd, _title = find_window(title_match)
    if hwnd is None:
        return False

    # GetWindowThreadProcessId → PID
    pid = ctypes.wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    target_pid = pid.value

    if target_pid == 0:
        return False

    # taskkill /F /T /PID — kills the entire process tree
    result = subprocess.run(
        ["taskkill", "/F", "/T", "/PID", str(target_pid)],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


# ---------------------------------------------------------------------------
# wait_for
# ---------------------------------------------------------------------------

def wait_for(
    title_match: str,
    *,
    timeout: float = 30.0,
    poll_interval: float = 0.5,
) -> int | None:
    """Poll for a window matching *title_match* until it appears or timeout.

    Returns the HWND on success, ``None`` on timeout.
    """
    deadline = time.monotonic() + timeout
    dots = 0

    while time.monotonic() < deadline:
        hwnd, _title = find_window(title_match)
        if hwnd is not None:
            if dots:
                print()  # newline after dots
            return hwnd
        # progress indicator
        print(".", end="", flush=True)
        dots += 1
        time.sleep(poll_interval)

    if dots:
        print()
    return None


# ---------------------------------------------------------------------------
# rebuild_and_launch
# ---------------------------------------------------------------------------

def rebuild_and_launch(
    build_cmd: str,
    run_cmd: str,
    title_match: str,
    *,
    cwd: str | None = None,
    timeout: float = 60.0,
) -> int | None:
    """Kill existing instance, rebuild, launch, and wait for the window.

    1. ``kill_by_title(title_match)`` if running
    2. Run *build_cmd* synchronously — raises on non-zero exit
    3. ``launch(run_cmd, cwd=cwd)``
    4. ``wait_for(title_match, timeout=timeout)``

    Returns the HWND of the new window, or ``None`` on timeout.
    """
    # 1. Kill old instance
    if find_window(title_match)[0] is not None:
        print(f"Killing existing '{title_match}' ...")
        kill_by_title(title_match)
        time.sleep(1.0)  # let the process die

    # 2. Build
    print(f"Building: {build_cmd}")
    result = subprocess.run(
        build_cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Build FAILED (exit {result.returncode}):", file=sys.stderr)
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        raise RuntimeError(f"Build command failed with exit code {result.returncode}")

    print("Build OK")

    # 3. Launch
    pid = launch(run_cmd, cwd=cwd)
    print(f"Launched PID {pid}: {run_cmd}")

    # 4. Wait
    print(f"Waiting for '{title_match}' (timeout={timeout}s) ", end="", flush=True)
    hwnd = wait_for(title_match, timeout=timeout)

    if hwnd is not None:
        print(f"Found HWND={hwnd}")
    else:
        print("TIMEOUT — window not found")

    return hwnd


# ---------------------------------------------------------------------------
# log reading
# ---------------------------------------------------------------------------

def read_latest_log(lines: int = 50) -> str | None:
    """Read the last *lines* of the most recent log file.

    Returns the text, or ``None`` if no logs exist.
    """
    _ensure_dirs()
    logs = sorted(_LOGS_DIR.glob("*.log"))
    if not logs:
        return None

    latest = logs[-1]
    all_lines = latest.read_text(encoding="utf-8", errors="replace").splitlines()
    tail = all_lines[-lines:] if len(all_lines) > lines else all_lines
    header = f"--- {latest.name} ({len(all_lines)} total lines, showing last {len(tail)}) ---"
    return header + "\n" + "\n".join(tail)

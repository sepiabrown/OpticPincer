"""Window focus management via Win32 API.

The key insight: ``SetForegroundWindow`` only works if the calling thread
is the foreground thread.  The Alt-key trick (``keybd_event(VK_MENU)``)
works but **triggers the menu bar** in many apps (egui, Qt, etc.).

Instead we use ``AttachThreadInput`` to temporarily link the calling
thread with the current foreground thread, which grants permission
to call ``SetForegroundWindow`` without any keyboard side-effects.
"""

from __future__ import annotations

import ctypes
import time

user32 = ctypes.windll.user32  # type: ignore[attr-defined]
kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]

# Constants
SW_RESTORE = 9
SW_MINIMIZE = 6


def foreground(hwnd: int, *, wait: float = 0.3) -> None:
    """Bring *hwnd* to the foreground reliably without triggering menus.

    Uses ``AttachThreadInput`` so ``SetForegroundWindow`` succeeds even
    from a background console process.
    """
    # Restore if minimized
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
        time.sleep(0.2)

    fg_hwnd = user32.GetForegroundWindow()
    if fg_hwnd == hwnd:
        return  # already foreground

    # Get thread IDs
    fg_tid = user32.GetWindowThreadProcessId(fg_hwnd, None)
    target_tid = user32.GetWindowThreadProcessId(hwnd, None)
    our_tid = kernel32.GetCurrentThreadId()

    attached_fg = False
    attached_target = False

    try:
        # Attach our thread to the foreground thread
        if fg_tid != our_tid:
            attached_fg = bool(user32.AttachThreadInput(our_tid, fg_tid, True))

        # Attach our thread to the target thread (if different from fg)
        if target_tid != our_tid and target_tid != fg_tid:
            attached_target = bool(user32.AttachThreadInput(our_tid, target_tid, True))

        # Now we have permission
        user32.SetForegroundWindow(hwnd)
        user32.BringWindowToTop(hwnd)

    finally:
        # Always detach
        if attached_fg:
            user32.AttachThreadInput(our_tid, fg_tid, False)
        if attached_target:
            user32.AttachThreadInput(our_tid, target_tid, False)

    if wait > 0:
        time.sleep(wait)


def background() -> None:
    """Minimise the console window that launched this process.

    Useful so the target GUI stays on top after we call :func:`foreground`.
    """
    console_hwnd = kernel32.GetConsoleWindow()
    if console_hwnd:
        user32.ShowWindow(console_hwnd, SW_MINIMIZE)


def is_foreground(hwnd: int) -> bool:
    """Return *True* if *hwnd* is currently the foreground window."""
    return user32.GetForegroundWindow() == hwnd

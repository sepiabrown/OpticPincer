"""Core window discovery and inspection via Win32 API.

All Win32 calls go through ctypes -- no pywin32 dependency.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes
from dataclasses import dataclass

user32 = ctypes.windll.user32  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

@dataclass
class WindowInfo:
    """Snapshot of a window's geometry and state."""
    hwnd: int
    title: str
    left: int
    top: int
    width: int
    height: int
    is_minimized: bool
    is_visible: bool
    is_foreground: bool


# ---------------------------------------------------------------------------
# Window discovery
# ---------------------------------------------------------------------------

def find_window(title_match: str) -> tuple[int, str] | tuple[None, None]:
    """Find the first visible window whose title contains *title_match*.

    Returns ``(hwnd, full_title)`` or ``(None, None)`` if not found.
    """
    results: list[tuple[int, str]] = []

    def _enum_cb(hwnd: int, _lp: int) -> bool:
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            if title_match in buf.value:
                results.append((hwnd, buf.value))
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    user32.EnumWindows(WNDENUMPROC(_enum_cb), 0)

    if not results:
        return None, None
    return results[0]


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------

def get_window_rect(hwnd: int) -> tuple[int, int, int, int]:
    """Return ``(left, top, width, height)`` in screen coordinates.

    Uses the **outer** window rect (includes title bar and borders).
    For client-area origin, use :func:`get_client_origin`.
    """
    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top


def get_client_origin(hwnd: int) -> tuple[int, int]:
    """Return the client-area origin ``(left, top)`` in screen coordinates.

    This is where egui logical point (0, 0) maps to on screen. It excludes
    the title bar and window borders. Use this (not :func:`get_window_rect`)
    when converting widget rects from ``ui_tree.json`` to screen coordinates.
    """
    pt = ctypes.wintypes.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(pt))
    return pt.x, pt.y


def screen_to_client(hwnd: int, screen_x: int, screen_y: int) -> tuple[int, int]:
    """Convert screen coordinates to client-area coordinates."""
    pt = ctypes.wintypes.POINT(screen_x, screen_y)
    user32.ScreenToClient(hwnd, ctypes.byref(pt))
    return pt.x, pt.y


# ---------------------------------------------------------------------------
# Info
# ---------------------------------------------------------------------------

def get_window_info(hwnd: int) -> WindowInfo:
    """Return a full :class:`WindowInfo` snapshot."""
    left, top, w, h = get_window_rect(hwnd)

    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)

    fg_hwnd = user32.GetForegroundWindow()

    return WindowInfo(
        hwnd=hwnd,
        title=buf.value,
        left=left,
        top=top,
        width=w,
        height=h,
        is_minimized=bool(user32.IsIconic(hwnd)),
        is_visible=bool(user32.IsWindowVisible(hwnd)),
        is_foreground=(fg_hwnd == hwnd),
    )

"""Mouse click delivery with three-strategy fallback.

Strategy 1 -- SetCursorPos + mouse_event (OS-level)
    Works with winit / eframe / GLFW because they read from the OS input
    queue.  Requires the target window to be **foreground** at the moment
    the event fires.

Strategy 2 -- PostMessage WM_LBUTTONDOWN / WM_LBUTTONUP (async)
    Sends a window message directly to the HWND.  Works with many Win32
    apps but NOT with winit/eframe (which reads raw input, not WM_*).

Strategy 3 -- SendMessage (sync)
    Same as PostMessage but blocks until the target processes the message.
    Last resort.

The public ``click_at`` uses strategy 1 by default.  ``click_at_message``
uses strategy 2+3 with fallback.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import time

from opticpincer.core import get_window_rect, screen_to_client
from opticpincer.window import foreground

user32 = ctypes.windll.user32  # type: ignore[attr-defined]

# Win32 constants
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
MK_LBUTTON = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004


def _make_lparam(client_x: int, client_y: int) -> int:
    """Pack two 16-bit coordinates into a single lParam (MAKELONG)."""
    return ((client_y & 0xFFFF) << 16) | (client_x & 0xFFFF)


# ---------------------------------------------------------------------------
# Strategy 1: OS-level (works with winit/eframe/GLFW)
# ---------------------------------------------------------------------------

def click_at(
    hwnd: int,
    screen_x: int,
    screen_y: int,
    *,
    pre_focus: bool = True,
    focus_wait: float = 0.3,
    hover_time: float = 0.2,
    click_pause: float = 0.05,
) -> None:
    """Click at *absolute* screen coordinates using SetCursorPos + mouse_event.

    Sequence: focus → move cursor → hover (let egui detect) → click.
    The hover delay is critical: egui/winit needs at least one frame
    to process the cursor position before it can register a click.
    """
    if pre_focus:
        foreground(hwnd, wait=focus_wait)

    # Move cursor to target
    user32.SetCursorPos(screen_x, screen_y)

    # Let egui process the hover (needs 1-2 frames at 60fps ≈ 33ms)
    time.sleep(hover_time)

    # Click: down → pause → up (tight timing, no focus loss)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(click_pause)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    time.sleep(0.2)


def click_relative(
    hwnd: int,
    rel_x: int,
    rel_y: int,
    **kwargs,  # noqa: ANN003 -- forwarded to click_at
) -> tuple[int, int]:
    """Click at coordinates *relative* to the window's top-left corner.

    Returns the absolute screen coordinates that were clicked.
    """
    wx, wy, _, _ = get_window_rect(hwnd)
    abs_x = wx + rel_x
    abs_y = wy + rel_y
    click_at(hwnd, abs_x, abs_y, **kwargs)
    return abs_x, abs_y


# ---------------------------------------------------------------------------
# Strategy 2+3: Window messages (PostMessage, SendMessage)
# ---------------------------------------------------------------------------

def click_at_message(
    hwnd: int,
    screen_x: int,
    screen_y: int,
    *,
    click_pause: float = 0.05,
) -> None:
    """Click via PostMessage, falling back to SendMessage on failure.

    Coordinates are *screen* coordinates; they are converted to client
    coordinates internally.  This does NOT require the window to be
    foreground but does NOT work with winit/eframe (use :func:`click_at`
    for those).
    """
    cx, cy = screen_to_client(hwnd, screen_x, screen_y)
    lp = _make_lparam(cx, cy)

    ok_down = user32.PostMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lp)
    time.sleep(click_pause)
    ok_up = user32.PostMessageW(hwnd, WM_LBUTTONUP, 0, lp)

    if not ok_down or not ok_up:
        # Fallback: synchronous SendMessage
        user32.SendMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lp)
        time.sleep(click_pause)
        user32.SendMessageW(hwnd, WM_LBUTTONUP, 0, lp)

"""Test: Ctrl+click using SetKeyboardState to inject modifier into thread state.

Usage:
    uv run python tests/test_ctrl_click.py --title "MyApp" --widget-id hole_1 --tree-path /path/to/ui_tree.json
"""

import argparse
import time
import ctypes
import ctypes.wintypes
from pathlib import Path

from opticpincer.core import find_window, get_window_rect
from opticpincer.uitree import UiTree
from opticpincer.screenshot import take_screenshot

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

VK_CONTROL = 0x11
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008


def ctrl_click(hwnd: int, screen_x: int, screen_y: int) -> None:
    """Ctrl+click using AttachThreadInput + keybd_event with scan codes.

    Strategy: attach our thread to the target thread's input queue (sharing
    keyboard state), inject VK_CONTROL via keybd_event with scan code,
    wait for the target to process it, then click.
    """
    from opticpincer.window import foreground as _foreground

    our_tid = kernel32.GetCurrentThreadId()
    target_pid = ctypes.wintypes.DWORD()
    target_tid = user32.GetWindowThreadProcessId(hwnd, ctypes.byref(target_pid))

    # Attach our thread to target's input queue
    attached = user32.AttachThreadInput(our_tid, target_tid, True)
    print(f"  AttachThreadInput({our_tid} -> {target_tid}): {attached}")

    # Focus the window
    user32.SetForegroundWindow(hwnd)
    user32.BringWindowToTop(hwnd)
    time.sleep(0.5)

    # Move cursor to target position
    user32.SetCursorPos(screen_x, screen_y)
    time.sleep(0.3)

    # Inject Ctrl key down via keybd_event with scan code
    # The KEYEVENTF_SCANCODE flag is NOT set — we want VK-based injection
    # which updates GetKeyState for the shared input queue
    user32.keybd_event(VK_CONTROL, 0x1D, 0, 0)

    # Wait for message loop to process WM_KEYDOWN(VK_CONTROL)
    # This is the critical delay — winit must see the Ctrl state
    time.sleep(1.0)

    # Verify: read key state from our thread (shared via AttachThreadInput)
    state = user32.GetKeyState(VK_CONTROL)
    print(f"  GetKeyState(VK_CONTROL) after keybd_event: 0x{state & 0xFFFF:04X} (bit0={'down' if state & 0x8000 else 'up'})")

    # Now click — mouse_event injects into the system queue
    user32.mouse_event(0x0002, 0, 0, 0, 0)  # LEFTDOWN
    time.sleep(0.05)
    user32.mouse_event(0x0004, 0, 0, 0, 0)  # LEFTUP
    time.sleep(0.3)

    # Release Ctrl
    user32.keybd_event(VK_CONTROL, 0x1D, KEYEVENTF_KEYUP, 0)
    time.sleep(0.2)

    # Detach
    user32.AttachThreadInput(our_tid, target_tid, False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Test Ctrl+click on a widget")
    parser.add_argument("--title", required=True, help="Window title substring to match")
    parser.add_argument("--widget-id", required=True, help="Widget test ID to Ctrl+click")
    parser.add_argument("--tree-path", required=True, help="Path to ui_tree.json")
    parser.add_argument("--wait", type=float, default=10.0, help="Seconds to wait after click")
    parser.add_argument("--output-dir", "-o", default="screenshots", help="Screenshot output dir")
    args = parser.parse_args()

    hwnd, title = find_window(args.title)
    assert hwnd, f"Window matching '{args.title}' not found"
    print(f"Found: {title} (HWND={hwnd})")

    tree = UiTree.load(args.tree_path)
    widget = tree.find(args.widget_id)
    assert widget, f"Widget '{args.widget_id}' not found. Available: {[w.id for w in tree.widgets]}"

    wl, wt, _, _ = get_window_rect(hwnd)
    sx, sy = tree.screen_center(widget, current_window_pos=(wl, wt))
    print(f"Target: {args.widget_id} ({widget.label}) at screen ({sx}, {sy})")

    print("Sending Ctrl+Click...")
    ctrl_click(hwnd, sx, sy)

    print(f"Waiting {args.wait}s...")
    time.sleep(args.wait)

    out_dir = Path(args.output_dir)
    path = take_screenshot(hwnd, label="after_ctrl_click", output_dir=out_dir)
    print(f"Screenshot: {path}")

    tree2 = UiTree.load(args.tree_path)
    print(f"Widgets after click: {len(tree2.widgets)}")
    for w in tree2.widgets:
        print(f"  {w.id}: {w.label} [{w.kind}]")


if __name__ == "__main__":
    main()

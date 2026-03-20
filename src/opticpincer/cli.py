"""Argparse-based CLI for OpticPincer.

Usage::

    opticpincer info "MyApp"
    opticpincer screenshot "MyApp"
    opticpincer focus "MyApp"
    opticpincer background
    opticpincer click "MyApp" 100 200
    opticpincer click-relative "MyApp" 60 83
    opticpincer click-test "MyApp" 60 83
    opticpincer launch "./my-app.exe"
    opticpincer kill "MyApp"
    opticpincer wait-for "MyApp" --timeout 30
    opticpincer rebuild --build-cmd "cargo build" --run-cmd "cargo run" --title "MyApp"
    opticpincer log --lines 50
    opticpincer ui-tree
    opticpincer click-widget "MyApp" item_0
    opticpincer click-label "MyApp" "Dataset A"
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from opticpincer.click import click_at, click_relative
from opticpincer.core import find_window, get_window_info
from opticpincer.process import (
    kill_by_title,
    launch,
    read_latest_log,
    rebuild_and_launch,
    wait_for,
)
from opticpincer.screenshot import compare_screenshots, take_screenshot
from opticpincer.uitree import UiTree, DEFAULT_UI_TREE_PATH
from opticpincer.window import background, foreground


def _find_or_exit(title: str) -> int:
    hwnd, full_title = find_window(title)
    if hwnd is None:
        print(f"ERROR: No window matching '{title}' found", file=sys.stderr)
        sys.exit(1)
    print(f"Window: {full_title}  (HWND={hwnd})")
    return hwnd


# ---------------------------------------------------------------------------
# Window commands
# ---------------------------------------------------------------------------

def cmd_info(args: argparse.Namespace) -> None:
    hwnd = _find_or_exit(args.title)
    info = get_window_info(hwnd)
    print(f"  Position : ({info.left}, {info.top})")
    print(f"  Size     : {info.width}x{info.height}")
    print(f"  Minimized: {info.is_minimized}")
    print(f"  Visible  : {info.is_visible}")
    print(f"  Foregnd  : {info.is_foreground}")


def cmd_screenshot(args: argparse.Namespace) -> None:
    hwnd = _find_or_exit(args.title)
    label = args.label or ""
    path = take_screenshot(hwnd, label=label, output_dir=args.output_dir)
    print(f"Saved: {path}")


def cmd_focus(args: argparse.Namespace) -> None:
    hwnd = _find_or_exit(args.title)
    foreground(hwnd)
    print("Foreground: OK")


def cmd_background(_args: argparse.Namespace) -> None:
    background()
    print("Console minimised")


# ---------------------------------------------------------------------------
# Click commands
# ---------------------------------------------------------------------------

def cmd_click(args: argparse.Namespace) -> None:
    hwnd = _find_or_exit(args.title)
    click_at(hwnd, args.x, args.y)
    print(f"Clicked at screen ({args.x}, {args.y})")
    if args.screenshot:
        time.sleep(0.3)
        path = take_screenshot(hwnd, label="after_click", output_dir=args.output_dir)
        print(f"Saved: {path}")


def cmd_click_relative(args: argparse.Namespace) -> None:
    hwnd = _find_or_exit(args.title)
    abs_x, abs_y = click_relative(hwnd, args.rx, args.ry)
    print(f"Clicked at rel ({args.rx}, {args.ry}) -> screen ({abs_x}, {abs_y})")
    if args.screenshot:
        time.sleep(0.3)
        path = take_screenshot(hwnd, label="after_click", output_dir=args.output_dir)
        print(f"Saved: {path}")


def cmd_click_test(args: argparse.Namespace) -> None:
    hwnd = _find_or_exit(args.title)
    out = Path(args.output_dir)

    print("Taking BEFORE screenshot...")
    before = take_screenshot(hwnd, label="before", output_dir=out)
    print(f"  {before}")

    print(f"Clicking at relative ({args.rx}, {args.ry})...")
    abs_x, abs_y = click_relative(hwnd, args.rx, args.ry)
    print(f"  -> screen ({abs_x}, {abs_y})")

    time.sleep(1.0)

    print("Taking AFTER screenshot...")
    after = take_screenshot(hwnd, label="after", output_dir=out)
    print(f"  {after}")

    changed = compare_screenshots(before, after)
    if changed:
        print("RESULT: Screenshots DIFFER -- click registered")
    else:
        print("RESULT: Screenshots IDENTICAL -- click may not have registered")


# ---------------------------------------------------------------------------
# Process commands
# ---------------------------------------------------------------------------

def cmd_launch(args: argparse.Namespace) -> None:
    cwd = args.cwd if hasattr(args, "cwd") and args.cwd else None
    pid = launch(args.command, cwd=cwd)
    print(f"Launched PID {pid}: {args.command}")


def cmd_kill(args: argparse.Namespace) -> None:
    killed = kill_by_title(args.title)
    if killed:
        print(f"Killed process for '{args.title}'")
    else:
        print(f"No window matching '{args.title}' found (or kill failed)")


def cmd_wait_for(args: argparse.Namespace) -> None:
    timeout = args.timeout
    print(f"Waiting for '{args.title}' (timeout={timeout}s) ", end="", flush=True)
    hwnd = wait_for(args.title, timeout=timeout)
    if hwnd is not None:
        print(f"Found HWND={hwnd}")
    else:
        print("TIMEOUT")
        sys.exit(1)


def cmd_rebuild(args: argparse.Namespace) -> None:
    cwd = args.cwd if hasattr(args, "cwd") and args.cwd else None
    timeout = args.timeout
    try:
        hwnd = rebuild_and_launch(
            args.build_cmd,
            args.run_cmd,
            args.title,
            cwd=cwd,
            timeout=timeout,
        )
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if hwnd is None:
        sys.exit(1)


def cmd_log(args: argparse.Namespace) -> None:
    text = read_latest_log(lines=args.lines)
    if text is None:
        print("No log files found in ~/.opticpincer/logs/")
    else:
        print(text)


# ---------------------------------------------------------------------------
# UI Tree commands
# ---------------------------------------------------------------------------

def _load_tree_or_exit(args: argparse.Namespace) -> UiTree:
    tree_path = getattr(args, "tree_path", DEFAULT_UI_TREE_PATH)
    path = Path(tree_path)
    if not path.exists():
        print(f"ERROR: {path} not found", file=sys.stderr)
        print("  Is the GUI running with test mode enabled?", file=sys.stderr)
        sys.exit(1)
    return UiTree.load(path)


def cmd_ui_tree(args: argparse.Namespace) -> None:
    tree = _load_tree_or_exit(args)
    print(f"UI Tree: {len(tree.widgets)} widgets")
    print(f"  Window: left={tree.window_left} top={tree.window_top} "
          f"{tree.window_width}x{tree.window_height}")
    print(f"  pixels_per_point: {tree.pixels_per_point}")
    print()
    for w in tree.widgets:
        sx, sy = tree.screen_center(w)
        print(f"  {w.id:<25s} {w.kind:<12s} {w.label:<30s} "
              f"rect=[{w.rect[0]:.0f},{w.rect[1]:.0f},{w.rect[2]:.0f},{w.rect[3]:.0f}] "
              f"-> screen({sx},{sy})")


def cmd_click_widget(args: argparse.Namespace) -> None:
    tree = _load_tree_or_exit(args)
    widget = tree.find(args.widget_id)
    if widget is None:
        print(f"ERROR: Widget '{args.widget_id}' not found in ui_tree.json", file=sys.stderr)
        print(f"  Available: {[w.id for w in tree.widgets]}", file=sys.stderr)
        sys.exit(1)

    hwnd = _find_or_exit(args.title)
    # Use CURRENT client-area origin (not window rect — excludes title bar)
    from opticpincer.core import get_client_origin
    current_pos = get_client_origin(hwnd)
    sx, sy = tree.screen_center(widget, current_window_pos=current_pos)
    print(f"Widget: {widget.id} ({widget.label}) -> screen({sx}, {sy})")
    click_at(hwnd, sx, sy)
    print(f"Clicked widget '{widget.id}'")

    if args.screenshot:
        delay = getattr(args, "screenshot_delay", 1.0)
        time.sleep(delay)
        path = take_screenshot(hwnd, label=f"widget_{widget.id}", output_dir=args.output_dir)
        print(f"Saved: {path}")


def cmd_click_label(args: argparse.Namespace) -> None:
    tree = _load_tree_or_exit(args)
    widget = tree.find_by_label(args.label_text)
    if widget is None:
        print(f"ERROR: No widget with label containing '{args.label_text}'", file=sys.stderr)
        labels = [(w.id, w.label) for w in tree.widgets]
        print(f"  Available: {labels}", file=sys.stderr)
        sys.exit(1)

    hwnd = _find_or_exit(args.title)
    from opticpincer.core import get_client_origin
    current_pos = get_client_origin(hwnd)
    sx, sy = tree.screen_center(widget, current_window_pos=current_pos)
    print(f"Widget: {widget.id} ({widget.label}) -> screen({sx}, {sy})")
    click_at(hwnd, sx, sy)
    print(f"Clicked widget '{widget.id}' (matched label '{args.label_text}')")

    if args.screenshot:
        delay = getattr(args, "screenshot_delay", 1.0)
        time.sleep(delay)
        path = take_screenshot(hwnd, label=f"label_{widget.id}", output_dir=args.output_dir)
        print(f"Saved: {path}")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="opticpincer",
        description="Native desktop GUI automation for LLM agents",
    )
    parser.add_argument(
        "--output-dir", "-o", default="screenshots",
        help="Directory for screenshot output (default: screenshots/)",
    )
    sub = parser.add_subparsers(dest="subcommand")

    # --- Window ---

    p = sub.add_parser("info", help="Print window info")
    p.add_argument("title", help="Window title substring to match")

    p = sub.add_parser("screenshot", help="Capture window screenshot")
    p.add_argument("title", help="Window title substring to match")
    p.add_argument("label", nargs="?", default="", help="Optional label suffix")

    p = sub.add_parser("focus", help="Bring window to foreground")
    p.add_argument("title", help="Window title substring to match")

    sub.add_parser("background", help="Minimise console window")

    # --- Click ---

    p = sub.add_parser("click", help="Click at absolute screen coordinates")
    p.add_argument("title", help="Window title substring to match")
    p.add_argument("x", type=int, help="Screen X")
    p.add_argument("y", type=int, help="Screen Y")
    p.add_argument("--screenshot", "-s", action="store_true", help="Take screenshot after click")

    p = sub.add_parser("click-relative", help="Click at window-relative coordinates")
    p.add_argument("title", help="Window title substring to match")
    p.add_argument("rx", type=int, help="Relative X from window left")
    p.add_argument("ry", type=int, help="Relative Y from window top")
    p.add_argument("--screenshot", "-s", action="store_true", help="Take screenshot after click")

    p = sub.add_parser("click-test", help="Click and verify via before/after screenshots")
    p.add_argument("title", help="Window title substring to match")
    p.add_argument("rx", type=int, help="Relative X from window left")
    p.add_argument("ry", type=int, help="Relative Y from window top")

    # --- Process ---

    p = sub.add_parser("launch", help="Start a background process")
    p.add_argument("command", help="Command string to run")
    p.add_argument("--cwd", default=None, help="Working directory")

    p = sub.add_parser("kill", help="Kill process by window title")
    p.add_argument("title", help="Window title substring to match")

    p = sub.add_parser("wait-for", help="Wait for a window to appear")
    p.add_argument("title", help="Window title substring to match")
    p.add_argument("--timeout", type=float, default=30.0, help="Seconds to wait (default: 30)")

    p = sub.add_parser("rebuild", help="Kill, rebuild, launch, and wait")
    p.add_argument("--build-cmd", required=True, help="Build command (run synchronously)")
    p.add_argument("--run-cmd", required=True, help="Run command (launched in background)")
    p.add_argument("--title", required=True, help="Window title to wait for")
    p.add_argument("--cwd", default=None, help="Working directory")
    p.add_argument("--timeout", type=float, default=60.0, help="Seconds to wait (default: 60)")

    p = sub.add_parser("log", help="Print recent process log output")
    p.add_argument("--lines", "-n", type=int, default=50, help="Number of lines (default: 50)")

    # --- UI Tree ---

    p = sub.add_parser("ui-tree", help="List widgets from ui_tree.json")
    p.add_argument("--tree-path", default=DEFAULT_UI_TREE_PATH,
                   help="Path to ui_tree.json")

    p = sub.add_parser("click-widget", help="Click a widget by its test ID")
    p.add_argument("title", help="Window title substring to match")
    p.add_argument("widget_id", help="Widget test ID (e.g. item_0, menu_file)")
    p.add_argument("--tree-path", default=DEFAULT_UI_TREE_PATH,
                   help="Path to ui_tree.json")
    p.add_argument("--screenshot", "-s", action="store_true", help="Take screenshot after click")
    p.add_argument("--screenshot-delay", type=float, default=1.0,
                   help="Seconds to wait before screenshot (default: 1.0)")

    p = sub.add_parser("click-label", help="Click a widget by label text match")
    p.add_argument("title", help="Window title substring to match")
    p.add_argument("label_text", help="Label text to search for (substring match)")
    p.add_argument("--tree-path", default=DEFAULT_UI_TREE_PATH,
                   help="Path to ui_tree.json")
    p.add_argument("--screenshot", "-s", action="store_true", help="Take screenshot after click")
    p.add_argument("--screenshot-delay", type=float, default=1.0,
                   help="Seconds to wait before screenshot (default: 1.0)")

    args = parser.parse_args(argv)

    if args.subcommand is None:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "info": cmd_info,
        "screenshot": cmd_screenshot,
        "focus": cmd_focus,
        "background": cmd_background,
        "click": cmd_click,
        "click-relative": cmd_click_relative,
        "click-test": cmd_click_test,
        "launch": cmd_launch,
        "kill": cmd_kill,
        "wait-for": cmd_wait_for,
        "rebuild": cmd_rebuild,
        "log": cmd_log,
        "ui-tree": cmd_ui_tree,
        "click-widget": cmd_click_widget,
        "click-label": cmd_click_label,
    }
    dispatch[args.subcommand](args)

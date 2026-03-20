# Your first GUI test

This tutorial walks you through launching a native desktop app, taking a screenshot, clicking a button, and verifying the click registered. By the end, you will be able to use OpticPincer to automate any visible window on your desktop.

## Prerequisites

- Windows 10 or 11
- Python 3.11+
- OpticPincer installed (`pip install -e .` from the opticpincer directory)
- A GUI application to automate (we'll use Notepad, which is already on your system)

## Step 1: Find a window

Open Notepad manually (Start → Notepad). Then find it with OpticPincer:

```bash
opticpincer info "Notepad"
```

You will see output like:

```
Window: Untitled - Notepad  (HWND=1234567)
  Position : (100, 200)
  Size     : 800x600
  Minimized: False
  Visible  : True
  Foregnd  : False
```

The `title` argument is a substring match — `"Notepad"` matches any window whose title contains that text. This is how OpticPincer identifies windows throughout every command.

## Step 2: Take a screenshot

Capture the window contents:

```bash
opticpincer screenshot "Notepad"
```

```
Window: Untitled - Notepad  (HWND=1234567)
Saved: screenshots/capture_20250320_143052.png
```

OpticPincer brings the window to the foreground, reads its screen coordinates via `GetWindowRect`, and captures that region using pyautogui. The screenshot is saved to the `screenshots/` directory by default.

Open the PNG to confirm it shows the Notepad window.

## Step 3: Click at a position

Click the text area inside Notepad. Notepad's text area starts roughly 60 pixels from the left edge and 80 pixels from the top of the window:

```bash
opticpincer click-relative "Notepad" 60 80 --screenshot
```

```
Window: Untitled - Notepad  (HWND=1234567)
Clicked at rel (60, 80) -> screen (160, 280)
Saved: screenshots/capture_20250320_143105_after_click.png
```

The `click-relative` command takes coordinates relative to the window's top-left corner. The `--screenshot` flag captures a screenshot 300ms after the click so you can verify what happened.

## Step 4: Verify a click with before/after comparison

The `click-test` command automates the verification loop: screenshot before, click, wait, screenshot after, compare:

```bash
opticpincer click-test "Notepad" 60 80
```

```
Window: Untitled - Notepad  (HWND=1234567)
Taking BEFORE screenshot...
  screenshots/capture_20250320_143120_before.png
Clicking at relative (60, 80)...
  -> screen (160, 280)
Taking AFTER screenshot...
  screenshots/capture_20250320_143121_after.png
RESULT: Screenshots DIFFER -- click registered
```

If the screenshots are identical, the click did not produce a visible change. This is the basic feedback loop for GUI automation: click → screenshot → compare.

## Step 5: Manage the window

Bring the window to the foreground programmatically:

```bash
opticpincer focus "Notepad"
```

```
Window: Untitled - Notepad  (HWND=1234567)
Foreground: OK
```

Minimize the console so it doesn't cover the GUI app:

```bash
opticpincer background
```

```
Console minimised
```

## Step 6: Use with an egui app (optional)

If you have an egui/eframe application that exports `ui_tree.json` (see [How to automate an egui app](../how-to/automate-egui-app.md)), you can click widgets by their test ID instead of guessing pixel coordinates:

```bash
opticpincer ui-tree
```

```
UI Tree: 12 widgets
  Window: left=112 top=135 1920x1080
  pixels_per_point: 1.0

  item_0                    selectable   Dataset A                      rect=[10,60,170,78] -> screen(202,204)
  item_1                    selectable   Dataset B                      rect=[10,78,170,96] -> screen(202,222)
  menu_file                 button       File                           rect=[0,0,40,20] -> screen(132,145)
```

Then click a specific widget:

```bash
opticpincer click-widget "MyApp" item_0 --screenshot
```

```
Widget: item_0 (Dataset A) -> screen(202, 204)
Clicked widget 'item_0'
Saved: screenshots/capture_20250320_143200_widget_item_0.png
```

No pixel guessing. The widget ID is stable across window moves and resizes.

## What you learned

You now know how to:
- Find windows by title substring with `info`
- Capture screenshots with `screenshot`
- Click at window-relative coordinates with `click-relative`
- Verify clicks with before/after comparison using `click-test`
- Manage window focus with `focus` and `background`
- Click egui widgets by test ID with `click-widget` (when ui_tree.json is available)

For clicking by widget ID instead of pixel coordinates, see [Click by widget ID](../how-to/click-by-widget-id.md). For understanding why clicks sometimes don't register, see [Debug click not registering](../how-to/debug-click-not-registering.md).

# CLI commands

All commands are subcommands of `opticpincer`. The global option `--output-dir` / `-o` sets the screenshot output directory (default: `screenshots/`).

```bash
opticpincer [--output-dir DIR] <subcommand> [args...]
```

If no subcommand is given, prints the help message and exits with code 0.

## Window commands

### info

Print window geometry and state.

```bash
opticpincer info <title>
```

| Argument | Description |
|----------|-------------|
| `title` | Window title substring to match |

Output fields: position, size, minimized, visible, foreground.

Exit codes: 0 on success, 1 if no matching window found.

Example:

```bash
opticpincer info "MyApp"
```

```
Window: MyApp  (HWND=1234567)
  Position : (100, 200)
  Size     : 1920x1080
  Minimized: False
  Visible  : True
  Foregnd  : True
```

### screenshot

Capture the window contents as a PNG.

```bash
opticpincer screenshot <title> [label]
```

| Argument | Description |
|----------|-------------|
| `title` | Window title substring to match |
| `label` | Optional suffix appended to the filename |

The window is brought to the foreground before capture. Screenshots are saved as `<prefix>_<timestamp>[_<label>].png` in the output directory.

Exit codes: 0 on success, 1 if no matching window found.

Example:

```bash
opticpincer screenshot "MyApp" after_click
```

```
Window: MyApp  (HWND=1234567)
Saved: screenshots/capture_20250320_143052_after_click.png
```

### focus

Bring a window to the foreground.

```bash
opticpincer focus <title>
```

| Argument | Description |
|----------|-------------|
| `title` | Window title substring to match |

Uses `AttachThreadInput` + `SetForegroundWindow` to reliably bring the window to front without triggering the Alt key menu bar. See [How clicking works](../explanation/how-clicking-works.md) for details.

Exit codes: 0 on success, 1 if no matching window found.

### background

Minimize the console window.

```bash
opticpincer background
```

No arguments. Minimizes the console window that launched OpticPincer. Useful before clicking so the console doesn't cover the target GUI.

Exit codes: always 0.

## Click commands

### click

Click at absolute screen coordinates.

```bash
opticpincer click <title> <x> <y> [--screenshot]
```

| Argument | Description |
|----------|-------------|
| `title` | Window title substring to match |
| `x` | Absolute screen X coordinate |
| `y` | Absolute screen Y coordinate |
| `--screenshot`, `-s` | Take screenshot 300ms after click |

Uses Strategy 1 (SetCursorPos + mouse_event). The window is brought to the foreground before clicking.

Exit codes: 0 on success, 1 if no matching window found.

### click-relative

Click at window-relative coordinates.

```bash
opticpincer click-relative <title> <rx> <ry> [--screenshot]
```

| Argument | Description |
|----------|-------------|
| `title` | Window title substring to match |
| `rx` | X offset from window left edge |
| `ry` | Y offset from window top edge |
| `--screenshot`, `-s` | Take screenshot 300ms after click |

Converts relative coordinates to absolute: `screen_x = window.left + rx`. Note that window coordinates include the title bar.

Exit codes: 0 on success, 1 if no matching window found.

### click-test

Click and verify via before/after screenshot comparison.

```bash
opticpincer click-test <title> <rx> <ry>
```

| Argument | Description |
|----------|-------------|
| `title` | Window title substring to match |
| `rx` | Relative X from window left |
| `ry` | Relative Y from window top |

Sequence: screenshot → click → wait 1 second → screenshot → compare. Reports whether the screenshots differ (click registered) or are identical (click may not have registered).

Exit codes: 0 on success, 1 if no matching window found.

Example:

```bash
opticpincer click-test "MyApp" 60 83
```

```
Taking BEFORE screenshot...
  screenshots/capture_20250320_143120_before.png
Clicking at relative (60, 83)...
  -> screen (172, 218)
Taking AFTER screenshot...
  screenshots/capture_20250320_143121_after.png
RESULT: Screenshots DIFFER -- click registered
```

## Process commands

### launch

Start a background process.

```bash
opticpincer launch <command> [--cwd DIR]
```

| Argument | Description |
|----------|-------------|
| `command` | Command string to run (passed to shell) |
| `--cwd` | Working directory for the process |

The process runs detached with stdout/stderr redirected to `~/.opticpincer/logs/<timestamp>.log`. The PID is saved to `~/.opticpincer/pids/<sanitized>.pid`.

Exit codes: always 0 (the launched process runs independently).

### kill

Kill a process by its window title.

```bash
opticpincer kill <title>
```

| Argument | Description |
|----------|-------------|
| `title` | Window title substring to match |

Finds the window, gets its PID via `GetWindowThreadProcessId`, and runs `taskkill /F /T /PID` to kill the entire process tree.

Exit codes: always 0 (prints whether kill succeeded or no matching window was found).

### wait-for

Wait for a window to appear.

```bash
opticpincer wait-for <title> [--timeout SECONDS]
```

| Argument | Description |
|----------|-------------|
| `title` | Window title substring to match |
| `--timeout` | Seconds to wait (default: 30) |

Polls every 500ms for a window matching the title. Prints dots during polling.

Exit codes: 0 if the window appeared, 1 on timeout.

### rebuild

Kill, rebuild, launch, and wait — the full development cycle.

```bash
opticpincer rebuild --build-cmd CMD --run-cmd CMD --title TITLE [--cwd DIR] [--timeout SECONDS]
```

| Argument | Description |
|----------|-------------|
| `--build-cmd` | Build command (run synchronously, required) |
| `--run-cmd` | Run command (launched in background, required) |
| `--title` | Window title to wait for (required) |
| `--cwd` | Working directory |
| `--timeout` | Seconds to wait for window (default: 60) |

Sequence: kill existing window → run build command → launch run command → wait for window.

Exit codes: 0 on success, 1 if build fails or window timeout.

### log

Print recent process log output.

```bash
opticpincer log [--lines N]
```

| Argument | Description |
|----------|-------------|
| `--lines`, `-n` | Number of lines to show (default: 50) |

Reads the most recent log file from `~/.opticpincer/logs/`. Prints a header with the filename, total line count, and how many lines are shown.

Exit codes: always 0.

## UI tree commands

### ui-tree

List all widgets from `ui_tree.json`.

```bash
opticpincer ui-tree [--tree-path PATH]
```

| Argument | Description |
|----------|-------------|
| `--tree-path` | Path to `ui_tree.json` (default: current working directory) |

Prints widget count, window geometry, `pixels_per_point`, and a table of all widgets with their IDs, kinds, labels, egui rects, and computed screen coordinates.

Exit codes: 0 on success, 1 if `ui_tree.json` not found.

### click-widget

Click a widget by its test ID.

```bash
opticpincer click-widget <title> <widget_id> [--tree-path PATH] [--screenshot] [--screenshot-delay SECONDS]
```

| Argument | Description |
|----------|-------------|
| `title` | Window title substring to match |
| `widget_id` | Widget test ID (e.g., `item_0`, `menu_file`) |
| `--tree-path` | Path to `ui_tree.json` |
| `--screenshot`, `-s` | Take screenshot after click |
| `--screenshot-delay` | Seconds to wait before screenshot (default: 1.0) |

Loads the widget from `ui_tree.json`, reads the current window position via `GetWindowRect` (not the stale position from the JSON), converts the widget center to screen coordinates, and clicks using SetCursorPos + mouse_event.

Exit codes: 0 on success, 1 if `ui_tree.json` not found or widget ID not found.

### click-label

Click a widget by label text match.

```bash
opticpincer click-label <title> <label_text> [--tree-path PATH] [--screenshot] [--screenshot-delay SECONDS]
```

| Argument | Description |
|----------|-------------|
| `title` | Window title substring to match |
| `label_text` | Label text to search for (substring match) |
| `--tree-path` | Path to `ui_tree.json` |
| `--screenshot`, `-s` | Take screenshot after click |
| `--screenshot-delay` | Seconds to wait before screenshot (default: 1.0) |

Same as `click-widget` but finds the widget by substring match against the `label` field instead of the `id` field.

Exit codes: 0 on success, 1 if `ui_tree.json` not found or no matching label found.

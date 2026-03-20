# How to integrate OpticPincer with cargo watch

Use OpticPincer's `rebuild` command to create a rapid feedback loop for Rust GUI development: edit code, auto-rebuild, re-launch, and verify with screenshots.

## Basic rebuild loop

The `rebuild` command performs four steps in sequence: kill the existing instance, build, launch, and wait for the window:

```bash
opticpincer rebuild --build-cmd "cargo build -p your-gui" --run-cmd "cargo run -p your-gui" --title "YourApp"
```

```
Killing existing 'YourApp' ...
Building: cargo build -p your-gui
Build OK
Launched PID 12345: cargo run -p your-gui
Waiting for 'YourApp' (timeout=60s) ....Found HWND=67890
```

After the window appears, you can immediately take screenshots or click widgets:

```bash
opticpincer screenshot "YourApp" after_rebuild
opticpincer click-widget "YourApp" item_0 --screenshot
```

## Set the working directory

If your cargo workspace is not the current directory:

```bash
opticpincer rebuild --build-cmd "cargo build -p your-gui" --run-cmd "cargo run -p your-gui" --title "YourApp" --cwd C:\path\to\workspace
```

## Adjust the timeout

The default window-appearance timeout is 60 seconds. For fast Rust builds, reduce it. For large projects, increase it:

```bash
opticpincer rebuild --build-cmd "cargo build -p your-gui" --run-cmd "cargo run -p your-gui" --title "YourApp" --timeout 120
```

If the window doesn't appear within the timeout, the command exits with code 1. Check the build log:

```bash
opticpincer log
```

## Script a full test cycle

Combine `rebuild` with widget clicks and screenshots in a shell script:

```bash
#!/bin/bash
set -e

# Rebuild and wait for window
opticpincer rebuild \
  --build-cmd "cargo build -p your-gui" \
  --run-cmd "cargo run -p your-gui" \
  --title "YourApp" \
  --cwd C:\path\to\workspace

# Minimize console so it doesn't cover the GUI
opticpincer background

# Click through the UI and capture screenshots
opticpincer click-widget "YourApp" item_0 --screenshot
opticpincer click-widget "YourApp" item_1 --screenshot
opticpincer click-widget "YourApp" menu_file --screenshot

echo "Test cycle complete — check screenshots/"
```

## Use with cargo watch

Run the test script automatically on every code change:

```bash
cargo watch -w src -s "opticpincer rebuild --build-cmd 'cargo build -p your-gui' --run-cmd 'cargo run -p your-gui' --title 'YourApp' && opticpincer click-widget 'YourApp' item_0 --screenshot"
```

This watches the `src/` directory and re-runs the rebuild + click sequence on every file change. The feedback loop is: edit → save → cargo watch triggers → rebuild → launch → click → screenshot.

## Process management details

OpticPincer stores process state under `~/.opticpincer/`:

| Directory | Contents |
|-----------|----------|
| `~/.opticpincer/pids/` | PID files for launched processes (one per command) |
| `~/.opticpincer/logs/` | stdout/stderr logs for launched processes (timestamped) |

The `kill` command finds the window by title, gets its PID via `GetWindowThreadProcessId`, and uses `taskkill /F /T /PID` to kill the entire process tree. This ensures child processes (like the Rust binary spawned by `cargo run`) are also terminated.

The `log` command reads the most recent log file:

```bash
opticpincer log --lines 100
```

This is useful for diagnosing build failures or runtime crashes that happened in the background process.

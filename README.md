# OpticPincer

Native desktop GUI automation for LLM agents -- screenshot, click, and verify.

OpticPincer provides reliable mouse click delivery to native Windows applications
(including GLFW, eframe/egui, winit, and other frameworks that don't respond to
simple SendInput). It uses three click strategies with automatic fallback:

1. **SetCursorPos + mouse_event** -- OS-level input injection (works with winit/eframe)
2. **PostMessage WM_LBUTTONDOWN/UP** -- async window message (works with some Win32 apps)
3. **SendMessage WM_LBUTTONDOWN/UP** -- sync window message (last resort)

## Install

```bash
uv sync
```

## Usage

```bash
# CLI
opticpincer info "MyApp"           # Print window info
opticpincer screenshot "MyApp"     # Capture window screenshot
opticpincer focus "MyApp"          # Bring window to foreground
opticpincer click "MyApp" 100 200  # Click at absolute coords
opticpincer click-relative "MyApp" 60 83  # Click relative to window
opticpincer click-test "MyApp" 60 83      # Click and verify via before/after

# Python
python -m opticpincer info "MyApp"
```

```python
# As a library
from opticpincer import find_window, click_at, take_screenshot, foreground

hwnd, title = find_window("MyApp")
foreground(hwnd)
click_at(hwnd, 100, 200)
take_screenshot(hwnd, label="after_click")
```

## Widget-aware clicking (egui apps)

If your egui app exports `ui_tree.json` with widget test IDs, you can click
widgets by name instead of guessing pixel coordinates:

```bash
opticpincer ui-tree
opticpincer click-widget "MyApp" item_0 --screenshot
```

See the [documentation](docs/index.md) for setup instructions.

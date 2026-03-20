# Click strategies

OpticPincer implements three click strategies. Each uses a different Win32 mechanism to deliver mouse input. Strategy 1 is the default and the only one that works with winit/eframe/GLFW.

## Strategy 1: SetCursorPos + mouse_event (OS-level)

The default strategy. Injects input at the OS level — the same mechanism the physical mouse uses.

### Mechanism

```
SetCursorPos(screen_x, screen_y)    → move the cursor
sleep(hover_time)                   → let the app process the hover
mouse_event(MOUSEEVENTF_LEFTDOWN)  → press left button
sleep(click_pause)                  → hold briefly
mouse_event(MOUSEEVENTF_LEFTUP)    → release left button
```

### Timing parameters

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `focus_wait` | 0.3s | Wait after bringing window to foreground |
| `hover_time` | 0.2s | Wait after cursor move for the app to detect the position |
| `click_pause` | 0.05s | Hold duration between mouse down and mouse up |
| Post-click | 0.2s | Wait after click for the app to process the event |

The `hover_time` is critical for egui/winit. These frameworks read cursor position from the OS input queue on each frame. If you click before the framework has processed the cursor move, the click registers at the old cursor position. At 60fps, one frame is ~17ms, so 200ms gives at least 10 frames of hover time.

### Requirements

- The target window **must be foreground**. `mouse_event` injects into the OS input queue, and the foreground window receives it.
- OpticPincer calls `foreground(hwnd)` automatically before clicking (controlled by the `pre_focus` parameter).

### Compatibility

| Framework | Works? | Why |
|-----------|--------|-----|
| egui/eframe | Yes | Reads from OS input queue via winit |
| winit | Yes | Uses `WM_MOUSEMOVE` / `WM_LBUTTONDOWN` from Windows message loop |
| GLFW | Yes | Reads from OS input queue |
| Qt | Yes | Standard Windows message processing |
| Win32 native | Yes | Standard Windows message processing |

### Python API

```python
from opticpincer import click_at, click_relative

click_at(hwnd, screen_x, screen_y)
click_at(hwnd, screen_x, screen_y, hover_time=0.5)  # slower app
click_relative(hwnd, rel_x, rel_y)
```

### CLI

```bash
opticpincer click "YourApp" 200 300
opticpincer click-relative "YourApp" 60 80
```

## Strategy 2: PostMessage (async window message)

Sends `WM_LBUTTONDOWN` / `WM_LBUTTONUP` messages directly to the window handle. The message is posted to the window's message queue and returns immediately.

### Mechanism

```
PostMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, MAKELONG(client_x, client_y))
sleep(click_pause)
PostMessageW(hwnd, WM_LBUTTONUP, 0, MAKELONG(client_x, client_y))
```

### Coordinate conversion

Screen coordinates are converted to client-area coordinates via `ScreenToClient` before packing into the `lParam`.

### Requirements

- Does NOT require the window to be foreground.
- Coordinates must be client-area relative (handled automatically by `click_at_message`).

### Compatibility

| Framework | Works? | Why |
|-----------|--------|-----|
| Win32 native | Yes | Processes `WM_LBUTTON*` messages directly |
| Qt | Yes | Standard message processing |
| egui/eframe | **No** | winit reads raw input, not `WM_LBUTTON*` messages |
| winit | **No** | Same reason — raw input model |
| GLFW | **No** | Same reason — raw input model |

### Python API

```python
from opticpincer.click import click_at_message

click_at_message(hwnd, screen_x, screen_y)
```

Not exposed via CLI — Strategy 1 is the default for all CLI commands.

## Strategy 3: SendMessage (sync window message)

Same as Strategy 2 but synchronous. `SendMessage` blocks until the target window processes the message.

### Mechanism

```
SendMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, MAKELONG(client_x, client_y))
sleep(click_pause)
SendMessageW(hwnd, WM_LBUTTONUP, 0, MAKELONG(client_x, client_y))
```

### When it's used

Strategy 3 is the fallback when Strategy 2 fails. `click_at_message` tries PostMessage first; if `PostMessageW` returns 0 (failure), it falls back to `SendMessageW`.

### Compatibility

Same as Strategy 2 — does not work with winit/eframe/GLFW.

## Choosing a strategy

| Scenario | Strategy |
|----------|----------|
| Automating egui/eframe/winit/GLFW apps | Strategy 1 (default) |
| Automating classic Win32 or Qt apps | Strategy 1 (default) or Strategy 2 |
| Window must stay in background during click | Strategy 2 (but not for winit/eframe) |
| Strategy 2 fails silently | Strategy 3 is tried automatically |

For egui/eframe apps, always use Strategy 1. There is no workaround for the winit raw-input model with window messages.

## Win32 constants

| Constant | Value | Meaning |
|----------|-------|---------|
| `WM_LBUTTONDOWN` | `0x0201` | Left mouse button pressed |
| `WM_LBUTTONUP` | `0x0202` | Left mouse button released |
| `MK_LBUTTON` | `0x0001` | Left button is down (wParam flag) |
| `MOUSEEVENTF_LEFTDOWN` | `0x0002` | Inject left-button-down event |
| `MOUSEEVENTF_LEFTUP` | `0x0004` | Inject left-button-up event |

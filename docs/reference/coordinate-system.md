# Coordinate system

OpticPincer works with four coordinate spaces. Understanding how they relate is essential for clicking the right pixel.

## The four coordinate spaces

| Space | Origin | Unit | Used by |
|-------|--------|------|---------|
| Screen | Top-left of primary monitor | Pixels | `click`, `SetCursorPos`, `GetWindowRect` |
| Window | Top-left of window (includes title bar and borders) | Pixels | `click-relative`, `GetWindowRect` |
| Client | Top-left of client area (inside borders, below title bar) | Pixels | `PostMessage`, `ScreenToClient`, `ui_tree.json window.*` |
| egui logical | Top-left of egui viewport | Logical points | `ui_tree.json widget.rect` |

## Screen coordinates

Absolute pixel position on the monitor. The primary monitor starts at (0, 0). On multi-monitor setups, the secondary monitor may start at (1920, 0) or (0, -1080) depending on arrangement.

`GetWindowRect` returns the window's bounding rectangle in screen coordinates:

```python
left, top, width, height = get_window_rect(hwnd)
# left, top = screen position of window's top-left corner (including title bar)
# width, height = total window size (including title bar and borders)
```

## Window coordinates

Relative to the window's top-left corner, including the title bar and window borders. When you use `click-relative`, coordinates are in this space:

```bash
opticpincer click-relative "YourApp" 60 80
# Clicks at screen position (window.left + 60, window.top + 80)
```

The title bar is typically 30-40 pixels tall. A click at `(0, 0)` hits the top-left pixel of the title bar, not the client area.

## Client coordinates

Relative to the top-left corner of the client area — the drawable region inside the window borders and below the title bar. Win32's `ScreenToClient` converts between screen and client coordinates:

```python
client_x, client_y = screen_to_client(hwnd, screen_x, screen_y)
```

The `ui_tree.json` `window` object uses client coordinates:

```json
"window": {"left": 112, "top": 135, "width": 1920, "height": 1080}
```

Here, `left=112` and `top=135` are the screen position of the client area's top-left corner, not the window's top-left corner. This is what egui reports as its viewport origin.

## egui logical points

egui uses a virtual coordinate space called "logical points." At 100% DPI scaling, 1 logical point = 1 pixel. At 150% scaling, 1 logical point = 1.5 pixels.

Widget rects in `ui_tree.json` are in logical points relative to the egui viewport origin:

```json
{"id": "item_0", "rect": [10.0, 60.0, 170.0, 78.0]}
```

This means: left edge at 10 logical points, top at 60, right at 170, bottom at 78.

## Converting egui logical points to screen pixels

The conversion formula:

```
screen_x = client_left + logical_x * pixels_per_point
screen_y = client_top  + logical_y * pixels_per_point
```

Where:
- `client_left`, `client_top` = client area origin in screen pixels (from `ui_tree.json window` or live `GetWindowRect`)
- `logical_x`, `logical_y` = widget center in egui logical points
- `pixels_per_point` = DPI scale factor from `ui_tree.json`

### Full example

Given:
- Window client area at screen position (112, 135)
- `pixels_per_point = 1.25`
- Widget rect: `[10.0, 60.0, 170.0, 78.0]`

```
center_x = (10.0 + 170.0) / 2 = 90.0
center_y = (60.0 + 78.0)  / 2 = 69.0

screen_x = 112 + 90.0 * 1.25 = 224
screen_y = 135 + 69.0 * 1.25 = 221
```

Click at screen pixel (224, 221) to hit the widget center.

## Window position: stale vs. current

`ui_tree.json` stores the window position at the time the JSON was written. If the window moves afterward, these values are stale.

OpticPincer's `click-widget` command handles this automatically:

1. Reads the widget rect from `ui_tree.json` (these are relative to the client area, so they stay valid)
2. Reads the **current** window position via `GetWindowRect` (live Win32 call)
3. Uses the current position for the coordinate conversion

This means `click-widget` works correctly even if the window has moved since the JSON was last written. The only assumption is that the widget layout has not changed — which is valid because `ui_tree.json` updates every frame while the app runs.

## Common pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Using window coordinates when client coordinates are needed | Click lands 30-40px too high (hits title bar) | Use `click-widget` or add title bar offset |
| Ignoring `pixels_per_point` | Click lands at wrong position on high-DPI displays | Multiply logical points by `pixels_per_point` |
| Using stale window position from JSON | Click lands at old window position | `click-widget` handles this; for manual clicks, use live `info` output |
| Confusing `GetWindowRect` (includes borders) with client position | Off-by-border-width errors | Use `ScreenToClient` or `ui_tree.json` client position |

# How to debug a click not registering

You clicked at the right coordinates, the command reported success, but the app didn't respond. Here's how to diagnose and fix it.

## Verify the click landed

Use `click-test` to take before/after screenshots and compare:

```bash
opticpincer click-test "YourApp" 60 80
```

```
RESULT: Screenshots IDENTICAL -- click may not have registered
```

If the screenshots are identical, the click did not produce a visible effect. If they differ, the click landed but may have hit the wrong widget.

## Check: is the window actually foreground?

OpticPincer's default click strategy (SetCursorPos + mouse_event) requires the target window to be the foreground window. If another window steals focus between the focus call and the click, the click goes to the wrong window.

```bash
opticpincer info "YourApp"
```

Check the `Foregnd` field. If `False`, something is stealing focus. Common causes:
- A notification popup appeared
- The console window regained focus
- Another application raised itself

Fix: use `opticpincer background` before clicking to minimize the console, and ensure no other apps are stealing focus.

## Check: are the coordinates correct?

Take a screenshot and measure the pixel coordinates of your target widget manually:

```bash
opticpincer screenshot "YourApp"
```

Open the screenshot in an image editor and check the pixel position. Compare with what OpticPincer reports. Remember:
- `click` uses absolute screen coordinates
- `click-relative` uses coordinates relative to the window's top-left corner (including the title bar)
- `click-widget` reads coordinates from `ui_tree.json` and converts them to screen pixels

For egui apps, prefer `click-widget` over manual coordinates — it handles coordinate conversion automatically.

## Check: egui hover delay

egui and winit need at least one frame to process the cursor position before they register a click. OpticPincer's `click_at` function includes a 200ms hover delay by default. If your app runs at a low frame rate (below 30fps), the hover delay may be too short.

Signs of this problem:
- The click works sometimes but not always
- The click works reliably when the app is under low load but fails under heavy load
- Adding `time.sleep(0.5)` before the click in a Python script fixes it

The hover delay is controlled by the `hover_time` parameter in the Python API:

```python
from opticpincer import click_at

click_at(hwnd, x, y, hover_time=0.5)  # 500ms hover for slow apps
```

## Check: the app uses a non-standard input model

OpticPincer's default strategy (Strategy 1: SetCursorPos + mouse_event) works with frameworks that read from the OS input queue:

| Framework | Strategy 1 works? |
|-----------|-------------------|
| egui/eframe | Yes |
| winit | Yes |
| GLFW | Yes |
| Qt | Yes |
| Win32 native | Yes |
| DirectX/OpenGL overlay | Sometimes (depends on input handling) |

If the app processes raw input (`WM_INPUT` via `RegisterRawInputDevices`), Strategy 1 may not work. This is rare outside of games and fullscreen applications.

## Check: DPI scaling

On high-DPI displays, Windows may scale coordinates. If the app is DPI-unaware but the system is at 125% or 150% scaling, pixel coordinates may be off.

For egui apps, the `pixels_per_point` field in `ui_tree.json` accounts for this. The coordinate conversion formula is:

```
screen_x = window.left + center_x * pixels_per_point
screen_y = window.top  + center_y * pixels_per_point
```

If `pixels_per_point` is 1.0 but your display scaling is 1.25, the app may be DPI-aware and handling scaling internally. Check the egui app's viewport settings.

## Check: the click hits the title bar or border

Window coordinates from `GetWindowRect` include the title bar and window borders. If you're clicking near the top of the window, your click may be landing on the title bar instead of the client area.

The title bar is typically 30-40 pixels tall. Add that offset to your Y coordinate:

```bash
# Instead of clicking at relative (10, 5) which hits the title bar:
opticpincer click-relative "YourApp" 10 40
```

For egui apps, `click-widget` handles this automatically because `ui_tree.json` stores the client-area position, not the window position.

## Last resort: check the process log

If the app launched via `opticpincer launch`, its stdout/stderr is captured in `~/.opticpincer/logs/`:

```bash
opticpincer log --lines 100
```

Look for error messages, crash output, or input-handling debug logs from the GUI framework.

# How to click by widget ID

Use `ui_tree.json` and OpticPincer's `click-widget` command to click egui widgets by their stable test ID instead of guessing pixel coordinates.

## List available widgets

First, check what widgets the app exports:

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

Each line shows: widget ID, kind, label, egui rect, and computed screen coordinates.

## Click by exact widget ID

```bash
opticpincer click-widget "YourApp" item_0
```

```
Widget: item_0 (Dataset A) -> screen(202, 204)
Clicked widget 'item_0'
```

OpticPincer performs these steps internally:
1. Loads `ui_tree.json` and finds the widget by ID
2. Finds the window by title substring and reads its current position via `GetWindowRect`
3. Converts the widget's center from egui logical points to screen pixels: `screen_x = window.left + center_x * pixels_per_point`
4. Uses the current window position (not the stale position from `ui_tree.json`) — so it works even if the window moved
5. Clicks using SetCursorPos + mouse_event (the OS-level strategy that works with winit/eframe)

## Click by label text

When you know the displayed text but not the widget ID:

```bash
opticpincer click-label "YourApp" "Dataset A"
```

This performs a substring match against all widget labels. Useful when widget IDs follow a generated pattern but labels are human-readable.

## Add a screenshot after clicking

```bash
opticpincer click-widget "YourApp" item_0 --screenshot
opticpincer click-widget "YourApp" item_0 --screenshot --screenshot-delay 2.0
```

The `--screenshot` flag captures the window after clicking. The default delay is 1.0 seconds (enough for most egui apps to re-render). Increase `--screenshot-delay` for operations that trigger loading (e.g., opening a file).

## Use a custom tree path

By default, OpticPincer reads `ui_tree.json` from the current working directory. Override with `--tree-path`:

```bash
opticpincer click-widget "YourApp" item_0 --tree-path C:\myproject\ui_tree.json
```

The same flag works for `ui-tree` and `click-label`.

## When the widget is not found

If the widget ID does not exist in `ui_tree.json`, OpticPincer prints all available IDs:

```
ERROR: Widget 'nonexistent' not found in ui_tree.json
  Available: ['item_0', 'item_1', 'menu_file', 'save_button']
```

Check that:
1. The app is running with test mode enabled (e.g. `APP_TEST_MODE=1`)
2. The widget has a test ID assigned in the egui code
3. The `ui_tree.json` is current (it updates every frame while the app runs)

## Why this is better than pixel coordinates

| Approach | Breaks when |
|----------|-------------|
| Absolute pixel coordinates | Window moves, resolution changes, any layout change |
| Relative pixel coordinates | Widget repositions within the window, font size changes |
| Widget ID via ui_tree | Never — the ID is stable across moves, resizes, and layout changes |

The widget rect in `ui_tree.json` updates every frame, so it always reflects the current layout. The ID stays the same regardless of where the widget ends up on screen.

For how to add test IDs to your egui app, see [Automate an egui app](automate-egui-app.md).

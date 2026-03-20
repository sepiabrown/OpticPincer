# ui_tree.json schema

The `ui_tree.json` file is exported by egui apps running in test mode. It contains a snapshot of all tagged widgets with their positions, updated every frame.

## Top-level structure

```json
{
  "timestamp_ms": 1234567890,
  "window": {
    "left": 112,
    "top": 135,
    "width": 1920,
    "height": 1080
  },
  "pixels_per_point": 1.0,
  "widgets": [
    {
      "id": "item_0",
      "label": "Dataset A",
      "kind": "selectable",
      "rect": [10.0, 60.0, 170.0, 78.0]
    }
  ]
}
```

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `timestamp_ms` | integer | Unix timestamp in milliseconds when the tree was written |
| `window` | object | Client-area position and size in screen pixels |
| `window.left` | integer | Left edge of the client area in screen pixels |
| `window.top` | integer | Top edge of the client area in screen pixels |
| `window.width` | integer | Client area width in screen pixels |
| `window.height` | integer | Client area height in screen pixels |
| `pixels_per_point` | float | egui's DPI scale factor (1.0 at 100% scaling, 1.25 at 125%, etc.) |
| `widgets` | array | List of widget entries |

## Widget entry

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Stable test ID assigned in the egui code (e.g., `item_0`, `menu_file`) |
| `label` | string | Display text of the widget (may be empty for non-text widgets) |
| `kind` | string | Widget type: `selectable`, `button`, `label`, `text_edit`, etc. |
| `rect` | array of 4 floats | Bounding box in egui logical points: `[left, top, right, bottom]` |

## Coordinate system

Widget `rect` values are in **egui logical points** relative to the viewport origin (top-left corner of the client area). They are not pixel values.

To convert a widget's center to screen pixels:

```
center_x = (rect[0] + rect[2]) / 2
center_y = (rect[1] + rect[3]) / 2

screen_x = window.left + center_x * pixels_per_point
screen_y = window.top  + center_y * pixels_per_point
```

### Example

Given:
- `window.left = 112`, `window.top = 135`
- `pixels_per_point = 1.0`
- Widget rect: `[10.0, 60.0, 170.0, 78.0]`

```
center_x = (10 + 170) / 2 = 90
center_y = (60 + 78) / 2 = 69

screen_x = 112 + 90 * 1.0 = 202
screen_y = 135 + 69 * 1.0 = 204
```

The widget center is at screen pixel (202, 204).

## Stale window position

The `window.left` and `window.top` values are written when the JSON is exported. If the window moves after the export, these values become stale. OpticPincer's `click-widget` command handles this by reading the current window position via `GetWindowRect` and using that instead of the stale JSON values.

The widget `rect` values remain valid because they are relative to the client area, not to the screen.

## File location

The default path is `ui_tree.json` in the current working directory. Override with `--tree-path` on any `ui-tree`, `click-widget`, or `click-label` command.

## Producer

The JSON is written by a test export module in your egui app (e.g., `src/test_export.rs`) on every frame when test mode is enabled. The export iterates over all widgets in the egui response, filters for those with test IDs, and writes their metadata.

For how to add test IDs to your egui widgets, see [Automate an egui app](../how-to/automate-egui-app.md).

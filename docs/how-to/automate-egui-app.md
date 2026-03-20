# How to automate an egui app with OpticPincer

Add stable test IDs to your egui/eframe widgets so OpticPincer can click them by name instead of pixel position.

## Add test IDs to your egui code

In your egui rendering code, add `.id()` or `.id_source()` calls to give widgets stable identifiers:

```rust
// In your egui UI code
ui.push_id("item_list", |ui| {
    for (i, item) in items.iter().enumerate() {
        let response = ui.selectable_label(
            selected == Some(i),
            &item.name,
        );
        // Tag this widget for test automation
        response.id = egui::Id::new(format!("item_{i}"));
    }
});
```

Choose IDs that describe the widget's purpose, not its position: `item_0`, `menu_file`, `save_button` — not `button_3` or `item_at_200_300`.

## Export the UI tree as JSON

Enable the JSON export by setting an environment variable (e.g. `APP_TEST_MODE=1`) before launching your app. Your egui app needs a test export module (typically `src/test_export.rs`) that writes `ui_tree.json` on every frame:

```json
{
  "timestamp_ms": 1234567890,
  "window": {"left": 112, "top": 135, "width": 1920, "height": 1080},
  "pixels_per_point": 1.0,
  "widgets": [
    {"id": "item_0", "label": "Dataset A", "kind": "selectable",
     "rect": [10.0, 60.0, 170.0, 78.0]}
  ]
}
```

The `window` object stores the client-area position in screen pixels. Widget `rect` values are in egui logical points relative to the viewport origin.

For the full JSON schema, see [ui_tree.json reference](../reference/ui-tree-json.md).

## Launch with test mode enabled

```bash
set APP_TEST_MODE=1
cargo run -p your-gui-app
```

Or use OpticPincer's process management:

```bash
opticpincer launch "cargo run -p your-gui-app" --cwd C:\path\to\project
opticpincer wait-for "YourApp" --timeout 30
```

## Verify the UI tree is exported

```bash
opticpincer ui-tree
```

This reads `ui_tree.json` and lists all widgets with their IDs, labels, kinds, rects, and computed screen coordinates.

If you get `ERROR: ui_tree.json not found`, check that:
1. The app is running with test mode enabled (e.g. `APP_TEST_MODE=1`)
2. The `--tree-path` points to the correct location (default: current working directory)

## Click widgets by ID

```bash
opticpincer click-widget "YourApp" item_0 --screenshot
```

OpticPincer reads the widget's rect from `ui_tree.json`, converts its center to screen coordinates using the current window position (not the stale position from the JSON), and clicks there using SetCursorPos + mouse_event.

## Click widgets by label text

When you don't know the exact widget ID but know the displayed text:

```bash
opticpincer click-label "YourApp" "Dataset A"
```

This searches all widgets for a label containing the given substring and clicks the first match.

## Full automation loop

A typical test sequence:

```bash
# 1. Build and launch
opticpincer rebuild --build-cmd "cargo build" --run-cmd "cargo run" --title "YourApp" --cwd C:\project

# 2. Background the console
opticpincer background

# 3. Click a widget
opticpincer click-widget "YourApp" item_0 --screenshot

# 4. Verify the result visually (or via screenshot comparison)
opticpincer click-test "YourApp" 60 80
```

For more on the click-widget workflow, see [Click by widget ID](click-by-widget-id.md).

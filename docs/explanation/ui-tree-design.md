# Why egui test IDs + JSON export beats pixel guessing and vision models

## The problem: how do you name a pixel?

Native GUI apps render to a framebuffer. From the outside, they are a rectangle of pixels. To click a button, you need its coordinates. But how do you know where the button is?

Three approaches exist:

1. **Hard-code pixel coordinates.** Measure once, click at (200, 300) forever. Breaks when the window moves, resizes, or the layout changes.

2. **Ask a vision model.** Screenshot the app, send it to GPT-4V or Claude, ask "where is the Save button?" Works, but slow (2-10s per query), expensive (1000+ tokens per screenshot), and imprecise (±5 pixels).

3. **Ask the app itself.** Have the app export its widget positions as structured data. The widget ID is the "name" for the pixel region. Zero latency, pixel-perfect, free.

OpticPincer uses approach 3 via `ui_tree.json`. The egui app tags its widgets with stable test IDs and exports their positions every frame. OpticPincer reads the JSON, looks up the widget by ID, and clicks its center.

## Why the app must cooperate

This design requires modifying the app — you have to add test IDs and the JSON export code. This is an intentional trade-off.

### What you give up

- **Zero-setup automation.** You can't automate an arbitrary app without modifying it.
- **Black-box testing.** The app knows it's being tested.

### What you gain

- **Stable identifiers.** `item_0` means the same widget across window moves, resizes, theme changes, and layout reflows. No pixel coordinate ever has this property.
- **Zero latency.** A JSON file read is instantaneous. No network call, no model inference.
- **Pixel-perfect accuracy.** The app knows its own layout to subpixel precision. No estimation.
- **Framework independence.** Any framework that can write a JSON file can participate. The UI tree design is not egui-specific — it's a pattern that Qt, GLFW, or Dear ImGui apps could adopt.
- **Deterministic.** Same widget ID → same click target. No stochastic vision model in the loop.

The trade-off is strongly in favor of cooperation for apps you control, which is the common case for development and testing workflows.

## The JSON schema design

The `ui_tree.json` schema was designed for minimal complexity:

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

### Design choices

**Flat widget list, not a tree.** Although egui has a widget hierarchy (panels contain groups contain buttons), the exported list is flat. OpticPincer doesn't need hierarchy — it needs to find a widget by ID and get its screen position. A flat list with a linear scan is simpler and sufficient for the ~10-100 widgets a typical UI exports.

**Rects in egui logical points.** Not screen pixels. This separates the widget layout (which egui controls) from the screen mapping (which depends on window position and DPI). The conversion is a simple multiply: `screen = client_origin + logical * pixels_per_point`.

**Client-area origin, not window origin.** The `window.left` and `window.top` in the JSON refer to the client area (the drawable region inside the title bar and borders), not the window's outer edge. This matches egui's viewport origin and avoids title-bar-offset calculations.

**Per-frame export.** The JSON is rewritten every frame. This means it's always current — if a widget moves because of a layout change, the next read will get the updated position. The downside (disk I/O every frame) is negligible for development/test builds.

**`pixels_per_point` as a top-level field.** DPI scaling affects all widget positions uniformly. Storing it once at the top level instead of per-widget avoids redundancy and makes the conversion formula obvious.

## Why not a hierarchical tree?

A full widget tree (parent → children with nested rects) would be useful for understanding the UI structure, but it adds complexity that OpticPincer doesn't need:

- **For clicking**, you need: widget ID → screen position. Hierarchy is irrelevant.
- **For verification**, you need: screenshot comparison. The visual result doesn't depend on widget hierarchy.
- **For debugging**, you need: list of all widgets with their IDs and positions. A flat list is easier to scan than a nested tree.

If a future use case requires hierarchy (e.g., "click the Save button inside the File menu inside the menu bar"), it can be added by extending the schema with an optional `parent` field. The flat structure is forward-compatible.

## How it compares to browser DOM automation

Browser automation (Playwright, Selenium) works because:
1. Every element has a selector (CSS, XPath, or test ID)
2. The browser exposes a structured API to find elements by selector
3. The browser handles the coordinate conversion and click delivery

`ui_tree.json` achieves the same pattern for native apps:
1. Every widget has a test ID
2. The JSON file is the "API" to find widgets by ID
3. OpticPincer handles the coordinate conversion and click delivery

The main difference: in browsers, the infrastructure exists universally. In native apps, each app must opt in by exporting its widget tree. This is the cost of framework diversity — there is no universal native DOM.

## When to use pixel coordinates instead

The UI tree approach requires app modification. Use pixel coordinates when:

- **You can't modify the app.** Automating a third-party application where you don't have the source code.
- **The app has no widgets.** A fullscreen renderer or game with no standard GUI widgets.
- **One-off testing.** A quick check where adding test IDs would take more time than guessing coordinates.

For one-off pixel guessing, `click-relative` with a screenshot for verification is sufficient. For repeated automation, invest in test IDs — the reliability gain pays for itself immediately.

## The path forward

The `ui_tree.json` pattern is not limited to egui. Any GUI framework that knows its own widget layout can export a similar file:

- **Qt:** Override `paintEvent` to write widget geometries
- **Dear ImGui:** Export the item rect stack after each frame
- **GLFW apps with custom UI:** Write the UI state to JSON alongside the render loop

The schema is simple enough to implement in any language in under 100 lines of code. The value comes from the stable-ID-to-coordinate mapping, not from any framework-specific feature.

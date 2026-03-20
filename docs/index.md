# OpticPincer documentation

OpticPincer gives LLM agents eyes and hands on native desktop applications. It captures screenshots, clicks buttons, reads UI trees, and manages processes — all through Win32 API calls that work with native GUI frameworks (egui/eframe, Qt, GLFW, winit) where browser automation cannot reach.

This documentation is organized following the [Diataxis](https://diataxis.fr/) framework into four quadrants.

## Tutorials

Learn OpticPincer by doing.

- [Your first GUI test](tutorials/first-gui-test.md) — Launch an app, screenshot it, click a button, and verify the result.

## How-to guides

Solve specific problems.

- [Automate an egui app](how-to/automate-egui-app.md) — Add test IDs to an egui app and automate it with OpticPincer.
- [Click by widget ID](how-to/click-by-widget-id.md) — Use ui-tree + click-widget instead of pixel guessing.
- [Debug click not registering](how-to/debug-click-not-registering.md) — Troubleshooting: when clicks land but don't register.
- [Integrate with cargo watch](how-to/integrate-with-cargo-watch.md) — Use OpticPincer with cargo watch for Rust GUI development.

## Reference

Technical descriptions of every command and data format.

- [CLI commands](reference/cli-commands.md) — All CLI commands with arguments, examples, and exit codes.
- [ui_tree.json schema](reference/ui-tree-json.md) — JSON schema for the UI tree export.
- [Click strategies](reference/click-strategies.md) — The three click strategies: SetCursorPos, PostMessage, SendMessage.
- [Coordinate system](reference/coordinate-system.md) — How screen, window, client, and egui coordinates relate.

## Explanation

Understand why OpticPincer works the way it does.

- [Why OpticPincer](explanation/why-opticpincer.md) — Why LLM agents need native GUI automation, not just browser automation.
- [How clicking works](explanation/how-clicking-works.md) — Deep dive: Win32 input injection, winit message loop, AttachThreadInput.
- [UI tree design](explanation/ui-tree-design.md) — Why egui test IDs + JSON export beats pixel guessing and vision models.

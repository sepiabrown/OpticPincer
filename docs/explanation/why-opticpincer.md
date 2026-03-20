# Why LLM agents need native GUI automation

## The gap between browser and desktop

LLM agents have mature tools for browser automation: Playwright, Puppeteer, Selenium. They can navigate web apps, fill forms, click buttons, and read the DOM. But when the agent needs to interact with a native desktop application — an egui viewer, a Qt editor, a GLFW renderer — these tools cannot help.

Browser automation works because browsers expose a structured DOM. Every button has an ID, every input has a name, every element has a CSS selector. The automation tool never guesses where to click — it asks the browser "where is the element with id='submit'?" and the browser tells it.

Native desktop apps have no equivalent. There is no DOM. There is no universal accessibility tree that works across frameworks. The window is a rectangle of pixels, and the only way to interact with it is to move the mouse cursor and click.

## Why not use vision models?

A natural reaction: "Just screenshot the app, send it to a vision model, and ask where the button is." This works — sometimes. The problems:

1. **Latency.** A vision model call takes 2-10 seconds. A coordinate lookup in a JSON file takes 0ms. For a test that clicks 20 widgets, vision adds 40-200 seconds of overhead.

2. **Accuracy.** Vision models estimate positions. They might say "the button is at roughly (200, 300)" when it's actually at (205, 295). A 5-pixel error on a small button means a miss.

3. **Cost.** Each screenshot sent to a vision model consumes tokens. A high-resolution screenshot is 1000+ tokens. Over hundreds of test iterations, this adds up.

4. **Fragility.** Vision models are influenced by theme, font size, window decorations, and background content. A dark theme may cause different predictions than a light theme for the same widget at the same position.

The UI tree approach (JSON export of widget IDs and positions) solves all four problems: zero latency, pixel-perfect accuracy, zero token cost, theme-independent.

## Why not use accessibility APIs?

Windows has UI Automation (UIA) and MSAA. These APIs expose widget trees for accessible applications. The problem: most native GUI frameworks used in scientific and engineering tools don't fully implement accessibility.

| Framework | UIA support |
|-----------|-------------|
| Qt | Good (QAccessible) |
| WPF | Good (AutomationPeer) |
| Win32 native | Partial |
| egui/eframe | None |
| winit | None |
| GLFW | None |
| Dear ImGui | None |

egui, winit, GLFW, and Dear ImGui are immediate-mode or low-level frameworks. They render directly to a graphics surface and don't expose a widget tree through Windows accessibility APIs. For these frameworks, there is no system-level way to discover "where is the button labeled 'Save'?"

OpticPincer bridges this gap by having the app itself export its widget tree as JSON. The egui app knows its own layout — it just needs to write it down.

## Why OS-level input injection?

OpticPincer uses `SetCursorPos` + `mouse_event` to click. This is the same mechanism as a physical mouse — it injects input into the OS input queue, and the foreground window receives it.

The alternative — sending `WM_LBUTTONDOWN` / `WM_LBUTTONUP` window messages via `PostMessage` — does not work with modern frameworks like winit and eframe. These frameworks read from the OS input queue (raw input), not from the window message queue. A `PostMessage` click is invisible to them.

This is the single most important technical decision in OpticPincer: use Strategy 1 (OS-level) by default, because the frameworks that need automation most (egui, winit, GLFW) are exactly the ones that ignore window messages.

## Why AttachThreadInput for foreground?

`SetForegroundWindow` only works if the calling thread is the foreground thread. The classic workaround is to simulate an Alt keypress (`keybd_event(VK_MENU)`) to trick Windows into granting foreground permission. But this triggers the menu bar in many applications — egui, Qt, and most GUI apps interpret Alt as "activate the menu."

OpticPincer uses `AttachThreadInput` instead: temporarily link the calling thread with the current foreground thread, call `SetForegroundWindow`, then detach. This grants foreground permission without any keyboard side-effects.

## The design: eyes + hands + names

OpticPincer gives agents three capabilities:

1. **Eyes** — `screenshot` captures what the app looks like right now. This is the agent's visual feedback channel.

2. **Hands** — `click`, `click-relative`, `click-widget` let the agent interact with the app. SetCursorPos + mouse_event works with every GUI framework.

3. **Names** — `ui-tree`, `click-widget`, `click-label` let the agent refer to widgets by stable identifiers instead of pixel positions. This requires cooperation from the app (exporting `ui_tree.json`), but it transforms GUI automation from fragile pixel guessing into reliable named-widget interaction.

The combination makes native GUI automation practical for LLM agents. Eyes without hands is observation. Hands without names is pixel guessing. All three together is reliable automation.

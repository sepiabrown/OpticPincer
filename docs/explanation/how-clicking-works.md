# How clicking works: Win32 input injection and foreground management

This page explains the mechanics of how OpticPincer delivers mouse clicks to native desktop applications, why the approach differs from browser automation, and how the foreground permission system works.

## The Windows input pipeline

When you move a physical mouse and click, the input travels through several layers:

```
Physical mouse
  → HID driver
    → Windows input queue (system-wide)
      → Thread input queue (per-thread)
        → Window message loop (GetMessage / PeekMessage)
          → App processes WM_LBUTTONDOWN / WM_LBUTTONUP
```

The key insight: `SetCursorPos` and `mouse_event` inject at the **system-wide input queue** level. To the application, the injected input is indistinguishable from a physical mouse click. The cursor visibly moves on screen, and the foreground window receives the events through its normal message loop.

## Why winit/eframe needs OS-level injection

winit (used by eframe/egui) processes input through its event loop, which reads from the system input queue via `GetMessage` / `PeekMessage`. When it receives `WM_LBUTTONDOWN`, it translates it into a winit `WindowEvent::MouseInput` and passes it to the application.

Crucially, winit processes these events as part of its **message loop iteration**. It does not respond to `PostMessage`-delivered `WM_LBUTTONDOWN` in the same way, because:

1. winit's message loop calls `GetMessage`, which retrieves messages from both the system queue and the posted queue
2. But winit also tracks cursor position via `WM_MOUSEMOVE` — if the cursor never moved (because `PostMessage` doesn't move the cursor), the click registers at the wrong position
3. Some winit configurations use `WM_INPUT` (raw input) for mouse tracking, which `PostMessage` cannot trigger at all

`SetCursorPos` + `mouse_event` solves this because:
- `SetCursorPos` generates a real `WM_MOUSEMOVE` in the system queue
- `mouse_event` generates real `WM_LBUTTONDOWN` / `WM_LBUTTONUP` in the system queue
- winit processes both through its normal path

## The hover delay

egui runs at a fixed frame rate (typically 60fps). On each frame, it reads the current cursor position and processes any pending input events. If OpticPincer moves the cursor and clicks in the same instant (within one frame), egui may process the click at the **previous** cursor position.

The solution is the hover delay: move the cursor, wait for at least one frame, then click.

```python
SetCursorPos(x, y)
time.sleep(0.2)       # 200ms = ~12 frames at 60fps
mouse_event(LEFTDOWN)
time.sleep(0.05)      # 50ms hold
mouse_event(LEFTUP)
```

The 200ms default is conservative — it works even at 15fps. For high-performance apps, 50ms would suffice. For apps under heavy load (e.g., loading a large dataset), 500ms or more may be needed.

## Foreground window permission

Windows enforces a rule: only the foreground thread can call `SetForegroundWindow` to bring a window to the front. A background process (like OpticPincer running from a terminal) is not the foreground thread, so `SetForegroundWindow` is silently ignored.

### The Alt key hack (and why it's bad)

The classic workaround:

```python
keybd_event(VK_MENU, 0, 0, 0)        # Press Alt
SetForegroundWindow(hwnd)
keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)  # Release Alt
```

Pressing Alt tricks Windows into thinking the user initiated the focus change. But it has a critical side effect: most GUI frameworks interpret the Alt keypress as "activate the menu bar." In egui, Qt, and many apps, this opens the File menu or highlights the menu bar. This makes the app state unpredictable for automation.

### AttachThreadInput (what OpticPincer uses)

`AttachThreadInput` is a Win32 function that links two threads' input queues together. While attached, they share focus and foreground state.

OpticPincer's `foreground()` function:

```python
def foreground(hwnd, wait=0.3):
    # Get thread IDs
    fg_tid = GetWindowThreadProcessId(GetForegroundWindow())
    target_tid = GetWindowThreadProcessId(hwnd)
    our_tid = GetCurrentThreadId()

    # Attach our thread to the foreground thread
    AttachThreadInput(our_tid, fg_tid, True)

    # Now we have permission
    SetForegroundWindow(hwnd)
    BringWindowToTop(hwnd)

    # Detach
    AttachThreadInput(our_tid, fg_tid, False)

    time.sleep(wait)  # Let the window fully activate
```

The sequence:
1. **Attach** our thread to the current foreground thread's input queue — this gives us foreground permission
2. **Call** `SetForegroundWindow` — now it succeeds because we're "part of" the foreground thread
3. **Detach** — clean up the thread attachment
4. **Wait** — the target window needs time to fully activate and process `WM_ACTIVATE`

No keyboard events are generated. No menu bar is triggered. The focus change is clean.

### When the window is minimized

If the target window is minimized (`IsIconic` returns true), it must be restored before it can become the foreground window:

```python
if IsIconic(hwnd):
    ShowWindow(hwnd, SW_RESTORE)
    time.sleep(0.2)
```

`SW_RESTORE` brings the window back to its previous size and position. The 200ms wait gives the window time to finish its restore animation.

## Console window management

OpticPincer is a CLI tool — it runs from a console window. When it brings the target app to the foreground, the console is still visible and may partially cover the target.

The `background` command minimizes the console window:

```python
def background():
    console_hwnd = kernel32.GetConsoleWindow()
    if console_hwnd:
        ShowWindow(console_hwnd, SW_MINIMIZE)
```

This is especially important for screenshot accuracy — you don't want the console window appearing in the captured region.

## The click sequence in full

Here is the complete sequence when you run `opticpincer click-widget "MyApp" item_0`:

```
1. Load ui_tree.json → find widget "item_0" → get rect [10, 60, 170, 78]
2. find_window("MyApp") → enumerate all windows → match "MyApp" → get HWND
3. get_window_info(HWND) → get current window position (left, top)
4. Convert: screen_x = left + center_x * pixels_per_point
5. foreground(HWND):
   a. AttachThreadInput(our_tid, fg_tid, True)
   b. SetForegroundWindow(HWND)
   c. AttachThreadInput(our_tid, fg_tid, False)
   d. sleep(0.3)
6. SetCursorPos(screen_x, screen_y) → cursor moves visibly
7. sleep(0.2) → hover delay for egui to detect cursor
8. mouse_event(LEFTDOWN) → press
9. sleep(0.05) → hold
10. mouse_event(LEFTUP) → release
11. sleep(0.2) → let app process the click
```

Steps 5-11 happen in `click_at()`. The hover delay (step 7) is what makes egui clicks reliable. The AttachThreadInput dance (step 5a-5c) is what makes foreground focus reliable.

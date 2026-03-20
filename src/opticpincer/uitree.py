"""Read ``ui_tree.json`` exported by an egui app in test mode.

Enables clicking widgets by their stable test ID instead of guessing
pixel coordinates.

The JSON schema (written by a test-export module in the egui app)::

    {
      "timestamp_ms": 1234567890,
      "window": {"left": 112, "top": 135, "width": 1920, "height": 1080},
      "pixels_per_point": 1.0,
      "widgets": [
        {"id": "item_0", "label": "Dataset A", "kind": "selectable",
         "rect": [10.0, 60.0, 170.0, 78.0]}
      ]
    }

``window.left/top`` is the **inner** (client-area) position in screen
pixels.  Widget rects are in egui logical points relative to the viewport
origin.  To convert to screen pixels::

    screen_x = window.left + rect_center_x * pixels_per_point
    screen_y = window.top  + rect_center_y * pixels_per_point
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

# Default location: current working directory
DEFAULT_UI_TREE_PATH = "ui_tree.json"


@dataclass
class WidgetEntry:
    """A single widget from the UI tree."""

    id: str
    label: str
    kind: str
    rect: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])

    @property
    def center(self) -> tuple[float, float]:
        """Center of the rect in egui logical points."""
        left, top, right, bottom = self.rect
        return ((left + right) / 2.0, (top + bottom) / 2.0)

    @property
    def width(self) -> float:
        return self.rect[2] - self.rect[0]

    @property
    def height(self) -> float:
        return self.rect[3] - self.rect[1]


@dataclass
class UiTree:
    """Parsed ``ui_tree.json`` with lookup and coordinate conversion."""

    timestamp_ms: int = 0
    window_left: int = 0
    window_top: int = 0
    window_width: int = 0
    window_height: int = 0
    pixels_per_point: float = 1.0
    widgets: list[WidgetEntry] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    @staticmethod
    def load(path: str | Path = DEFAULT_UI_TREE_PATH) -> UiTree:
        """Parse ``ui_tree.json`` and return a :class:`UiTree`."""
        text = Path(path).read_text(encoding="utf-8")
        data = json.loads(text)

        win = data.get("window", {})
        widgets = [
            WidgetEntry(
                id=w["id"],
                label=w["label"],
                kind=w["kind"],
                rect=w["rect"],
            )
            for w in data.get("widgets", [])
        ]

        return UiTree(
            timestamp_ms=data.get("timestamp_ms", 0),
            window_left=win.get("left", 0),
            window_top=win.get("top", 0),
            window_width=win.get("width", 0),
            window_height=win.get("height", 0),
            pixels_per_point=data.get("pixels_per_point", 1.0),
            widgets=widgets,
        )

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def find(self, widget_id: str) -> WidgetEntry | None:
        """Find a widget by exact *widget_id*."""
        for w in self.widgets:
            if w.id == widget_id:
                return w
        return None

    def find_by_label(self, label: str) -> WidgetEntry | None:
        """Find the first widget whose label contains *label*."""
        for w in self.widgets:
            if label in w.label:
                return w
        return None

    def find_all(self, prefix: str) -> list[WidgetEntry]:
        """Return all widgets whose id starts with *prefix*."""
        return [w for w in self.widgets if w.id.startswith(prefix)]

    def list(self) -> list[WidgetEntry]:
        """Return all widgets."""
        return list(self.widgets)

    # ------------------------------------------------------------------
    # Coordinate conversion
    # ------------------------------------------------------------------

    def screen_center(
        self,
        widget: WidgetEntry,
        *,
        current_window_pos: tuple[int, int] | None = None,
    ) -> tuple[int, int]:
        """Convert widget center from egui logical points to screen pixels.

        If *current_window_pos* ``(left, top)`` is given, it overrides the
        stale position stored in ``ui_tree.json``.  This is important
        because the window may have moved since the JSON was written.

        Uses the formula::

            screen_x = window.left + center_x * pixels_per_point
            screen_y = window.top  + center_y * pixels_per_point
        """
        if current_window_pos is not None:
            wl, wt = current_window_pos
        else:
            wl, wt = self.window_left, self.window_top
        cx, cy = widget.center
        sx = int(wl + cx * self.pixels_per_point)
        sy = int(wt + cy * self.pixels_per_point)
        return sx, sy

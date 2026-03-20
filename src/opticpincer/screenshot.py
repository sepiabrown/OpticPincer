"""Screenshot capture using pyautogui.

Screenshots are saved to a configurable directory with timestamps.
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

import pyautogui

from opticpincer.core import get_window_rect
from opticpincer.window import foreground

# Disable pyautogui fail-safe and set minimal pause for automation
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.05


def take_screenshot(
    hwnd: int | None = None,
    *,
    label: str = "",
    output_dir: Path | str = Path("screenshots"),
    prefix: str = "capture",
    ensure_foreground: bool = True,
) -> Path:
    """Capture a screenshot and save it to *output_dir*.

    Parameters
    ----------
    hwnd:
        If given, capture only the window region.  If ``None``, capture the
        full desktop.
    label:
        Optional suffix appended to the filename.
    output_dir:
        Directory to save into (created automatically).
    prefix:
        Filename prefix before the timestamp.
    ensure_foreground:
        If *True* and *hwnd* is provided, bring the window to the foreground
        before capturing.

    Returns
    -------
    Path to the saved PNG file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = f"_{label}" if label else ""
    filepath = output_dir / f"{prefix}_{ts}{suffix}.png"

    if hwnd is not None:
        if ensure_foreground:
            foreground(hwnd, wait=0.3)

        x, y, w, h = get_window_rect(hwnd)
        # Minimized windows report bogus coordinates
        if x < -9000:
            foreground(hwnd, wait=0.5)
            x, y, w, h = get_window_rect(hwnd)
        img = pyautogui.screenshot(region=(x, y, w, h))
    else:
        img = pyautogui.screenshot()

    img.save(str(filepath))
    return filepath


def compare_screenshots(path_a: Path, path_b: Path) -> bool:
    """Return *True* if *path_a* and *path_b* are visually different.

    Uses a simple file-content comparison (re-encoded to PNG bytes).
    """
    import io

    from PIL import Image

    img1 = Image.open(path_a)
    img2 = Image.open(path_b)

    if img1.size != img2.size:
        return True  # different dimensions => definitely different

    if img1.mode != img2.mode:
        img2 = img2.convert(img1.mode)

    buf1, buf2 = io.BytesIO(), io.BytesIO()
    img1.save(buf1, format="PNG")
    img2.save(buf2, format="PNG")
    return buf1.getvalue() != buf2.getvalue()

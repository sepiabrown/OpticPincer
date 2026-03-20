"""Basic tests for opticpincer.core -- run on any Windows machine."""

from __future__ import annotations

import sys

import pytest

# Skip entire module on non-Windows
pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows-only")


def test_find_window_nonexistent():
    """Searching for a nonsense title returns (None, None)."""
    from opticpincer.core import find_window

    hwnd, title = find_window("__opticpincer_test_window_that_does_not_exist__")
    assert hwnd is None
    assert title is None


def test_find_window_returns_tuple():
    """Return type is always a 2-tuple."""
    from opticpincer.core import find_window

    result = find_window("__nonexistent__")
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_window_info_dataclass():
    """WindowInfo has all expected fields."""
    from opticpincer.core import WindowInfo

    info = WindowInfo(
        hwnd=0,
        title="test",
        left=0,
        top=0,
        width=800,
        height=600,
        is_minimized=False,
        is_visible=True,
        is_foreground=False,
    )
    assert info.width == 800
    assert info.title == "test"


def test_make_lparam():
    """MAKELONG packing works for typical coordinates."""
    from opticpincer.click import _make_lparam

    lp = _make_lparam(100, 200)
    # Low 16 bits = x, high 16 bits = y
    assert (lp & 0xFFFF) == 100
    assert ((lp >> 16) & 0xFFFF) == 200


def test_version():
    """Package exposes __version__."""
    import opticpincer

    assert opticpincer.__version__ == "0.1.0"

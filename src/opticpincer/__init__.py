"""OpticPincer -- Native desktop GUI automation for LLM agents."""

__version__ = "0.1.0"

from opticpincer.core import find_window, get_window_rect, get_window_info
from opticpincer.click import click_at, click_relative
from opticpincer.screenshot import take_screenshot
from opticpincer.window import foreground, background, is_foreground
from opticpincer.process import launch, kill_by_title, wait_for, rebuild_and_launch
from opticpincer.uitree import UiTree, WidgetEntry

__all__ = [
    "find_window",
    "get_window_rect",
    "get_window_info",
    "click_at",
    "click_relative",
    "take_screenshot",
    "foreground",
    "background",
    "is_foreground",
    "launch",
    "kill_by_title",
    "wait_for",
    "rebuild_and_launch",
    "UiTree",
    "WidgetEntry",
]

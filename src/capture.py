from dataclasses import dataclass

import numpy as np


@dataclass
class WindowBounds:
    left: int
    top: int
    width: int
    height: int


def find_window_bounds(title_keyword: str) -> WindowBounds | None:
    import pygetwindow as gw

    keyword = title_keyword.lower()
    for window in gw.getAllWindows():
        title = getattr(window, "title", "") or ""
        if keyword in title.lower():
            return WindowBounds(
                left=window.left,
                top=window.top,
                width=window.width,
                height=window.height,
            )
    return None


def capture_roi(bounds: WindowBounds, roi) -> np.ndarray:
    import mss

    monitor = {
        "left": bounds.left + roi.x,
        "top": bounds.top + roi.y,
        "width": roi.width,
        "height": roi.height,
    }
    with mss.mss() as sct:
        shot = sct.grab(monitor)
    return np.array(shot)[:, :, :3]

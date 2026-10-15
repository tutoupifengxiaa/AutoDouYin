import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RoiConfig:
    x: int
    y: int
    width: int
    height: int


@dataclass
class AppConfig:
    cs2_window_title: str
    browser_window_title: str
    ocr_roi: RoiConfig
    ocr_reference_width: int
    ocr_reference_height: int
    ocr_lang: str
    ocr_keywords: list[str]
    poll_interval_ms: int
    ocr_scale: float
    threshold_value: int
    death_confirm_frames: int
    alive_confirm_frames: int
    action_cooldown_ms: int
    focus_settle_ms: int
    scroll_mode: str
    scroll_amount: int
    log_level: str


def load_config(path: str | Path) -> AppConfig:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return AppConfig(
        cs2_window_title=data["cs2_window_title"],
        browser_window_title=data["browser_window_title"],
        ocr_roi=RoiConfig(**data["ocr_roi"]),
        ocr_reference_width=data["ocr_reference_width"],
        ocr_reference_height=data["ocr_reference_height"],
        ocr_lang=data["ocr_lang"],
        ocr_keywords=data["ocr_keywords"],
        poll_interval_ms=data["poll_interval_ms"],
        ocr_scale=data["ocr_scale"],
        threshold_value=data["threshold_value"],
        death_confirm_frames=data["death_confirm_frames"],
        alive_confirm_frames=data["alive_confirm_frames"],
        action_cooldown_ms=data["action_cooldown_ms"],
        focus_settle_ms=data["focus_settle_ms"],
        scroll_mode=data["scroll_mode"],
        scroll_amount=data["scroll_amount"],
        log_level=data["log_level"],
    )


def scale_roi_to_window(
    roi: RoiConfig,
    reference_width: int,
    reference_height: int,
    window_width: int,
    window_height: int,
) -> RoiConfig:
    if reference_width <= 0 or reference_height <= 0:
        raise ValueError("OCR reference dimensions must be positive")

    return RoiConfig(
        x=round(roi.x * window_width / reference_width),
        y=round(roi.y * window_height / reference_height),
        width=round(roi.width * window_width / reference_width),
        height=round(roi.height * window_height / reference_height),
    )

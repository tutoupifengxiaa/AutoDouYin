import logging
import time

from src.actions import ActionExecutor
from src.browser_controller import BrowserController
from src.capture import capture_roi, find_window_bounds
from src.config import load_config, scale_roi_to_window
from src.ocr_detector import OcrDetectionResult, PaddleOcrDetector, create_paddle_ocr_engine
from src.preprocess import preprocess_for_ocr
from src.state_machine import TriggerStateMachine


class AppLoop:
    def __init__(self, config, detector, browser_controller, action_executor) -> None:
        self._config = config
        self._detector = detector
        self._browser_controller = browser_controller
        self._action_executor = action_executor
        self._logger = logging.getLogger(__name__)
        self._machine = TriggerStateMachine(
            death_confirm_frames=config.death_confirm_frames,
            alive_confirm_frames=config.alive_confirm_frames,
            action_cooldown_ms=config.action_cooldown_ms,
        )

    def run_iteration(self, now_ms: int | None = None) -> None:
        detection = self._detector.detect_current_state()
        current_ms = now_ms if now_ms is not None else int(time.time() * 1000)
        was_dead = self._machine.state == "dead"
        should_trigger = self._machine.update(detection.is_death_detected, current_ms)
        returned_to_alive = was_dead and self._machine.state == "alive"
        self._logger.info(
            "ocr_text=%r matched=%s state=%s",
            detection.text,
            detection.is_death_detected,
            self._machine.state,
        )

        if returned_to_alive:
            focused = self._browser_controller.focus(self._config.cs2_window_title)
            if not focused:
                self._logger.warning(
                    "Failed to focus CS2 window: %s",
                    self._config.cs2_window_title,
                )
            return

        if not should_trigger:
            return

        focused = self._browser_controller.focus(self._config.browser_window_title)
        if not focused:
            self._logger.warning(
                "Failed to focus browser window: %s",
                self._config.browser_window_title,
            )
            return

        self._action_executor.run(
            self._config.scroll_mode,
            self._config.scroll_amount,
        )


class LiveDetector:
    def __init__(self, config, model_dir=None) -> None:
        self._config = config
        options = {"lang": config.ocr_lang}
        if model_dir is not None:
            options["model_dir"] = model_dir
        self._detector = PaddleOcrDetector(
            create_paddle_ocr_engine(**options),
            config.ocr_keywords,
        )

    def detect_current_state(self) -> OcrDetectionResult:
        bounds = find_window_bounds(self._config.cs2_window_title)
        if bounds is None:
            return OcrDetectionResult(text="", is_death_detected=False)

        scaled_roi = scale_roi_to_window(
            self._config.ocr_roi,
            self._config.ocr_reference_width,
            self._config.ocr_reference_height,
            bounds.width,
            bounds.height,
        )
        roi_image = capture_roi(bounds, scaled_roi)
        processed = preprocess_for_ocr(
            roi_image,
            scale=self._config.ocr_scale,
            threshold_value=self._config.threshold_value,
        )
        return self._detector.detect(processed)


def build_live_app(config_path: str = "config.json", model_dir=None) -> AppLoop:
    config = load_config(config_path)
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper(), logging.INFO)
    )
    return AppLoop(
        config=config,
        detector=LiveDetector(config, model_dir=model_dir),
        browser_controller=BrowserController(),
        action_executor=ActionExecutor(),
    )


def main() -> None:
    app = build_live_app()
    while True:
        app.run_iteration()
        time.sleep(app._config.poll_interval_ms / 1000)

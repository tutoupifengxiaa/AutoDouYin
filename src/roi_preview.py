import argparse
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from src.capture import capture_roi, find_window_bounds
from src.config import load_config, scale_roi_to_window
from src.ocr_detector import OcrDetectionResult, PaddleOcrDetector, create_paddle_ocr_engine
from src.preprocess import preprocess_for_ocr


@dataclass
class PreviewResult:
    window_found: bool
    ocr_text: str
    matched_keywords: bool
    roi_size: tuple[int, int] | None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preview OCR output for the configured CS2 ROI")
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--save-path")
    return parser


def save_processed_image(path: str | Path, image: Any) -> None:
    import numpy as np
    from PIL import Image

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    array = np.asarray(image, dtype=np.uint8)
    Image.fromarray(array).save(target)


def run_preview_once(
    config: Any,
    find_bounds: Callable[[str], Any],
    capture: Callable[[Any, Any], Any],
    preprocess: Callable[[Any, float, int], Any],
    detect: Callable[[Any], OcrDetectionResult],
    emit: Callable[[str], None],
    save_image: Callable[[str | Path, Any], None],
    save_path: str | Path | None,
) -> PreviewResult:
    bounds = find_bounds(config.cs2_window_title)
    if bounds is None:
        emit("window_found=false ocr_text='' matched_keywords=false roi_size=None message='window not found'")
        return PreviewResult(
            window_found=False,
            ocr_text="",
            matched_keywords=False,
            roi_size=None,
        )

    scaled_roi = scale_roi_to_window(
        config.ocr_roi,
        config.ocr_reference_width,
        config.ocr_reference_height,
        bounds.width,
        bounds.height,
    )
    roi_image = capture(bounds, scaled_roi)
    processed = preprocess(roi_image, config.ocr_scale, config.threshold_value)
    detection = detect(processed)
    roi_size = (scaled_roi.width, scaled_roi.height)

    emit(
        f"window_found=true ocr_text={detection.text!r} "
        f"matched_keywords={str(detection.is_death_detected).lower()} roi_size={roi_size}"
    )

    if save_path is not None:
        save_image(save_path, processed)

    return PreviewResult(
        window_found=True,
        ocr_text=detection.text,
        matched_keywords=detection.is_death_detected,
        roi_size=roi_size,
    )


class PreviewDetector:
    def __init__(self, config: Any) -> None:
        self._detector = PaddleOcrDetector(
            create_paddle_ocr_engine(lang=config.ocr_lang),
            config.ocr_keywords,
        )

    def detect(self, image: Any) -> OcrDetectionResult:
        return self._detector.detect(image)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args.config)
    detector = PreviewDetector(config)

    while True:
        run_preview_once(
            config=config,
            find_bounds=find_window_bounds,
            capture=capture_roi,
            preprocess=preprocess_for_ocr,
            detect=detector.detect,
            emit=print,
            save_image=save_processed_image,
            save_path=args.save_path,
        )
        if args.once:
            return 0
        time.sleep(config.poll_interval_ms / 1000)


if __name__ == "__main__":
    raise SystemExit(main())

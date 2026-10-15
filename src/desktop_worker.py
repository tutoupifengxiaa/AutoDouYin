"""Run the OCR application behind the desktop launcher."""

import argparse
import json
import logging
import sys
import threading
from pathlib import Path

from src.app import build_live_app


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if stream is not None:
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--models", type=Path)
    parser.add_argument("--self-test", type=Path)
    args = parser.parse_args()
    stopped = threading.Event()

    def read_stop() -> None:
        if sys.stdin is not None:
            for line in sys.stdin:
                if line.strip() == "stop":
                    break
        stopped.set()

    try:
        app = build_live_app(args.config, model_dir=args.models)
        logging.getLogger().setLevel(getattr(logging, app._config.log_level.upper(), logging.INFO))
        if args.self_test is not None:
            import importlib.metadata

            import numpy as np
            from PIL import Image, ImageDraw, ImageFont

            from src.ocr_detector import PaddleOcrDetector
            from src.preprocess import preprocess_for_ocr

            image = Image.new("RGB", (600, 100), "white")
            ImageDraw.Draw(image).text((20, 20), "NEXT PLAYER", fill="black", font=ImageFont.load_default(size=42))
            detector = PaddleOcrDetector(app._detector._detector._engine, ["next", "player"])
            processed = preprocess_for_ocr(np.asarray(image), scale=app._config.ocr_scale, threshold_value=app._config.threshold_value)
            detection = detector.detect(processed)
            if not detection.is_death_detected:
                raise RuntimeError(f"OCR inference check failed: {detection.text!r}")
            report = {
                "status": "passed",
                "python": sys.version.split()[0],
                "paddlepaddle": importlib.metadata.version("paddlepaddle"),
                "paddleocr": importlib.metadata.version("paddleocr"),
                "ocr_text": detection.text,
                "bundled_models": args.models is not None,
            }
            args.self_test.write_text(json.dumps(report, indent=2), encoding="utf-8")
            return 0
        threading.Thread(target=read_stop, daemon=True).start()
        logging.getLogger(__name__).info("OCR ready; monitoring started")
        while not stopped.is_set():
            app.run_iteration()
            stopped.wait(app._config.poll_interval_ms / 1000)
        return 0
    except Exception:
        logging.exception("AutoDouYin worker failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

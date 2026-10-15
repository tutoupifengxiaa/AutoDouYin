from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Protocol


@dataclass
class OcrDetectionResult:
    text: str
    is_death_detected: bool


class OcrEngine(Protocol):
    def ocr(self, image: Any) -> Any:
        ...


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def classify_ocr_text(text: str, keywords: list[str]) -> bool:
    normalized = normalize_text(text)
    return any(normalize_text(keyword) in normalized for keyword in keywords)


class PaddleOcrDetector:
    def __init__(self, engine: OcrEngine, keywords: list[str]) -> None:
        self._engine = engine
        self._keywords = keywords

    def detect(self, image: Any) -> OcrDetectionResult:
        raw_result = self._engine.ocr(image)
        pieces: list[str] = []

        for block in raw_result or []:
            for line in block or []:
                if len(line) > 1 and isinstance(line[1], (list, tuple)) and line[1]:
                    pieces.append(str(line[1][0]))

        text = " ".join(pieces).strip()
        return OcrDetectionResult(
            text=text,
            is_death_detected=classify_ocr_text(text, self._keywords),
        )


def create_paddle_ocr_engine(lang: str = "en", model_dir: str | Path | None = None) -> OcrEngine:
    from paddleocr import PaddleOCR

    options = {"use_angle_cls": False, "lang": lang, "use_gpu": False, "show_log": False}
    if model_dir is not None and lang == "ch":
        root = Path(model_dir)
        options.update(
            det_model_dir=str(root / "det"),
            rec_model_dir=str(root / "rec"),
            cls_model_dir=str(root / "cls"),
        )
    return PaddleOCR(**options)

import numpy as np


def preprocess_for_ocr(
    image: np.ndarray,
    scale: float,
    threshold_value: int,
) -> np.ndarray:
    if image.ndim == 3:
        gray = image.mean(axis=2).astype(np.uint8)
    else:
        gray = image.astype(np.uint8)

    if scale <= 0:
        raise ValueError("scale must be positive")

    if scale != 1.0:
        gray = np.repeat(gray, max(1, int(round(scale))), axis=0)
        gray = np.repeat(gray, max(1, int(round(scale))), axis=1)

    thresholded = np.where(gray >= threshold_value, 255, 0).astype(np.uint8)
    return thresholded

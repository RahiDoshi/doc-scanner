"""Step 5: filters that give the final 'scanned' look."""

from enum import Enum

import cv2
import numpy as np


class ScanMode(str, Enum):
    BW = "bw"            # black & white, like a photocopy
    GRAY = "gray"        # contrast-enhanced grayscale
    COLOR = "color"      # sharpened colour ("magic colour")
    ORIGINAL = "original"


def black_and_white(image: np.ndarray, block_size: int = 21, c: int = 10) -> np.ndarray:
    """Adaptive thresholding handles uneven lighting / shadows across the page."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 3)
    return cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, block_size, c
    )


def enhanced_gray(image: np.ndarray) -> np.ndarray:
    """CLAHE (adaptive histogram equalization) for even contrast."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def sharpen(image: np.ndarray) -> np.ndarray:
    """Unsharp masking: original + (original - blurred)."""
    blurred = cv2.GaussianBlur(image, (0, 0), 3)
    return cv2.addWeighted(image, 1.5, blurred, -0.5, 0)


def enhanced_color(image: np.ndarray) -> np.ndarray:
    """Equalize brightness in LAB space, then sharpen."""
    l, a, b = cv2.split(cv2.cvtColor(image, cv2.COLOR_BGR2LAB))
    l = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(l)
    merged = cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)
    return sharpen(merged)


def apply_mode(image: np.ndarray, mode: ScanMode) -> np.ndarray:
    filters = {
        ScanMode.BW: black_and_white,
        ScanMode.GRAY: enhanced_gray,
        ScanMode.COLOR: enhanced_color,
        ScanMode.ORIGINAL: lambda img: img,
    }
    return filters[mode](image)

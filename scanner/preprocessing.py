"""Step 1-2: resize, grayscale, smoothing and edge detection."""

import cv2
import numpy as np


def resize_to_height(image: np.ndarray, height: int) -> tuple[np.ndarray, float]:
    """Resize keeping aspect ratio. Returns the resized image and the scale ratio
    (original / resized) so detected points can be mapped back."""
    ratio = image.shape[0] / height
    width = int(image.shape[1] / ratio)
    resized = cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)
    return resized, ratio


def to_grayscale(image: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def smooth(gray: np.ndarray, kernel_size: int = 5) -> np.ndarray:
    """Gaussian blur to suppress noise and text texture before edge detection."""
    return cv2.GaussianBlur(gray, (kernel_size, kernel_size), 0)


def detect_edges(blurred: np.ndarray, low: int = 75, high: int = 200) -> np.ndarray:
    """Canny edge detection followed by a morphological closing so that
    small gaps in the page border are joined into one continuous outline."""
    edges = cv2.Canny(blurred, low, high)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    return cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

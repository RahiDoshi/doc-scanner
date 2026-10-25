"""Ties every step together into a single DocumentScanner."""

from dataclasses import dataclass, field

import cv2
import numpy as np

from .detection import find_document_contour, full_image_corners
from .enhance import ScanMode, apply_mode
from .preprocessing import detect_edges, resize_to_height, smooth, to_grayscale
from .transform import four_point_warp

PROCESSING_HEIGHT = 500  # detection runs on a small copy for speed


@dataclass
class ScanResult:
    scanned: np.ndarray
    document_found: bool
    steps: dict[str, np.ndarray] = field(default_factory=dict)


class DocumentScanner:
    def __init__(self, mode: ScanMode = ScanMode.BW):
        self.mode = mode

    def scan(self, image: np.ndarray) -> ScanResult:
        small, ratio = resize_to_height(image, PROCESSING_HEIGHT)
        gray = to_grayscale(small)
        blurred = smooth(gray)
        edges = detect_edges(blurred)

        corners = find_document_contour(edges, gray)
        found = corners is not None
        if not found:
            corners = full_image_corners(small.shape)

        outlined = small.copy()
        cv2.drawContours(outlined, [corners.astype(int)], -1, (0, 255, 0), 2)

        # Warp the full-resolution image for maximum output quality.
        warped = four_point_warp(image, corners * ratio)
        scanned = apply_mode(warped, self.mode)

        steps = {
            "1_original": small,
            "2_grayscale": gray,
            "3_blurred": blurred,
            "4_edges": edges,
            "5_detected": outlined,
            "6_warped": warped,
            "7_scanned": scanned,
        }
        return ScanResult(scanned=scanned, document_found=found, steps=steps)

"""Step 4: perspective transform to get a flat, top-down view of the page."""

import cv2
import numpy as np


def order_points(points: np.ndarray) -> np.ndarray:
    """Order corners as top-left, top-right, bottom-right, bottom-left.

    - top-left has the smallest x + y, bottom-right the largest
    - top-right has the smallest y - x, bottom-left the largest
    """
    rect = np.zeros((4, 2), dtype="float32")
    s = points.sum(axis=1)
    diff = np.diff(points, axis=1).ravel()
    rect[0] = points[np.argmin(s)]
    rect[2] = points[np.argmax(s)]
    rect[1] = points[np.argmin(diff)]
    rect[3] = points[np.argmax(diff)]
    return rect


def four_point_warp(image: np.ndarray, points: np.ndarray) -> np.ndarray:
    """Warp the quadrilateral given by `points` into a rectangle."""
    tl, tr, br, bl = rect = order_points(points)

    width = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
    height = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))

    destination = np.array(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
        dtype="float32",
    )
    matrix = cv2.getPerspectiveTransform(rect, destination)
    return cv2.warpPerspective(image, matrix, (width, height))

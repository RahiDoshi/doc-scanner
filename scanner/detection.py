"""Step 3: locate the document as the largest four-cornered contour."""

import cv2
import numpy as np


def is_brighter_than_background(gray: np.ndarray, quad: np.ndarray, min_contrast: float) -> bool:
    """A real page is noticeably brighter than what surrounds it. This rejects
    boxes/tables printed inside a page that already fills the whole photo."""
    mask = np.zeros(gray.shape, dtype=np.uint8)
    cv2.fillPoly(mask, [quad.astype(int)], 255)
    inside = cv2.mean(gray, mask=mask)[0]
    outside = cv2.mean(gray, mask=cv2.bitwise_not(mask))[0]
    return inside - outside >= min_contrast


def find_document_contour(
    edges: np.ndarray,
    gray: np.ndarray,
    min_area_ratio: float = 0.2,
    min_contrast: float = 20,
) -> np.ndarray | None:
    """Return the 4 corner points (shape (4, 2)) of the document, or None.

    Contours are checked from largest to smallest; the first one that
    approximates to a quadrilateral, covers enough of the image and stands
    out from the background wins.
    """
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    # The convex hull smooths over dents (fingers, curled corners) in the outline.
    hulls = sorted((cv2.convexHull(c) for c in contours), key=cv2.contourArea, reverse=True)[:5]

    min_area = min_area_ratio * edges.shape[0] * edges.shape[1]
    for hull in hulls:
        if cv2.contourArea(hull) < min_area:
            break
        perimeter = cv2.arcLength(hull, True)
        # Gradually loosen the approximation until the shape reduces to 4 corners.
        for epsilon in (0.02, 0.03, 0.04, 0.05):
            approx = cv2.approxPolyDP(hull, epsilon * perimeter, True)
            if len(approx) == 4:
                quad = approx.reshape(4, 2).astype("float32")
                if is_brighter_than_background(gray, quad, min_contrast):
                    return quad
                break
    return None


def full_image_corners(shape: tuple[int, ...]) -> np.ndarray:
    """Fallback when no page is found: use the whole image."""
    h, w = shape[:2]
    return np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], dtype="float32")

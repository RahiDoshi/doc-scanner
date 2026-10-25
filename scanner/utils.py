"""Image I/O and visualization helpers."""

import io
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

_ROTATIONS = {
    90: cv2.ROTATE_90_CLOCKWISE,
    180: cv2.ROTATE_180,
    270: cv2.ROTATE_90_COUNTERCLOCKWISE,
}


def decode_image(data: bytes) -> np.ndarray:
    image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image data")
    return image


def rotate(image: np.ndarray, degrees: int) -> np.ndarray:
    """Rotate clockwise by 0, 90, 180 or 270 degrees."""
    return image if degrees % 360 == 0 else cv2.rotate(image, _ROTATIONS[degrees % 360])


def to_rgb(image: np.ndarray) -> np.ndarray:
    """OpenCV uses BGR; most other libraries expect RGB."""
    if image.ndim == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def encode_png(image: np.ndarray) -> bytes:
    return cv2.imencode(".png", image)[1].tobytes()


def images_to_pdf(images: list[np.ndarray]) -> bytes:
    """Combine scanned pages into one multi-page PDF."""
    pages = [Image.fromarray(to_rgb(img)).convert("RGB") for img in images]
    buffer = io.BytesIO()
    pages[0].save(buffer, format="PDF", save_all=True, append_images=pages[1:], resolution=150)
    return buffer.getvalue()


def load_image(path: Path) -> np.ndarray:
    # Reading bytes first handles non-ASCII Windows paths, unlike cv2.imread
    try:
        return decode_image(path.read_bytes())
    except ValueError:
        raise ValueError(f"Could not read image: {path}") from None


def save_image(path: Path, image: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, buffer = cv2.imencode(path.suffix or ".png", image)
    if not ok:
        raise ValueError(f"Could not encode image: {path}")
    buffer.tofile(str(path))


def save_steps(steps: dict[str, np.ndarray], directory: Path) -> None:
    for name, image in steps.items():
        save_image(directory / f"{name}.png", image)


def make_step_grid(steps: dict[str, np.ndarray], tile_height: int = 300) -> np.ndarray:
    """Place every intermediate image side by side with a label, for reports."""
    tiles = []
    for name, image in steps.items():
        if image.ndim == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        scale = tile_height / image.shape[0]
        tile = cv2.resize(image, (int(image.shape[1] * scale), tile_height))
        cv2.putText(tile, name, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        tiles.append(tile)
    return cv2.hconcat(tiles)

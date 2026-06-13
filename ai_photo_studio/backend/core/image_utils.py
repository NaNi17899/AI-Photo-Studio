"""
Common image utility functions used across plugins.
"""

import os
import cv2
import numpy as np
from PIL import Image
from typing import Optional, Tuple


def load_image_pil(path: str) -> Image.Image:
    """Load an image as PIL Image (RGB)."""
    img = Image.open(path)
    if img.mode == "RGBA":
        return img  # Preserve alpha when present
    return img.convert("RGB")


def load_image_cv2(path: str) -> np.ndarray:
    """Load an image as OpenCV BGR numpy array."""
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(f"Could not load image: {path}")
    return img


def save_image_pil(img: Image.Image, path: str, quality: int = 95) -> str:
    """Save a PIL Image. Format determined by extension."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ext = os.path.splitext(path)[1].lower()
    if ext in (".jpg", ".jpeg"):
        if img.mode == "RGBA":
            img = img.convert("RGB")
        img.save(path, quality=quality)
    elif ext == ".webp":
        img.save(path, quality=quality)
    else:
        img.save(path)
    return path


def save_image_cv2(img: np.ndarray, path: str, quality: int = 95) -> str:
    """Save an OpenCV image. Format determined by extension."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ext = os.path.splitext(path)[1].lower()
    if ext in (".jpg", ".jpeg"):
        cv2.imwrite(path, img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    elif ext == ".webp":
        cv2.imwrite(path, img, [cv2.IMWRITE_WEBP_QUALITY, quality])
    else:
        cv2.imwrite(path, img)
    return path


def pil_to_cv2(img: Image.Image) -> np.ndarray:
    """Convert PIL Image (RGB/RGBA) to OpenCV BGR/BGRA."""
    arr = np.array(img)
    if len(arr.shape) == 2:
        return arr  # Grayscale
    if arr.shape[2] == 4:
        return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGRA)
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


def cv2_to_pil(img: np.ndarray) -> Image.Image:
    """Convert OpenCV BGR/BGRA to PIL Image RGB/RGBA."""
    if len(img.shape) == 2:
        return Image.fromarray(img)
    if img.shape[2] == 4:
        return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA))
    return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))


def resize_to_max(img: Image.Image, max_size: int = 2048) -> Image.Image:
    """Resize image so the longest edge is at most max_size, preserving aspect ratio."""
    w, h = img.size
    if max(w, h) <= max_size:
        return img
    scale = max_size / max(w, h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    return img.resize((new_w, new_h), Image.LANCZOS)


def create_thumbnail(img: Image.Image, size: Tuple[int, int] = (256, 256)) -> Image.Image:
    """Create a thumbnail preserving aspect ratio."""
    thumb = img.copy()
    thumb.thumbnail(size, Image.LANCZOS)
    return thumb


def composite_on_background(
    foreground: Image.Image,
    background_color: Optional[Tuple[int, int, int]] = None,
    background_image: Optional[Image.Image] = None,
) -> Image.Image:
    """
    Composite an RGBA foreground onto a background.
    If background_image is provided, use that. Otherwise use background_color.
    """
    if foreground.mode != "RGBA":
        return foreground

    if background_image is not None:
        bg = background_image.convert("RGBA").resize(foreground.size, Image.LANCZOS)
    else:
        color = background_color or (255, 255, 255)
        bg = Image.new("RGBA", foreground.size, color + (255,))

    bg.paste(foreground, mask=foreground.split()[3])
    return bg.convert("RGB")


def refine_mask_edges(mask: np.ndarray, blur_radius: int = 3, threshold: int = 128) -> np.ndarray:
    """Refine a binary mask by blurring edges and re-thresholding."""
    if blur_radius > 0:
        mask = cv2.GaussianBlur(mask, (blur_radius * 2 + 1, blur_radius * 2 + 1), 0)
    _, mask = cv2.threshold(mask, threshold, 255, cv2.THRESH_BINARY)
    return mask


def detect_faces_cv2(img: np.ndarray) -> list:
    """
    Simple face detection using OpenCV's DNN face detector.
    Returns list of (x, y, w, h) bounding boxes.
    """
    proto = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    cascade = cv2.CascadeClassifier(proto)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    faces = cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))
    return [tuple(f) for f in faces]


def get_image_info(path: str) -> dict:
    """Get basic image information."""
    img = Image.open(path)
    file_size = os.path.getsize(path)
    return {
        "width": img.size[0],
        "height": img.size[1],
        "mode": img.mode,
        "format": img.format,
        "file_size_bytes": file_size,
        "file_size_mb": round(file_size / 1024**2, 2),
    }

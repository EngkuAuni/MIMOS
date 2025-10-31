from typing import List, Optional, Tuple

import cv2
import numpy as np

from .types import PreprocessResult


def _apply_clahe(gray: np.ndarray) -> np.ndarray:
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def _illumination_correction(gray: np.ndarray, kernel_size: int = 31) -> np.ndarray:
    # Estimate background via morphological opening and subtract
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    background = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
    corrected = cv2.subtract(gray, background)
    corrected = cv2.normalize(corrected, None, 0, 255, cv2.NORM_MINMAX)
    return corrected


def _adaptive_binarize(gray: np.ndarray) -> np.ndarray:
    h, w = gray.shape[:2]
    # Choose adaptive window roughly proportional to image size
    block_size = max(15, (min(h, w) // 40) | 1)  # odd
    bin_img = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        block_size,
        10,
    )
    return bin_img


def _estimate_skew(binary: np.ndarray) -> float:
    # Invert for text as white
    inv = 255 - binary
    # Use probabilistic Hough on edges to estimate baseline angle
    edges = cv2.Canny(inv, 50, 150)
    lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=200)
    if lines is None:
        return 0.0
    # Compute average angle near horizontal
    angles = []
    for rho_theta in lines[:200]:
        rho, theta = rho_theta[0]
        deg = (theta * 180.0 / np.pi) - 90.0
        if -20.0 <= deg <= 20.0:
            angles.append(deg)
    if not angles:
        return 0.0
    return float(np.median(angles))


def _rotate_image(image: np.ndarray, angle_deg: float) -> np.ndarray:
    if abs(angle_deg) < 0.1:
        return image
    h, w = image.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle_deg, 1.0)
    return cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


def preprocess_page(image_bgr: np.ndarray, debug: bool = False) -> PreprocessResult:
    overlays: List[np.ndarray] = []
    # Convert to gray
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    gray = _apply_clahe(gray)
    gray = _illumination_correction(gray)

    # Binarize
    try:
        bin_img = _adaptive_binarize(gray)
    except Exception:
        _, bin_img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Estimate skew and rotate both gray and original
    angle = _estimate_skew(bin_img)
    rotated_bgr = _rotate_image(image_bgr, -angle)
    rotated_gray = _rotate_image(gray, -angle)
    rotated_bin = _rotate_image(bin_img, -angle)

    if debug:
        overlays.extend([gray, bin_img, rotated_bin])

    # Return RGB-like array (still BGR, handled upstream)
    return PreprocessResult(processed_image=rotated_bgr, skew_angle_deg=-angle, binarized_image=rotated_bin, debug_overlays=overlays)




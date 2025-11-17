from typing import List, Tuple

import cv2
import numpy as np

from .types import LineRegion


def _projection_profile(binary: np.ndarray) -> np.ndarray:
    # Expect text as black (0). If white-on-black, invert.
    if binary.mean() > 127:
        proj = (255 - binary)
    else:
        proj = binary
    # Sum per row
    profile = proj.sum(axis=1)
    return profile


def _smooth_profile(profile: np.ndarray, k: int = 15) -> np.ndarray:
    k = max(3, k | 1)
    kernel = np.ones(k, dtype=np.float32) / k
    return np.convolve(profile, kernel, mode="same")


def segment_lines(binarized: np.ndarray, rgb_image: np.ndarray, min_line_h: int = 20, max_line_h: int = 200, pad: int = 4) -> List[LineRegion]:
    h, w = binarized.shape[:2]
    profile = _projection_profile(binarized)
    smoothed = _smooth_profile(profile, max(9, h // 200 * 2 + 1))

    # Normalize and threshold valleys (spaces between lines)
    norm = (smoothed - smoothed.min()) / (smoothed.ptp() + 1e-6)
    # Valleys where norm is low; detect transitions to form bands
    thresh = 0.25
    is_text = norm > thresh

    lines: List[Tuple[int, int]] = []
    in_band = False
    start = 0
    for i, flag in enumerate(is_text):
        if flag and not in_band:
            in_band = True
            start = i
        elif not flag and in_band:
            in_band = False
            end = i
            if end - start >= min_line_h:
                lines.append((start, end))
    if in_band:
        end = h - 1
        if end - start >= min_line_h:
            lines.append((start, end))

    # Merge very thin bands and clamp sizes
    merged: List[Tuple[int, int]] = []
    for y0, y1 in lines:
        if merged and (y1 - y0) < min_line_h:
            py0, py1 = merged[-1]
            merged[-1] = (py0, y1)
        else:
            merged.append((y0, y1))

    regions: List[LineRegion] = []
    for y0, y1 in merged:
        height = y1 - y0
        if height < min_line_h:
            continue
        if height > max_line_h:
            # Split tall band into chunks of ~max_line_h
            step = max_line_h
            for sy in range(y0, y1, step):
                ey = min(y1, sy + step)
                yy0 = max(0, sy - pad)
                yy1 = min(h, ey + pad)
                crop = rgb_image[yy0:yy1, 0:w]
                regions.append(LineRegion(bbox=(0, yy0, w, yy1 - yy0), image=crop))
        else:
            yy0 = max(0, y0 - pad)
            yy1 = min(h, y1 + pad)
            crop = rgb_image[yy0:yy1, 0:w]
            regions.append(LineRegion(bbox=(0, yy0, w, yy1 - yy0), image=crop))

    return regions




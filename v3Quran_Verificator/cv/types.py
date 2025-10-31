from dataclasses import dataclass
from typing import Any, List, Optional, Tuple


@dataclass
class PreprocessResult:
    processed_image: Any  # numpy.ndarray; kept as Any to avoid import-time dep
    skew_angle_deg: float
    binarized_image: Optional[Any] = None
    debug_overlays: Optional[List[Any]] = None


@dataclass
class LineRegion:
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    image: Any  # numpy.ndarray; cropped RGB/gray
    score: float = 1.0



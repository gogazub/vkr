"""IoU utilities"""
from typing import Dict, Tuple


def _to_xyxy(box: Dict[str, float]) -> Tuple[float, float, float, float] | None:
    try:
        x_center = float(box["x_center"])
        y_center = float(box["y_center"])
        width = float(box["width"])
        height = float(box["height"])
    except (KeyError, TypeError, ValueError):
        return None

    if width <= 0 or height <= 0:
        return None

    x1 = x_center - width / 2
    y1 = y_center - height / 2
    x2 = x_center + width / 2
    y2 = y_center + height / 2

    x1 = max(0.0, min(1.0, x1))
    y1 = max(0.0, min(1.0, y1))
    x2 = max(0.0, min(1.0, x2))
    y2 = max(0.0, min(1.0, y2))

    if x2 <= x1 or y2 <= y1:
        return None

    return x1, y1, x2, y2


def compute_iou(box_a: Dict[str, float], box_b: Dict[str, float]) -> float:
    """Compute IoU for two boxes in normalized center format."""
    xyxy_a = _to_xyxy(box_a)
    xyxy_b = _to_xyxy(box_b)
    if xyxy_a is None or xyxy_b is None:
        return 0.0

    ax1, ay1, ax2, ay2 = xyxy_a
    bx1, by1, bx2, by2 = xyxy_b

    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)

    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    union = area_a + area_b - inter_area
    if union <= 0:
        return 0.0

    return inter_area / union

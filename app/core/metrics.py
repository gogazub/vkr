"""Metrics utilities"""
from typing import Any, Dict, List


def _safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def build_stats(
    matches: List[Dict[str, Any]],
    pred_count: int,
    gt_count: int,
    iou_threshold: float,
    class_aware: bool,
) -> Dict[str, Any]:
    tp = len(matches)
    fp = max(0, pred_count - tp)
    fn = max(0, gt_count - tp)

    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    f1 = _safe_div(2 * precision * recall, precision + recall) if (precision + recall) else 0.0

    return {
        "expert_count": gt_count,
        "model_count": pred_count,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "iou_threshold": iou_threshold,
        "class_aware": class_aware,
    }

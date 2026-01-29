"""Box matching utilities"""
from typing import Any, Dict, List

from app.core.iou import compute_iou


def match_boxes(
    pred_boxes: List[Dict[str, Any]],
    gt_boxes: List[Dict[str, Any]],
    iou_threshold: float = 0.5,
    class_aware: bool = True,
) -> Dict[str, Any]:
    """Greedy IoU matching between predicted and ground-truth boxes."""
    candidates: List[tuple[float, int, int]] = []
    for pred_idx, pred in enumerate(pred_boxes):
        pred_class = pred.get("class_id")
        for gt_idx, gt in enumerate(gt_boxes):
            gt_class = gt.get("class_id")
            if class_aware and pred_class is not None and gt_class is not None:
                if pred_class != gt_class:
                    continue
            iou = compute_iou(pred, gt)
            if iou >= iou_threshold:
                candidates.append((iou, pred_idx, gt_idx))

    candidates.sort(key=lambda item: item[0], reverse=True)

    matched_preds: set[int] = set()
    matched_gts: set[int] = set()
    matches: List[Dict[str, Any]] = []

    for iou, pred_idx, gt_idx in candidates:
        if pred_idx in matched_preds or gt_idx in matched_gts:
            continue
        matched_preds.add(pred_idx)
        matched_gts.add(gt_idx)
        matches.append({"pred_index": pred_idx, "gt_index": gt_idx, "iou": iou})

    unmatched_pred = [idx for idx in range(len(pred_boxes)) if idx not in matched_preds]
    unmatched_gt = [idx for idx in range(len(gt_boxes)) if idx not in matched_gts]

    return {
        "matches": matches,
        "unmatched_pred": unmatched_pred,
        "unmatched_gt": unmatched_gt,
    }

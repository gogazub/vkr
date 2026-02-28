"""Dataset report export helpers."""
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Sequence, Tuple


@dataclass(frozen=True)
class ReportField:
    key: str
    header: str
    getter: Callable[[Dict[str, Any]], Any]


def _stat(row: Dict[str, Any], key: str, default: Any = "") -> Any:
    stats = row.get("stats") or {}
    return stats.get(key, default)


# Update this list to change the exported structure.
DEFAULT_IMAGE_REPORT_FIELDS: Sequence[ReportField] = (
    ReportField("image_id", "Image ID", lambda row: row.get("image_id", "")),
    ReportField("expert_count", "Expert boxes", lambda row: _stat(row, "expert_count", 0)),
    ReportField("model_count", "Model boxes", lambda row: _stat(row, "model_count", 0)),
    ReportField("tp", "TP", lambda row: _stat(row, "tp", 0)),
    ReportField("fp", "FP", lambda row: _stat(row, "fp", 0)),
    ReportField("fn", "FN", lambda row: _stat(row, "fn", 0)),
    ReportField("precision", "Precision", lambda row: _stat(row, "precision", 0.0)),
    ReportField("recall", "Recall", lambda row: _stat(row, "recall", 0.0)),
    ReportField("f1", "F1", lambda row: _stat(row, "f1", 0.0)),
    ReportField("iou_threshold", "IoU threshold", lambda row: _stat(row, "iou_threshold", "")),
    ReportField("class_aware", "Class aware", lambda row: _stat(row, "class_aware", "")),
)


def build_report_table(
    rows: Iterable[Dict[str, Any]],
    fields: Sequence[ReportField] = DEFAULT_IMAGE_REPORT_FIELDS,
) -> Tuple[List[str], List[List[Any]]]:
    headers = [field.header for field in fields]
    data = [[field.getter(row) for field in fields] for row in rows]
    return headers, data

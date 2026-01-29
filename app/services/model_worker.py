"""Model worker orchestrating providers and model runner"""
from typing import Any, Dict

from app.core.matcher import match_boxes
from app.core.metrics import build_stats
from app.infrastructure.model_runner import IModelRunner
from app.providers.interfaces import IAnnotationProvider, IImageProvider


class ModelWorker:
    """Orchestrates inference and annotations for a single response"""

    def __init__(
        self,
        image_provider: IImageProvider,
        annotation_provider: IAnnotationProvider,
        model_runner: IModelRunner,
    ) -> None:
        self._image_provider = image_provider
        self._annotation_provider = annotation_provider
        self._model_runner = model_runner

    def analyze(
        self,
        image_id: str,
        *,
        iou_threshold: float = 0.5,
        class_aware: bool = True,
    ) -> Dict[str, Any]:
        image_bytes = self._image_provider.get_image(image_id)
        expert_boxes = self._annotation_provider.get_annotations(image_id)
        model_boxes = self._model_runner.predict(image_bytes)

        match_result = match_boxes(
            model_boxes,
            expert_boxes,
            iou_threshold=iou_threshold,
            class_aware=class_aware,
        )
        stats = build_stats(
            match_result["matches"],
            pred_count=len(model_boxes),
            gt_count=len(expert_boxes),
            iou_threshold=iou_threshold,
            class_aware=class_aware,
        )

        return {
            "image_id": image_id,
            "expert_boxes": expert_boxes,
            "model_boxes": model_boxes,
            "stats": stats,
            "matches": match_result["matches"],
        }

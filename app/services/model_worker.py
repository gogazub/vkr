"""Model worker orchestrating providers and model runner"""
from typing import Any, Dict

from app.core.matcher import match_boxes
from app.core.metrics import build_stats, build_stats_from_counts
from app.infrastructure.model_runner import IModelRunner
from app.providers.interfaces import IAnnotationProvider, IImageProvider
from app.utils.exceptions import AnnotationNotFoundError


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
        allow_missing_annotations: bool = False,
    ) -> Dict[str, Any]:
        image_bytes = self._image_provider.get_image(image_id)
        try:
            expert_boxes = self._annotation_provider.get_annotations(image_id)
        except AnnotationNotFoundError:
            if not allow_missing_annotations:
                raise
            expert_boxes = []
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

    def analyze_dataset(
        self,
        *,
        iou_threshold: float = 0.5,
        class_aware: bool = True,
    ) -> Dict[str, Any]:
        image_ids = self._image_provider.list_image_ids()
        total_pred = 0
        total_gt = 0
        total_tp = 0

        for image_id in image_ids:
            image_bytes = self._image_provider.get_image(image_id)
            expert_boxes = self._annotation_provider.get_annotations(image_id)
            model_boxes = self._model_runner.predict(image_bytes)

            match_result = match_boxes(
                model_boxes,
                expert_boxes,
                iou_threshold=iou_threshold,
                class_aware=class_aware,
            )

            total_tp += len(match_result["matches"])
            total_pred += len(model_boxes)
            total_gt += len(expert_boxes)

        stats = build_stats_from_counts(
            total_tp,
            total_pred,
            total_gt,
            iou_threshold=iou_threshold,
            class_aware=class_aware,
        )

        return {
            "image_count": len(image_ids),
            "processed_count": len(image_ids),
            "stats": stats,
        }

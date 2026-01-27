"""Model runner interface and stub implementation"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class IModelRunner(ABC):
    """Interface for model inference"""

    @abstractmethod
    def predict(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        """Return model prediction boxes for image bytes"""
        raise NotImplementedError


class StubModelRunner(IModelRunner):
    """Stub model runner for development"""

    def __init__(self, boxes: List[Dict[str, Any]] | None = None) -> None:
        self._boxes = boxes or [
            {
                "class_id": 0,
                "x_center": 0.52,
                "y_center": 0.52,
                "width": 0.18,
                "height": 0.18,
                "score": 0.9,
            },
            {
                "class_id": 1,
                "x_center": 0.68,
                "y_center": 0.38,
                "width": 0.2,
                "height": 0.14,
                "score": 0.84,
            },
        ]

    def predict(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        return [dict(box) for box in self._boxes]

"""Model runner interface and implementations"""
from abc import ABC, abstractmethod
from io import BytesIO
import logging
from pathlib import Path
from typing import Any, Dict, List, Sequence

import numpy as np
from PIL import Image

try:
    import onnxruntime as ort
    _ORT_IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover - depends on runtime env
    ort = None
    _ORT_IMPORT_ERROR = exc

from app.utils.exceptions import InvalidFormatError, ModelNotFoundError

logger = logging.getLogger(__name__)


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


class OnnxModelRunner(IModelRunner):
    """ONNX model runner for object detection"""

    def __init__(
        self,
        model_path: str | Path,
        img_size: int = 640,
        conf_threshold: float = 0.25,
        max_det: int = 100,
        providers: Sequence[str] | None = None,
    ) -> None:
        if ort is None:
            raise InvalidFormatError(f"onnxruntime import failed: {_ORT_IMPORT_ERROR}")

        self.model_path = Path(model_path)
        if not self.model_path.is_file():
            raise ModelNotFoundError(f"Model file not found: {self.model_path}")

        self.img_size = img_size
        self.conf_threshold = conf_threshold
        self.max_det = max_det
        self._providers = list(providers) if providers else ["CPUExecutionProvider"]
        logger.info("Loading ONNX model: %s", self.model_path)
        try:
            self._session = ort.InferenceSession(str(self.model_path), providers=self._providers)
        except Exception:
            logger.exception("Failed to load ONNX model: %s", self.model_path)
            raise
        self._input_name = self._session.get_inputs()[0].name
        logger.info("ONNX model loaded. input=%s providers=%s", self._input_name, self._providers)

    def predict(self, image_bytes: bytes) -> List[Dict[str, Any]]:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        orig_width, orig_height = image.size
        if orig_width == 0 or orig_height == 0:
            raise InvalidFormatError("Invalid image size")

        input_img, scale, pad = self._letterbox(np.array(image), self.img_size)
        blob = input_img.astype(np.float32) / 255.0
        blob = np.transpose(blob, (2, 0, 1))[None, ...]

        outputs = self._session.run(None, {self._input_name: blob})
        logger.debug(
            "ONNX outputs shapes: %s",
            [np.asarray(output).shape for output in outputs],
        )
        return self._parse_outputs(
            outputs,
            orig_width,
            orig_height,
            scale,
            pad,
            self.img_size,
        )

    @staticmethod
    def _letterbox(image: np.ndarray, new_size: int) -> tuple[np.ndarray, float, tuple[float, float]]:
        height, width = image.shape[:2]
        scale = min(new_size / width, new_size / height)
        new_w = int(round(width * scale))
        new_h = int(round(height * scale))

        resized = np.array(Image.fromarray(image).resize((new_w, new_h), Image.BILINEAR))
        canvas = np.full((new_size, new_size, 3), 114, dtype=np.uint8)
        pad_x = (new_size - new_w) / 2
        pad_y = (new_size - new_h) / 2
        x0 = int(round(pad_x))
        y0 = int(round(pad_y))
        canvas[y0 : y0 + new_h, x0 : x0 + new_w] = resized
        return canvas, scale, (pad_x, pad_y)

    def _parse_outputs(
        self,
        outputs: Sequence[np.ndarray],
        orig_width: int,
        orig_height: int,
        scale: float,
        pad: tuple[float, float],
        input_size: int,
    ) -> List[Dict[str, Any]]:
        if not outputs:
            return []

        arrays = [np.squeeze(output) for output in outputs]

        nms_detections = self._extract_nms_detections(arrays)
        if nms_detections is not None:
            return self._format_detections(
                nms_detections,
                orig_width,
                orig_height,
                scale,
                pad,
                input_size,
                xyxy=True,
            )

        raw = arrays[0]
        if raw.ndim == 3 and raw.shape[0] == 1:
            raw = raw[0]
        if raw.ndim != 2:
            raise InvalidFormatError("Unexpected model output shape")

        if raw.shape[0] < raw.shape[1]:
            raw = raw.T

        if raw.shape[1] < 6:
            raise InvalidFormatError("Model output does not contain class scores")

        boxes = raw[:, :4]
        scores = raw[:, 4:]
        class_ids = np.argmax(scores, axis=1)
        confidences = scores[np.arange(scores.shape[0]), class_ids]
        mask = confidences >= self.conf_threshold

        boxes = boxes[mask]
        class_ids = class_ids[mask]
        confidences = confidences[mask]

        if boxes.shape[0] == 0:
            return []

        if boxes.shape[0] > self.max_det:
            order = np.argsort(confidences)[::-1][: self.max_det]
            boxes = boxes[order]
            class_ids = class_ids[order]
            confidences = confidences[order]

        detections = np.column_stack([boxes, confidences, class_ids])
        return self._format_detections(
            detections,
            orig_width,
            orig_height,
            scale,
            pad,
            input_size,
            xyxy=False,
        )

    def _extract_nms_detections(self, arrays: Sequence[np.ndarray]) -> np.ndarray | None:
        for arr in arrays:
            if arr.ndim == 3 and arr.shape[0] == 1:
                arr = arr[0]
            if arr.ndim != 2:
                continue
            if arr.shape[1] in (6, 7):
                return arr
            if arr.shape[0] in (6, 7) and arr.shape[1] > arr.shape[0]:
                return arr.T
        return None

    def _format_detections(
        self,
        detections: np.ndarray,
        orig_width: int,
        orig_height: int,
        scale: float,
        pad: tuple[float, float],
        input_size: int,
        *,
        xyxy: bool,
    ) -> List[Dict[str, Any]]:
        pad_x, pad_y = pad
        results: List[Dict[str, Any]] = []
        for det in detections:
            if det.shape[0] < 6:
                continue
            x1, y1, x2, y2, score, class_id = det[:6]
            if score < self.conf_threshold:
                continue

            if xyxy:
                if max(x1, y1, x2, y2) <= 1.5:
                    x1 *= input_size
                    x2 *= input_size
                    y1 *= input_size
                    y2 *= input_size
            else:
                x_center, y_center, width, height = x1, y1, x2, y2
                if max(x_center, y_center, width, height) <= 1.5:
                    x_center *= input_size
                    y_center *= input_size
                    width *= input_size
                    height *= input_size
                x1 = x_center - width / 2
                y1 = y_center - height / 2
                x2 = x_center + width / 2
                y2 = y_center + height / 2

            x1 = (x1 - pad_x) / scale
            y1 = (y1 - pad_y) / scale
            x2 = (x2 - pad_x) / scale
            y2 = (y2 - pad_y) / scale

            x1 = float(np.clip(x1, 0, orig_width))
            y1 = float(np.clip(y1, 0, orig_height))
            x2 = float(np.clip(x2, 0, orig_width))
            y2 = float(np.clip(y2, 0, orig_height))

            if x2 <= x1 or y2 <= y1:
                continue

            x_center = ((x1 + x2) / 2) / orig_width
            y_center = ((y1 + y2) / 2) / orig_height
            width = (x2 - x1) / orig_width
            height = (y2 - y1) / orig_height

            results.append(
                {
                    "class_id": int(class_id),
                    "x_center": x_center,
                    "y_center": y_center,
                    "width": width,
                    "height": height,
                    "score": float(score),
                }
            )
        return results

"""Local filesystem providers"""
from pathlib import Path
from typing import Any, Dict, List

from app.config import settings
from app.providers.interfaces import IAnnotationProvider, IImageProvider
from app.utils.exceptions import (
    AnnotationNotFoundError,
    ImageNotFoundError,
    InvalidFormatError,
)


class LocalFSImageProvider(IImageProvider):
    """Load images from local filesystem"""

    def __init__(self, data_path: str | Path | None = None, images_dir: str | None = None) -> None:
        base_path = Path(data_path or settings.DATA_PATH)
        images_folder = images_dir or settings.IMAGES_DIR
        self.images_path = base_path / images_folder

    def get_image_path(self, image_id: str) -> Path:
        """Resolve image path by id"""
        if not image_id:
            raise InvalidFormatError("image_id is required")

        if not self.images_path.exists():
            raise ImageNotFoundError(f"Images directory not found: {self.images_path}")

        for image_path in sorted(self.images_path.glob(f"{image_id}.*")):
            if image_path.is_file():
                return image_path

        raise ImageNotFoundError(f"Image '{image_id}' not found")

    def get_image(self, image_id: str) -> bytes:
        return self.get_image_path(image_id).read_bytes()


class LocalFSAnnotationProvider(IAnnotationProvider):
    """Load YOLO annotations from local filesystem"""

    def __init__(self, data_path: str | Path | None = None, labels_dir: str | None = None) -> None:
        base_path = Path(data_path or settings.DATA_PATH)
        labels_folder = labels_dir or settings.LABELS_DIR
        self.labels_path = base_path / labels_folder

    def get_annotations(self, image_id: str) -> List[Dict[str, Any]]:
        if not image_id:
            raise InvalidFormatError("image_id is required")

        labels_file = self.labels_path / f"{image_id}.txt"
        if not labels_file.is_file():
            raise AnnotationNotFoundError(f"Annotation '{image_id}' not found")

        lines = labels_file.read_text().splitlines()
        boxes: List[Dict[str, Any]] = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            parts = stripped.split()
            if len(parts) != 5:
                raise InvalidFormatError(f"Invalid annotation format: '{line}'")
            try:
                class_id = int(parts[0])
                x_center = float(parts[1])
                y_center = float(parts[2])
                width = float(parts[3])
                height = float(parts[4])
            except ValueError as exc:
                raise InvalidFormatError(f"Invalid numeric values in annotation: '{line}'") from exc
            boxes.append(
                {
                    "class_id": class_id,
                    "x_center": x_center,
                    "y_center": y_center,
                    "width": width,
                    "height": height,
                }
            )
        return boxes

"""Provider interfaces"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class IImageProvider(ABC):
    """Interface for image data access"""

    @abstractmethod
    def get_image(self, image_id: str) -> bytes:
        """Return raw image bytes by image id"""
        raise NotImplementedError

    @abstractmethod
    def list_image_ids(self) -> List[str]:
        """Return list of available image ids"""
        raise NotImplementedError


class IAnnotationProvider(ABC):
    """Interface for annotation data access"""

    @abstractmethod
    def get_annotations(self, image_id: str) -> List[Dict[str, Any]]:
        """Return list of annotation boxes for image id"""
        raise NotImplementedError

"""Tests for local filesystem providers"""
import pytest

from app.providers.local_fs import LocalFSAnnotationProvider, LocalFSImageProvider
from app.utils.exceptions import AnnotationNotFoundError, ImageNotFoundError, InvalidFormatError


def test_local_fs_image_provider_reads_image(tmp_path):
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    image_path = images_dir / "IMG-123.png"
    image_path.write_bytes(b"image-bytes")

    provider = LocalFSImageProvider(data_path=tmp_path)
    assert provider.get_image("IMG-123") == b"image-bytes"


def test_local_fs_image_provider_missing_image(tmp_path):
    images_dir = tmp_path / "images"
    images_dir.mkdir()

    provider = LocalFSImageProvider(data_path=tmp_path)
    with pytest.raises(ImageNotFoundError):
        provider.get_image("MISSING")


def test_local_fs_annotation_provider_reads_boxes(tmp_path):
    labels_dir = tmp_path / "labels"
    labels_dir.mkdir()
    labels_file = labels_dir / "IMG-123.txt"
    labels_file.write_text("0 0.5 0.5 0.1 0.2\n1 0.1 0.2 0.3 0.4\n")

    provider = LocalFSAnnotationProvider(data_path=tmp_path)
    boxes = provider.get_annotations("IMG-123")

    assert boxes == [
        {
            "class_id": 0,
            "x_center": 0.5,
            "y_center": 0.5,
            "width": 0.1,
            "height": 0.2,
        },
        {
            "class_id": 1,
            "x_center": 0.1,
            "y_center": 0.2,
            "width": 0.3,
            "height": 0.4,
        },
    ]


def test_local_fs_annotation_provider_missing_file(tmp_path):
    labels_dir = tmp_path / "labels"
    labels_dir.mkdir()

    provider = LocalFSAnnotationProvider(data_path=tmp_path)
    with pytest.raises(AnnotationNotFoundError):
        provider.get_annotations("MISSING")


def test_local_fs_annotation_provider_invalid_line(tmp_path):
    labels_dir = tmp_path / "labels"
    labels_dir.mkdir()
    labels_file = labels_dir / "IMG-123.txt"
    labels_file.write_text("bad line\n")

    provider = LocalFSAnnotationProvider(data_path=tmp_path)
    with pytest.raises(InvalidFormatError):
        provider.get_annotations("IMG-123")

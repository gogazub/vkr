"""Tests for model worker"""
from app.infrastructure.model_runner import StubModelRunner
from app.providers.local_fs import LocalFSAnnotationProvider, LocalFSImageProvider
from app.services.model_worker import ModelWorker


def test_model_worker_returns_combined_payload(tmp_path):
    images_dir = tmp_path / "images"
    labels_dir = tmp_path / "labels"
    images_dir.mkdir()
    labels_dir.mkdir()

    (images_dir / "IMG-001.png").write_bytes(b"fake-image")
    (labels_dir / "IMG-001.txt").write_text("0 0.5 0.5 0.2 0.2\n")

    image_provider = LocalFSImageProvider(data_path=tmp_path)
    annotation_provider = LocalFSAnnotationProvider(data_path=tmp_path)
    model_runner = StubModelRunner(
        boxes=[
            {
                "class_id": 1,
                "x_center": 0.6,
                "y_center": 0.4,
                "width": 0.1,
                "height": 0.1,
                "score": 0.8,
            }
        ]
    )

    worker = ModelWorker(image_provider, annotation_provider, model_runner)
    result = worker.analyze("IMG-001")

    assert result["image_id"] == "IMG-001"
    assert len(result["expert_boxes"]) == 1
    assert len(result["model_boxes"]) == 1
    assert result["stats"]["expert_count"] == 1
    assert result["stats"]["model_count"] == 1
    assert "tp" in result["stats"]

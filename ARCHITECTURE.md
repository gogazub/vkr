# Architecture

This document describes the current and near-term architecture of the validation microservice.
Principles: YAGNI first, evolve in small working steps, keep the system runnable at each step.

## Current State (as-is)
Implemented:
- FastAPI app with `/health` and `/api/v1/info`
- Pydantic settings
- Basic custom exceptions
- Health/info tests

Key files:
- `app/main.py` (FastAPI entrypoint)
- `app/config.py` (settings)
- `app/utils/exceptions.py` (custom exceptions)
- `tests/` (health/info tests)

## Target Minimal Architecture (next steps)

### Layers
1) API layer (FastAPI endpoints)
2) Service layer (use-cases / orchestration)
3) Core layer (pure logic: IoU, matching, metrics)
4) Providers layer (data access; LocalFS first)
5) Infrastructure layer (ONNX runtime integration)

### Modules (planned, minimal)
```
app/
  api/
    v1/
      images.py
      inference.py
      comparison.py
      statistics.py
  schemas/
    image.py
    box.py
    prediction.py
    comparison.py
    stats.py
  core/
    iou.py
    matcher.py
    metrics.py
  providers/
    interfaces.py
    local_fs.py
  services/
    inference_service.py
    comparison_service.py
  infrastructure/
    onnx_runtime.py
  utils/
    exceptions.py
  main.py
  config.py
```

## Classes and Responsibilities (minimal)

### Settings
- `Settings` (app/config.py): env-driven configuration.

### Schemas (Pydantic)
- `ImageId`: `{ image_id: str }`
- `Box`: `{ class_id, x_center, y_center, width, height, score? }`
- `Prediction`: `{ image_id, boxes[] }`
- `ComparisonResult`: `{ image_id, tp, fp, fn, matches[], unmatched_model[], unmatched_gt[] }`
- `Stats`: `{ image_id, accuracy, f1, kappa?, confusion_matrix? }`

### Providers
- `IImageProvider`: `get_image(image_id) -> bytes | PIL.Image`
- `IAnnotationProvider`: `get_annotations(image_id) -> list[Box]`
- `LocalFSImageProvider`: reads `./data/images/{id}.*`
- `LocalFSAnnotationProvider`: reads `./data/labels/{id}.txt` (YOLO format)

### Core (pure logic)
- `compute_iou(box_a, box_b) -> float`
- `match_boxes(pred_boxes, gt_boxes, iou_threshold=0.5) -> MatchResult`
- `compute_metrics(tp, fp, fn) -> dict`

### Services
- `InferenceService`: loads ONNX model, runs inference, returns `Prediction`
- `ComparisonService`: loads annotations + predictions, calls matcher, returns `ComparisonResult`

### Infrastructure
- `OnnxRuntime`: loads model from file, runs inference

## Evolution Plan (small, working steps)
1) LocalFS providers + `GET /api/v1/images`
2) Inference endpoint with stubbed response (no ONNX yet)
3) Comparison endpoint using IoU + TP/FP/FN
4) Real ONNX inference

Each step must pass existing tests and keep `/health` working.

## C4 (text form)

### C4 Context
```
User --> Validation Microservice --> Local FS (images/labels)
                          |
                          --> ONNX Model Files
```

### C4 Containers
```
[FastAPI App]
  |--> [Core Logic]
  |--> [Providers]
  |--> [ONNX Runtime]

[Providers] --> Local FS (images/labels)
[ONNX Runtime] --> Model Files
```

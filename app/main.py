"""FastAPI application entry point"""
import logging
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from openpyxl import Workbook
from app.config import settings
from app.infrastructure.model_runner import OnnxModelRunner, StubModelRunner
from app.providers.local_fs import LocalFSAnnotationProvider, LocalFSImageProvider
from app.services.model_worker import ModelWorker
from app.services.report_export import build_report_table
from app.utils.exceptions import (
    AnnotationNotFoundError,
    ImageNotFoundError,
    InvalidFormatError,
    ModelNotFoundError,
)

logger = logging.getLogger(__name__)
ERROR_PREFIX = "ERR"


def configure_logging() -> None:
    level_name = settings.LOG_LEVEL.upper()
    level = getattr(logging, level_name, logging.INFO)
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
    root_logger.setLevel(level)


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    configure_logging()
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Microservice for Comparative Analysis of Deep Learning Models and Expert Annotations in Biomedical Images",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # CORS middleware for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.DEBUG else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    image_provider = LocalFSImageProvider()
    annotation_provider = LocalFSAnnotationProvider()
    model_path = Path(settings.MODELS_PATH) / settings.MODEL_FILE
    try:
        model_runner = OnnxModelRunner(
            model_path=model_path,
            img_size=settings.MODEL_IMG_SIZE,
            conf_threshold=settings.MODEL_CONF_THRESHOLD,
            max_det=settings.MODEL_MAX_DET,
            letterbox=settings.MODEL_LETTERBOX,
        )
        logger.info("Using ONNX model: %s", model_path)
    except ModelNotFoundError:
        logger.warning("Model file not found. Using stub runner. path=%s", model_path)
        model_runner = StubModelRunner()
    except Exception:
        logger.exception("Failed to initialize ONNX model. Using stub runner. path=%s", model_path)
        model_runner = StubModelRunner()
    model_worker = ModelWorker(image_provider, annotation_provider, model_runner)

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENV_MODE,
        }
    
    # Info endpoint
    @app.get("/api/v1/info", tags=["Info"])
    async def get_info():
        """Get service information"""
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENV_MODE,
            "debug": settings.DEBUG,
        }

    @app.get("/api/v1/images/{image_id}/file", tags=["Images"])
    async def get_image_file(image_id: str):
        """Return raw image file by id"""
        try:
            image_path = image_provider.get_image_path(image_id)
        except ImageNotFoundError as exc:
            logger.warning("%s Image not found: image_id=%s", ERROR_PREFIX, image_id)
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except InvalidFormatError as exc:
            logger.warning("%s Invalid image id: image_id=%s", ERROR_PREFIX, image_id)
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return FileResponse(image_path)

    @app.get("/api/v1/images", tags=["Images"])
    async def list_images():
        """Return list of available images"""
        try:
            image_ids = image_provider.list_image_ids()
        except ImageNotFoundError as exc:
            logger.warning("%s Images directory not found", ERROR_PREFIX)
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        logger.info("List images: count=%d", len(image_ids))
        return {
            "count": len(image_ids),
            "items": [
                {"id": image_id, "image_url": f"/api/v1/images/{image_id}/file"}
                for image_id in image_ids
            ],
        }

    @app.get("/api/v1/images/{image_id}/annotations", tags=["Images"])
    async def get_image_annotations(image_id: str):
        """Return annotations for image id"""
        try:
            boxes = annotation_provider.get_annotations(image_id)
        except AnnotationNotFoundError as exc:
            logger.warning("%s Annotation not found: image_id=%s", ERROR_PREFIX, image_id)
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except InvalidFormatError as exc:
            logger.warning("%s Invalid annotation format: image_id=%s", ERROR_PREFIX, image_id)
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"image_id": image_id, "boxes": boxes}

    @app.get("/api/v1/viewer/{image_id}", tags=["Viewer"])
    async def get_viewer_payload(image_id: str):
        """Return viewer payload (image url + annotations)"""
        try:
            image_provider.get_image_path(image_id)
        except ImageNotFoundError as exc:
            logger.warning("%s Image not found: image_id=%s", ERROR_PREFIX, image_id)
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except InvalidFormatError as exc:
            logger.warning("%s Invalid image id: image_id=%s", ERROR_PREFIX, image_id)
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        try:
            boxes = annotation_provider.get_annotations(image_id)
        except AnnotationNotFoundError as exc:
            logger.warning("%s Annotation not found: image_id=%s", ERROR_PREFIX, image_id)
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except InvalidFormatError as exc:
            logger.warning("%s Invalid annotation format: image_id=%s", ERROR_PREFIX, image_id)
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return {
            "image_id": image_id,
            "image_url": f"/api/v1/images/{image_id}/file",
            "boxes": boxes,
        }

    @app.get("/api/v1/analysis/dataset", tags=["Analysis"])
    async def analyze_dataset(
        iou_threshold: float = 0.5,
        class_aware: bool = True,
    ):
        """Return aggregated stats for full dataset"""
        logger.info(
            "Dataset analysis request: iou_threshold=%.2f class_aware=%s",
            iou_threshold,
            class_aware,
        )
        try:
            result = model_worker.analyze_dataset(
                iou_threshold=iou_threshold,
                class_aware=class_aware,
            )
        except ImageNotFoundError as exc:
            logger.warning("%s Images directory not found during dataset analysis", ERROR_PREFIX)
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except AnnotationNotFoundError as exc:
            logger.warning("%s Annotation missing during dataset analysis", ERROR_PREFIX)
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except InvalidFormatError as exc:
            logger.warning("%s Invalid annotation format during dataset analysis", ERROR_PREFIX)
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception:
            logger.exception("%s Dataset analysis failed", ERROR_PREFIX)
            raise HTTPException(status_code=500, detail="Dataset analysis failed")
        return result

    @app.get("/api/v1/analysis/dataset/export", tags=["Analysis"])
    async def export_dataset_report(
        iou_threshold: float = 0.5,
        class_aware: bool = True,
    ):
        """Export per-image stats as Excel report"""
        logger.info(
            "Dataset export request: iou_threshold=%.2f class_aware=%s",
            iou_threshold,
            class_aware,
        )
        try:
            image_ids = image_provider.list_image_ids()
            rows = [
                model_worker.analyze(
                    image_id,
                    iou_threshold=iou_threshold,
                    class_aware=class_aware,
                    allow_missing_annotations=True,
                )
                for image_id in image_ids
            ]
        except ImageNotFoundError as exc:
            logger.warning("%s Images directory not found during export", ERROR_PREFIX)
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except AnnotationNotFoundError as exc:
            logger.warning("%s Annotation missing during export", ERROR_PREFIX)
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except InvalidFormatError as exc:
            logger.warning("%s Invalid annotation format during export", ERROR_PREFIX)
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception:
            logger.exception("%s Dataset export failed", ERROR_PREFIX)
            raise HTTPException(status_code=500, detail="Dataset export failed")

        headers, data = build_report_table(rows)
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Dataset report"
        sheet.append(headers)
        for row in data:
            sheet.append(row)

        output = BytesIO()
        workbook.save(output)
        output.seek(0)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"dataset_report_{timestamp}.xlsx"
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @app.get("/api/v1/analysis/{image_id}", tags=["Analysis"])
    async def analyze_image(
        image_id: str,
        iou_threshold: float = 0.5,
        class_aware: bool = True,
    ):
        """Return combined payload (image + expert + model + stats)"""
        logger.info(
            "Image analysis request: image_id=%s iou_threshold=%.2f class_aware=%s",
            image_id,
            iou_threshold,
            class_aware,
        )
        try:
            result = model_worker.analyze(
                image_id,
                iou_threshold=iou_threshold,
                class_aware=class_aware,
                allow_missing_annotations=True,
            )
        except ImageNotFoundError as exc:
            logger.warning("%s Image not found: image_id=%s", ERROR_PREFIX, image_id)
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except AnnotationNotFoundError as exc:
            logger.warning("%s Annotation not found: image_id=%s", ERROR_PREFIX, image_id)
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except InvalidFormatError as exc:
            logger.warning("%s Invalid format during analysis: image_id=%s", ERROR_PREFIX, image_id)
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception:
            logger.exception("%s Analysis failed for image_id=%s", ERROR_PREFIX, image_id)
            raise HTTPException(status_code=500, detail="Analysis failed")
        return {
            **result,
            "image_url": f"/api/v1/images/{image_id}/file",
        }

    return app


# Create app instance
app = create_app()

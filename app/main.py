"""FastAPI application entry point"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from app.config import settings
from app.infrastructure.model_runner import StubModelRunner
from app.providers.local_fs import LocalFSAnnotationProvider, LocalFSImageProvider
from app.services.model_worker import ModelWorker
from app.utils.exceptions import AnnotationNotFoundError, ImageNotFoundError, InvalidFormatError


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
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
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except InvalidFormatError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return FileResponse(image_path)

    @app.get("/api/v1/images/{image_id}/annotations", tags=["Images"])
    async def get_image_annotations(image_id: str):
        """Return annotations for image id"""
        try:
            boxes = annotation_provider.get_annotations(image_id)
        except AnnotationNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except InvalidFormatError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"image_id": image_id, "boxes": boxes}

    @app.get("/api/v1/viewer/{image_id}", tags=["Viewer"])
    async def get_viewer_payload(image_id: str):
        """Return viewer payload (image url + annotations)"""
        try:
            image_provider.get_image_path(image_id)
        except ImageNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except InvalidFormatError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        try:
            boxes = annotation_provider.get_annotations(image_id)
        except AnnotationNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except InvalidFormatError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return {
            "image_id": image_id,
            "image_url": f"/api/v1/images/{image_id}/file",
            "boxes": boxes,
        }

    @app.get("/api/v1/analysis/{image_id}", tags=["Analysis"])
    async def analyze_image(image_id: str):
        """Return combined payload (image + expert + model + stats)"""
        try:
            result = model_worker.analyze(image_id)
        except ImageNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except AnnotationNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except InvalidFormatError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {
            **result,
            "image_url": f"/api/v1/images/{image_id}/file",
        }

    return app


# Create app instance
app = create_app()

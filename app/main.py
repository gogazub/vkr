"""FastAPI application entry point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings


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
    
    return app


# Create app instance
app = create_app()

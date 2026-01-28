"""Application configuration"""
import os
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    ENV_MODE: Literal["DEV", "PROD"] = "DEV"
    DEBUG: bool = True
    
    # Application
    APP_NAME: str = "validation-microservice"
    APP_VERSION: str = "0.1.0"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/validation_db"
    
    # Data paths (for DEV mode)
    DATA_PATH: str = "./data"
    MODELS_PATH: str = "./models"
    IMAGES_DIR: str = "images"
    LABELS_DIR: str = "labels"
    MODEL_FILE: str = "model.onnx"

    # Model inference defaults
    MODEL_IMG_SIZE: int = 640
    MODEL_CONF_THRESHOLD: float = 0.25
    MODEL_MAX_DET: int = 100
    
    # Security
    SECRET_KEY: str = "dev-secret-key"

    # Logging
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )


settings = Settings()

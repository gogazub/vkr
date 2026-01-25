"""Custom exceptions"""


class ValidationMicroserviceError(Exception):
    """Base exception for validation microservice"""
    pass


class ImageNotFoundError(ValidationMicroserviceError):
    """Image not found"""
    pass


class AnnotationNotFoundError(ValidationMicroserviceError):
    """Annotation not found"""
    pass


class ModelNotFoundError(ValidationMicroserviceError):
    """Model not found"""
    pass


class InvalidFormatError(ValidationMicroserviceError):
    """Invalid data format"""
    pass

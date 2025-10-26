"""
Custom exceptions for DeepSeek OCR
"""


class OCRError(Exception):
    """Base exception for OCR-related errors"""
    pass


class ModelError(Exception):
    """Exception for model loading/inference errors"""
    pass


class ImageProcessingError(Exception):
    """Exception for image processing errors"""
    pass


class ConfigurationError(Exception):
    """Exception for configuration-related errors"""
    pass


class ValidationError(Exception):
    """Exception for input validation errors"""
    pass


class APIError(Exception):
    """Exception for API-related errors"""
    pass
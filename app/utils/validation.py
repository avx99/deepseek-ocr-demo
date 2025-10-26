"""
Input validation utilities
"""

import os
import mimetypes
from typing import List, Optional, Tuple
from werkzeug.datastructures import FileStorage

from .config import Config
from .exceptions import ValidationError


class FileValidator:
    """Validates uploaded files"""
    
    def __init__(self, config: Config):
        self.config = config
        self.allowed_extensions = set(ext.lower() for ext in config.upload.allowed_extensions)
        self.max_file_size = config.upload.max_file_size
    
    def validate_file(self, file: FileStorage) -> bool:
        """
        Validate uploaded file
        
        Args:
            file: Uploaded file object
            
        Returns:
            True if valid, raises ValidationError if invalid
        """
        if not file or not file.filename:
            raise ValidationError("No file provided")
        
        # Check file extension
        if not self._is_allowed_extension(file.filename):
            raise ValidationError(
                f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}"
            )
        
        # Check file size
        if not self._is_valid_size(file):
            max_mb = self.max_file_size / (1024 * 1024)
            raise ValidationError(f"File too large. Maximum size: {max_mb:.1f}MB")
        
        # Check MIME type
        if not self._is_valid_mime_type(file):
            raise ValidationError("Invalid file type")
        
        return True
    
    def _is_allowed_extension(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        if '.' not in filename:
            return False
        
        extension = filename.rsplit('.', 1)[1].lower()
        return extension in self.allowed_extensions
    
    def _is_valid_size(self, file: FileStorage) -> bool:
        """Check if file size is within limits"""
        # Get file size
        file.seek(0, 2)  # Seek to end
        size = file.tell()
        file.seek(0)  # Reset to beginning
        
        return size <= self.max_file_size
    
    def _is_valid_mime_type(self, file: FileStorage) -> bool:
        """Check if MIME type is valid for images"""
        valid_mime_types = {
            'image/jpeg', 'image/jpg', 'image/png', 'image/bmp',
            'image/tiff', 'image/webp', 'image/gif',
            'application/pdf'
        }
        
        # Get MIME type from file content
        mime_type, _ = mimetypes.guess_type(file.filename)
        
        if mime_type in valid_mime_types:
            return True
        
        # Additional check using file content (first few bytes)
        file.seek(0)
        header = file.read(1024)
        file.seek(0)
        
        # Check for common image headers
        if header.startswith(b'\xff\xd8\xff'):  # JPEG
            return True
        elif header.startswith(b'\x89PNG\r\n\x1a\n'):  # PNG
            return True
        elif header.startswith(b'BM'):  # BMP
            return True
        elif header.startswith(b'%PDF'):  # PDF
            return True
        
        return False


class InputValidator:
    """Validates various input parameters"""
    
    @staticmethod
    def validate_prompt(prompt: str, max_length: int = 1000) -> str:
        """
        Validate OCR prompt
        
        Args:
            prompt: User-provided prompt
            max_length: Maximum allowed length
            
        Returns:
            Cleaned prompt string
        """
        if not prompt:
            return ""
        
        # Clean the prompt
        prompt = prompt.strip()
        
        if len(prompt) > max_length:
            raise ValidationError(f"Prompt too long. Maximum length: {max_length}")
        
        # Basic sanitization
        prompt = prompt.replace('\x00', '')  # Remove null bytes
        
        return prompt
    
    @staticmethod
    def validate_file_path(file_path: str, allowed_dirs: List[str]) -> bool:
        """
        Validate file path for security
        
        Args:
            file_path: Path to validate
            allowed_dirs: List of allowed directories
            
        Returns:
            True if valid, raises ValidationError if invalid
        """
        # Normalize path
        normalized_path = os.path.normpath(file_path)
        
        # Check for path traversal attempts
        if '..' in normalized_path:
            raise ValidationError("Path traversal not allowed")
        
        # Check if path is within allowed directories
        for allowed_dir in allowed_dirs:
            if normalized_path.startswith(os.path.normpath(allowed_dir)):
                return True
        
        raise ValidationError("File path not in allowed directories")
    
    @staticmethod
    def validate_batch_size(batch_size: int, max_batch_size: int = 10) -> int:
        """
        Validate batch processing size
        
        Args:
            batch_size: Requested batch size
            max_batch_size: Maximum allowed batch size
            
        Returns:
            Validated batch size
        """
        if batch_size < 1:
            raise ValidationError("Batch size must be at least 1")
        
        if batch_size > max_batch_size:
            raise ValidationError(f"Batch size too large. Maximum: {max_batch_size}")
        
        return batch_size
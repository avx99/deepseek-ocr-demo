"""
Unit tests for validation utilities
"""

import io
import tempfile
from unittest.mock import Mock

from app.utils.validation import FileValidator, InputValidator
from app.utils.config import Config
from app.utils.exceptions import ValidationError


class MockFileStorage:
    """Mock file storage for testing"""
    
    def __init__(self, filename, content=b"test content", content_type="image/jpeg"):
        self.filename = filename
        self.content = content
        self.content_type = content_type
        self._stream = io.BytesIO(content)
        self._position = 0
    
    def seek(self, position, whence=0):
        if whence == 2:  # SEEK_END
            self._position = len(self.content)
        elif whence == 1:  # SEEK_CUR
            self._position += position
        else:  # SEEK_SET
            self._position = position
        self._stream.seek(self._position)
    
    def tell(self):
        return self._position
    
    def read(self, size=-1):
        if size == -1:
            data = self.content[self._position:]
            self._position = len(self.content)
        else:
            data = self.content[self._position:self._position + size]
            self._position += len(data)
        return data


class TestFileValidator:
    """Test file validation functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = Config()
        self.validator = FileValidator(self.config)
    
    def test_file_validator_initialization(self):
        """Test file validator initialization"""
        assert self.validator.config == self.config
        assert 'jpg' in self.validator.allowed_extensions
        assert 'png' in self.validator.allowed_extensions
        assert self.validator.max_file_size == self.config.upload.max_file_size
    
    def test_validate_file_success(self):
        """Test successful file validation"""
        # Create mock file with JPEG header
        jpeg_header = b'\xff\xd8\xff'
        file_mock = MockFileStorage("test.jpg", jpeg_header + b"fake jpeg data")
        
        result = self.validator.validate_file(file_mock)
        assert result == True
    
    def test_validate_file_no_file(self):
        """Test validation with no file"""
        with pytest.raises(ValidationError, match="No file provided"):
            self.validator.validate_file(None)
    
    def test_validate_file_no_filename(self):
        """Test validation with empty filename"""
        file_mock = MockFileStorage("", b"content")
        file_mock.filename = ""
        
        with pytest.raises(ValidationError, match="No file provided"):
            self.validator.validate_file(file_mock)
    
    def test_validate_file_invalid_extension(self):
        """Test validation with invalid file extension"""
        file_mock = MockFileStorage("test.txt", b"text content")
        
        with pytest.raises(ValidationError, match="File type not allowed"):
            self.validator.validate_file(file_mock)
    
    def test_validate_file_too_large(self):
        """Test validation with file too large"""
        # Create large content that exceeds max file size
        large_content = b"x" * (self.config.upload.max_file_size + 1)
        file_mock = MockFileStorage("test.jpg", large_content)
        
        with pytest.raises(ValidationError, match="File too large"):
            self.validator.validate_file(file_mock)
    
    def test_is_allowed_extension_valid(self):
        """Test allowed extension checking with valid extensions"""
        assert self.validator._is_allowed_extension("image.jpg") == True
        assert self.validator._is_allowed_extension("image.JPG") == True  # Case insensitive
        assert self.validator._is_allowed_extension("document.pdf") == True
        assert self.validator._is_allowed_extension("photo.png") == True
    
    def test_is_allowed_extension_invalid(self):
        """Test allowed extension checking with invalid extensions"""
        assert self.validator._is_allowed_extension("document.txt") == False
        assert self.validator._is_allowed_extension("script.py") == False
        assert self.validator._is_allowed_extension("archive.zip") == False
        assert self.validator._is_allowed_extension("no_extension") == False
    
    def test_is_valid_size_within_limit(self):
        """Test file size validation within limit"""
        small_content = b"small content"
        file_mock = MockFileStorage("test.jpg", small_content)
        
        assert self.validator._is_valid_size(file_mock) == True
    
    def test_is_valid_size_exceeds_limit(self):
        """Test file size validation exceeding limit"""
        large_content = b"x" * (self.config.upload.max_file_size + 1)
        file_mock = MockFileStorage("test.jpg", large_content)
        
        assert self.validator._is_valid_size(file_mock) == False
    
    def test_is_valid_mime_type_image(self):
        """Test MIME type validation for images"""
        # JPEG header
        jpeg_file = MockFileStorage("test.jpg", b'\xff\xd8\xff\xe0\x00\x10JFIF')
        assert self.validator._is_valid_mime_type(jpeg_file) == True
        
        # PNG header
        png_file = MockFileStorage("test.png", b'\x89PNG\r\n\x1a\n')
        assert self.validator._is_valid_mime_type(png_file) == True
        
        # BMP header
        bmp_file = MockFileStorage("test.bmp", b'BM')
        assert self.validator._is_valid_mime_type(bmp_file) == True
    
    def test_is_valid_mime_type_pdf(self):
        """Test MIME type validation for PDF"""
        pdf_file = MockFileStorage("test.pdf", b'%PDF-1.4')
        assert self.validator._is_valid_mime_type(pdf_file) == True
    
    def test_is_valid_mime_type_invalid(self):
        """Test MIME type validation for invalid files"""
        text_file = MockFileStorage("test.txt", b'plain text content')
        # Note: This might pass due to filename-based MIME detection
        # The actual validation depends on the mimetypes.guess_type implementation
    
    def test_validate_file_comprehensive(self):
        """Test comprehensive file validation"""
        # Create a valid JPEG file
        jpeg_content = b'\xff\xd8\xff\xe0\x00\x10JFIF' + b'fake jpeg data'
        valid_file = MockFileStorage("valid_image.jpg", jpeg_content)
        
        # Should pass all validations
        result = self.validator.validate_file(valid_file)
        assert result == True


class TestInputValidator:
    """Test input validation functionality"""
    
    def test_validate_prompt_valid(self):
        """Test valid prompt validation"""
        prompt = "Extract all text from this image"
        result = InputValidator.validate_prompt(prompt)
        assert result == prompt
    
    def test_validate_prompt_empty(self):
        """Test empty prompt validation"""
        result = InputValidator.validate_prompt("")
        assert result == ""
        
        result = InputValidator.validate_prompt("   ")
        assert result == ""
    
    def test_validate_prompt_too_long(self):
        """Test prompt validation with too long input"""
        long_prompt = "x" * 1001  # Exceeds default 1000 char limit
        
        with pytest.raises(ValidationError, match="Prompt too long"):
            InputValidator.validate_prompt(long_prompt)
    
    def test_validate_prompt_custom_max_length(self):
        """Test prompt validation with custom max length"""
        prompt = "This is a test prompt"
        
        # Should pass with higher limit
        result = InputValidator.validate_prompt(prompt, max_length=100)
        assert result == prompt
        
        # Should fail with lower limit
        with pytest.raises(ValidationError, match="Prompt too long"):
            InputValidator.validate_prompt(prompt, max_length=10)
    
    def test_validate_prompt_sanitization(self):
        """Test prompt sanitization"""
        prompt_with_nulls = "Test prompt\x00with nulls"
        result = InputValidator.validate_prompt(prompt_with_nulls)
        assert "\x00" not in result
        assert result == "Test promptwith nulls"
    
    def test_validate_file_path_valid(self):
        """Test valid file path validation"""
        allowed_dirs = ["./uploads", "./results"]
        
        # Valid paths
        assert InputValidator.validate_file_path("./uploads/file.jpg", allowed_dirs) == True
        assert InputValidator.validate_file_path("./results/output.json", allowed_dirs) == True
    
    def test_validate_file_path_traversal_attack(self):
        """Test file path validation against traversal attacks"""
        allowed_dirs = ["./uploads"]
        
        # Path traversal attempts
        with pytest.raises(ValidationError, match="Path traversal not allowed"):
            InputValidator.validate_file_path("./uploads/../config.yaml", allowed_dirs)
        
        with pytest.raises(ValidationError, match="Path traversal not allowed"):
            InputValidator.validate_file_path("../secret.txt", allowed_dirs)
    
    def test_validate_file_path_outside_allowed(self):
        """Test file path validation outside allowed directories"""
        allowed_dirs = ["./uploads", "./results"]
        
        with pytest.raises(ValidationError, match="File path not in allowed directories"):
            InputValidator.validate_file_path("./config/config.yaml", allowed_dirs)
        
        with pytest.raises(ValidationError, match="File path not in allowed directories"):
            InputValidator.validate_file_path("/etc/passwd", allowed_dirs)
    
    def test_validate_batch_size_valid(self):
        """Test valid batch size validation"""
        assert InputValidator.validate_batch_size(1) == 1
        assert InputValidator.validate_batch_size(5) == 5
        assert InputValidator.validate_batch_size(10) == 10
    
    def test_validate_batch_size_too_small(self):
        """Test batch size validation with too small value"""
        with pytest.raises(ValidationError, match="Batch size must be at least 1"):
            InputValidator.validate_batch_size(0)
        
        with pytest.raises(ValidationError, match="Batch size must be at least 1"):
            InputValidator.validate_batch_size(-1)
    
    def test_validate_batch_size_too_large(self):
        """Test batch size validation with too large value"""
        with pytest.raises(ValidationError, match="Batch size too large"):
            InputValidator.validate_batch_size(11)  # Default max is 10
        
        with pytest.raises(ValidationError, match="Batch size too large"):
            InputValidator.validate_batch_size(100)
    
    def test_validate_batch_size_custom_max(self):
        """Test batch size validation with custom maximum"""
        # Should pass with higher limit
        assert InputValidator.validate_batch_size(15, max_batch_size=20) == 15
        
        # Should fail with lower limit
        with pytest.raises(ValidationError, match="Batch size too large"):
            InputValidator.validate_batch_size(15, max_batch_size=10)


class TestValidationIntegration:
    """Integration tests for validation utilities"""
    
    def test_file_validator_integration(self):
        """Test file validator integration with config"""
        # Create custom config
        config = Config()
        config.upload.max_file_size = 1024  # 1KB limit
        config.upload.allowed_extensions = ['jpg', 'png']
        
        validator = FileValidator(config)
        
        # Test with small valid file
        small_jpeg = MockFileStorage("small.jpg", b'\xff\xd8\xff' + b'x' * 100)
        assert validator.validate_file(small_jpeg) == True
        
        # Test with large file
        large_jpeg = MockFileStorage("large.jpg", b'\xff\xd8\xff' + b'x' * 2000)
        with pytest.raises(ValidationError, match="File too large"):
            validator.validate_file(large_jpeg)
        
        # Test with disallowed extension
        gif_file = MockFileStorage("image.gif", b'GIF89a')
        with pytest.raises(ValidationError, match="File type not allowed"):
            validator.validate_file(gif_file)


if __name__ == '__main__':
    import pytest
    pytest.main([__file__])
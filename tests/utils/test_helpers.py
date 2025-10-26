"""
Test utility functions and helpers
"""

import os
import json
import tempfile
import shutil
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, MagicMock
from io import BytesIO
import base64


class TestHelpers:
    """Helper utilities for testing"""
    
    @staticmethod
    def create_temp_dir() -> str:
        """Create temporary directory for testing"""
        return tempfile.mkdtemp()
    
    @staticmethod
    def cleanup_temp_dir(temp_dir: str):
        """Clean up temporary directory"""
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    @staticmethod
    def create_mock_image_file(filename: str = "test.jpg") -> Mock:
        """Create mock image file for testing"""
        mock_file = Mock()
        mock_file.filename = filename
        mock_file.content_type = "image/jpeg"
        mock_file.read.return_value = b"fake_image_data"
        mock_file.stream = BytesIO(b"fake_image_data")
        return mock_file
    
    @staticmethod
    def create_mock_invalid_file(filename: str = "test.txt") -> Mock:
        """Create mock invalid file for testing"""
        mock_file = Mock()
        mock_file.filename = filename
        mock_file.content_type = "text/plain"
        mock_file.read.return_value = b"not_image_data"
        mock_file.stream = BytesIO(b"not_image_data")
        return mock_file
    
    @staticmethod
    def create_large_mock_file(size_mb: int = 10) -> Mock:
        """Create large mock file for testing"""
        data = b"x" * (size_mb * 1024 * 1024)
        mock_file = Mock()
        mock_file.filename = f"large_file_{size_mb}mb.jpg"
        mock_file.content_type = "image/jpeg"
        mock_file.read.return_value = data
        mock_file.stream = BytesIO(data)
        return mock_file


class MockDeepSeekModel:
    """Mock DeepSeek model for testing"""
    
    def __init__(self, responses: Dict[str, str] = None):
        self.responses = responses or {
            "default": "Extracted text from image"
        }
        self.call_count = 0
        self.last_input = None
    
    def __call__(self, inputs):
        """Mock model call"""
        self.call_count += 1
        self.last_input = inputs
        
        # Simulate processing delay
        import time
        time.sleep(0.1)
        
        # Return mock response
        if "simple" in str(inputs):
            return [{"generated_text": "Hello World!"}]
        elif "error" in str(inputs):
            raise Exception("Mock model error")
        else:
            return [{"generated_text": self.responses.get("default", "Mock OCR result")}]


class MockTransformersComponents:
    """Mock transformers components for testing"""
    
    @staticmethod
    def mock_auto_model():
        """Mock AutoModel"""
        mock_model = Mock()
        mock_model.from_pretrained.return_value = MockDeepSeekModel()
        return mock_model
    
    @staticmethod
    def mock_auto_processor():
        """Mock AutoProcessor"""
        mock_processor = Mock()
        mock_processor.from_pretrained.return_value = Mock()
        mock_processor.return_value.return_value = {
            "input_ids": [[1, 2, 3]],
            "pixel_values": [[[0.5, 0.5, 0.5]]]
        }
        return mock_processor


class APITestClient:
    """Test client for API testing"""
    
    def __init__(self, app):
        self.app = app
        self.client = app.test_client()
    
    def upload_image(self, image_data: bytes, filename: str = "test.jpg", 
                    extract_format: str = "plain", **kwargs) -> Dict[str, Any]:
        """Upload image for OCR processing"""
        data = {
            'image': (BytesIO(image_data), filename),
            'extract_format': extract_format
        }
        data.update(kwargs)
        
        response = self.client.post('/api/ocr/upload', 
                                   data=data,
                                   content_type='multipart/form-data')
        return response.get_json(), response.status_code
    
    def upload_multiple_images(self, images: List[tuple], **kwargs) -> Dict[str, Any]:
        """Upload multiple images for batch processing"""
        data = {}
        for i, (image_data, filename) in enumerate(images):
            data[f'images[{i}]'] = (BytesIO(image_data), filename)
        
        data.update(kwargs)
        
        response = self.client.post('/api/ocr/batch',
                                   data=data,
                                   content_type='multipart/form-data')
        return response.get_json(), response.status_code
    
    def get_health(self) -> Dict[str, Any]:
        """Get health status"""
        response = self.client.get('/api/health')
        return response.get_json(), response.status_code


class ConfigTestHelper:
    """Helper for configuration testing"""
    
    @staticmethod
    def create_temp_config(config_data: Dict[str, Any]) -> str:
        """Create temporary config file"""
        import yaml
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(config_data, temp_file)
        temp_file.close()
        return temp_file.name
    
    @staticmethod
    def create_invalid_config() -> str:
        """Create invalid config file"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        temp_file.write("invalid: yaml: content: [")
        temp_file.close()
        return temp_file.name
    
    @staticmethod
    def cleanup_config(config_path: str):
        """Clean up config file"""
        if os.path.exists(config_path):
            os.unlink(config_path)


class ImageTestHelper:
    """Helper for image testing"""
    
    @staticmethod
    def create_test_image_bytes(width: int = 100, height: int = 100, 
                               color: str = 'white') -> bytes:
        """Create test image as bytes"""
        try:
            from PIL import Image
            import io
            
            image = Image.new('RGB', (width, height), color)
            image_bytes = io.BytesIO()
            image.save(image_bytes, format='JPEG')
            return image_bytes.getvalue()
        except ImportError:
            # Return mock image bytes if PIL not available
            return b"fake_jpeg_header\xff\xd8\xff\xe0" + b"x" * (width * height // 10)
    
    @staticmethod
    def create_corrupted_image_bytes() -> bytes:
        """Create corrupted image bytes"""
        return b"not_a_valid_image"
    
    @staticmethod
    def create_large_image_bytes(size_mb: int = 5) -> bytes:
        """Create large image bytes"""
        base_image = ImageTestHelper.create_test_image_bytes(1000, 1000)
        # Repeat the image data to reach desired size
        multiplier = (size_mb * 1024 * 1024) // len(base_image) + 1
        return base_image * multiplier


class PerformanceTestHelper:
    """Helper for performance testing"""
    
    def __init__(self):
        self.metrics = {}
    
    def start_timer(self, operation: str):
        """Start timing an operation"""
        import time
        self.metrics[operation] = {'start': time.time()}
    
    def end_timer(self, operation: str):
        """End timing an operation"""
        import time
        if operation in self.metrics:
            self.metrics[operation]['end'] = time.time()
            self.metrics[operation]['duration'] = (
                self.metrics[operation]['end'] - self.metrics[operation]['start']
            )
    
    def get_duration(self, operation: str) -> float:
        """Get operation duration"""
        return self.metrics.get(operation, {}).get('duration', 0.0)
    
    def assert_performance(self, operation: str, max_duration: float):
        """Assert that operation completed within time limit"""
        duration = self.get_duration(operation)
        assert duration <= max_duration, f"Operation {operation} took {duration}s, expected <= {max_duration}s"


class LogTestHelper:
    """Helper for testing logging functionality"""
    
    def __init__(self):
        self.captured_logs = []
    
    def capture_logs(self, logger_name: str = None):
        """Capture logs for testing"""
        import logging
        
        class LogCapture(logging.Handler):
            def __init__(self, helper):
                super().__init__()
                self.helper = helper
            
            def emit(self, record):
                self.helper.captured_logs.append({
                    'level': record.levelname,
                    'message': record.getMessage(),
                    'module': record.module
                })
        
        logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
        handler = LogCapture(self)
        logger.addHandler(handler)
        return handler
    
    def assert_log_contains(self, message: str, level: str = None):
        """Assert that logs contain specific message"""
        for log in self.captured_logs:
            if message in log['message']:
                if level is None or log['level'] == level:
                    return True
        raise AssertionError(f"Log message '{message}' not found" + 
                           (f" at level {level}" if level else ""))
    
    def clear_logs(self):
        """Clear captured logs"""
        self.captured_logs.clear()


# Global test helpers instance
test_helpers = TestHelpers()
config_helper = ConfigTestHelper()
image_helper = ImageTestHelper()
performance_helper = PerformanceTestHelper()
log_helper = LogTestHelper()
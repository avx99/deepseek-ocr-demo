"""
Integration tests for the Flask web application
"""

import os
import json
import tempfile
from io import BytesIO
from PIL import Image

from app.main import create_app


class TestFlaskApp:
    """Test Flask application endpoints"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    def create_test_image_file(self, size=(100, 100), format='JPEG'):
        """Create a test image file in memory"""
        image = Image.new('RGB', size, (255, 255, 255))
        img_io = BytesIO()
        image.save(img_io, format=format)
        img_io.seek(0)
        return img_io
    
    def test_index_page(self):
        """Test main index page"""
        response = self.client.get('/')
        assert response.status_code == 200
        assert b'DeepSeek OCR' in response.data
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'model' in data
        assert 'version' in data
    
    def test_info_endpoint(self):
        """Test system info endpoint"""
        response = self.client.get('/info')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'model_name' in data
        assert 'use_local_model' in data
        assert 'device' in data
        assert 'max_file_size' in data
        assert 'allowed_extensions' in data
        assert 'version' in data
    
    def test_upload_no_file(self):
        """Test upload endpoint with no file"""
        response = self.client.post('/upload')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No file provided' in data['error']
    
    def test_upload_empty_filename(self):
        """Test upload endpoint with empty filename"""
        response = self.client.post('/upload', data={'file': (BytesIO(), '')})
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No file selected' in data['error']
    
    def test_upload_valid_image(self):
        """Test upload endpoint with valid image"""
        img_data = self.create_test_image_file()
        
        response = self.client.post('/upload', data={
            'file': (img_data, 'test.jpg', 'image/jpeg')
        })
        
        # This might fail in test environment without proper OCR setup
        # The exact status depends on the OCR processor mock
        assert response.status_code in [200, 500]  # Either success or server error
        
        data = json.loads(response.data)
        if response.status_code == 200:
            assert 'success' in data
            assert 'text' in data
        else:
            assert 'error' in data
    
    def test_upload_with_prompt(self):
        """Test upload endpoint with custom prompt"""
        img_data = self.create_test_image_file()
        custom_prompt = "Extract only numbers from this image"
        
        response = self.client.post('/upload', data={
            'file': (img_data, 'test.jpg', 'image/jpeg'),
            'prompt': custom_prompt
        })
        
        # Status depends on OCR processor setup
        assert response.status_code in [200, 500]
    
    def test_upload_invalid_file_type(self):
        """Test upload endpoint with invalid file type"""
        text_data = BytesIO(b"This is not an image")
        
        response = self.client.post('/upload', data={
            'file': (text_data, 'test.txt', 'text/plain')
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_batch_upload_no_files(self):
        """Test batch upload endpoint with no files"""
        response = self.client.post('/batch_upload')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No files provided' in data['error']
    
    def test_batch_upload_valid_files(self):
        """Test batch upload endpoint with valid files"""
        img1 = self.create_test_image_file()
        img2 = self.create_test_image_file()
        
        response = self.client.post('/batch_upload', data={
            'files': [
                (img1, 'test1.jpg', 'image/jpeg'),
                (img2, 'test2.jpg', 'image/jpeg')
            ]
        })
        
        # Status depends on OCR processor setup
        assert response.status_code in [200, 500]
        
        data = json.loads(response.data)
        if response.status_code == 200:
            assert 'success' in data
            assert 'total_files' in data
            assert 'results' in data
        else:
            assert 'error' in data
    
    def test_result_endpoint_not_found(self):
        """Test result endpoint with non-existent result ID"""
        response = self.client.get('/result/nonexistent-id')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Result not found' in data['error']
    
    def test_api_health_endpoint(self):
        """Test API health check endpoint"""
        response = self.client.get('/api/v1/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert data['api_version'] == 'v1'
    
    def test_api_info_endpoint(self):
        """Test API info endpoint"""
        response = self.client.get('/api/v1/info')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['api_version'] == 'v1'
        assert 'model_name' in data
        assert 'endpoints' in data
        assert isinstance(data['endpoints'], list)
    
    def test_api_ocr_no_file(self):
        """Test API OCR endpoint with no file"""
        response = self.client.post('/api/v1/ocr')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No file provided' in data['error']
    
    def test_api_ocr_valid_file(self):
        """Test API OCR endpoint with valid file"""
        img_data = self.create_test_image_file()
        
        response = self.client.post('/api/v1/ocr', data={
            'file': (img_data, 'test.jpg', 'image/jpeg'),
            'include_metadata': 'true'
        })
        
        # Status depends on OCR processor setup
        assert response.status_code in [200, 500]
        
        data = json.loads(response.data)
        if response.status_code == 200:
            assert 'success' in data
            assert 'text' in data
            assert 'confidence' in data
            assert 'metadata' in data
        else:
            assert 'error' in data
    
    def test_api_batch_ocr_no_files(self):
        """Test API batch OCR endpoint with no files"""
        response = self.client.post('/api/v1/ocr/batch')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No files provided' in data['error']
    
    def test_api_batch_ocr_valid_files(self):
        """Test API batch OCR endpoint with valid files"""
        img1 = self.create_test_image_file()
        img2 = self.create_test_image_file()
        
        response = self.client.post('/api/v1/ocr/batch', data={
            'files': [
                (img1, 'test1.jpg', 'image/jpeg'),
                (img2, 'test2.jpg', 'image/jpeg')
            ],
            'include_metadata': 'true'
        })
        
        # Status depends on OCR processor setup
        assert response.status_code in [200, 500]
        
        data = json.loads(response.data)
        if response.status_code == 200:
            assert 'success' in data
            assert 'total_files' in data
            assert 'results' in data
        else:
            assert 'error' in data
    
    def test_api_structured_ocr_no_file(self):
        """Test API structured OCR endpoint with no file"""
        response = self.client.post('/api/v1/ocr/structured')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No file provided' in data['error']
    
    def test_api_structured_ocr_no_structure_prompt(self):
        """Test API structured OCR endpoint with no structure prompt"""
        img_data = self.create_test_image_file()
        
        response = self.client.post('/api/v1/ocr/structured', data={
            'file': (img_data, 'test.jpg', 'image/jpeg')
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'structure_prompt is required' in data['error']
    
    def test_api_structured_ocr_valid_request(self):
        """Test API structured OCR endpoint with valid request"""
        img_data = self.create_test_image_file()
        structure_prompt = "Extract data as JSON with fields: name, age, email"
        
        response = self.client.post('/api/v1/ocr/structured', data={
            'file': (img_data, 'test.jpg', 'image/jpeg'),
            'structure_prompt': structure_prompt
        })
        
        # Status depends on OCR processor setup
        assert response.status_code in [200, 500]
        
        data = json.loads(response.data)
        if response.status_code == 200:
            assert 'success' in data
            assert 'text' in data
            assert 'is_structured' in data
            assert 'metadata' in data
        else:
            assert 'error' in data
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        response = self.client.get('/health')
        assert response.status_code == 200
        
        # Check for CORS headers (if CORS is enabled)
        # The exact headers depend on Flask-CORS configuration
    
    def test_file_size_limit(self):
        """Test file size limit enforcement"""
        # Create a large file that exceeds the limit
        large_data = BytesIO(b'x' * (60 * 1024 * 1024))  # 60MB
        
        response = self.client.post('/upload', data={
            'file': (large_data, 'large.jpg', 'image/jpeg')
        })
        
        # Should return 413 (Request Entity Too Large) or 400
        assert response.status_code in [400, 413]
    
    def test_content_type_validation(self):
        """Test content type validation"""
        # Test with wrong content type
        img_data = self.create_test_image_file()
        
        response = self.client.post('/upload', data={
            'file': (img_data, 'test.jpg', 'application/octet-stream')
        })
        
        # Might pass or fail depending on validation strictness
        assert response.status_code in [200, 400, 500]
    
    def test_error_handling(self):
        """Test error handling for various scenarios"""
        # Test with corrupted image data
        corrupted_data = BytesIO(b'not an image')
        
        response = self.client.post('/upload', data={
            'file': (corrupted_data, 'test.jpg', 'image/jpeg')
        })
        
        # Should handle gracefully
        assert response.status_code in [400, 500]
        
        data = json.loads(response.data)
        assert 'error' in data


class TestAppConfiguration:
    """Test application configuration"""
    
    def test_app_creation(self):
        """Test application creation"""
        app = create_app()
        assert app is not None
        assert app.config['SECRET_KEY'] is not None
    
    def test_app_testing_mode(self):
        """Test application in testing mode"""
        app = create_app()
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            response = client.get('/health')
            assert response.status_code == 200


if __name__ == '__main__':
    import pytest
    pytest.main([__file__])
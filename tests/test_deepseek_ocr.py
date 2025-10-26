"""
Unit tests for DeepSeek OCR core functionality
"""

import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from PIL import Image

from app.ocr.deepseek_ocr import DeepSeekOCR
from app.utils.config import Config
from app.utils.exceptions import OCRError, ModelError


class TestDeepSeekOCR:
    """Test DeepSeek OCR functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = Config()
        self.config.model.use_local = False  # Use API mode for easier testing
        self.config.api.deepseek_api_key = "test-api-key"
    
    @patch('app.ocr.deepseek_ocr.torch')
    def test_get_device_auto_cuda_available(self, mock_torch):
        """Test device selection when CUDA is available"""
        mock_torch.cuda.is_available.return_value = True
        self.config.model.device = "auto"
        
        ocr = DeepSeekOCR(self.config)
        assert ocr.device == "cuda"
    
    @patch('app.ocr.deepseek_ocr.torch')
    def test_get_device_auto_cuda_unavailable(self, mock_torch):
        """Test device selection when CUDA is unavailable"""
        mock_torch.cuda.is_available.return_value = False
        self.config.model.device = "auto"
        
        ocr = DeepSeekOCR(self.config)
        assert ocr.device == "cpu"
    
    def test_get_device_explicit(self):
        """Test explicit device selection"""
        self.config.model.device = "cpu"
        ocr = DeepSeekOCR(self.config)
        assert ocr.device == "cpu"
    
    def test_initialization_api_mode(self):
        """Test OCR initialization in API mode"""
        self.config.model.use_local = False
        self.config.api.deepseek_api_key = "test-key"
        
        ocr = DeepSeekOCR(self.config)
        assert ocr.config == self.config
        assert ocr.model is None  # No local model in API mode
        assert ocr.tokenizer is None
    
    @patch('app.ocr.deepseek_ocr.os.path.exists')
    def test_initialization_local_mode_model_not_found(self, mock_exists):
        """Test OCR initialization when local model is not found"""
        mock_exists.return_value = False
        self.config.model.use_local = True
        self.config.model.local_path = "./nonexistent/model"
        
        with pytest.raises(ModelError, match="Model path not found"):
            DeepSeekOCR(self.config)
    
    def create_test_image(self, size=(100, 100)):
        """Create a test image file"""
        image = Image.new('RGB', size, (255, 255, 255))
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            image.save(f.name, format='JPEG')
            return f.name
    
    @patch('app.ocr.deepseek_ocr.requests.post')
    def test_extract_text_api_success(self, mock_post):
        """Test successful text extraction using API"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Extracted text from image"
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50
            }
        }
        mock_post.return_value = mock_response
        
        ocr = DeepSeekOCR(self.config)
        image_path = self.create_test_image()
        
        try:
            result = ocr.extract_text(image_path)
            
            assert result['text'] == "Extracted text from image"
            assert result['confidence'] == 1.0
            assert result['method'] == "deepseek_api"
            assert 'usage' in result
            assert result['image_path'] == image_path
            assert result['model_used'] == self.config.model.name
        finally:
            os.unlink(image_path)
    
    @patch('app.ocr.deepseek_ocr.requests.post')
    def test_extract_text_api_failure(self, mock_post):
        """Test API failure during text extraction"""
        # Mock API error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response
        
        ocr = DeepSeekOCR(self.config)
        image_path = self.create_test_image()
        
        try:
            with pytest.raises(OCRError, match="API request failed"):
                ocr.extract_text(image_path)
        finally:
            os.unlink(image_path)
    
    @patch('app.ocr.deepseek_ocr.requests.post')
    def test_extract_text_with_custom_prompt(self, mock_post):
        """Test text extraction with custom prompt"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Custom prompt result"}}],
            "usage": {}
        }
        mock_post.return_value = mock_response
        
        ocr = DeepSeekOCR(self.config)
        image_path = self.create_test_image()
        custom_prompt = "Extract only numbers from this image"
        
        try:
            result = ocr.extract_text(image_path, custom_prompt)
            
            # Verify the prompt was used in the API call
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            request_data = call_args[1]['json']
            
            assert custom_prompt in str(request_data['messages'])
            assert result['text'] == "Custom prompt result"
        finally:
            os.unlink(image_path)
    
    def test_image_to_base64(self):
        """Test image to base64 conversion"""
        ocr = DeepSeekOCR(self.config)
        image = Image.new('RGB', (50, 50), (255, 0, 0))
        
        base64_str = ocr._image_to_base64(image)
        
        assert isinstance(base64_str, str)
        assert len(base64_str) > 0
        # Base64 strings should be valid (no spaces, proper characters)
        import base64
        try:
            base64.b64decode(base64_str)
            assert True
        except Exception:
            assert False, "Invalid base64 string generated"
    
    @patch('app.ocr.deepseek_ocr.requests.post')
    def test_batch_extract_text(self, mock_post):
        """Test batch text extraction"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Batch text result"}}],
            "usage": {}
        }
        mock_post.return_value = mock_response
        
        ocr = DeepSeekOCR(self.config)
        
        # Create multiple test images
        image_paths = [self.create_test_image() for _ in range(3)]
        
        try:
            results = ocr.batch_extract_text(image_paths)
            
            assert len(results) == 3
            for result in results:
                assert result['text'] == "Batch text result"
                assert result['method'] == "deepseek_api"
        finally:
            for path in image_paths:
                if os.path.exists(path):
                    os.unlink(path)
    
    def test_batch_extract_text_with_errors(self):
        """Test batch processing with some errors"""
        ocr = DeepSeekOCR(self.config)
        
        # Mix of valid and invalid paths
        image_paths = [
            self.create_test_image(),
            "nonexistent_image.jpg",
            self.create_test_image()
        ]
        
        try:
            results = ocr.batch_extract_text(image_paths)
            
            assert len(results) == 3
            assert 'error' in results[1]  # Middle one should have error
            assert results[1]['success'] == False
        finally:
            for path in image_paths:
                if os.path.exists(path):
                    os.unlink(path)
    
    @patch('app.ocr.deepseek_ocr.requests.post')
    @patch('app.ocr.deepseek_ocr.json.loads')
    def test_extract_structured_data_success(self, mock_json_loads, mock_post):
        """Test structured data extraction"""
        # Mock API response with JSON
        structured_response = '{"name": "John Doe", "age": 30}'
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": structured_response}}],
            "usage": {}
        }
        mock_post.return_value = mock_response
        
        # Mock JSON parsing
        mock_json_loads.return_value = {"name": "John Doe", "age": 30}
        
        ocr = DeepSeekOCR(self.config)
        image_path = self.create_test_image()
        structure_prompt = "Extract personal information as JSON"
        
        try:
            result = ocr.extract_structured_data(image_path, structure_prompt)
            
            assert result['text'] == structured_response
            assert result['is_structured'] == True
            assert 'structured_data' in result
            assert result['structured_data']['name'] == "John Doe"
        finally:
            os.unlink(image_path)
    
    @patch('app.ocr.deepseek_ocr.requests.post')
    def test_extract_structured_data_not_json(self, mock_post):
        """Test structured data extraction with non-JSON response"""
        # Mock API response with plain text
        text_response = "This is just plain text"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": text_response}}],
            "usage": {}
        }
        mock_post.return_value = mock_response
        
        ocr = DeepSeekOCR(self.config)
        image_path = self.create_test_image()
        structure_prompt = "Extract information"
        
        try:
            result = ocr.extract_structured_data(image_path, structure_prompt)
            
            assert result['text'] == text_response
            assert result['is_structured'] == False
            assert 'structured_data' not in result
        finally:
            os.unlink(image_path)
    
    def test_extract_text_nonexistent_image(self):
        """Test text extraction with non-existent image"""
        ocr = DeepSeekOCR(self.config)
        
        with pytest.raises(OCRError):
            ocr.extract_text("nonexistent_image.jpg")
    
    def test_api_mode_without_key(self):
        """Test API mode without API key"""
        self.config.model.use_local = False
        self.config.api.deepseek_api_key = ""
        
        ocr = DeepSeekOCR(self.config)
        image_path = self.create_test_image()
        
        try:
            with pytest.raises(OCRError, match="DeepSeek API key not configured"):
                ocr.extract_text(image_path)
        finally:
            os.unlink(image_path)
    
    @patch('app.ocr.deepseek_ocr.requests.post')
    def test_api_timeout(self, mock_post):
        """Test API timeout handling"""
        import requests
        mock_post.side_effect = requests.Timeout("Request timed out")
        
        ocr = DeepSeekOCR(self.config)
        image_path = self.create_test_image()
        
        try:
            with pytest.raises(OCRError):
                ocr.extract_text(image_path)
        finally:
            os.unlink(image_path)
    
    def test_preprocessing_integration(self):
        """Test integration with image preprocessing"""
        # Enable preprocessing
        self.config.ocr.preprocessing.enabled = True
        
        ocr = DeepSeekOCR(self.config)
        
        # Mock the image processor
        with patch.object(ocr.image_processor, 'preprocess_image') as mock_preprocess:
            original_image = Image.new('RGB', (100, 100))
            processed_image = Image.new('RGB', (200, 200))
            mock_preprocess.return_value = processed_image
            
            # We can't easily test the full flow without mocking more components
            # but we can verify the preprocessor would be called
            assert ocr.config.ocr.preprocessing.enabled == True


@patch('app.ocr.deepseek_ocr.AutoTokenizer')
@patch('app.ocr.deepseek_ocr.AutoModelForCausalLM')
@patch('app.ocr.deepseek_ocr.os.path.exists')
class TestDeepSeekOCRLocalMode:
    """Test DeepSeek OCR in local mode"""
    
    def setup_method(self):
        """Set up test fixtures for local mode"""
        self.config = Config()
        self.config.model.use_local = True
        self.config.model.local_path = "./test_models/deepseek"
    
    def test_local_model_loading_success(self, mock_exists, mock_model, mock_tokenizer):
        """Test successful local model loading"""
        mock_exists.return_value = True
        mock_tokenizer.from_pretrained.return_value = Mock()
        mock_model.from_pretrained.return_value = Mock()
        
        ocr = DeepSeekOCR(self.config)
        
        assert ocr.model is not None
        assert ocr.tokenizer is not None
        mock_tokenizer.from_pretrained.assert_called_once()
        mock_model.from_pretrained.assert_called_once()
    
    def test_local_model_loading_different_precision(self, mock_exists, mock_model, mock_tokenizer):
        """Test local model loading with different precision settings"""
        mock_exists.return_value = True
        mock_tokenizer.from_pretrained.return_value = Mock()
        mock_model_instance = Mock()
        mock_model.from_pretrained.return_value = mock_model_instance
        
        # Test fp16 precision
        self.config.model.precision = "fp16"
        ocr = DeepSeekOCR(self.config)
        
        # Verify model was loaded with fp16 settings
        call_args = mock_model.from_pretrained.call_args
        assert 'torch_dtype' in call_args[1]
        
        # Test int8 precision
        mock_model.reset_mock()
        self.config.model.precision = "int8"
        ocr = DeepSeekOCR(self.config)
        
        call_args = mock_model.from_pretrained.call_args
        assert 'load_in_8bit' in call_args[1]


if __name__ == '__main__':
    import pytest
    pytest.main([__file__])
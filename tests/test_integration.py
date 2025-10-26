"""
Integration tests for the complete OCR pipeline
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock

from tests.utils.test_helpers import (
    test_helpers,
    image_helper, 
    APITestClient,
    performance_helper
)
from tests.data.test_data import SAMPLE_TEXTS, EXPECTED_RESULTS


class TestOCRPipeline:
    """Test complete OCR pipeline integration"""
    
    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = test_helpers.create_temp_dir()
        performance_helper.metrics.clear()
    
    def teardown_method(self):
        """Cleanup after each test"""
        test_helpers.cleanup_temp_dir(self.temp_dir)
    
    @pytest.mark.integration
    @patch('app.ocr.deepseek_ocr.AutoModelForCausalLM')
    @patch('app.ocr.deepseek_ocr.AutoProcessor')
    def test_end_to_end_ocr_processing(self, mock_processor, mock_model, test_app):
        """Test complete end-to-end OCR processing"""
        # Setup mocks
        mock_model.from_pretrained.return_value = Mock()
        mock_processor.from_pretrained.return_value = Mock()
        
        # Create test client
        client = APITestClient(test_app)
        
        # Create test image
        image_bytes = image_helper.create_test_image_bytes(300, 200)
        
        # Test OCR processing
        performance_helper.start_timer('ocr_processing')
        result, status = client.upload_image(
            image_bytes, 
            filename="test.jpg",
            extract_format="plain"
        )
        performance_helper.end_timer('ocr_processing')
        
        # Assertions
        assert status == 200
        assert 'text' in result
        assert 'confidence' in result
        assert 'processing_time' in result
        
        # Performance assertion
        performance_helper.assert_performance('ocr_processing', 30.0)
    
    @pytest.mark.integration
    @patch('app.ocr.deepseek_ocr.AutoModelForCausalLM')
    @patch('app.ocr.deepseek_ocr.AutoProcessor')
    def test_batch_processing_pipeline(self, mock_processor, mock_model, test_app):
        """Test batch processing pipeline"""
        # Setup mocks
        mock_model.from_pretrained.return_value = Mock()
        mock_processor.from_pretrained.return_value = Mock()
        
        client = APITestClient(test_app)
        
        # Create multiple test images
        images = [
            (image_helper.create_test_image_bytes(200, 150), f"test_{i}.jpg")
            for i in range(3)
        ]
        
        # Test batch processing
        performance_helper.start_timer('batch_processing')
        result, status = client.upload_multiple_images(images)
        performance_helper.end_timer('batch_processing')
        
        # Assertions
        assert status == 200
        assert 'results' in result
        assert len(result['results']) == 3
        
        for i, res in enumerate(result['results']):
            assert 'text' in res
            assert 'filename' in res
            assert res['filename'] == f"test_{i}.jpg"
    
    @pytest.mark.integration
    def test_error_handling_pipeline(self, test_app):
        """Test error handling in the pipeline"""
        client = APITestClient(test_app)
        
        # Test with invalid image
        invalid_data = b"not_an_image"
        result, status = client.upload_image(invalid_data, "invalid.txt")
        
        assert status == 400
        assert 'error' in result
    
    @pytest.mark.integration
    @patch('app.ocr.deepseek_ocr.AutoModelForCausalLM')
    def test_model_fallback_pipeline(self, mock_model, test_app):
        """Test model fallback mechanism"""
        # Make model loading fail
        mock_model.from_pretrained.side_effect = Exception("Model loading failed")
        
        client = APITestClient(test_app)
        image_bytes = image_helper.create_test_image_bytes()
        
        # This should still work with API fallback
        result, status = client.upload_image(image_bytes)
        
        # The exact behavior depends on fallback implementation
        # Either succeeds with API or fails gracefully
        assert status in [200, 503]  # Success or service unavailable
    
    @pytest.mark.integration
    @patch('app.ocr.deepseek_ocr.AutoModelForCausalLM')
    @patch('app.ocr.deepseek_ocr.AutoProcessor') 
    def test_structured_extraction_pipeline(self, mock_processor, mock_model, test_app):
        """Test structured data extraction pipeline"""
        # Setup mocks to return structured data
        mock_model_instance = Mock()
        mock_model_instance.generate.return_value = Mock()
        mock_model.from_pretrained.return_value = mock_model_instance
        mock_processor.from_pretrained.return_value = Mock()
        
        client = APITestClient(test_app)
        image_bytes = image_helper.create_test_image_bytes()
        
        result, status = client.upload_image(
            image_bytes,
            extract_format="structured"
        )
        
        assert status == 200
        # Structured format should include additional metadata
        assert 'text' in result
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_performance_under_load(self, test_app):
        """Test system performance under load"""
        client = APITestClient(test_app)
        
        # Create multiple test images
        images = [
            image_helper.create_test_image_bytes(100, 100)
            for _ in range(10)
        ]
        
        # Test concurrent processing
        performance_helper.start_timer('load_test')
        
        results = []
        for i, image_bytes in enumerate(images):
            result, status = client.upload_image(image_bytes, f"load_test_{i}.jpg")
            results.append((result, status))
        
        performance_helper.end_timer('load_test')
        
        # Assertions
        successful_results = [r for r, s in results if s == 200]
        assert len(successful_results) >= 8  # At least 80% success rate
        
        # Performance should be reasonable even under load
        performance_helper.assert_performance('load_test', 60.0)


class TestConfigurationIntegration:
    """Test configuration integration across components"""
    
    @pytest.mark.integration
    def test_config_propagation(self, test_app):
        """Test that configuration propagates correctly through all components"""
        from app.utils.config import get_config
        
        config = get_config()
        
        # Test that config is accessible
        assert config is not None
        assert hasattr(config, 'model')
        assert hasattr(config, 'server')
        assert hasattr(config, 'ocr')
    
    @pytest.mark.integration
    def test_environment_override(self, monkeypatch, test_app):
        """Test environment variable configuration override"""
        # Set environment variable
        monkeypatch.setenv('OCR_MAX_FILE_SIZE', '20971520')  # 20MB
        
        # Reload config (this depends on implementation)
        from app.utils.config import get_config
        config = get_config()
        
        # Verify override took effect
        assert config.ocr.max_file_size == 20971520


class TestHealthAndMonitoring:
    """Test health checks and monitoring integration"""
    
    @pytest.mark.integration
    def test_health_endpoint_comprehensive(self, test_app):
        """Test comprehensive health check"""
        client = APITestClient(test_app)
        
        result, status = client.get_health()
        
        assert status == 200
        assert 'status' in result
        assert 'components' in result
        
        # Check component health
        components = result['components']
        assert 'ocr_engine' in components
        assert 'file_system' in components
    
    @pytest.mark.integration
    def test_logging_integration(self, test_app, caplog):
        """Test logging integration across components"""
        client = APITestClient(test_app)
        
        # Make request that should generate logs
        image_bytes = image_helper.create_test_image_bytes()
        client.upload_image(image_bytes)
        
        # Check that logs were generated
        assert len(caplog.records) > 0
        
        # Check log levels and sources
        log_levels = [record.levelname for record in caplog.records]
        assert 'INFO' in log_levels


class TestSecurityIntegration:
    """Test security features integration"""
    
    @pytest.mark.integration
    def test_file_size_limits(self, test_app):
        """Test file size limit enforcement"""
        client = APITestClient(test_app)
        
        # Create oversized file
        large_image = image_helper.create_large_image_bytes(15)  # 15MB
        
        result, status = client.upload_image(large_image, "large.jpg")
        
        assert status == 400
        assert 'error' in result
        assert 'size' in result['error'].lower()
    
    @pytest.mark.integration
    def test_file_type_validation(self, test_app):
        """Test file type validation"""
        client = APITestClient(test_app)
        
        # Try to upload non-image file
        text_data = b"This is not an image"
        result, status = client.upload_image(text_data, "malicious.exe")
        
        assert status == 400
        assert 'error' in result
    
    @pytest.mark.integration
    def test_input_sanitization(self, test_app):
        """Test input sanitization"""
        client = APITestClient(test_app)
        
        # Try to upload with malicious filename
        image_bytes = image_helper.create_test_image_bytes()
        result, status = client.upload_image(
            image_bytes, 
            "../../../etc/passwd"
        )
        
        # Should either sanitize filename or reject
        if status == 200:
            # If accepted, filename should be sanitized
            assert 'filename' in result
            assert '../' not in result.get('filename', '')
        else:
            # If rejected, should be 400
            assert status == 400


class TestRecoveryAndResilience:
    """Test system recovery and resilience"""
    
    @pytest.mark.integration
    def test_graceful_degradation(self, test_app):
        """Test graceful degradation when components fail"""
        # This test would mock component failures and verify 
        # the system continues to operate in degraded mode
        pass
    
    @pytest.mark.integration
    def test_resource_cleanup(self, test_app):
        """Test that resources are properly cleaned up"""
        client = APITestClient(test_app)
        
        # Process multiple images
        for i in range(5):
            image_bytes = image_helper.create_test_image_bytes()
            client.upload_image(image_bytes, f"cleanup_test_{i}.jpg")
        
        # Verify no resource leaks (implementation specific)
        # This would check memory usage, file handles, etc.
        pass
"""
Unit tests for image processing utilities
"""

import os
import tempfile
import numpy as np
from PIL import Image
from unittest.mock import patch, Mock

from app.utils.image_processor import ImageProcessor
from app.utils.config import Config
from app.utils.exceptions import ImageProcessingError


class TestImageProcessor:
    """Test image processing functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = Config()
        self.processor = ImageProcessor(self.config)
    
    def create_test_image(self, size=(100, 100), color='RGB'):
        """Create a test image"""
        image = Image.new(color, size, (255, 255, 255))
        return image
    
    def test_image_processor_initialization(self):
        """Test image processor initialization"""
        assert self.processor.config == self.config
        assert self.processor.max_size == self.config.ocr.max_image_size
    
    def test_load_image_success(self):
        """Test successful image loading"""
        # Create temporary image file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            image = self.create_test_image((200, 200))
            image.save(f.name, format='JPEG')
            temp_path = f.name
        
        try:
            loaded_image = self.processor.load_image(temp_path)
            assert isinstance(loaded_image, Image.Image)
            assert loaded_image.mode == 'RGB'
            assert loaded_image.size == (200, 200)
        finally:
            os.unlink(temp_path)
    
    def test_load_image_nonexistent_file(self):
        """Test loading non-existent image file"""
        with pytest.raises(ImageProcessingError, match="Image file not found"):
            self.processor.load_image("nonexistent.jpg")
    
    def test_load_image_resize_large(self):
        """Test automatic resizing of large images"""
        # Create large image
        large_size = (5000, 5000)
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            image = self.create_test_image(large_size)
            image.save(f.name, format='JPEG')
            temp_path = f.name
        
        try:
            loaded_image = self.processor.load_image(temp_path)
            # Should be resized to max_size
            assert max(loaded_image.size) == self.config.ocr.max_image_size
        finally:
            os.unlink(temp_path)
    
    def test_resize_image(self):
        """Test image resizing functionality"""
        image = self.create_test_image((1000, 800))
        resized = self.processor._resize_image(image, 500)
        
        # Should maintain aspect ratio
        assert max(resized.size) == 500
        assert resized.size[0] == 500  # Width should be the larger dimension
        assert resized.size[1] == 400  # Height should be proportional
    
    def test_resize_image_already_small(self):
        """Test resizing image that's already smaller than max size"""
        image = self.create_test_image((200, 150))
        resized = self.processor._resize_image(image, 500)
        
        # Should remain unchanged
        assert resized.size == (200, 150)
    
    def test_optimize_size(self):
        """Test size optimization for small images"""
        small_image = self.create_test_image((50, 50))
        optimized = self.processor._optimize_size(small_image)
        
        # Should be upscaled
        assert max(optimized.size) >= 1000
    
    def test_preprocess_image_enabled(self):
        """Test image preprocessing when enabled"""
        image = self.create_test_image((500, 400))
        
        # Mock the individual preprocessing methods
        with patch.object(self.processor, '_optimize_size', return_value=image) as mock_resize, \
             patch.object(self.processor, '_enhance_contrast', return_value=image) as mock_contrast, \
             patch.object(self.processor, '_denoise_image', return_value=image) as mock_denoise:
            
            processed = self.processor.preprocess_image(image)
            
            # All preprocessing steps should be called when enabled
            mock_resize.assert_called_once()
            mock_contrast.assert_called_once()
            mock_denoise.assert_called_once()
            assert processed == image
    
    def test_preprocess_image_disabled(self):
        """Test image preprocessing when disabled"""
        # Disable preprocessing
        self.config.ocr.preprocessing.enabled = False
        processor = ImageProcessor(self.config)
        
        image = self.create_test_image((500, 400))
        processed = processor.preprocess_image(image)
        
        # Should return original image when preprocessing disabled
        assert processed == image
    
    @patch('cv2.cvtColor')
    @patch('cv2.createCLAHE')
    def test_enhance_contrast(self, mock_clahe, mock_cvt):
        """Test contrast enhancement"""
        image = self.create_test_image((100, 100))
        
        # Mock OpenCV operations
        mock_lab = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_cvt.return_value = mock_lab
        mock_clahe_obj = Mock()
        mock_clahe_obj.apply.return_value = np.zeros((100, 100), dtype=np.uint8)
        mock_clahe.return_value = mock_clahe_obj
        
        try:
            enhanced = self.processor._enhance_contrast(image)
            assert isinstance(enhanced, Image.Image)
        except Exception:
            # If OpenCV is not available, should return original image
            enhanced = self.processor._enhance_contrast(image)
            assert enhanced == image
    
    @patch('cv2.fastNlMeansDenoisingColored')
    def test_denoise_image(self, mock_denoise):
        """Test image denoising"""
        image = self.create_test_image((100, 100))
        
        # Mock OpenCV denoising
        mock_denoise.return_value = np.array(image)
        
        try:
            denoised = self.processor._denoise_image(image)
            assert isinstance(denoised, Image.Image)
        except Exception:
            # If OpenCV is not available, should return original image
            denoised = self.processor._denoise_image(image)
            assert denoised == image
    
    def test_detect_text_regions(self):
        """Test text region detection"""
        image = self.create_test_image((200, 200))
        
        try:
            regions = self.processor.detect_text_regions(image)
            assert isinstance(regions, list)
            # Each region should be a tuple of coordinates
            for region in regions:
                assert len(region) == 4  # (x1, y1, x2, y2)
        except Exception:
            # If OpenCV is not available, should return empty list
            regions = self.processor.detect_text_regions(image)
            assert regions == []
    
    def test_crop_text_regions(self):
        """Test cropping text regions from image"""
        image = self.create_test_image((200, 200))
        regions = [(10, 10, 50, 50), (100, 100, 150, 150)]
        
        cropped = self.processor.crop_text_regions(image, regions)
        
        assert len(cropped) == 2
        for i, crop_data in enumerate(cropped):
            assert 'image' in crop_data
            assert 'bbox' in crop_data
            assert 'region_id' in crop_data
            assert isinstance(crop_data['image'], Image.Image)
            assert crop_data['bbox'] == regions[i]
            assert crop_data['region_id'] == i
    
    def test_save_processed_image(self):
        """Test saving processed image"""
        image = self.create_test_image((100, 100))
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            temp_path = f.name
        
        try:
            # Remove the file so we can test creation
            os.unlink(temp_path)
            
            success = self.processor.save_processed_image(image, temp_path)
            assert success == True
            assert os.path.exists(temp_path)
            
            # Verify saved image
            saved_image = Image.open(temp_path)
            assert saved_image.size == image.size
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_save_processed_image_invalid_path(self):
        """Test saving image to invalid path"""
        image = self.create_test_image((100, 100))
        
        # Try to save to invalid path
        success = self.processor.save_processed_image(image, "/invalid/path/image.jpg")
        assert success == False
    
    def test_convert_modes(self):
        """Test image mode conversions"""
        # Test RGBA to RGB conversion
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            rgba_image = Image.new('RGBA', (100, 100), (255, 255, 255, 128))
            rgba_image.save(f.name, format='PNG')
            temp_path = f.name
        
        try:
            loaded_image = self.processor.load_image(temp_path)
            assert loaded_image.mode == 'RGB'
        finally:
            os.unlink(temp_path)
    
    def test_preprocessing_error_handling(self):
        """Test error handling in preprocessing"""
        image = self.create_test_image((100, 100))
        
        # Test with mock that raises exception
        with patch.object(self.processor, '_enhance_contrast', side_effect=Exception("Test error")):
            # Should not raise exception, but continue processing
            processed = self.processor.preprocess_image(image)
            assert isinstance(processed, Image.Image)


if __name__ == '__main__':
    import pytest
    pytest.main([__file__])
"""
Image preprocessing utilities for OCR
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from typing import Tuple, Optional
import os
from loguru import logger

from ..utils.exceptions import ImageProcessingError


class ImageProcessor:
    """Handles image preprocessing for better OCR results"""
    
    def __init__(self, config):
        self.config = config
        self.max_size = config.ocr.max_image_size
    
    def load_image(self, image_path: str) -> Image.Image:
        """
        Load an image from file path
        
        Args:
            image_path: Path to the image file
            
        Returns:
            PIL Image object
        """
        try:
            if not os.path.exists(image_path):
                raise ImageProcessingError(f"Image file not found: {image_path}")
            
            image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large
            if max(image.size) > self.max_size:
                image = self._resize_image(image, self.max_size)
            
            logger.info(f"Loaded image: {image_path}, size: {image.size}")
            return image
            
        except Exception as e:
            logger.error(f"Failed to load image {image_path}: {e}")
            raise ImageProcessingError(f"Image loading failed: {e}")
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Apply preprocessing to improve OCR accuracy
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed PIL Image object
        """
        try:
            processed_image = image.copy()
            
            # Apply preprocessing steps if enabled
            if self.config.ocr.preprocessing.resize:
                processed_image = self._optimize_size(processed_image)
            
            if self.config.ocr.preprocessing.enhance_contrast:
                processed_image = self._enhance_contrast(processed_image)
            
            if self.config.ocr.preprocessing.denoise:
                processed_image = self._denoise_image(processed_image)
            
            logger.info("Image preprocessing completed")
            return processed_image
            
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            raise ImageProcessingError(f"Preprocessing failed: {e}")
    
    def _resize_image(self, image: Image.Image, max_size: int) -> Image.Image:
        """Resize image while maintaining aspect ratio"""
        width, height = image.size
        
        if max(width, height) <= max_size:
            return image
        
        if width > height:
            new_width = max_size
            new_height = int((height * max_size) / width)
        else:
            new_height = max_size
            new_width = int((width * max_size) / height)
        
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def _optimize_size(self, image: Image.Image) -> Image.Image:
        """Optimize image size for OCR"""
        width, height = image.size
        
        # Ensure minimum size for small text
        min_size = 1000
        if max(width, height) < min_size:
            scale_factor = min_size / max(width, height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        return image
    
    def _enhance_contrast(self, image: Image.Image) -> Image.Image:
        """Enhance image contrast for better text recognition"""
        try:
            # Convert to numpy array for OpenCV processing
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            lab = cv2.cvtColor(cv_image, cv2.COLOR_BGR2LAB)
            l_channel, a, b = cv2.split(lab)
            
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            cl = clahe.apply(l_channel)
            
            enhanced = cv2.merge((cl, a, b))
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB)
            
            return Image.fromarray(enhanced)
            
        except Exception as e:
            logger.warning(f"Contrast enhancement failed, using original: {e}")
            return image
    
    def _denoise_image(self, image: Image.Image) -> Image.Image:
        """Remove noise from image"""
        try:
            # Convert to numpy array
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Apply non-local means denoising
            denoised = cv2.fastNlMeansDenoisingColored(cv_image, None, 10, 10, 7, 21)
            denoised_rgb = cv2.cvtColor(denoised, cv2.COLOR_BGR2RGB)
            
            return Image.fromarray(denoised_rgb)
            
        except Exception as e:
            logger.warning(f"Denoising failed, using original: {e}")
            return image
    
    def detect_text_regions(self, image: Image.Image) -> list:
        """
        Detect text regions in the image
        
        Args:
            image: PIL Image object
            
        Returns:
            List of bounding boxes for text regions
        """
        try:
            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Use EAST text detector or similar
            # This is a simplified version - you might want to use more sophisticated methods
            
            # Apply morphological operations to find text regions
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            grad = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, kernel)
            
            # Apply threshold
            _, bw = cv2.threshold(grad, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            
            # Connect horizontally oriented regions
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 1))
            connected = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, kernel)
            
            # Find contours
            contours, _ = cv2.findContours(connected, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter and return bounding boxes
            text_regions = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                if w > 10 and h > 10:  # Filter small regions
                    text_regions.append((x, y, x + w, y + h))
            
            return text_regions
            
        except Exception as e:
            logger.error(f"Text region detection failed: {e}")
            return []
    
    def crop_text_regions(self, image: Image.Image, regions: list) -> list:
        """
        Crop text regions from image
        
        Args:
            image: PIL Image object
            regions: List of bounding boxes
            
        Returns:
            List of cropped image regions
        """
        cropped_regions = []
        
        for i, (x1, y1, x2, y2) in enumerate(regions):
            try:
                cropped = image.crop((x1, y1, x2, y2))
                cropped_regions.append({
                    'image': cropped,
                    'bbox': (x1, y1, x2, y2),
                    'region_id': i
                })
            except Exception as e:
                logger.warning(f"Failed to crop region {i}: {e}")
        
        return cropped_regions
    
    def save_processed_image(self, image: Image.Image, output_path: str) -> bool:
        """
        Save processed image to file
        
        Args:
            image: PIL Image object
            output_path: Path to save the image
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            image.save(output_path, format='JPEG', quality=95)
            logger.info(f"Processed image saved: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save processed image: {e}")
            return False
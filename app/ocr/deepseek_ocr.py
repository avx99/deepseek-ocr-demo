"""
DeepSeek OCR Core Module
Handles OCR processing using DeepSeek Vision-Language models
"""

import os
import sys
import io
import base64
import torch
from PIL import Image
from typing import List, Dict, Optional, Union, Tuple
from transformers import AutoTokenizer, AutoModelForCausalLM
import cv2
import numpy as np
from loguru import logger
import requests
import json

# Add the project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.utils.config import Config
from app.utils.image_processor import ImageProcessor
from app.utils.exceptions import OCRError, ModelError


class DeepSeekOCR:
    """Main OCR processor using DeepSeek Vision-Language model"""
    
    def __init__(self, config: Config):
        self.config = config
        self.model = None
        self.tokenizer = None
        self.device = self._get_device()
        self.image_processor = ImageProcessor(config)
        self._initialize_model()
    
    def _get_device(self) -> str:
        """Determine the best device for model inference"""
        if self.config.model.device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            else:
                return "cpu"
        return self.config.model.device
    
    def _initialize_model(self):
        """Initialize the DeepSeek model and tokenizer"""
        try:
            if self.config.model.use_local:
                try:
                    self._load_local_model()
                except ModelError as e:
                    logger.warning(f"Local model loading failed: {e}")
                    logger.info("Attempting to fall back to API mode...")
                    
                    # Check if we have API credentials
                    if self.config.api.deepseek_api_key:
                        logger.info("API key found, switching to API mode")
                        self.config.model.use_local = False
                    else:
                        logger.warning("No API key configured, will use demo mode")
                        self.config.model.use_local = False
            else:
                logger.info("Using DeepSeek API for OCR processing")
        except Exception as e:
            logger.error(f"Failed to initialize model: {e}")
            # Don't raise error, allow application to start in demo mode
            logger.warning("Model initialization failed, running in demo mode")
            self.config.model.use_local = False
    
    def _load_local_model(self):
        """Load the local DeepSeek model"""
        try:
            model_path = self.config.model.local_path
            if not os.path.exists(model_path):
                raise ModelError(f"Model path not found: {model_path}")
            
            logger.info(f"Loading DeepSeek model from {model_path}")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_path,
                trust_remote_code=True
            )
            
            # Load model with appropriate precision
            if self.config.model.precision == "fp16":
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    trust_remote_code=True
                )
            elif self.config.model.precision == "int8":
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    load_in_8bit=True,
                    device_map="auto",
                    trust_remote_code=True
                )
            else:
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    device_map="auto",
                    trust_remote_code=True
                )
            
            self.model.eval()
            logger.info("DeepSeek model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load local model: {e}")
            raise ModelError(f"Local model loading failed: {e}")
    
    def extract_text(self, image_path: str, prompt: Optional[str] = None) -> Dict[str, any]:
        """
        Extract text from an image using DeepSeek OCR
        
        Args:
            image_path: Path to the image file
            prompt: Optional custom prompt for OCR
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        try:
            # Load and preprocess image
            image = self.image_processor.load_image(image_path)
            
            # Preprocess if enabled
            if self.config.ocr.preprocessing.enabled:
                image = self.image_processor.preprocess_image(image)
            
            # Extract text using the appropriate method
            if self.config.model.use_local and self.model and self.tokenizer:
                result = self._extract_text_local(image, prompt)
            elif not self.config.model.use_local and self.config.api.deepseek_api_key:
                # Try API first, but fall back to alternative OCR if API doesn't support vision
                try:
                    result = self._extract_text_api(image, prompt)
                    # If API returns limitation notice, try fallback OCR
                    if result.get("method") == "api_limitation":
                        logger.info("API doesn't support vision, trying fallback OCR...")
                        result = self._extract_text_fallback(image, prompt)
                except Exception as e:
                    logger.warning(f"API failed, trying fallback OCR: {e}")
                    result = self._extract_text_fallback(image, prompt)
            else:
                # Try fallback OCR engines
                result = self._extract_text_fallback(image, prompt)
            
            # Add metadata
            result.update({
                "image_path": image_path,
                "image_size": image.size,
                "model_used": self.config.model.name,
                "processing_method": "local" if self.config.model.use_local else "api"
            })
            
            return result
            
        except Exception as e:
            logger.error(f"OCR extraction failed for {image_path}: {e}")
            raise OCRError(f"Text extraction failed: {e}")
    
    def _extract_text_local(self, image: Image.Image, prompt: Optional[str] = None) -> Dict[str, any]:
        """Extract text using local DeepSeek model"""
        try:
            if not self.model or not self.tokenizer:
                raise ModelError("Local model not initialized")
            
            # Default OCR prompt
            if prompt is None:
                prompt = "Extract all text from this image. Provide the text exactly as it appears, maintaining formatting and structure."
            
            # Convert image to base64 for model input
            image_b64 = self._image_to_base64(image)
            
            # Prepare conversation
            conversation = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image_b64},
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
            
            # Generate response
            inputs = self.tokenizer.apply_chat_template(
                conversation,
                add_generation_prompt=True,
                tokenize=True,
                return_tensors="pt"
            ).to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_new_tokens=self.config.model.max_length,
                    temperature=self.config.model.temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode response
            response = self.tokenizer.decode(
                outputs[0][len(inputs[0]):], 
                skip_special_tokens=True
            )
            
            return {
                "text": response.strip(),
                "confidence": 1.0,  # DeepSeek doesn't provide confidence scores
                "method": "deepseek_local"
            }
            
        except Exception as e:
            logger.error(f"Local OCR processing failed: {e}")
            raise OCRError(f"Local OCR processing failed: {e}")
    
    def _extract_text_demo(self, image: Image.Image, prompt: Optional[str] = None) -> Dict[str, any]:
        """Demo mode - return sample text when no model/API is available"""
        try:
            logger.warning("Running in demo mode - no model or API available")
            
            # Simulate some basic image analysis
            width, height = image.size
            mode = image.mode
            
            demo_text = f"""OCR Processing Failed
            
All OCR methods were attempted but none could extract text from this image.

Image Details:
- Dimensions: {width} x {height} pixels
- Color mode: {mode}
- Format: {image.format or 'Unknown'}

Attempted Methods:
1. ✗ DeepSeek API (not supported yet)
2. ✗ EasyOCR (no text found with sufficient confidence)
3. ✗ Tesseract (no text detected or not installed)

Possible reasons:
- Image may not contain readable text
- Text might be too small, blurry, or in a complex layout
- Handwritten text is harder to recognize
- Image quality might be too low

Suggestions:
- Try a clearer, higher resolution image
- Ensure text is clearly visible and readable
- Use images with printed (not handwritten) text
- Check if the image actually contains text"""
            
            return {
                "text": demo_text.strip(),
                "confidence": 0.0,  # No confidence in demo mode
                "method": "demo_mode",
                "warning": "Demo mode active - please configure model or API for real OCR"
            }
            
        except Exception as e:
            logger.error(f"Demo mode processing failed: {e}")
            raise OCRError(f"Demo mode processing failed: {e}")
    
    def _extract_text_api(self, image: Image.Image, prompt: Optional[str] = None) -> Dict[str, any]:
        """Extract text using DeepSeek API - Note: DeepSeek may not support vision API"""
        try:
            if not self.config.api.deepseek_api_key:
                raise OCRError("DeepSeek API key not configured")
            
            # Default OCR prompt
            if prompt is None:
                prompt = "Extract all text from this image. Provide the text exactly as it appears, maintaining formatting and structure."
            
            # Note: DeepSeek's current API may not support vision/image inputs
            # This is a limitation of their current API offering
            logger.warning("DeepSeek API may not support image processing yet")
            
            return {
                "text": f"""API Limitation Notice:

DeepSeek's current API does not support image processing/vision capabilities yet.

To use OCR functionality, you have these options:

1. **Use Local Model** (Recommended):
   - Download the DeepSeek-VL model
   - Set USE_LOCAL_MODEL=true in your .env file
   - Requires ~14GB of disk space and GPU/CPU resources

2. **Use Alternative OCR**:
   - Install EasyOCR: pip install easyocr
   - Or use Tesseract OCR for basic text extraction

3. **Wait for API Update**:
   - DeepSeek may add vision capabilities to their API in the future

For now, the application is running in demonstration mode.
Your image was uploaded successfully but cannot be processed via API.

Original prompt: {prompt}
Image size: {image.size}
Image mode: {image.mode}""",
                "confidence": 0.0,
                "method": "api_limitation",
                "warning": "DeepSeek API does not currently support image processing"
            }
            
        except Exception as e:
            logger.error(f"API OCR processing failed: {e}")
            return {
                "text": f"API Error: {str(e)}\n\nPlease use local model for image processing.",
                "confidence": 0.0,
                "method": "api_error",
                "error": str(e)
            }
    
    def _extract_text_fallback(self, image: Image.Image, prompt: Optional[str] = None) -> Dict[str, any]:
        """Fallback OCR using alternative engines (EasyOCR, Tesseract, etc.)"""
        try:
            logger.info("Attempting fallback OCR methods")
            
            # Try EasyOCR first
            try:
                logger.info("Trying EasyOCR...")
                import easyocr
                
                # Initialize reader (this might take a moment on first run)
                reader = easyocr.Reader(['en'], verbose=False)
                
                # Convert PIL image to numpy array
                import numpy as np
                image_np = np.array(image)
                
                # Perform OCR
                results = reader.readtext(image_np, detail=1)
                
                # Extract text from results with confidence filtering
                text_parts = []
                total_confidence = 0
                valid_results = 0
                
                for bbox, text, confidence in results:
                    if confidence > 0.3:  # Lower threshold for better text detection
                        text_parts.append(text)
                        total_confidence += confidence
                        valid_results += 1
                
                if text_parts:
                    extracted_text = '\n'.join(text_parts)
                    avg_confidence = total_confidence / valid_results if valid_results > 0 else 0
                    
                    logger.info(f"EasyOCR extracted {len(text_parts)} text segments with avg confidence {avg_confidence:.2f}")
                    
                    return {
                        "text": extracted_text.strip(),
                        "confidence": round(avg_confidence, 2),
                        "method": "easyocr_fallback",
                        "note": f"Using EasyOCR - extracted {len(text_parts)} text segments",
                        "segments_found": len(text_parts)
                    }
                else:
                    logger.warning("EasyOCR found no text with sufficient confidence")
                    
            except ImportError:
                logger.info("EasyOCR not available, trying next fallback")
            except Exception as e:
                logger.warning(f"EasyOCR failed: {e}")
            
            # Try Tesseract OCR
            try:
                logger.info("Trying Tesseract OCR...")
                import pytesseract
                
                # Extract text using Tesseract
                extracted_text = pytesseract.image_to_string(image, config='--psm 6')
                
                if extracted_text.strip():
                    logger.info(f"Tesseract extracted {len(extracted_text.strip())} characters")
                    
                    return {
                        "text": extracted_text.strip(),
                        "confidence": 0.7,
                        "method": "tesseract_fallback", 
                        "note": "Using Tesseract as fallback OCR engine",
                        "character_count": len(extracted_text.strip())
                    }
                else:
                    logger.warning("Tesseract found no text")
                    
            except ImportError:
                logger.info("Tesseract not available")
            except Exception as e:
                logger.warning(f"Tesseract failed: {e}")
            
            # If all OCR methods fail, return demo mode with helpful info
            logger.warning("All OCR methods failed, returning demo mode")
            return self._extract_text_demo(image, prompt)
            
        except Exception as e:
            logger.error(f"Fallback OCR processing failed: {e}")
            return self._extract_text_demo(image, prompt)
            
        except Exception as e:
            logger.error(f"Fallback OCR processing failed: {e}")
            return self._extract_text_demo(image, prompt)
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string"""
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        image_b64 = base64.b64encode(buffer.getvalue()).decode()
        return image_b64
    
    def batch_extract_text(self, image_paths: List[str], prompt: Optional[str] = None) -> List[Dict[str, any]]:
        """
        Extract text from multiple images
        
        Args:
            image_paths: List of image file paths
            prompt: Optional custom prompt for OCR
            
        Returns:
            List of dictionaries containing extracted text and metadata
        """
        results = []
        
        for image_path in image_paths:
            try:
                result = self.extract_text(image_path, prompt)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {image_path}: {e}")
                results.append({
                    "image_path": image_path,
                    "text": "",
                    "error": str(e),
                    "success": False
                })
        
        return results
    
    def extract_structured_data(self, image_path: str, structure_prompt: str) -> Dict[str, any]:
        """
        Extract structured data from an image
        
        Args:
            image_path: Path to the image file
            structure_prompt: Prompt describing the desired structure
            
        Returns:
            Dictionary containing structured data
        """
        try:
            result = self.extract_text(image_path, structure_prompt)
            
            # Try to parse as JSON if the response looks structured
            text = result["text"]
            try:
                if text.strip().startswith('{') and text.strip().endswith('}'):
                    structured_data = json.loads(text)
                    result["structured_data"] = structured_data
                    result["is_structured"] = True
                else:
                    result["is_structured"] = False
            except json.JSONDecodeError:
                result["is_structured"] = False
            
            return result
            
        except Exception as e:
            logger.error(f"Structured data extraction failed: {e}")
            raise OCRError(f"Structured extraction failed: {e}")
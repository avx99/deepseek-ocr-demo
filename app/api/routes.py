"""
API routes for DeepSeek OCR
"""

import os
import sys
import uuid
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import traceback

# Add the project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.utils.logger import get_logger
from app.utils.validation import InputValidator
from app.utils.exceptions import OCRError, ValidationError


def create_api_blueprint(ocr_processor, file_validator, config):
    """Create API blueprint with OCR endpoints"""
    
    api = Blueprint('api', __name__)
    logger = get_logger(__name__)
    
    @api.route('/ocr', methods=['POST'])
    def api_ocr():
        """API endpoint for single image OCR"""
        try:
            # Check if file is present
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Validate file
            file_validator.validate_file(file)
            
            # Get optional parameters
            prompt = request.form.get('prompt', '')
            if prompt:
                prompt = InputValidator.validate_prompt(prompt)
            
            return_metadata = request.form.get('include_metadata', 'false').lower() == 'true'
            
            # Save uploaded file temporarily
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(config.upload.upload_folder, unique_filename)
            file.save(file_path)
            
            try:
                # Process OCR
                result = ocr_processor.extract_text(file_path, prompt)
                
                response_data = {
                    'success': True,
                    'text': result['text'],
                    'confidence': result.get('confidence', 1.0)
                }
                
                if return_metadata:
                    response_data['metadata'] = {
                        'filename': filename,
                        'image_size': result.get('image_size'),
                        'model_used': result.get('model_used'),
                        'processing_method': result.get('processing_method'),
                        'timestamp': datetime.now().isoformat()
                    }
                
                logger.info(f"API OCR completed for {filename}")
                return jsonify(response_data)
                
            finally:
                # Cleanup uploaded file
                if os.path.exists(file_path):
                    os.remove(file_path)
            
        except ValidationError as e:
            logger.warning(f"API validation error: {e}")
            return jsonify({'error': str(e)}), 400
        except OCRError as e:
            logger.error(f"API OCR error: {e}")
            return jsonify({'error': str(e)}), 500
        except Exception as e:
            logger.error(f"API unexpected error: {e}")
            logger.error(traceback.format_exc())
            return jsonify({'error': 'Internal server error'}), 500
    
    @api.route('/ocr/batch', methods=['POST'])
    def api_batch_ocr():
        """API endpoint for batch OCR processing"""
        try:
            files = request.files.getlist('files')
            if not files:
                return jsonify({'error': 'No files provided'}), 400
            
            # Validate batch size
            max_batch = config.performance.batch_size
            InputValidator.validate_batch_size(len(files), max_batch)
            
            # Get optional parameters
            prompt = request.form.get('prompt', '')
            if prompt:
                prompt = InputValidator.validate_prompt(prompt)
            
            return_metadata = request.form.get('include_metadata', 'false').lower() == 'true'
            
            results = []
            file_paths = []
            
            # Save and validate files
            for file in files:
                try:
                    if file.filename == '':
                        continue
                    
                    file_validator.validate_file(file)
                    
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    file_path = os.path.join(config.upload.upload_folder, unique_filename)
                    file.save(file_path)
                    file_paths.append((file_path, filename))
                    
                except Exception as e:
                    results.append({
                        'filename': file.filename,
                        'success': False,
                        'error': str(e)
                    })
            
            try:
                # Process OCR for valid files
                if file_paths:
                    paths_only = [fp[0] for fp in file_paths]
                    ocr_results = ocr_processor.batch_extract_text(paths_only, prompt)
                    
                    for i, ocr_result in enumerate(ocr_results):
                        _, filename = file_paths[i]
                        
                        if 'error' in ocr_result:
                            results.append({
                                'filename': filename,
                                'success': False,
                                'error': ocr_result['error']
                            })
                        else:
                            result_data = {
                                'filename': filename,
                                'success': True,
                                'text': ocr_result['text'],
                                'confidence': ocr_result.get('confidence', 1.0)
                            }
                            
                            if return_metadata:
                                result_data['metadata'] = {
                                    'image_size': ocr_result.get('image_size'),
                                    'model_used': ocr_result.get('model_used'),
                                    'processing_method': ocr_result.get('processing_method'),
                                    'timestamp': datetime.now().isoformat()
                                }
                            
                            results.append(result_data)
                
                response_data = {
                    'success': True,
                    'total_files': len(files),
                    'processed_files': len([r for r in results if r['success']]),
                    'failed_files': len([r for r in results if not r['success']]),
                    'results': results
                }
                
                logger.info(f"API batch processing completed: {len(results)} files")
                return jsonify(response_data)
                
            finally:
                # Cleanup uploaded files
                for file_path, _ in file_paths:
                    if os.path.exists(file_path):
                        os.remove(file_path)
            
        except ValidationError as e:
            logger.warning(f"API batch validation error: {e}")
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"API batch processing error: {e}")
            logger.error(traceback.format_exc())
            return jsonify({'error': 'Internal server error'}), 500
    
    @api.route('/ocr/structured', methods=['POST'])
    def api_structured_ocr():
        """API endpoint for structured data extraction"""
        try:
            # Check if file is present
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Validate file
            file_validator.validate_file(file)
            
            # Get structure prompt (required for this endpoint)
            structure_prompt = request.form.get('structure_prompt', '')
            if not structure_prompt:
                return jsonify({'error': 'structure_prompt is required'}), 400
            
            structure_prompt = InputValidator.validate_prompt(structure_prompt, 2000)
            
            # Save uploaded file temporarily
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(config.upload.upload_folder, unique_filename)
            file.save(file_path)
            
            try:
                # Process structured OCR
                result = ocr_processor.extract_structured_data(file_path, structure_prompt)
                
                response_data = {
                    'success': True,
                    'text': result['text'],
                    'is_structured': result.get('is_structured', False),
                    'confidence': result.get('confidence', 1.0)
                }
                
                if result.get('is_structured') and 'structured_data' in result:
                    response_data['structured_data'] = result['structured_data']
                
                response_data['metadata'] = {
                    'filename': filename,
                    'image_size': result.get('image_size'),
                    'model_used': result.get('model_used'),
                    'processing_method': result.get('processing_method'),
                    'timestamp': datetime.now().isoformat()
                }
                
                logger.info(f"API structured OCR completed for {filename}")
                return jsonify(response_data)
                
            finally:
                # Cleanup uploaded file
                if os.path.exists(file_path):
                    os.remove(file_path)
            
        except ValidationError as e:
            logger.warning(f"API structured validation error: {e}")
            return jsonify({'error': str(e)}), 400
        except OCRError as e:
            logger.error(f"API structured OCR error: {e}")
            return jsonify({'error': str(e)}), 500
        except Exception as e:
            logger.error(f"API structured unexpected error: {e}")
            logger.error(traceback.format_exc())
            return jsonify({'error': 'Internal server error'}), 500
    
    @api.route('/health', methods=['GET'])
    def api_health():
        """API health check"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'api_version': 'v1'
        })
    
    @api.route('/info', methods=['GET'])
    def api_info():
        """API information"""
        return jsonify({
            'api_version': 'v1',
            'model_name': config.model.name,
            'use_local_model': config.model.use_local,
            'device': config.model.device,
            'max_file_size_mb': config.upload.max_file_size / (1024 * 1024),
            'allowed_extensions': config.upload.allowed_extensions,
            'max_batch_size': config.performance.batch_size,
            'endpoints': [
                '/api/v1/ocr',
                '/api/v1/ocr/batch',
                '/api/v1/ocr/structured',
                '/api/v1/health',
                '/api/v1/info'
            ]
        })
    
    return api
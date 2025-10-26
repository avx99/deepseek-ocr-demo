"""
Main Flask application for DeepSeek OCR
"""

import os
import sys
import uuid
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory, flash, redirect, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import traceback

# Add the project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.config import get_config
from app.utils.logger import setup_logging, get_logger
from app.utils.validation import FileValidator, InputValidator
from app.utils.exceptions import OCRError, ValidationError, ModelError
from app.ocr.deepseek_ocr import DeepSeekOCR
from app.api.routes import create_api_blueprint


def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    config = get_config()
    
    # Configure Flask
    app.config['SECRET_KEY'] = config.server.secret_key
    app.config['MAX_CONTENT_LENGTH'] = config.upload.max_file_size
    app.config['UPLOAD_FOLDER'] = config.upload.upload_folder
    app.config['RESULTS_FOLDER'] = config.upload.results_folder
    
    # Setup logging
    setup_logging(config)
    logger = get_logger(__name__)
    
    # Enable CORS
    CORS(app, origins=config.security.allowed_origins)
    
    # Initialize OCR processor
    ocr_processor = DeepSeekOCR(config)
    file_validator = FileValidator(config)
    
    # Register error handlers
    @app.errorhandler(413)
    def too_large(e):
        return jsonify({'error': 'File too large'}), 413
    
    @app.errorhandler(ValidationError)
    def validation_error(e):
        return jsonify({'error': str(e)}), 400
    
    @app.errorhandler(OCRError)
    def ocr_error(e):
        return jsonify({'error': str(e)}), 500
    
    @app.errorhandler(ModelError)
    def model_error(e):
        return jsonify({'error': str(e)}), 500
    
    # Routes
    @app.route('/')
    def index():
        """Main page with upload interface"""
        return render_template('index.html')
    
    @app.route('/upload', methods=['POST'])
    def upload_file():
        """Handle file upload and OCR processing"""
        try:
            # Check if file is present
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Validate file
            file_validator.validate_file(file)
            
            # Get optional prompt
            prompt = request.form.get('prompt', '')
            if prompt:
                prompt = InputValidator.validate_prompt(prompt)
            
            # Save uploaded file
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            
            logger.info(f"File uploaded: {unique_filename}")
            
            # Process OCR
            result = ocr_processor.extract_text(file_path, prompt)
            
            # Save result
            result_id = str(uuid.uuid4())
            result_data = {
                'id': result_id,
                'timestamp': datetime.now().isoformat(),
                'filename': filename,
                'file_path': file_path,
                'prompt': prompt,
                'result': result
            }
            
            result_file = os.path.join(app.config['RESULTS_FOLDER'], f"{result_id}.json")
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"OCR completed for {filename}, result ID: {result_id}")
            
            return jsonify({
                'success': True,
                'result_id': result_id,
                'text': result['text'],
                'confidence': result.get('confidence', 1.0),
                'metadata': {
                    'filename': filename,
                    'image_size': result.get('image_size'),
                    'model_used': result.get('model_used'),
                    'processing_method': result.get('processing_method')
                }
            })
            
        except ValidationError as e:
            logger.warning(f"Validation error: {e}")
            return jsonify({'error': str(e)}), 400
        except OCRError as e:
            logger.error(f"OCR error: {e}")
            return jsonify({'error': str(e)}), 500
        except Exception as e:
            logger.error(f"Unexpected error in upload: {e}")
            logger.error(traceback.format_exc())
            return jsonify({'error': 'Internal server error'}), 500
        finally:
            # Cleanup uploaded file if needed
            if 'file_path' in locals() and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.warning(f"Failed to cleanup uploaded file: {e}")
    
    @app.route('/batch_upload', methods=['POST'])
    def batch_upload():
        """Handle batch file upload and OCR processing"""
        try:
            files = request.files.getlist('files')
            if not files:
                return jsonify({'error': 'No files provided'}), 400
            
            # Validate batch size
            max_batch = config.performance.batch_size
            InputValidator.validate_batch_size(len(files), max_batch)
            
            # Get optional prompt
            prompt = request.form.get('prompt', '')
            if prompt:
                prompt = InputValidator.validate_prompt(prompt)
            
            results = []
            file_paths = []
            
            # Process each file
            for file in files:
                try:
                    if file.filename == '':
                        continue
                    
                    # Validate file
                    file_validator.validate_file(file)
                    
                    # Save file
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4()}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(file_path)
                    file_paths.append(file_path)
                    
                    logger.info(f"Batch file uploaded: {unique_filename}")
                    
                except Exception as e:
                    results.append({
                        'filename': file.filename,
                        'success': False,
                        'error': str(e)
                    })
                    continue
            
            # Process OCR for all valid files
            if file_paths:
                ocr_results = ocr_processor.batch_extract_text(file_paths, prompt)
                
                for i, ocr_result in enumerate(ocr_results):
                    filename = os.path.basename(file_paths[i]).split('_', 1)[1]  # Remove UUID prefix
                    
                    if 'error' in ocr_result:
                        results.append({
                            'filename': filename,
                            'success': False,
                            'error': ocr_result['error']
                        })
                    else:
                        # Save result
                        result_id = str(uuid.uuid4())
                        result_data = {
                            'id': result_id,
                            'timestamp': datetime.now().isoformat(),
                            'filename': filename,
                            'file_path': file_paths[i],
                            'prompt': prompt,
                            'result': ocr_result
                        }
                        
                        result_file = os.path.join(app.config['RESULTS_FOLDER'], f"{result_id}.json")
                        with open(result_file, 'w', encoding='utf-8') as f:
                            json.dump(result_data, f, ensure_ascii=False, indent=2)
                        
                        results.append({
                            'filename': filename,
                            'success': True,
                            'result_id': result_id,
                            'text': ocr_result['text'],
                            'confidence': ocr_result.get('confidence', 1.0)
                        })
            
            logger.info(f"Batch processing completed: {len(results)} files")
            
            return jsonify({
                'success': True,
                'total_files': len(files),
                'processed_files': len([r for r in results if r['success']]),
                'failed_files': len([r for r in results if not r['success']]),
                'results': results
            })
            
        except ValidationError as e:
            logger.warning(f"Batch validation error: {e}")
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            logger.error(traceback.format_exc())
            return jsonify({'error': 'Internal server error'}), 500
        finally:
            # Cleanup uploaded files
            for file_path in file_paths:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    logger.warning(f"Failed to cleanup batch file: {e}")
    
    @app.route('/result/<result_id>')
    def get_result(result_id):
        """Get OCR result by ID"""
        try:
            result_file = os.path.join(app.config['RESULTS_FOLDER'], f"{result_id}.json")
            
            if not os.path.exists(result_file):
                return jsonify({'error': 'Result not found'}), 404
            
            with open(result_file, 'r', encoding='utf-8') as f:
                result_data = json.load(f)
            
            return jsonify(result_data)
            
        except Exception as e:
            logger.error(f"Error retrieving result {result_id}: {e}")
            return jsonify({'error': 'Failed to retrieve result'}), 500
    
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'model': config.model.name,
            'version': '1.0.0'
        })
    
    @app.route('/info')
    def info():
        """Get system information"""
        return jsonify({
            'model_name': config.model.name,
            'use_local_model': config.model.use_local,
            'device': config.model.device,
            'max_file_size': config.upload.max_file_size,
            'allowed_extensions': config.upload.allowed_extensions,
            'version': '1.0.0'
        })
    
    # Register API blueprint
    api_bp = create_api_blueprint(ocr_processor, file_validator, config)
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    return app


def main():
    """Main entry point"""
    try:
        app = create_app()
        config = get_config()
        
        logger = get_logger(__name__)
        logger.info(f"Starting DeepSeek OCR server on {config.server.host}:{config.server.port}")
        
        app.run(
            host=config.server.host,
            port=config.server.port,
            debug=config.server.debug
        )
        
    except Exception as e:
        print(f"Failed to start server: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
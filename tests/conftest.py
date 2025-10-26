"""
Test configuration for DeepSeek OCR
"""

import os
import tempfile
import pytest
from unittest.mock import Mock

# Test configuration
TEST_CONFIG = {
    'server': {
        'host': '127.0.0.1',
        'port': 5001,
        'debug': True,
        'secret_key': 'test-secret-key'
    },
    'model': {
        'name': 'test-model',
        'use_local': False,  # Use mock for tests
        'local_path': './test_models/mock-model',
        'device': 'cpu',
        'precision': 'fp32',
        'max_length': 1000,
        'temperature': 0.1
    },
    'api': {
        'deepseek_api_key': 'test-api-key',
        'openai_api_base': 'http://localhost:8000',
        'rate_limit': 100,
        'timeout': 10
    },
    'upload': {
        'max_file_size': 1048576,  # 1MB for tests
        'allowed_extensions': ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'pdf'],
        'upload_folder': './test_uploads',
        'results_folder': './test_results',
        'cleanup_after': 300
    },
    'ocr': {
        'confidence_threshold': 0.5,
        'max_image_size': 1024,
        'preprocessing': {
            'enabled': True,
            'resize': True,
            'denoise': False,  # Disable for faster tests
            'enhance_contrast': False
        },
        'fallback_engines': ['mock']
    },
    'logging': {
        'level': 'DEBUG',
        'file': './test_logs/test.log',
        'rotation': '1 MB',
        'retention': '1 day',
        'format': '{time} | {level} | {message}'
    },
    'performance': {
        'batch_size': 1,
        'max_workers': 2,
        'cache_enabled': False,  # Disable for predictable tests
        'cache_ttl': 300,
        'gpu_memory_fraction': 0.5
    },
    'security': {
        'max_requests_per_ip': 1000,
        'request_window': 3600,
        'allowed_origins': ['*'],
        'csrf_protection': False  # Disable for easier testing
    }
}

# Test data directory
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

# Ensure test directories exist
os.makedirs(TEST_DATA_DIR, exist_ok=True)
os.makedirs('./test_uploads', exist_ok=True)
os.makedirs('./test_results', exist_ok=True)
os.makedirs('./test_logs', exist_ok=True)


@pytest.fixture
def test_config():
    """Provide test configuration"""
    return TEST_CONFIG


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_image_path():
    """Path to sample test image"""
    return os.path.join(TEST_DATA_DIR, 'sample.jpg')


@pytest.fixture
def sample_pdf_path():
    """Path to sample test PDF"""
    return os.path.join(TEST_DATA_DIR, 'sample.pdf')


@pytest.fixture
def mock_ocr_processor():
    """Mock OCR processor for testing"""
    mock = Mock()
    mock.extract_text.return_value = {
        'text': 'Sample extracted text',
        'confidence': 0.95,
        'image_size': [800, 600],
        'model_used': 'test-model',
        'processing_method': 'mock'
    }
    mock.batch_extract_text.return_value = [
        {
            'text': 'Text from image 1',
            'confidence': 0.9,
            'image_size': [800, 600],
            'model_used': 'test-model',
            'processing_method': 'mock'
        },
        {
            'text': 'Text from image 2',
            'confidence': 0.85,
            'image_size': [1024, 768],
            'model_used': 'test-model',
            'processing_method': 'mock'
        }
    ]
    mock.extract_structured_data.return_value = {
        'text': '{"name": "John Doe", "email": "john@example.com"}',
        'is_structured': True,
        'structured_data': {
            'name': 'John Doe',
            'email': 'john@example.com'
        },
        'confidence': 0.88,
        'image_size': [600, 800],
        'model_used': 'test-model',
        'processing_method': 'mock'
    }
    return mock


@pytest.fixture
def client(test_config, mock_ocr_processor):
    """Flask test client"""
    from app.main import create_app
    
    # Override configuration for testing
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SECRET_KEY': test_config['server']['secret_key'],
        'UPLOAD_FOLDER': test_config['upload']['upload_folder'],
        'RESULTS_FOLDER': test_config['upload']['results_folder'],
        'MAX_CONTENT_LENGTH': test_config['upload']['max_file_size']
    })
    
    # Mock the OCR processor
    app.ocr_processor = mock_ocr_processor
    
    with app.test_client() as client:
        yield client


def cleanup_test_files():
    """Clean up test files after tests"""
    import shutil
    
    for directory in ['./test_uploads', './test_results', './test_logs']:
        if os.path.exists(directory):
            shutil.rmtree(directory)
    
    # Recreate empty directories
    os.makedirs('./test_uploads', exist_ok=True)
    os.makedirs('./test_results', exist_ok=True)
    os.makedirs('./test_logs', exist_ok=True)
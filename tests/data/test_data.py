"""
Sample test data for OCR testing
"""

# Sample text content for testing
SAMPLE_TEXTS = {
    'simple': "Hello World!",
    'multiline': """This is a sample document for testing OCR functionality.
It contains multiple lines of text with different content.
The OCR system should be able to extract all this text
accurately and maintain the structure of the document.""",
    'contact_info': """Contact Information:
Email: test@example.com
Phone: (555) 123-4567
Address: 123 Main St, Anytown, USA 12345""",
    'invoice': """Invoice #: INV-2024-001
Amount: $1,234.56
Date: 01/15/2024
Tax: 8.25%
Total: $1,336.12""",
    'table': """Product         Qty    Price
=====================================
Widget A        2      $25.00
Widget B        1      $15.50
Widget C        3      $8.75
=====================================
TOTAL                  $74.75""",
    'mixed_content': """Sample Document

This document contains various types of content:
- Text paragraphs
- Contact information
- Numerical data
- Special characters: @#$%^&*()

Date: January 15, 2024
Reference: DOC-2024-001

For more information, visit: https://example.com
or call us at +1 (555) 123-4567"""
}

# Expected OCR results for validation
EXPECTED_RESULTS = {
    'simple_text.jpg': {
        'text': 'Hello World!',
        'confidence_threshold': 0.8
    },
    'document.jpg': {
        'text': 'Sample Document',
        'should_contain': [
            'Sample Document',
            'testing OCR functionality',
            'test@example.com',
            '(555) 123-4567'
        ]
    },
    'numbers.jpg': {
        'should_contain': [
            'INV-2024-001',
            '$1,234.56',
            '01/15/2024',
            '8.25%'
        ]
    }
}

# Test file configurations
TEST_FILES = {
    'valid_images': [
        'simple_text.jpg',
        'document.jpg',
        'numbers.jpg',
        'mixed.jpg'
    ],
    'invalid_files': [
        'not_an_image.txt',
        'corrupted.jpg',
        'empty.jpg'
    ],
    'large_files': [
        'large_image.jpg'
    ]
}

# API test data
API_TEST_DATA = {
    'valid_requests': [
        {
            'extract_format': 'plain',
            'preprocess': True,
            'language': 'en'
        },
        {
            'extract_format': 'structured',
            'preprocess': False,
            'language': 'en'
        }
    ],
    'invalid_requests': [
        {
            'extract_format': 'invalid_format'
        },
        {
            'language': 'invalid_lang'
        }
    ]
}

# Configuration test data
CONFIG_TEST_DATA = {
    'valid_configs': {
        'model_name': 'deepseek-ai/deepseek-vl-7b-chat',
        'device': 'cuda',
        'max_tokens': 2048,
        'temperature': 0.1
    },
    'invalid_configs': {
        'max_tokens': -1,
        'temperature': 2.0,
        'device': 'invalid_device'
    }
}

# Performance test parameters
PERFORMANCE_TEST_PARAMS = {
    'batch_sizes': [1, 5, 10],
    'image_sizes': [(100, 100), (500, 500), (1000, 1000)],
    'timeout_tests': {
        'small_image': 5.0,  # seconds
        'medium_image': 15.0,
        'large_image': 30.0
    }
}

# Error simulation data
ERROR_SIMULATION = {
    'network_errors': [
        'Connection timeout',
        'DNS resolution failed',
        'HTTP 500 Internal Server Error'
    ],
    'file_errors': [
        'File not found',
        'Permission denied',
        'Corrupted file'
    ],
    'model_errors': [
        'CUDA out of memory',
        'Model loading failed',
        'Invalid input format'
    ]
}
# Test Utilities

This directory contains utility modules for testing the DeepSeek OCR application.

## Files

### test_helpers.py
Comprehensive test utilities and helper classes:
- `TestHelpers`: General testing utilities
- `MockDeepSeekModel`: Mock model for testing OCR functionality
- `MockTransformersComponents`: Mock transformers components
- `APITestClient`: Test client for API testing
- `ConfigTestHelper`: Configuration testing utilities
- `ImageTestHelper`: Image processing test utilities
- `PerformanceTestHelper`: Performance testing utilities
- `LogTestHelper`: Logging test utilities

### Example Usage

```python
from tests.utils.test_helpers import (
    test_helpers, 
    config_helper, 
    image_helper,
    APITestClient
)

# Create mock image file
mock_file = test_helpers.create_mock_image_file("test.jpg")

# Create test image bytes
image_bytes = image_helper.create_test_image_bytes(200, 200)

# Test API endpoint
client = APITestClient(app)
result, status = client.upload_image(image_bytes)

# Create temporary config
config_data = {"model": {"name": "test-model"}}
config_path = config_helper.create_temp_config(config_data)
```

## Test Data Structure

The test utilities work with the following data structure:
- `tests/data/` - Test images and sample data
- `tests/utils/` - Test utilities and helpers
- Mock objects for external dependencies
- Performance benchmarking tools
- Configuration testing helpers
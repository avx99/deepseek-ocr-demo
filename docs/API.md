# DeepSeek OCR API Documentation

This document provides comprehensive documentation for the DeepSeek OCR REST API.

## Base URL

```
http://localhost:5000/api/v1
```

## Authentication

Currently, the API does not require authentication. In production environments, consider implementing API key authentication or other security measures.

## Rate Limiting

- API endpoints: 60 requests per minute per IP
- Upload endpoints: 20 requests per minute per IP
- Batch upload: 5 requests per minute per IP

## Content Type

All API endpoints accept `multipart/form-data` for file uploads and return `application/json`.

## Error Handling

All endpoints return consistent error responses:

```json
{
    "error": "Error description",
    "timestamp": "2024-01-01T12:00:00Z"
}
```

### HTTP Status Codes

- `200 OK` - Request successful
- `400 Bad Request` - Invalid request parameters
- `413 Payload Too Large` - File too large
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

## Endpoints

### 1. Single Image OCR

Extract text from a single image.

**Endpoint:** `POST /api/v1/ocr`

**Parameters:**
- `file` (required) - Image file (multipart/form-data)
- `prompt` (optional) - Custom prompt for OCR processing
- `include_metadata` (optional) - Include processing metadata (default: false)

**Supported File Formats:**
- Images: JPG, JPEG, PNG, BMP, TIFF, WebP, GIF
- Documents: PDF
- Maximum file size: 50MB

**Example Request:**

```bash
curl -X POST http://localhost:5000/api/v1/ocr \
  -F "file=@image.jpg" \
  -F "prompt=Extract all text from this image" \
  -F "include_metadata=true"
```

**Example Response:**

```json
{
    "success": true,
    "text": "Extracted text content goes here...",
    "confidence": 0.95,
    "metadata": {
        "filename": "image.jpg",
        "image_size": [1920, 1080],
        "model_used": "deepseek-vl-7b-chat",
        "processing_method": "local",
        "timestamp": "2024-01-01T12:00:00Z"
    }
}
```

### 2. Batch OCR Processing

Process multiple images in a single request.

**Endpoint:** `POST /api/v1/ocr/batch`

**Parameters:**
- `files` (required) - Multiple image files (multipart/form-data)
- `prompt` (optional) - Custom prompt for all images
- `include_metadata` (optional) - Include processing metadata (default: false)

**Limits:**
- Maximum files per batch: 10 (configurable)
- Maximum file size: 50MB per file

**Example Request:**

```bash
curl -X POST http://localhost:5000/api/v1/ocr/batch \
  -F "files=@image1.jpg" \
  -F "files=@image2.png" \
  -F "files=@image3.pdf" \
  -F "prompt=Extract all visible text"
```

**Example Response:**

```json
{
    "success": true,
    "total_files": 3,
    "processed_files": 3,
    "failed_files": 0,
    "results": [
        {
            "filename": "image1.jpg",
            "success": true,
            "text": "Text from first image...",
            "confidence": 0.92
        },
        {
            "filename": "image2.png",
            "success": true,
            "text": "Text from second image...",
            "confidence": 0.88
        },
        {
            "filename": "image3.pdf",
            "success": false,
            "error": "Unsupported file format for this endpoint"
        }
    ]
}
```

### 3. Structured Data Extraction

Extract structured data from images using custom prompts.

**Endpoint:** `POST /api/v1/ocr/structured`

**Parameters:**
- `file` (required) - Image file (multipart/form-data)
- `structure_prompt` (required) - Detailed prompt describing the desired structure

**Example Request:**

```bash
curl -X POST http://localhost:5000/api/v1/ocr/structured \
  -F "file=@invoice.jpg" \
  -F "structure_prompt=Extract the following information as JSON: company name, invoice number, date, total amount, line items with descriptions and prices"
```

**Example Response:**

```json
{
    "success": true,
    "text": "{\n  \"company_name\": \"ABC Corp\",\n  \"invoice_number\": \"INV-2024-001\",\n  \"date\": \"2024-01-01\",\n  \"total_amount\": \"$1,250.00\",\n  \"line_items\": [\n    {\n      \"description\": \"Consulting Services\",\n      \"price\": \"$1,000.00\"\n    },\n    {\n      \"description\": \"Software License\",\n      \"price\": \"$250.00\"\n    }\n  ]\n}",
    "is_structured": true,
    "structured_data": {
        "company_name": "ABC Corp",
        "invoice_number": "INV-2024-001",
        "date": "2024-01-01",
        "total_amount": "$1,250.00",
        "line_items": [
            {
                "description": "Consulting Services",
                "price": "$1,000.00"
            },
            {
                "description": "Software License",
                "price": "$250.00"
            }
        ]
    },
    "confidence": 0.90,
    "metadata": {
        "filename": "invoice.jpg",
        "image_size": [2480, 3508],
        "model_used": "deepseek-vl-7b-chat",
        "processing_method": "local",
        "timestamp": "2024-01-01T12:00:00Z"
    }
}
```

### 4. Health Check

Check the API health status.

**Endpoint:** `GET /api/v1/health`

**Example Request:**

```bash
curl http://localhost:5000/api/v1/health
```

**Example Response:**

```json
{
    "status": "healthy",
    "timestamp": "2024-01-01T12:00:00Z",
    "api_version": "v1"
}
```

### 5. System Information

Get system and API information.

**Endpoint:** `GET /api/v1/info`

**Example Request:**

```bash
curl http://localhost:5000/api/v1/info
```

**Example Response:**

```json
{
    "api_version": "v1",
    "model_name": "deepseek-vl-7b-chat",
    "use_local_model": true,
    "device": "cuda",
    "max_file_size_mb": 50.0,
    "allowed_extensions": ["jpg", "jpeg", "png", "bmp", "tiff", "pdf", "webp", "gif"],
    "max_batch_size": 10,
    "endpoints": [
        "/api/v1/ocr",
        "/api/v1/ocr/batch",
        "/api/v1/ocr/structured",
        "/api/v1/health",
        "/api/v1/info"
    ]
}
```

## Prompt Engineering

### Basic OCR Prompts

```
"Extract all text from this image"
"Read the text in this document"
"Transcribe the content of this image"
```

### Specific Extraction Prompts

```
"Extract only phone numbers from this image"
"Find all email addresses in this document"
"Get the table data from this image"
"Extract the headline and main text"
```

### Structured Data Prompts

```
"Extract invoice details as JSON with fields: number, date, amount, vendor"
"Convert this receipt to structured data with items and prices"
"Extract form data as key-value pairs"
"Parse this table into CSV format"
```

### Language-Specific Prompts

```
"Extract text in Chinese characters only"
"Transcribe the English text, ignore other languages"
"Translate the extracted text to English"
```

## Code Examples

### Python

```python
import requests

# Single image OCR
def extract_text(image_path, prompt=None):
    url = "http://localhost:5000/api/v1/ocr"
    
    with open(image_path, 'rb') as f:
        files = {'file': f}
        data = {}
        if prompt:
            data['prompt'] = prompt
        
        response = requests.post(url, files=files, data=data)
        return response.json()

# Batch processing
def batch_ocr(image_paths, prompt=None):
    url = "http://localhost:5000/api/v1/ocr/batch"
    
    files = []
    for path in image_paths:
        files.append(('files', open(path, 'rb')))
    
    data = {}
    if prompt:
        data['prompt'] = prompt
    
    try:
        response = requests.post(url, files=files, data=data)
        return response.json()
    finally:
        # Close all file handles
        for _, file_handle in files:
            file_handle.close()

# Structured extraction
def extract_structured(image_path, structure_prompt):
    url = "http://localhost:5000/api/v1/ocr/structured"
    
    with open(image_path, 'rb') as f:
        files = {'file': f}
        data = {'structure_prompt': structure_prompt}
        
        response = requests.post(url, files=files, data=data)
        return response.json()

# Usage examples
result = extract_text("document.jpg", "Extract all text")
print(result['text'])

batch_result = batch_ocr(["img1.jpg", "img2.png"])
for item in batch_result['results']:
    print(f"{item['filename']}: {item['text']}")

invoice_data = extract_structured(
    "invoice.jpg",
    "Extract as JSON: company, invoice_number, date, total"
)
if invoice_data['is_structured']:
    print(invoice_data['structured_data'])
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

// Single image OCR
async function extractText(imagePath, prompt = null) {
    const form = new FormData();
    form.append('file', fs.createReadStream(imagePath));
    if (prompt) {
        form.append('prompt', prompt);
    }

    try {
        const response = await axios.post(
            'http://localhost:5000/api/v1/ocr',
            form,
            { headers: form.getHeaders() }
        );
        return response.data;
    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
        throw error;
    }
}

// Batch processing
async function batchOCR(imagePaths, prompt = null) {
    const form = new FormData();
    
    imagePaths.forEach(path => {
        form.append('files', fs.createReadStream(path));
    });
    
    if (prompt) {
        form.append('prompt', prompt);
    }

    try {
        const response = await axios.post(
            'http://localhost:5000/api/v1/ocr/batch',
            form,
            { headers: form.getHeaders() }
        );
        return response.data;
    } catch (error) {
        console.error('Error:', error.response?.data || error.message);
        throw error;
    }
}

// Usage
(async () => {
    try {
        const result = await extractText('document.jpg', 'Extract all text');
        console.log('Extracted text:', result.text);
        
        const batchResult = await batchOCR(['img1.jpg', 'img2.png']);
        batchResult.results.forEach(item => {
            console.log(`${item.filename}: ${item.text}`);
        });
    } catch (error) {
        console.error('Processing failed:', error);
    }
})();
```

### curl Examples

```bash
# Basic OCR
curl -X POST http://localhost:5000/api/v1/ocr \
  -F "file=@document.jpg" \
  -F "prompt=Extract all text"

# Batch processing
curl -X POST http://localhost:5000/api/v1/ocr/batch \
  -F "files=@image1.jpg" \
  -F "files=@image2.png" \
  -F "prompt=Extract text from all images"

# Structured extraction
curl -X POST http://localhost:5000/api/v1/ocr/structured \
  -F "file=@receipt.jpg" \
  -F "structure_prompt=Extract receipt data as JSON with store, date, items, total"

# Health check
curl http://localhost:5000/api/v1/health

# System info
curl http://localhost:5000/api/v1/info
```

## Best Practices

### File Optimization
1. **Image Quality:** Use high-resolution images for better OCR accuracy
2. **File Format:** PNG and TIFF provide better quality than JPEG
3. **Preprocessing:** Ensure good contrast and minimal noise
4. **Size Limits:** Keep files under 50MB for optimal performance

### Prompt Engineering
1. **Be Specific:** Clear, detailed prompts yield better results
2. **Format Specification:** Specify desired output format (JSON, CSV, etc.)
3. **Language:** Mention the expected language if not English
4. **Context:** Provide context about the document type

### Performance Optimization
1. **Batch Processing:** Use batch endpoints for multiple files
2. **Concurrent Requests:** Limit concurrent API calls to avoid overload
3. **Caching:** Implement client-side caching for repeated requests
4. **Error Handling:** Implement proper retry logic with exponential backoff

### Error Handling
1. **Validation:** Validate files client-side before upload
2. **Retry Logic:** Implement retries for transient errors
3. **Fallback:** Have fallback strategies for processing failures
4. **Monitoring:** Monitor API response times and error rates

## WebSocket Support (Future Feature)

Real-time processing updates via WebSocket connection:

```javascript
const ws = new WebSocket('ws://localhost:5000/ws');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Processing update:', data);
};

// Send processing request
ws.send(JSON.stringify({
    type: 'ocr_request',
    file_id: 'uploaded_file_id',
    prompt: 'Extract all text'
}));
```

## SDK Libraries (Planned)

Official SDK libraries will be available for:
- Python (`pip install deepseek-ocr-sdk`)
- Node.js (`npm install deepseek-ocr-sdk`)
- Go (`go get github.com/deepseek/ocr-sdk-go`)
- Java (Maven/Gradle packages)

## Support and Resources

- **Documentation:** Full API documentation and examples
- **GitHub Issues:** Report bugs and request features
- **Community:** Join our Discord/Slack for support
- **Examples:** Check the `/examples` directory for sample implementations
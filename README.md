# DeepSeek OCR Project

A comprehensive, production-ready OCR (Optical Character Recognition) application using DeepSeek's vision-language model. This project provides both a web interface and REST API for text extraction from images, with support for local deployment, Docker containerization, and extensive customization options.

## 🚀 Key Features

- **DeepSeek Vision-Language Model Integration**: Leverages state-of-the-art AI for accurate text extraction
- **Dual Processing Modes**: Local model inference and API fallback support  
- **Web Interface**: User-friendly upload interface with real-time results
- **REST API**: Comprehensive API for programmatic access
- **Batch Processing**: Handle multiple images simultaneously
- **Docker Support**: Easy containerization with CUDA GPU acceleration
- **Comprehensive Testing**: Unit, integration, and performance test suites
- **Production Ready**: Logging, monitoring, error handling, and configuration management
- **Extensive Documentation**: Complete setup guides from scratch

## 📋 Table of Contents

- [🚀 Key Features](#-key-features)
- [🛠️ Installation](#️-installation)
  - [Prerequisites](#prerequisites)  
  - [Python Environment Setup](#python-environment-setup)
  - [Project Installation](#project-installation)
  - [Docker Installation](#docker-installation)
- [🎯 Quick Start](#-quick-start)
- [📚 Usage](#-usage)
  - [Web Interface](#web-interface)
  - [REST API](#rest-api)
  - [Batch Processing](#batch-processing)
- [⚙️ Configuration](#️-configuration)
- [🧪 Testing](#-testing)
- [📦 Deployment](#-deployment)
- [🔧 Troubleshooting](#-troubleshooting)
- [📖 Documentation](#-documentation)
- [🤝 Contributing](#-contributing)

## 🛠️ Installation

### Prerequisites

**Required Software (install in order):**

1. **NVIDIA CUDA Toolkit 11.8 or 12.x** (if using GPU)
   - Download from: https://developer.nvidia.com/cuda-downloads
   - Verify installation: `nvcc --version`

2. **Python 3.9, 3.10, or 3.11**
   - Download from: https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"
   - Verify: `python --version`

3. **Git** (for cloning repository)
   - Download from: https://git-scm.com/downloads
   - Verify: `git --version`

4. **Docker & Docker Compose** (optional, for containerized deployment)
   - Download Docker Desktop: https://www.docker.com/products/docker-desktop/
   - For GPU support, install NVIDIA Container Toolkit

### Python Environment Setup

1. **Create Virtual Environment**
   ```powershell
   # Create virtual environment
   python -m venv deepseek-ocr-env
   
   # Activate environment (Windows PowerShell)
   .\deepseek-ocr-env\Scripts\Activate.ps1
   
   # If execution policy error, run:
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

2. **Upgrade pip and install dependencies**
   ```powershell
   python -m pip install --upgrade pip
   pip install wheel setuptools
   ```

### Project Installation

1. **Clone Repository**
   ```powershell
   git clone https://github.com/yourusername/deepseek-ocr.git
   cd deepseek-ocr
   ```

2. **Install Dependencies**
   ```powershell
   # Install Python packages
   pip install -r requirements.txt
   
   # For GPU support (if you have CUDA)
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

3. **Configure Environment**
   ```powershell
   # Copy example environment file
   copy .env.example .env
   
   # Edit .env file with your preferences (optional)
   notepad .env
   ```

4. **Verify Installation**
   ```powershell
   # Test configuration
   python -c "from app.utils.config import get_config; print('Configuration loaded successfully')"
   
   # Test dependencies
   python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')"
   ```

### Docker Installation

For containerized deployment:

```powershell
# Build Docker image
docker build -f docker/Dockerfile -t deepseek-ocr .

# Run with Docker Compose
docker-compose -f docker/docker-compose.yml up -d

# For GPU support
docker-compose -f docker/docker-compose.gpu.yml up -d
```

## 🎯 Quick Start

1. **Start the Application**
   ```powershell
   # Activate environment
   .\deepseek-ocr-env\Scripts\Activate.ps1
   
   # Start Flask application
   python app/main.py
   ```

2. **Access Web Interface**
   - Open browser: http://localhost:5000
   - Upload image using the web form
   - View extracted text results

3. **Test API Endpoint**
   ```powershell
   # Test health endpoint
   curl http://localhost:5000/api/health
   
   # Upload image via API (example)
   curl -X POST -F "image=@test_image.jpg" http://localhost:5000/api/ocr/upload
   ```

## 📚 Usage

### Web Interface

1. **Basic Usage**
   - Navigate to http://localhost:5000
   - Click "Choose File" to select an image
   - Select extraction format (Plain Text or Structured)
   - Click "Extract Text" to process
   - View results and download if needed

2. **Supported Formats**
   - Images: JPG, JPEG, PNG, GIF, BMP, TIFF
   - Maximum file size: 10MB (configurable)
   - Batch upload: Multiple files supported

### REST API

**Base URL:** `http://localhost:5000/api`

#### Single Image Processing
```bash
POST /api/ocr/upload
Content-Type: multipart/form-data

Parameters:
- image: Image file
- extract_format: "plain" or "structured" (default: "plain")
- preprocess: true/false (default: true)
- language: "en", "es", "fr", etc. (default: "en")
```

**Example Response:**
```json
{
  "text": "Extracted text content...",
  "confidence": 0.95,
  "processing_time": 2.34,
  "filename": "document.jpg",
  "format": "plain"
}
```

#### Batch Processing
```bash
POST /api/ocr/batch
Content-Type: multipart/form-data

Parameters:
- images[]: Multiple image files
- extract_format: "plain" or "structured"
```

#### Health Check
```bash
GET /api/health

Response:
{
  "status": "healthy",
  "components": {
    "ocr_engine": "ready",
    "file_system": "accessible"
  }
}
```

### Batch Processing

Process multiple images programmatically:

```python
import requests

# Prepare files
files = [
    ('images[]', ('doc1.jpg', open('doc1.jpg', 'rb'), 'image/jpeg')),
    ('images[]', ('doc2.jpg', open('doc2.jpg', 'rb'), 'image/jpeg'))
]

# Send request
response = requests.post(
    'http://localhost:5000/api/ocr/batch',
    files=files,
    data={'extract_format': 'structured'}
)

results = response.json()
```

## ⚙️ Configuration

### Configuration File (config/config.yaml)

```yaml
model:
  name: "deepseek-ai/deepseek-vl-7b-chat"
  device: "cuda"  # or "cpu"
  max_tokens: 2048
  temperature: 0.1

server:
  host: "0.0.0.0"
  port: 5000
  debug: false

ocr:
  max_file_size: 10485760  # 10MB
  supported_formats: ["jpg", "jpeg", "png", "gif", "bmp", "tiff"]
  preprocessing: true
  default_language: "en"

logging:
  level: "INFO"
  file: "logs/app.log"
  max_size: "10MB"
  backup_count: 5
```

### Environment Variables

Create `.env` file for sensitive configurations:

```bash
# Model Configuration
MODEL_NAME=deepseek-ai/deepseek-vl-7b-chat
MODEL_DEVICE=cuda

# API Keys (if using API mode)
DEEPSEEK_API_KEY=your_api_key_here

# Server Configuration
FLASK_ENV=production
SECRET_KEY=your_secret_key

# Logging
LOG_LEVEL=INFO
```

### Advanced Configuration

- **GPU Memory Management**: Adjust `max_tokens` based on available VRAM
- **Performance Tuning**: Configure batch sizes and threading
- **Security Settings**: File size limits, allowed formats, CORS policies
- **Monitoring**: Health check intervals, logging levels

## 🧪 Testing

### Run Test Suite

```powershell
# Install test dependencies
pip install pytest pytest-cov pytest-mock

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest -m "not slow"  # Skip slow tests
pytest tests/test_integration.py  # Integration tests only
```

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing  
- **Performance Tests**: Load and speed testing
- **API Tests**: REST endpoint testing

### Create Test Images

```powershell
# Generate sample test images
python tests/create_test_images.py
```

## 📦 Deployment

### Local Development
```powershell
python app/main.py
```

### Production with Gunicorn
```powershell
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app.main:app
```

### Docker Deployment
```powershell
# Standard deployment
docker-compose up -d

# GPU-enabled deployment
docker-compose -f docker/docker-compose.gpu.yml up -d

# Scale workers
docker-compose up --scale web=3
```

### Cloud Deployment

**AWS/Azure/GCP:**
- Use provided Docker images
- Configure GPU instances for better performance
- Set up load balancing for high availability
- Configure persistent storage for logs

## 🔧 Troubleshooting

### Common Issues

1. **CUDA Not Available**
   ```
   Error: CUDA device not found
   Solution: Install CUDA toolkit or set MODEL_DEVICE=cpu
   ```

2. **Memory Issues**
   ```
   Error: CUDA out of memory
   Solution: Reduce max_tokens or use CPU mode
   ```

3. **Model Download Fails**
   ```
   Error: Failed to download model
   Solution: Check internet connection, verify model name
   ```

4. **Import Errors**
   ```
   Error: Module not found
   Solution: Activate virtual environment, reinstall requirements
   ```

### Debug Mode

Enable debug logging:
```python
# In config.yaml
logging:
  level: "DEBUG"

# Or via environment
export LOG_LEVEL=DEBUG
```

### Performance Optimization

1. **GPU Utilization**
   - Monitor: `nvidia-smi`
   - Optimize batch sizes
   - Use mixed precision

2. **Memory Management**
   - Clear cache between requests
   - Monitor RAM usage
   - Configure swap if needed

3. **API Response Times**
   - Enable preprocessing caching
   - Use connection pooling
   - Implement request queuing

## 📖 Documentation

Detailed documentation available in `/docs`:

- **[Installation Guide](docs/installation.md)**: Step-by-step setup instructions
- **[API Reference](docs/api.md)**: Complete API documentation
- **[Configuration Guide](docs/configuration.md)**: Advanced configuration options
- **[Troubleshooting](docs/troubleshooting.md)**: Common issues and solutions
- **[Development Guide](docs/development.md)**: Contributing and development setup

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Run test suite: `pytest`
5. Submit pull request

### Development Setup

```powershell
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run linting
flake8 app/
black app/
```

## 📄 Project Structure

```
deepseek-ocr/
├── app/
│   ├── __init__.py
│   ├── main.py              # Flask application entry point
│   ├── api/
│   │   └── routes.py        # API route definitions
│   ├── ocr/
│   │   └── deepseek_ocr.py  # Core OCR processing engine
│   ├── static/              # Web assets (CSS, JS, images)
│   ├── templates/           # HTML templates
│   └── utils/               # Utility modules
│       ├── config.py        # Configuration management
│       ├── validation.py    # Input validation
│       ├── image_processor.py  # Image preprocessing
│       ├── logger.py        # Logging utilities
│       └── exceptions.py    # Custom exceptions
├── config/
│   └── config.yaml          # Application configuration
├── docker/
│   ├── Dockerfile           # Docker image definition
│   ├── docker-compose.yml   # Standard deployment
│   └── docker-compose.gpu.yml  # GPU-enabled deployment
├── docs/                    # Comprehensive documentation
│   ├── installation.md     # Installation guide
│   ├── api.md              # API documentation
│   ├── configuration.md    # Configuration guide
│   └── troubleshooting.md  # Troubleshooting guide
├── tests/                   # Complete test suite
│   ├── conftest.py         # Test configuration
│   ├── data/               # Test data and samples
│   ├── utils/              # Test utilities
│   ├── test_*.py           # Unit tests
│   └── test_integration.py # Integration tests
├── uploads/                 # File upload directory
├── results/                 # Processing results
├── logs/                    # Application logs
├── models/                  # Model files (downloaded)
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
└── README.md               # This comprehensive guide
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- DeepSeek for providing the vision-language model
- Hugging Face for the transformers library
- Flask community for the web framework
- All contributors and users of this project

## 📞 Support

- **Issues**: https://github.com/yourusername/deepseek-ocr/issues
- **Discussions**: https://github.com/yourusername/deepseek-ocr/discussions
- **Documentation**: See `/docs` directory
- **Email**: your.email@example.com

---

**Made with ❤️ for the OCR community**

### Quick Reference Card

| Component | Purpose | Key Files |
|-----------|---------|-----------|
| **Core OCR** | Text extraction engine | `app/ocr/deepseek_ocr.py` |
| **Web Interface** | User-friendly upload form | `app/templates/index.html` |
| **REST API** | Programmatic access | `app/api/routes.py` |
| **Configuration** | Settings management | `config/config.yaml`, `.env` |
| **Docker** | Containerization | `docker/Dockerfile`, `docker-compose.yml` |
| **Testing** | Quality assurance | `tests/` directory |
| **Documentation** | Guides and references | `docs/` directory |

### Status Badges

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![PyTorch](https://img.shields.io/badge/pytorch-2.0%2B-red)
![Flask](https://img.shields.io/badge/flask-2.3%2B-green)
![Docker](https://img.shields.io/badge/docker-supported-blue)
![CUDA](https://img.shields.io/badge/cuda-11.8%2B-green)
![License](https://img.shields.io/badge/license-MIT-blue)

**🎉 Congratulations! You now have a complete, production-ready DeepSeek OCR application with comprehensive documentation, testing, and deployment options. Start by following the installation guide above to get your OCR system running locally.**
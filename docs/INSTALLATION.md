# DeepSeek OCR Installation Guide

This guide will help you install and set up the DeepSeek OCR project from scratch, assuming only CUDA drivers are already installed.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installing Python](#installing-python)
3. [Setting up the Project](#setting-up-the-project)
4. [Installing Dependencies](#installing-dependencies)
5. [Downloading the Model](#downloading-the-model)
6. [Configuration](#configuration)
7. [Running the Application](#running-the-application)
8. [Docker Installation](#docker-installation)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

- NVIDIA GPU with CUDA support (already installed)
- Windows 10/11, Linux, or macOS
- At least 8GB of RAM (16GB recommended)
- At least 20GB of free disk space for the model
- Internet connection for downloading dependencies

## Installing Python

### Windows

1. **Download Python 3.9-3.11** from [python.org](https://www.python.org/downloads/)
   - Choose the latest Python 3.11.x version
   - Download the Windows installer (64-bit)

2. **Install Python**
   ```powershell
   # Run the installer and check these options:
   # ✓ Add Python to PATH
   # ✓ Install for all users (optional)
   # ✓ Add Python to environment variables
   ```

3. **Verify Installation**
   ```powershell
   python --version
   pip --version
   ```

### Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install Python 3.11 and pip
sudo apt install python3.11 python3.11-pip python3.11-venv python3.11-dev

# Create symlinks (optional)
sudo ln -sf /usr/bin/python3.11 /usr/bin/python
sudo ln -sf /usr/bin/pip3 /usr/bin/pip

# Verify installation
python --version
pip --version
```

### macOS

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11

# Verify installation
python3 --version
pip3 --version
```

## Installing Git

### Windows
1. Download Git from [git-scm.com](https://git-scm.com/download/win)
2. Run the installer with default settings

### Linux
```bash
sudo apt install git
```

### macOS
```bash
brew install git
```

## Setting up the Project

1. **Clone the Repository** (or download the project files)
   ```bash
   git clone <your-repo-url>
   cd deepseek-ocr
   ```

   Or if you have the project files:
   ```bash
   # Extract to your desired location
   cd deepseek-ocr
   ```

2. **Create Python Virtual Environment**
   ```bash
   # Create virtual environment
   python -m venv venv

   # Activate virtual environment
   # Windows:
   venv\Scripts\activate
   
   # Linux/macOS:
   source venv/bin/activate
   ```

3. **Upgrade pip**
   ```bash
   python -m pip install --upgrade pip
   ```

## Installing Dependencies

### Method 1: Install from requirements.txt

```bash
# Make sure your virtual environment is activated
pip install -r requirements.txt
```

### Method 2: Manual Installation (if requirements.txt fails)

```bash
# Core dependencies
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install transformers>=4.35.0
pip install Pillow>=10.0.0
pip install numpy>=1.24.0
pip install opencv-python>=4.8.0

# Web framework
pip install flask>=2.3.0
pip install flask-cors>=4.0.0
pip install werkzeug>=2.3.0

# OCR libraries
pip install easyocr>=1.7.0
pip install pytesseract>=0.3.10

# API and utilities
pip install openai>=1.0.0
pip install requests>=2.31.0
pip install python-dotenv>=1.0.0
pip install pydantic>=2.0.0
pip install loguru>=0.7.0
pip install pyyaml>=6.0.1

# Additional utilities
pip install accelerate>=0.21.0
pip install python-magic>=0.4.27
```

### Installing System Dependencies

#### Windows
- Install [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
- Install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
  ```powershell
  # Download and install from: https://github.com/UB-Mannheim/tesseract/wiki
  # Add to PATH: C:\Program Files\Tesseract-OCR
  ```

#### Linux
```bash
sudo apt update
sudo apt install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgtk-3-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    poppler-utils \
    ffmpeg
```

#### macOS
```bash
brew install tesseract
brew install poppler
brew install ffmpeg
```

## Downloading the Model

### Option 1: Download DeepSeek-VL Model (Recommended for Local Processing)

```bash
# Install git-lfs if not already installed
# Windows: Download from https://git-lfs.github.io/
# Linux: sudo apt install git-lfs
# macOS: brew install git-lfs

git lfs install

# Create models directory
mkdir -p models

# Download the model (this will take some time - ~14GB)
cd models
git clone https://huggingface.co/deepseek-ai/deepseek-vl-7b-chat
cd ..
```

### Option 2: Use API Mode (Requires DeepSeek API Key)

If you prefer to use the API instead of downloading the model:
1. Sign up at [DeepSeek Platform](https://platform.deepseek.com/)
2. Get your API key
3. Set `USE_LOCAL_MODEL=false` in your configuration

## Configuration

1. **Create Environment File**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   ```

2. **Edit Configuration**
   
   Open `.env` file and configure:
   
   **For Local Model:**
   ```env
   # Model Configuration
   USE_LOCAL_MODEL=true
   MODEL_PATH=./models/deepseek-vl-7b-chat
   DEVICE=cuda  # or cpu if no GPU
   
   # Flask Configuration
   FLASK_ENV=development
   SECRET_KEY=your-secret-key-here
   HOST=0.0.0.0
   PORT=5000
   
   # Upload Configuration
   MAX_FILE_SIZE=50MB
   UPLOAD_FOLDER=./uploads
   RESULTS_FOLDER=./results
   
   # Logging
   LOG_LEVEL=INFO
   LOG_FILE=./logs/deepseek_ocr.log
   ```
   
   **For API Mode:**
   ```env
   # API Configuration
   USE_LOCAL_MODEL=false
   DEEPSEEK_API_KEY=your_api_key_here
   OPENAI_API_BASE=https://api.deepseek.com
   
   # Other settings same as above
   ```

3. **Test Configuration**
   ```bash
   python -c "from app.utils.config import get_config; print('Configuration loaded successfully')"
   ```

## Running the Application

### Method 1: Direct Python Execution

```bash
# Make sure virtual environment is activated
# Windows: venv\Scripts\activate
# Linux/macOS: source venv/bin/activate

# Run the application
python -m app.main
```

### Method 2: Using Flask CLI

```bash
# Set environment variables
# Windows:
set FLASK_APP=app.main
set FLASK_ENV=development

# Linux/macOS:
export FLASK_APP=app.main
export FLASK_ENV=development

# Run Flask
flask run --host=0.0.0.0 --port=5000
```

### Method 3: Using the Startup Script

Create a startup script:

**Windows (start.bat):**
```batch
@echo off
call venv\Scripts\activate
python -m app.main
pause
```

**Linux/macOS (start.sh):**
```bash
#!/bin/bash
source venv/bin/activate
python -m app.main
```

Make executable:
```bash
chmod +x start.sh
./start.sh
```

## Docker Installation

### Prerequisites
1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

### Using Docker Compose (Recommended)

```bash
# Navigate to project directory
cd deepseek-ocr

# Build and run with Docker Compose
docker-compose -f docker/docker-compose.yml up --build

# Run in background
docker-compose -f docker/docker-compose.yml up -d --build
```

### Manual Docker Build

```bash
# Build the image
docker build -f docker/Dockerfile -t deepseek-ocr .

# Run the container
docker run -p 5000:5000 \
  --gpus all \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/results:/app/results \
  -v $(pwd)/models:/app/models \
  deepseek-ocr
```

## Accessing the Application

Once running, access the application at:
- **Web Interface:** http://localhost:5000
- **API Documentation:** http://localhost:5000/api/v1/info
- **Health Check:** http://localhost:5000/health

## Verification Steps

1. **Test the Web Interface**
   - Open http://localhost:5000
   - Upload a test image
   - Verify text extraction

2. **Test the API**
   ```bash
   # Test health endpoint
   curl http://localhost:5000/health
   
   # Test file upload (replace with actual image file)
   curl -X POST http://localhost:5000/api/v1/ocr \
     -F "file=@test_image.jpg" \
     -F "prompt=Extract all text"
   ```

3. **Check Logs**
   ```bash
   # View logs
   tail -f logs/deepseek_ocr.log
   ```

## Next Steps

- Read the [API Documentation](API.md)
- Check [Configuration Guide](CONFIGURATION.md)
- See [Troubleshooting Guide](TROUBLESHOOTING.md)
- Run tests: `python -m pytest tests/`

## Performance Optimization

### For Better GPU Performance:
1. Ensure CUDA is properly installed
2. Monitor GPU memory usage
3. Adjust `gpu_memory_fraction` in config
4. Use appropriate model precision (fp16 for faster processing)

### For Better CPU Performance:
1. Increase `max_workers` in config
2. Use smaller batch sizes
3. Enable preprocessing to improve OCR accuracy

### Memory Management:
1. Monitor system memory usage
2. Adjust `cleanup_after` settings
3. Regularly clean up upload and result folders

## Security Considerations

1. Change default secret keys
2. Configure firewall rules
3. Use HTTPS in production
4. Implement rate limiting
5. Regular security updates

## Support

If you encounter any issues:
1. Check the [Troubleshooting Guide](TROUBLESHOOTING.md)
2. Review logs in `logs/deepseek_ocr.log`
3. Ensure all dependencies are properly installed
4. Verify CUDA installation for GPU support
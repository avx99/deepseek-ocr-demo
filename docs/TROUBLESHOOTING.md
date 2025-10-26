# DeepSeek OCR Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the DeepSeek OCR application.

## Table of Contents
1. [Installation Issues](#installation-issues)
2. [Model Loading Problems](#model-loading-problems)
3. [GPU and CUDA Issues](#gpu-and-cuda-issues)
4. [Memory Issues](#memory-issues)
5. [API and Network Issues](#api-and-network-issues)
6. [Performance Issues](#performance-issues)
7. [File Upload Issues](#file-upload-issues)
8. [OCR Accuracy Issues](#ocr-accuracy-issues)
9. [Docker Issues](#docker-issues)
10. [Common Error Messages](#common-error-messages)

## Installation Issues

### Python Version Compatibility

**Problem:** Import errors or dependency conflicts
```
ModuleNotFoundError: No module named 'torch'
```

**Solution:**
1. Ensure Python 3.9-3.11 is installed:
   ```bash
   python --version
   ```
2. Use a virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```
3. Reinstall dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

### Package Installation Failures

**Problem:** Pip install fails with compilation errors

**Solution:**

**Windows:**
1. Install Microsoft Visual C++ Build Tools
2. Use pre-compiled wheels:
   ```bash
   pip install --only-binary=all -r requirements.txt
   ```

**Linux:**
```bash
sudo apt-get update
sudo apt-get install python3-dev build-essential
pip install -r requirements.txt
```

**macOS:**
```bash
xcode-select --install
pip install -r requirements.txt
```

### Missing System Dependencies

**Problem:** OpenCV or other libraries not working

**Solution:**

**Linux:**
```bash
sudo apt-get install libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1
sudo apt-get install tesseract-ocr tesseract-ocr-eng
```

**Windows:**
- Download and install Tesseract OCR from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
- Add to PATH: `C:\Program Files\Tesseract-OCR`

## Model Loading Problems

### Model Not Found

**Problem:**
```
ModelError: Model path not found: ./models/deepseek-vl-7b-chat
```

**Solution:**
1. Download the model:
   ```bash
   git lfs install
   cd models
   git clone https://huggingface.co/deepseek-ai/deepseek-vl-7b-chat
   ```
2. Or use API mode:
   ```bash
   # In .env file:
   USE_LOCAL_MODEL=false
   DEEPSEEK_API_KEY=your_api_key_here
   ```

### Model Loading Timeout

**Problem:** Model takes too long to load or crashes

**Solution:**
1. Check available memory:
   ```bash
   # Linux/macOS:
   free -h
   # Windows:
   wmic OS get TotalVisibleMemorySize,FreePhysicalMemory /format:list
   ```
2. Use lower precision:
   ```yaml
   # In config.yaml:
   model:
     precision: "int8"  # or "fp16"
   ```
3. Reduce GPU memory usage:
   ```yaml
   performance:
     gpu_memory_fraction: 0.6
   ```

### Corrupted Model Files

**Problem:** Model files are corrupted or incomplete

**Solution:**
1. Remove and re-download:
   ```bash
   rm -rf models/deepseek-vl-7b-chat
   git lfs install
   git clone https://huggingface.co/deepseek-ai/deepseek-vl-7b-chat models/deepseek-vl-7b-chat
   ```
2. Verify file integrity:
   ```bash
   git lfs fsck
   ```

## GPU and CUDA Issues

### CUDA Not Available

**Problem:**
```
RuntimeError: CUDA is not available
```

**Solution:**
1. Check CUDA installation:
   ```bash
   nvidia-smi
   nvcc --version
   ```
2. Install PyTorch with CUDA support:
   ```bash
   pip uninstall torch torchvision torchaudio
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```
3. Verify in Python:
   ```python
   import torch
   print(torch.cuda.is_available())
   print(torch.cuda.get_device_name())
   ```

### CUDA Out of Memory

**Problem:**
```
RuntimeError: CUDA out of memory
```

**Solution:**
1. Reduce model precision:
   ```env
   # In .env:
   DEVICE=cuda
   MODEL_PRECISION=int8
   ```
2. Reduce batch size:
   ```yaml
   # In config.yaml:
   performance:
     batch_size: 1
     gpu_memory_fraction: 0.7
   ```
3. Clear GPU cache:
   ```python
   import torch
   torch.cuda.empty_cache()
   ```

### Wrong CUDA Version

**Problem:** PyTorch CUDA version mismatch

**Solution:**
1. Check CUDA version:
   ```bash
   nvidia-smi  # Look at CUDA Version
   ```
2. Install matching PyTorch:
   ```bash
   # For CUDA 11.8:
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   # For CUDA 12.1:
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```

## Memory Issues

### System Out of Memory

**Problem:** System becomes unresponsive or crashes

**Solution:**
1. Monitor memory usage:
   ```bash
   # Linux:
   htop
   # Windows:
   taskmgr
   ```
2. Increase swap space (Linux):
   ```bash
   sudo fallocate -l 8G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```
3. Use CPU mode for large models:
   ```env
   DEVICE=cpu
   ```

### Memory Leaks

**Problem:** Memory usage increases over time

**Solution:**
1. Enable cleanup:
   ```yaml
   upload:
     cleanup_after: 1800  # 30 minutes
   ```
2. Restart the service periodically
3. Monitor with:
   ```bash
   # Check memory usage
   ps aux | grep python
   ```

## API and Network Issues

### Connection Refused

**Problem:**
```
ConnectionError: HTTPConnectionPool(host='localhost', port=5000): Connection refused
```

**Solution:**
1. Check if service is running:
   ```bash
   # Linux/macOS:
   ps aux | grep python
   # Windows:
   tasklist | findstr python
   ```
2. Check port availability:
   ```bash
   # Linux/macOS:
   netstat -ln | grep 5000
   # Windows:
   netstat -an | findstr 5000
   ```
3. Try different port:
   ```env
   PORT=5001
   ```

### API Key Issues

**Problem:**
```
APIError: Invalid API key
```

**Solution:**
1. Verify API key format:
   ```env
   DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
   ```
2. Check API quota and billing
3. Test API key:
   ```bash
   curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://api.deepseek.com/v1/models
   ```

### Rate Limiting

**Problem:**
```
HTTPError: 429 Too Many Requests
```

**Solution:**
1. Implement retry with exponential backoff
2. Reduce request frequency
3. Use batch processing for multiple files
4. Check rate limits in config:
   ```yaml
   api:
     rate_limit: 30  # requests per minute
   ```

## Performance Issues

### Slow OCR Processing

**Problem:** OCR takes too long to complete

**Solution:**
1. Use GPU acceleration:
   ```env
   DEVICE=cuda
   ```
2. Optimize image preprocessing:
   ```yaml
   ocr:
     preprocessing:
       enabled: true
       resize: true
   ```
3. Reduce image size:
   ```yaml
   ocr:
     max_image_size: 2048  # pixels
   ```

### High CPU Usage

**Problem:** CPU usage is consistently high

**Solution:**
1. Limit worker processes:
   ```yaml
   performance:
     max_workers: 2
   ```
2. Use GPU for processing:
   ```env
   DEVICE=cuda
   ```
3. Enable caching:
   ```yaml
   performance:
     cache_enabled: true
   ```

## File Upload Issues

### File Size Limit

**Problem:**
```
Request Entity Too Large: 413
```

**Solution:**
1. Increase file size limit:
   ```env
   MAX_FILE_SIZE=100MB
   ```
2. Compress images before upload
3. Use PDF splitting for large PDFs

### Unsupported File Format

**Problem:**
```
ValidationError: File type not allowed
```

**Solution:**
1. Check allowed formats:
   ```bash
   curl http://localhost:5000/api/v1/info
   ```
2. Convert to supported format:
   ```bash
   # Convert to PNG using ImageMagick
   convert input.xyz output.png
   ```

### File Corruption

**Problem:** Uploaded files are corrupted

**Solution:**
1. Check file integrity before upload
2. Use binary mode for file transfers
3. Increase timeout settings:
   ```yaml
   server:
     timeout: 300  # seconds
   ```

## OCR Accuracy Issues

### Poor Text Recognition

**Problem:** OCR produces inaccurate or garbled text

**Solution:**
1. Improve image quality:
   - Higher resolution
   - Better contrast
   - Remove noise
2. Enable preprocessing:
   ```yaml
   ocr:
     preprocessing:
       enabled: true
       enhance_contrast: true
       denoise: true
   ```
3. Use better prompts:
   ```
   "Extract the printed text from this high-quality document image"
   ```

### Language Detection Issues

**Problem:** Wrong language detected or mixed languages

**Solution:**
1. Specify language in prompt:
   ```
   "Extract all English text from this image"
   "Extract Chinese characters only"
   ```
2. Use language-specific models
3. Preprocess to isolate text regions

### Missing Text

**Problem:** Some text is not detected

**Solution:**
1. Check image quality and resolution
2. Adjust confidence threshold:
   ```yaml
   ocr:
     confidence_threshold: 0.3  # lower threshold
   ```
3. Try different OCR engines:
   ```yaml
   ocr:
     fallback_engines: ["easyocr", "tesseract"]
   ```

## Docker Issues

### Docker Build Fails

**Problem:** Docker build process fails

**Solution:**
1. Clear Docker cache:
   ```bash
   docker system prune -a
   ```
2. Build with verbose output:
   ```bash
   docker build --no-cache -f docker/Dockerfile .
   ```
3. Check system resources:
   ```bash
   docker system df
   ```

### GPU Not Available in Container

**Problem:** NVIDIA GPU not accessible in Docker

**Solution:**
1. Install NVIDIA Container Toolkit:
   ```bash
   # Ubuntu/Debian:
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
   sudo apt-get update && sudo apt-get install -y nvidia-docker2
   sudo systemctl restart docker
   ```
2. Use `--gpus all` flag:
   ```bash
   docker run --gpus all deepseek-ocr
   ```
3. Verify GPU in container:
   ```bash
   docker run --gpus all nvidia/cuda:11.8-runtime-ubuntu22.04 nvidia-smi
   ```

### Container Memory Issues

**Problem:** Container runs out of memory

**Solution:**
1. Increase Docker memory limit:
   ```bash
   # Docker Desktop: Settings > Resources > Memory
   ```
2. Use memory limits:
   ```yaml
   # docker-compose.yml
   services:
     deepseek-ocr:
       deploy:
         resources:
           limits:
             memory: 16G
   ```

## Common Error Messages

### ConfigurationError: Failed to load configuration

**Cause:** Invalid YAML syntax or missing config file

**Solution:**
1. Validate YAML syntax:
   ```bash
   python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"
   ```
2. Check file permissions:
   ```bash
   ls -la config/config.yaml
   ```

### ImportError: No module named '_ctypes'

**Cause:** Missing system libraries

**Solution:**
```bash
# Ubuntu/Debian:
sudo apt-get install libffi-dev
# CentOS/RHEL:
sudo yum install libffi-devel
```

### OSError: libGL.so.1: cannot open shared object file

**Cause:** Missing OpenGL libraries

**Solution:**
```bash
# Ubuntu/Debian:
sudo apt-get install libgl1-mesa-glx
# Or use headless OpenCV:
pip uninstall opencv-python
pip install opencv-python-headless
```

### PermissionError: [Errno 13] Permission denied

**Cause:** Insufficient file permissions

**Solution:**
```bash
# Fix directory permissions:
chmod 755 uploads results logs
# Or run with sudo (not recommended for production):
sudo python -m app.main
```

### ModuleNotFoundError: No module named 'app'

**Cause:** Python path issues

**Solution:**
1. Run from project root:
   ```bash
   cd /path/to/deepseek-ocr
   python -m app.main
   ```
2. Set PYTHONPATH:
   ```bash
   export PYTHONPATH=/path/to/deepseek-ocr:$PYTHONPATH
   ```

## Debugging Tips

### Enable Debug Logging

```env
# In .env:
LOG_LEVEL=DEBUG
FLASK_DEBUG=true
```

### Check System Resources

```bash
# Monitor resources while running:
htop  # or top on older systems
nvidia-smi -l 1  # GPU monitoring
iostat -x 1  # I/O monitoring
```

### Test Components Individually

```python
# Test configuration loading:
from app.utils.config import get_config
config = get_config()
print("Config loaded successfully")

# Test model loading:
from app.ocr.deepseek_ocr import DeepSeekOCR
ocr = DeepSeekOCR(config)
print("Model loaded successfully")

# Test image processing:
from app.utils.image_processor import ImageProcessor
processor = ImageProcessor(config)
image = processor.load_image("test_image.jpg")
print(f"Image loaded: {image.size}")
```

### Collect System Information

```bash
# Create debug info file:
echo "System Information:" > debug_info.txt
echo "==================" >> debug_info.txt
uname -a >> debug_info.txt
python --version >> debug_info.txt
pip list >> debug_info.txt
nvidia-smi >> debug_info.txt
df -h >> debug_info.txt
free -h >> debug_info.txt
```

## Getting Help

If you're still experiencing issues:

1. **Check the logs:**
   ```bash
   tail -f logs/deepseek_ocr.log
   ```

2. **Search existing issues:** Check the GitHub issues page

3. **Create a bug report** with:
   - System information (OS, Python version)
   - Full error message and stack trace
   - Steps to reproduce
   - Configuration files (remove sensitive data)
   - Log files

4. **Community support:** Join our Discord/Slack channels

5. **Professional support:** Contact support for enterprise customers

## Performance Monitoring

### Set up monitoring:

```python
# Add to your application:
import psutil
import GPUtil

def log_system_stats():
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    
    if GPUtil.getGPUs():
        gpu = GPUtil.getGPUs()[0]
        print(f"GPU: {gpu.memoryUtil*100:.1f}% memory, {gpu.load*100:.1f}% load")
    
    print(f"CPU: {cpu_percent}%, Memory: {memory.percent}%")
```

### Automated health checks:

```bash
#!/bin/bash
# health_check.sh
curl -f http://localhost:5000/health || {
    echo "Health check failed, restarting service..."
    systemctl restart deepseek-ocr
}
```

Add to crontab:
```bash
*/5 * * * * /path/to/health_check.sh
```
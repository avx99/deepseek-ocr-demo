# DeepSeek OCR Configuration Guide

This guide explains all configuration options available in the DeepSeek OCR application.

## Configuration Files

The application uses multiple configuration sources:

1. **YAML Configuration** (`config/config.yaml`) - Main configuration file
2. **Environment Variables** (`.env`) - Runtime settings and secrets
3. **Command Line Arguments** - Override specific settings
4. **Default Values** - Built-in fallback values

## Configuration Hierarchy

Settings are applied in the following order (later sources override earlier ones):

1. Default values (hardcoded)
2. YAML configuration file
3. Environment variables
4. Command line arguments

## Environment Variables (.env)

Create a `.env` file in the project root:

```env
# Model Configuration
USE_LOCAL_MODEL=true
MODEL_NAME=deepseek-vl-7b-chat
MODEL_PATH=./models/deepseek-vl-7b-chat
DEVICE=cuda
MODEL_PRECISION=fp16

# API Configuration (if using API mode)
DEEPSEEK_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.deepseek.com

# Flask Server Configuration
FLASK_ENV=development
FLASK_DEBUG=true
SECRET_KEY=your-secret-key-change-this-in-production
HOST=0.0.0.0
PORT=5000

# Upload Configuration
MAX_FILE_SIZE=50MB
ALLOWED_EXTENSIONS=jpg,jpeg,png,bmp,tiff,pdf,webp,gif
UPLOAD_FOLDER=./uploads
RESULTS_FOLDER=./results

# OCR Configuration
OCR_CONFIDENCE_THRESHOLD=0.5
MAX_IMAGE_SIZE=4096
PREPROCESSING_ENABLED=true

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=./logs/deepseek_ocr.log
LOG_ROTATION=10MB
LOG_RETENTION=30

# Performance Configuration
BATCH_SIZE=1
MAX_WORKERS=4
CACHE_ENABLED=true
CACHE_TTL=3600
GPU_MEMORY_FRACTION=0.8

# Security Configuration
MAX_REQUESTS_PER_IP=100
REQUEST_WINDOW=3600
CSRF_PROTECTION=true
```

## YAML Configuration (config/config.yaml)

```yaml
# Server Configuration
server:
  host: "0.0.0.0"          # Server bind address
  port: 5000               # Server port
  debug: false             # Debug mode (true/false)
  secret_key: "change-this-key"  # Flask secret key

# Model Configuration
model:
  name: "deepseek-vl-7b-chat"     # Model identifier
  use_local: true                  # Use local model (true) or API (false)
  local_path: "./models/deepseek-vl-7b-chat"  # Path to local model
  device: "cuda"                   # Device: cuda, cpu, or auto
  precision: "fp16"                # Model precision: fp32, fp16, int8
  max_length: 4096                 # Maximum sequence length
  temperature: 0.1                 # Sampling temperature (0.0-1.0)

# API Configuration (for API mode)
api:
  deepseek_api_key: ""            # DeepSeek API key
  openai_api_base: "https://api.deepseek.com"  # API endpoint
  rate_limit: 60                  # Requests per minute
  timeout: 30                     # Request timeout in seconds

# Upload Configuration
upload:
  max_file_size: 52428800         # Maximum file size in bytes (50MB)
  allowed_extensions:             # Allowed file extensions
    - "jpg"
    - "jpeg"
    - "png"
    - "bmp"
    - "tiff"
    - "pdf"
    - "webp"
    - "gif"
  upload_folder: "./uploads"      # Upload directory
  results_folder: "./results"     # Results directory
  cleanup_after: 3600            # Auto-cleanup time in seconds

# OCR Configuration
ocr:
  confidence_threshold: 0.5       # Minimum confidence for OCR results
  max_image_size: 4096           # Maximum image dimension in pixels
  preprocessing:                  # Image preprocessing options
    enabled: true                 # Enable preprocessing
    resize: true                  # Auto-resize large images
    denoise: true                 # Apply denoising
    enhance_contrast: true        # Enhance image contrast
  fallback_engines:              # Fallback OCR engines
    - "easyocr"
    - "tesseract"

# Logging Configuration
logging:
  level: "INFO"                   # Log level: DEBUG, INFO, WARNING, ERROR
  file: "./logs/deepseek_ocr.log" # Log file path
  rotation: "10 MB"               # Log rotation size
  retention: "30 days"            # Log retention period
  format: "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"

# Performance Configuration
performance:
  batch_size: 1                   # Processing batch size
  max_workers: 4                  # Maximum worker threads
  cache_enabled: true             # Enable result caching
  cache_ttl: 3600                # Cache time-to-live in seconds
  gpu_memory_fraction: 0.8        # GPU memory usage limit (0.1-1.0)

# Security Configuration
security:
  max_requests_per_ip: 100        # Rate limit per IP
  request_window: 3600            # Rate limit window in seconds
  allowed_origins: ["*"]          # CORS allowed origins
  csrf_protection: true           # Enable CSRF protection
```

## Detailed Configuration Options

### Server Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `host` | string | "0.0.0.0" | Server bind address |
| `port` | integer | 5000 | Server port number |
| `debug` | boolean | false | Enable Flask debug mode |
| `secret_key` | string | "change-this" | Flask secret key for sessions |

**Environment Variable Mappings:**
- `HOST` → `server.host`
- `PORT` → `server.port`
- `FLASK_DEBUG` → `server.debug`
- `SECRET_KEY` → `server.secret_key`

### Model Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `name` | string | "deepseek-vl-7b-chat" | Model identifier |
| `use_local` | boolean | true | Use local model vs API |
| `local_path` | string | "./models/..." | Path to local model files |
| `device` | string | "cuda" | Processing device (cuda/cpu/auto) |
| `precision` | string | "fp16" | Model precision (fp32/fp16/int8) |
| `max_length` | integer | 4096 | Maximum token length |
| `temperature` | float | 0.1 | Sampling temperature |

**Device Options:**
- `cuda` - Use GPU (requires CUDA)
- `cpu` - Use CPU only
- `auto` - Automatically detect best device

**Precision Options:**
- `fp32` - Full precision (highest quality, most memory)
- `fp16` - Half precision (good balance)
- `int8` - 8-bit quantization (lowest memory, faster)

### API Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `deepseek_api_key` | string | "" | DeepSeek API key |
| `openai_api_base` | string | "https://api.deepseek.com" | API endpoint URL |
| `rate_limit` | integer | 60 | API requests per minute |
| `timeout` | integer | 30 | Request timeout in seconds |

### Upload Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `max_file_size` | integer | 52428800 | Max file size in bytes |
| `allowed_extensions` | list | [jpg, png, ...] | Allowed file types |
| `upload_folder` | string | "./uploads" | Upload directory |
| `results_folder` | string | "./results" | Results directory |
| `cleanup_after` | integer | 3600 | Auto-cleanup time in seconds |

**File Size Examples:**
- `1048576` = 1MB
- `10485760` = 10MB
- `52428800` = 50MB
- `104857600` = 100MB

### OCR Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `confidence_threshold` | float | 0.5 | Minimum confidence score |
| `max_image_size` | integer | 4096 | Max image dimension |
| `preprocessing.enabled` | boolean | true | Enable image preprocessing |
| `preprocessing.resize` | boolean | true | Auto-resize images |
| `preprocessing.denoise` | boolean | true | Apply noise reduction |
| `preprocessing.enhance_contrast` | boolean | true | Enhance image contrast |
| `fallback_engines` | list | ["easyocr"] | Backup OCR engines |

### Performance Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `batch_size` | integer | 1 | Processing batch size |
| `max_workers` | integer | 4 | Maximum worker threads |
| `cache_enabled` | boolean | true | Enable result caching |
| `cache_ttl` | integer | 3600 | Cache lifetime in seconds |
| `gpu_memory_fraction` | float | 0.8 | GPU memory usage limit |

**Performance Tuning:**
- Increase `batch_size` for better throughput
- Increase `max_workers` for CPU-bound tasks
- Reduce `gpu_memory_fraction` if running out of GPU memory
- Enable `cache_enabled` to avoid reprocessing identical files

### Security Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `max_requests_per_ip` | integer | 100 | Rate limit per IP address |
| `request_window` | integer | 3600 | Rate limit window in seconds |
| `allowed_origins` | list | ["*"] | CORS allowed origins |
| `csrf_protection` | boolean | true | Enable CSRF protection |

## Environment-Specific Configurations

### Development Environment

```yaml
# config/config.dev.yaml
server:
  debug: true
  host: "127.0.0.1"
  
logging:
  level: "DEBUG"
  
security:
  csrf_protection: false
  allowed_origins: ["*"]
```

### Production Environment

```yaml
# config/config.prod.yaml
server:
  debug: false
  host: "0.0.0.0"
  
logging:
  level: "INFO"
  
security:
  csrf_protection: true
  max_requests_per_ip: 50
  allowed_origins: ["https://yourdomain.com"]
  
performance:
  cache_enabled: true
  max_workers: 8
```

### Docker Environment

```yaml
# config/config.docker.yaml
server:
  host: "0.0.0.0"
  
upload:
  upload_folder: "/app/uploads"
  results_folder: "/app/results"
  
logging:
  file: "/app/logs/deepseek_ocr.log"
  
model:
  local_path: "/app/models/deepseek-vl-7b-chat"
```

## Advanced Configuration

### Custom Model Configuration

```yaml
model:
  name: "custom-deepseek-model"
  use_local: true
  local_path: "./models/custom-model"
  device: "cuda"
  precision: "fp16"
  
  # Advanced model settings
  torch_dtype: "float16"
  device_map: "auto"
  load_in_8bit: false
  trust_remote_code: true
  
  # Generation parameters
  max_length: 4096
  temperature: 0.1
  top_p: 0.9
  do_sample: true
  num_beams: 1
```

### Custom OCR Pipeline

```yaml
ocr:
  # Multiple OCR engines with priority
  engines:
    - name: "deepseek"
      priority: 1
      enabled: true
    - name: "easyocr"
      priority: 2
      enabled: true
      languages: ["en", "zh"]
    - name: "tesseract"
      priority: 3
      enabled: false
      
  # Custom preprocessing pipeline
  preprocessing:
    enabled: true
    steps:
      - name: "resize"
        enabled: true
        max_size: 4096
      - name: "contrast"
        enabled: true
        factor: 1.2
      - name: "denoise"
        enabled: true
        strength: 0.8
```

### Database Configuration

```yaml
# Future feature - database integration
database:
  enabled: false
  type: "postgresql"  # postgresql, mysql, sqlite
  host: "localhost"
  port: 5432
  database: "deepseek_ocr"
  username: "ocr_user"
  password: "secure_password"
  
  # Connection pool settings
  pool_size: 10
  max_overflow: 20
  pool_timeout: 30
```

### Monitoring and Metrics

```yaml
monitoring:
  enabled: true
  
  # Prometheus metrics
  prometheus:
    enabled: true
    port: 9090
    
  # Health checks
  health:
    enabled: true
    interval: 30  # seconds
    timeout: 10   # seconds
    
  # Performance metrics
  metrics:
    processing_time: true
    memory_usage: true
    gpu_utilization: true
    error_rates: true
```

## Configuration Validation

The application validates configuration on startup. Common validation errors:

### Invalid File Paths
```yaml
# ❌ Invalid - relative path without ./
model:
  local_path: "models/deepseek"

# ✅ Valid - proper relative path
model:
  local_path: "./models/deepseek"
```

### Invalid Data Types
```yaml
# ❌ Invalid - string instead of integer
server:
  port: "5000"

# ✅ Valid - proper integer
server:
  port: 5000
```

### Missing Required Settings
```yaml
# ❌ Invalid - missing required API key for API mode
model:
  use_local: false
api:
  deepseek_api_key: ""  # Empty key

# ✅ Valid - proper API key
model:
  use_local: false
api:
  deepseek_api_key: "sk-..."
```

## Configuration Best Practices

### Security
1. **Never commit secrets** to version control
2. **Use environment variables** for sensitive data
3. **Rotate API keys** regularly
4. **Limit CORS origins** in production

### Performance
1. **Monitor resource usage** and adjust limits
2. **Use appropriate precision** for your hardware
3. **Enable caching** for repeated requests
4. **Tune batch sizes** based on available memory

### Maintenance
1. **Regular log rotation** to prevent disk space issues
2. **Cleanup temporary files** automatically
3. **Monitor error rates** and adjust thresholds
4. **Keep configuration documented**

### Testing Configuration

```python
# Test configuration loading
from app.utils.config import get_config

try:
    config = get_config()
    print("✅ Configuration loaded successfully")
    print(f"Model: {config.model.name}")
    print(f"Device: {config.model.device}")
    print(f"Server: {config.server.host}:{config.server.port}")
except Exception as e:
    print(f"❌ Configuration error: {e}")
```

### Environment-Specific Loading

```python
import os

# Load different configs based on environment
env = os.getenv('ENVIRONMENT', 'development')
config_file = f"config/config.{env}.yaml"

if os.path.exists(config_file):
    # Load environment-specific config
    pass
else:
    # Fall back to default config
    config_file = "config/config.yaml"
```

## Configuration Templates

### Minimal Configuration (API Mode)
```yaml
server:
  port: 5000
  
model:
  use_local: false
  
api:
  deepseek_api_key: "your-api-key"
```

### High-Performance Configuration (Local Model)
```yaml
server:
  port: 5000
  
model:
  use_local: true
  device: "cuda"
  precision: "fp16"
  
performance:
  batch_size: 4
  max_workers: 8
  gpu_memory_fraction: 0.9
  cache_enabled: true
```

### Development Configuration
```yaml
server:
  debug: true
  port: 5000
  
logging:
  level: "DEBUG"
  
model:
  use_local: false  # Use API for faster development
  
api:
  deepseek_api_key: "dev-api-key"
```

This configuration system provides flexible deployment options while maintaining security and performance. Adjust settings based on your specific hardware, security requirements, and use case.
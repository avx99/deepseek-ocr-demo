"""
Configuration management for DeepSeek OCR
"""

import os
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

from .exceptions import ConfigurationError


@dataclass
class ModelConfig:
    """Model configuration settings"""
    name: str = "deepseek-vl-7b-chat"
    use_local: bool = True
    local_path: str = "./models/deepseek-vl-7b-chat"
    device: str = "cuda"
    precision: str = "fp16"
    max_length: int = 4096
    temperature: float = 0.1


@dataclass
class APIConfig:
    """API configuration settings"""
    deepseek_api_key: str = ""
    openai_api_base: str = "https://api.deepseek.com"
    rate_limit: int = 60
    timeout: int = 30


@dataclass
class ServerConfig:
    """Server configuration settings"""
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    secret_key: str = "your-secret-key-change-this"


@dataclass
class UploadConfig:
    """Upload configuration settings"""
    max_file_size: int = 52428800  # 50MB
    allowed_extensions: list = field(default_factory=lambda: ["jpg", "jpeg", "png", "bmp", "tiff", "pdf", "webp", "gif"])
    upload_folder: str = "./uploads"
    results_folder: str = "./results"
    cleanup_after: int = 3600


@dataclass
class PreprocessingConfig:
    """Image preprocessing configuration"""
    enabled: bool = True
    resize: bool = True
    denoise: bool = True
    enhance_contrast: bool = True


@dataclass
class OCRConfig:
    """OCR configuration settings"""
    confidence_threshold: float = 0.5
    max_image_size: int = 4096
    preprocessing: PreprocessingConfig = field(default_factory=PreprocessingConfig)
    fallback_engines: list = field(default_factory=lambda: ["easyocr", "tesseract"])


@dataclass
class LoggingConfig:
    """Logging configuration settings"""
    level: str = "INFO"
    file: str = "./logs/deepseek_ocr.log"
    rotation: str = "10 MB"
    retention: str = "30 days"
    format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"


@dataclass
class PerformanceConfig:
    """Performance configuration settings"""
    batch_size: int = 1
    max_workers: int = 4
    cache_enabled: bool = True
    cache_ttl: int = 3600
    gpu_memory_fraction: float = 0.8


@dataclass
class SecurityConfig:
    """Security configuration settings"""
    max_requests_per_ip: int = 100
    request_window: int = 3600
    allowed_origins: list = field(default_factory=lambda: ["*"])
    csrf_protection: bool = True


@dataclass
class Config:
    """Main configuration class"""
    server: ServerConfig = field(default_factory=ServerConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    api: APIConfig = field(default_factory=APIConfig)
    upload: UploadConfig = field(default_factory=UploadConfig)
    ocr: OCRConfig = field(default_factory=OCRConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)


class ConfigManager:
    """Manages configuration loading and validation"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "./config/config.yaml"
        self.config = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from files and environment variables"""
        try:
            # Load environment variables
            load_dotenv()
            
            # Load YAML configuration with error handling
            config_data = {}
            if os.path.exists(self.config_path):
                try:
                    with open(self.config_path, 'r', encoding='utf-8') as f:
                        config_data = yaml.safe_load(f) or {}
                except yaml.YAMLError as e:
                    print(f"⚠️  Warning: Error parsing YAML config file: {e}")
                    print("   Using default configuration...")
                    config_data = {}
                except Exception as e:
                    print(f"⚠️  Warning: Could not read config file {self.config_path}: {e}")
                    print("   Using default configuration...")
                    config_data = {}
            else:
                print(f"ℹ️  Config file {self.config_path} not found, using defaults")
            
            # Override with environment variables
            config_data = self._apply_env_overrides(config_data)
            
            # Create config object
            self.config = self._dict_to_config(config_data)
            
            # Validate configuration
            self._validate_config()
            
        except ConfigurationError:
            # Re-raise configuration errors
            raise
        except Exception as e:
            # For other errors, provide helpful message and use defaults
            print(f"⚠️  Warning: Error loading configuration: {e}")
            print("   Using default configuration...")
            try:
                self.config = self._dict_to_config({})
                self._validate_config()
            except Exception as fallback_error:
                raise ConfigurationError(f"Failed to load even default configuration: {fallback_error}")
    
    def _apply_env_overrides(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides"""
        env_mappings = {
            "DEEPSEEK_API_KEY": ["api", "deepseek_api_key"],
            "OPENAI_API_BASE": ["api", "openai_api_base"],
            "MODEL_NAME": ["model", "name"],
            "USE_LOCAL_MODEL": ["model", "use_local"],
            "MODEL_PATH": ["model", "local_path"],
            "DEVICE": ["model", "device"],
            "FLASK_ENV": ["server", "debug"],
            "FLASK_DEBUG": ["server", "debug"],
            "SECRET_KEY": ["server", "secret_key"],
            "HOST": ["server", "host"],
            "PORT": ["server", "port"],
            "MAX_FILE_SIZE": ["upload", "max_file_size"],
            "UPLOAD_FOLDER": ["upload", "upload_folder"],
            "RESULTS_FOLDER": ["upload", "results_folder"],
            "LOG_LEVEL": ["logging", "level"],
            "LOG_FILE": ["logging", "file"],
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Navigate to the nested config location
                current = config_data
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                
                # Convert string values to appropriate types
                final_key = config_path[-1]
                try:
                    if env_var in ["USE_LOCAL_MODEL", "FLASK_DEBUG"]:
                        current[final_key] = env_value.lower() in ("true", "1", "yes")
                    elif env_var in ["PORT", "MAX_FILE_SIZE"]:
                        # Handle both numeric strings and human-readable sizes
                        if env_var == "MAX_FILE_SIZE" and not env_value.isdigit():
                            # Parse human-readable sizes like "50MB", "10GB"
                            current[final_key] = self._parse_size(env_value)
                        else:
                            current[final_key] = int(env_value)
                    else:
                        current[final_key] = env_value
                except ValueError as e:
                    print(f"⚠️  Warning: Invalid value for {env_var}: {env_value} - {e}")
                    print(f"   Using default value for {env_var}")
        
        return config_data
    
    def _parse_size(self, size_str: str) -> int:
        """Parse human-readable size string to bytes"""
        size_str = size_str.upper().strip()
        
        # Size multipliers
        multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 * 1024,
            'GB': 1024 * 1024 * 1024,
            'TB': 1024 * 1024 * 1024 * 1024
        }
        
        # Extract number and unit
        import re
        match = re.match(r'^(\d+(?:\.\d+)?)\s*([KMGT]?B)?$', size_str)
        if not match:
            raise ValueError(f"Invalid size format: {size_str}")
        
        number, unit = match.groups()
        number = float(number)
        unit = unit or 'B'
        
        if unit not in multipliers:
            raise ValueError(f"Unknown size unit: {unit}")
        
        return int(number * multipliers[unit])
    
    def _dict_to_config(self, config_data: Dict[str, Any]) -> Config:
        """Convert dictionary to Config object"""
        try:
            # Create nested config objects
            server_config = ServerConfig(**config_data.get("server", {}))
            model_config = ModelConfig(**config_data.get("model", {}))
            api_config = APIConfig(**config_data.get("api", {}))
            upload_config = UploadConfig(**config_data.get("upload", {}))
            
            # Handle preprocessing config
            preprocessing_data = config_data.get("ocr", {}).get("preprocessing", {})
            preprocessing_config = PreprocessingConfig(**preprocessing_data)
            
            ocr_data = config_data.get("ocr", {})
            ocr_data["preprocessing"] = preprocessing_config
            ocr_config = OCRConfig(**ocr_data)
            
            logging_config = LoggingConfig(**config_data.get("logging", {}))
            performance_config = PerformanceConfig(**config_data.get("performance", {}))
            security_config = SecurityConfig(**config_data.get("security", {}))
            
            return Config(
                server=server_config,
                model=model_config,
                api=api_config,
                upload=upload_config,
                ocr=ocr_config,
                logging=logging_config,
                performance=performance_config,
                security=security_config
            )
            
        except Exception as e:
            raise ConfigurationError(f"Failed to parse configuration: {e}")
    
    def _validate_config(self):
        """Validate configuration settings"""
        # Validate model configuration
        if self.config.model.use_local and not self.config.model.local_path:
            raise ConfigurationError("Local model path required when use_local is True")
        
        if not self.config.model.use_local and not self.config.api.deepseek_api_key:
            raise ConfigurationError("DeepSeek API key required when using API")
        
        # Validate upload configuration
        if self.config.upload.max_file_size <= 0:
            raise ConfigurationError("Max file size must be positive")
        
        # Validate server configuration
        if not (1 <= self.config.server.port <= 65535):
            raise ConfigurationError("Server port must be between 1 and 65535")
        
        # Create necessary directories with error handling
        try:
            os.makedirs(self.config.upload.upload_folder, exist_ok=True)
            os.makedirs(self.config.upload.results_folder, exist_ok=True)
            log_dir = os.path.dirname(self.config.logging.file)
            if log_dir:  # Only create if there's a directory path
                os.makedirs(log_dir, exist_ok=True)
        except Exception as e:
            print(f"⚠️  Warning: Could not create directories: {e}")
            print("   Please ensure you have write permissions to the project directory")
    
    def get_config(self) -> Config:
        """Get the current configuration"""
        return self.config
    
    def reload_config(self):
        """Reload configuration from files"""
        self._load_config()


# Global config instance
_config_manager = None


def get_config() -> Config:
    """Get the global configuration instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager.get_config()


def reload_config():
    """Reload the global configuration"""
    global _config_manager
    if _config_manager is not None:
        _config_manager.reload_config()
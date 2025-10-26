"""
Unit tests for configuration management
"""

import os
import tempfile
import pytest
from unittest.mock import patch, mock_open

from app.utils.config import Config, ConfigManager, get_config
from app.utils.exceptions import ConfigurationError


class TestConfigClasses:
    """Test configuration data classes"""
    
    def test_default_config_creation(self):
        """Test creating config with default values"""
        config = Config()
        
        assert config.server.host == "0.0.0.0"
        assert config.server.port == 5000
        assert config.model.name == "deepseek-vl-7b-chat"
        assert config.model.use_local == True
        assert config.upload.max_file_size == 52428800
        assert config.ocr.confidence_threshold == 0.5
    
    def test_config_field_types(self):
        """Test configuration field types"""
        config = Config()
        
        assert isinstance(config.server.port, int)
        assert isinstance(config.server.debug, bool)
        assert isinstance(config.model.temperature, float)
        assert isinstance(config.upload.allowed_extensions, list)


class TestConfigManager:
    """Test configuration manager"""
    
    def test_config_manager_creation(self):
        """Test creating config manager"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
server:
  port: 8080
model:
  name: "test-model"
""")
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            assert manager.config.server.port == 8080
            assert manager.config.model.name == "test-model"
        finally:
            os.unlink(config_path)
    
    def test_config_manager_missing_file(self):
        """Test config manager with missing file"""
        manager = ConfigManager("nonexistent.yaml")
        # Should create config with defaults
        assert manager.config.server.port == 5000
    
    @patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'test-key', 'PORT': '8080'})
    def test_env_variable_override(self):
        """Test environment variable overrides"""
        manager = ConfigManager("nonexistent.yaml")
        
        assert manager.config.api.deepseek_api_key == 'test-key'
        assert manager.config.server.port == 8080
    
    def test_invalid_yaml(self):
        """Test handling of invalid YAML"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_path = f.name
        
        try:
            with pytest.raises(ConfigurationError):
                ConfigManager(config_path)
        finally:
            os.unlink(config_path)
    
    def test_config_validation_local_model_missing_path(self):
        """Test validation fails when local model path is missing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
model:
  use_local: true
  local_path: ""
""")
            config_path = f.name
        
        try:
            with pytest.raises(ConfigurationError, match="Local model path required"):
                ConfigManager(config_path)
        finally:
            os.unlink(config_path)
    
    def test_config_validation_api_mode_missing_key(self):
        """Test validation fails when API key is missing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
model:
  use_local: false
api:
  deepseek_api_key: ""
""")
            config_path = f.name
        
        try:
            with pytest.raises(ConfigurationError, match="DeepSeek API key required"):
                ConfigManager(config_path)
        finally:
            os.unlink(config_path)
    
    def test_config_validation_invalid_port(self):
        """Test validation fails with invalid port"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
server:
  port: 70000
""")
            config_path = f.name
        
        try:
            with pytest.raises(ConfigurationError, match="Server port must be between"):
                ConfigManager(config_path)
        finally:
            os.unlink(config_path)
    
    def test_config_reload(self):
        """Test configuration reloading"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
server:
  port: 6000
""")
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            assert manager.config.server.port == 6000
            
            # Modify file
            with open(config_path, 'w') as f:
                f.write("""
server:
  port: 7000
""")
            
            # Reload config
            manager.reload_config()
            assert manager.config.server.port == 7000
        finally:
            os.unlink(config_path)


class TestGlobalConfig:
    """Test global configuration functions"""
    
    def test_get_config(self):
        """Test getting global config"""
        config = get_config()
        assert isinstance(config, Config)
    
    @patch('app.utils.config._config_manager', None)
    def test_get_config_creates_manager(self):
        """Test that get_config creates manager if not exists"""
        config = get_config()
        assert isinstance(config, Config)


class TestConfigIntegration:
    """Integration tests for configuration"""
    
    def test_complete_config_flow(self):
        """Test complete configuration loading flow"""
        yaml_content = """
server:
  host: "127.0.0.1"
  port: 9000
  debug: true

model:
  name: "custom-model"
  use_local: false
  device: "cpu"
  precision: "fp32"

api:
  deepseek_api_key: "test-key"
  timeout: 60

upload:
  max_file_size: 10485760
  allowed_extensions: ["jpg", "png"]

ocr:
  confidence_threshold: 0.7
  max_image_size: 2048
  preprocessing:
    enabled: false

logging:
  level: "WARNING"
  file: "/tmp/test.log"

performance:
  batch_size: 5
  max_workers: 8
  cache_enabled: false

security:
  max_requests_per_ip: 50
  csrf_protection: false
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            config_path = f.name
        
        try:
            manager = ConfigManager(config_path)
            config = manager.get_config()
            
            # Verify all sections
            assert config.server.host == "127.0.0.1"
            assert config.server.port == 9000
            assert config.server.debug == True
            
            assert config.model.name == "custom-model"
            assert config.model.use_local == False
            assert config.model.device == "cpu"
            assert config.model.precision == "fp32"
            
            assert config.api.deepseek_api_key == "test-key"
            assert config.api.timeout == 60
            
            assert config.upload.max_file_size == 10485760
            assert config.upload.allowed_extensions == ["jpg", "png"]
            
            assert config.ocr.confidence_threshold == 0.7
            assert config.ocr.max_image_size == 2048
            assert config.ocr.preprocessing.enabled == False
            
            assert config.logging.level == "WARNING"
            assert config.logging.file == "/tmp/test.log"
            
            assert config.performance.batch_size == 5
            assert config.performance.max_workers == 8
            assert config.performance.cache_enabled == False
            
            assert config.security.max_requests_per_ip == 50
            assert config.security.csrf_protection == False
            
        finally:
            os.unlink(config_path)


if __name__ == '__main__':
    pytest.main([__file__])
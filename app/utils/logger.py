"""
Logging configuration and utilities
"""

import os
import sys
from loguru import logger
from typing import Optional

from .config import Config


def setup_logging(config: Config):
    """
    Configure logging based on the provided configuration
    
    Args:
        config: Configuration object containing logging settings
    """
    try:
        # Remove default logger
        logger.remove()
        
        # Ensure log directory exists
        log_dir = os.path.dirname(config.logging.file)
        os.makedirs(log_dir, exist_ok=True)
        
        # Add console handler
        logger.add(
            sys.stderr,
            format=config.logging.format,
            level=config.logging.level,
            colorize=True
        )
        
        # Add file handler with rotation
        logger.add(
            config.logging.file,
            format=config.logging.format,
            level=config.logging.level,
            rotation=config.logging.rotation,
            retention=config.logging.retention,
            compression="zip"
        )
        
        logger.info("Logging configured successfully")
        
    except Exception as e:
        print(f"Failed to configure logging: {e}")
        # Fallback to basic logging
        logger.add(sys.stderr, level="INFO")


def get_logger(name: Optional[str] = None):
    """
    Get a logger instance
    
    Args:
        name: Optional logger name
        
    Returns:
        Logger instance
    """
    if name:
        return logger.bind(name=name)
    return logger
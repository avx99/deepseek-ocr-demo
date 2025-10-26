#!/usr/bin/env python3
"""
Main launcher script for DeepSeek OCR application
Run this file from the project root directory
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

if __name__ == '__main__':
    try:
        from app.main import create_app
        
        # Create and run the application
        app = create_app()
        
        # Get configuration for host and port
        from app.utils.config import get_config
        config = get_config()
        
        print(f"🚀 Starting DeepSeek OCR Server...")
        print(f"📝 Server will be available at: http://{config.server.host}:{config.server.port}")
        print(f"📁 Upload directory: {os.path.join(project_root, 'uploads')}")
        print(f"📊 Results directory: {os.path.join(project_root, 'results')}")
        print(f"📋 Logs directory: {os.path.join(project_root, 'logs')}")
        print()
        
        # Check OCR configuration
        if config.model.use_local:
            print("🔧 Mode: Local Model")
            if not os.path.exists(config.model.local_path):
                print("⚠️  Warning: Local model path not found - will fall back to API/demo mode")
        elif config.api.deepseek_api_key:
            print("🌐 Mode: API")
        else:
            print("🎭 Mode: Demo (No model or API key configured)")
            print("   To enable full OCR:")
            print("   1. Get API key: https://platform.deepseek.com/")
            print("   2. Set DEEPSEEK_API_KEY environment variable, OR")
            print("   3. Download local model and set use_local: true in config")
        
        print()
        print("✅ Application started successfully!")
        print("🌐 Open your browser and navigate to the URL above")
        print("🛑 Press Ctrl+C to stop the server")
        print("-" * 50)
        
        app.run(
            host=config.server.host,
            port=config.server.port,
            debug=config.server.debug
        )
        
    except ImportError as e:
        print("❌ Import Error:")
        print(f"   {str(e)}")
        print()
        print("🔧 Troubleshooting:")
        print("   1. Make sure you've activated your virtual environment:")
        print("      .\\deepseek-ocr-env\\Scripts\\Activate.ps1")
        print()
        print("   2. Install the required dependencies:")
        print("      pip install -r requirements.txt")
        print()
        print("   3. If you have GPU support, install PyTorch with CUDA:")
        print("      pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
        print()
        sys.exit(1)
        
    except Exception as e:
        print("❌ Startup Error:")
        print(f"   {str(e)}")
        print()
        print("🔧 Check the troubleshooting guide in docs/TROUBLESHOOTING.md")
        sys.exit(1)
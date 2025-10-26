#!/usr/bin/env python3
"""
Dependency checker for DeepSeek OCR project
Run this to verify all required packages are installed
"""

import sys
import subprocess
import importlib
from typing import List, Tuple

# Required packages and their import names
REQUIRED_PACKAGES = [
    ("flask", "flask"),
    ("flask-cors", "flask_cors"),
    ("torch", "torch"),
    ("transformers", "transformers"),
    ("pillow", "PIL"),
    ("opencv-python", "cv2"),
    ("numpy", "numpy"),
    ("pyyaml", "yaml"),
    ("python-dotenv", "dotenv"),
    ("loguru", "loguru"),
    ("requests", "requests"),
]

OPTIONAL_PACKAGES = [
    ("pytest", "pytest"),
    ("pytest-cov", "pytest_cov"),
    ("pytest-mock", "pytest_mock"),
    ("black", "black"),
    ("flake8", "flake8"),
]


def check_package(package_name: str, import_name: str) -> Tuple[bool, str]:
    """Check if a package is installed and importable"""
    try:
        importlib.import_module(import_name)
        return True, "✅ Installed"
    except ImportError:
        return False, "❌ Missing"
    except Exception as e:
        return False, f"⚠️  Error: {str(e)[:50]}"


def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"🐍 Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major != 3 or version.minor < 9:
        print("❌ Python 3.9+ is required")
        return False
    elif version.minor >= 12:
        print("⚠️  Python 3.12+ detected - some packages may have compatibility issues")
    else:
        print("✅ Python version is compatible")
    
    return True


def check_cuda():
    """Check CUDA availability"""
    try:
        import torch
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            device_name = torch.cuda.get_device_name(0) if device_count > 0 else "Unknown"
            print(f"🎮 CUDA: Available ({device_count} device(s), {device_name})")
        else:
            print("🎮 CUDA: Not available (CPU mode will be used)")
    except ImportError:
        print("🎮 CUDA: Cannot check (PyTorch not installed)")


def install_missing_packages(missing_packages: List[str]):
    """Attempt to install missing packages"""
    if not missing_packages:
        return
    
    print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--upgrade"
        ] + missing_packages)
        print("✅ Installation completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        print("Please install manually using:")
        print(f"   pip install {' '.join(missing_packages)}")


def main():
    """Main dependency checker"""
    print("🔍 DeepSeek OCR Dependency Checker")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        print("\n❌ Python version check failed")
        sys.exit(1)
    
    print("\n📋 Checking Required Packages:")
    print("-" * 30)
    
    missing_packages = []
    
    for package_name, import_name in REQUIRED_PACKAGES:
        is_installed, status = check_package(package_name, import_name)
        print(f"{status:15} {package_name}")
        
        if not is_installed:
            missing_packages.append(package_name)
    
    print("\n📋 Checking Optional Packages:")
    print("-" * 30)
    
    for package_name, import_name in OPTIONAL_PACKAGES:
        is_installed, status = check_package(package_name, import_name)
        print(f"{status:15} {package_name} (optional)")
    
    # Check CUDA
    print("\n🎮 Hardware Support:")
    print("-" * 20)
    check_cuda()
    
    # Summary
    print("\n📊 Summary:")
    print("-" * 10)
    
    if missing_packages:
        print(f"❌ Missing {len(missing_packages)} required package(s)")
        print(f"   Missing: {', '.join(missing_packages)}")
        
        print("\n🔧 Installation Commands:")
        print("   Option 1 - Install all requirements:")
        print("   pip install -r requirements.txt")
        print()
        print("   Option 2 - Install missing packages only:")
        print(f"   pip install {' '.join(missing_packages)}")
        print()
        print("   Option 3 - For GPU support (if you have CUDA):")
        print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
        
        # Ask user if they want to install automatically
        try:
            response = input("\n❓ Would you like to install missing packages now? (y/N): ")
            if response.lower().startswith('y'):
                install_missing_packages(missing_packages)
            else:
                print("   Please install the missing packages manually before running the application.")
        except KeyboardInterrupt:
            print("\n   Installation cancelled.")
        
        return False
    else:
        print("✅ All required packages are installed!")
        print("🚀 You can now run the application with:")
        print("   python run_server.py")
        return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Setup script untuk Auto-DC Discord Bot
Membantu instalasi dan konfigurasi awal
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ diperlukan!")
        sys.exit(1)
    print("✅ Python version compatible")

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        sys.exit(1)

def setup_environment():
    """Setup environment file"""
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ .env file created from template")
        print("⚠️  Please edit .env file with your configuration")
    else:
        print("ℹ️  .env file already exists")

def create_directories():
    """Create necessary directories"""
    dirs = [
        "src/logs",
        ".temp",
        ".backups",
        "tests"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directories created")

def main():
    """Main setup function"""
    print("🚀 Setting up Auto-DC Discord Bot...")
    
    check_python_version()
    install_dependencies()
    setup_environment()
    create_directories()
    
    print("\n🎉 Setup completed!")
    print("\n📝 Next steps:")
    print("1. Edit .env file with your bot token and configuration")
    print("2. Run: python main.py")

if __name__ == "__main__":
    main()

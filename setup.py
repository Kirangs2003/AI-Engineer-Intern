#!/usr/bin/env python3
"""
Setup script for AI Marksheet Extraction API
"""

import os
import sys
import subprocess

def create_env_file():
    """Create .env file if it doesn't exist"""
    if not os.path.exists('.env'):
        print("Creating .env file...")
        with open('.env', 'w') as f:
            f.write("# Gemini API Configuration\n")
            f.write("GEMINI_API_KEY=your_gemini_api_key_here\n\n")
            f.write("# API Configuration\n")
            f.write("API_HOST=0.0.0.0\n")
            f.write("API_PORT=8000\n")
        print("✅ .env file created. Please add your Gemini API key.")
    else:
        print("✅ .env file already exists.")

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def test_imports():
    """Test if all imports work"""
    print("Testing imports...")
    try:
        import streamlit
        import google.generativeai
        import fastapi
        import uvicorn
        import pydantic
        from PIL import Image
        import PyPDF2
        import requests
        print("✅ All imports successful.")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    print("AI Marksheet Extraction API - Setup")
    print("=" * 40)
    
    # Create .env file
    create_env_file()
    
    # Install dependencies
    if not install_dependencies():
        print("Setup failed. Please check the error messages above.")
        return False
    
    # Test imports
    if not test_imports():
        print("Setup failed. Please check the error messages above.")
        return False
    
    print("\n" + "=" * 40)
    print("✅ Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file and add your Gemini API key")
    print("2. Run: python run_api.py (for API server)")
    print("3. Run: python run_streamlit.py (for web UI)")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

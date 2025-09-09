#!/usr/bin/env python3
"""
Test script to verify the setup and dependencies
"""

import sys
import importlib
import os

def test_imports():
    """Test if all required packages can be imported"""
    required_packages = [
        'streamlit',
        'google.generativeai',
        'fastapi',
        'uvicorn',
        'pydantic',
        'PIL',
        'PyPDF2',
        'dotenv',
        'requests'
    ]
    
    print("Testing package imports...")
    failed_imports = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError as e:
            print(f"❌ {package}: {e}")
            failed_imports.append(package)
    
    return failed_imports

def test_config():
    """Test configuration"""
    print("\nTesting configuration...")
    
    # Check if .env file exists
    if os.path.exists('.env'):
        print("✅ .env file found")
    else:
        print("⚠️  .env file not found - you'll need to create one with your GEMINI_API_KEY")
    
    # Check if config can be imported
    try:
        from config import GEMINI_API_KEY, MAX_FILE_SIZE, ALLOWED_EXTENSIONS
        print("✅ Configuration loaded successfully")
        print(f"   Max file size: {MAX_FILE_SIZE // (1024*1024)} MB")
        print(f"   Allowed extensions: {list(ALLOWED_EXTENSIONS)}")
        
        if GEMINI_API_KEY:
            print("✅ Gemini API key is configured")
        else:
            print("⚠️  Gemini API key not configured")
            
    except Exception as e:
        print(f"❌ Configuration error: {e}")

def test_models():
    """Test if models can be imported and instantiated"""
    print("\nTesting data models...")
    
    try:
        from models import MarksheetExtractionResponse, ExtractedField, FieldType
        print("✅ Data models imported successfully")
        
        # Test creating a sample field
        sample_field = ExtractedField(
            value="Test Value",
            confidence=0.95,
            field_type=FieldType.STRING
        )
        print("✅ Sample field created successfully")
        
    except Exception as e:
        print(f"❌ Model error: {e}")

def main():
    print("AI Marksheet Extraction - Setup Test")
    print("=" * 50)
    
    # Test imports
    failed_imports = test_imports()
    
    # Test configuration
    test_config()
    
    # Test models
    test_models()
    
    print("\n" + "=" * 50)
    
    if failed_imports:
        print(f"❌ Setup incomplete. Missing packages: {', '.join(failed_imports)}")
        print("Run: pip install -r requirements.txt")
        return False
    else:
        print("✅ Setup looks good!")
        print("\nNext steps:")
        print("1. Create a .env file with your GEMINI_API_KEY")
        print("2. Run the API: python run_api.py")
        print("3. Run the UI: python run_streamlit.py")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

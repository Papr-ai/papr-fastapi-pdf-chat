#!/usr/bin/env python3
"""
Test script to verify the FastAPI PDF Chat setup
"""
import os
import sys
from pathlib import Path

def check_environment():
    """Check if environment variables are set"""
    required_vars = ['PAPR_MEMORY_API_KEY', 'OPENAI_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var) or os.getenv(var) == f'your_{var.lower()}_here':
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing or default environment variables: {', '.join(missing_vars)}")
        print("Please edit .env file and add your actual API keys")
        return False
    
    print("✅ Environment variables are set")
    return True

def check_imports():
    """Check if all required packages can be imported"""
    try:
        import fastapi
        import papr_memory
        import openai
        import fitz  # PyMuPDF
        import pydantic
        import uvicorn
        print("✅ All required packages can be imported")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def check_file_structure():
    """Check if required files exist"""
    required_files = [
        'app/main.py',
        'app/services/papr_service.py',
        'app/services/llm_service.py',
        'app/services/chat_service.py',
        'static/index.html',
        'requirements.txt'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files are present")
    return True

def main():
    print("🧪 Testing FastAPI PDF Chat Setup")
    print("=" * 35)
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("⚠️  python-dotenv not installed, skipping .env loading")
    
    checks = [
        check_file_structure,
        check_imports,
        check_environment
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
        print()
    
    if all_passed:
        print("🎉 Setup test completed successfully!")
        print("\nNext steps:")
        print("1. Edit .env file and add your API keys")
        print("2. Run: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print("3. Open: http://localhost:8000")
        return 0
    else:
        print("❌ Setup test failed. Please fix the issues above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())

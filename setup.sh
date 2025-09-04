#!/bin/bash

# FastAPI PDF Chat - Setup Script
# This script automates the setup process for the FastAPI PDF Chat application

set -e  # Exit on any error

echo "🚀 FastAPI PDF Chat - Setup Script"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3.8+ is installed
print_status "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)"; then
    print_error "Python $PYTHON_VERSION found, but Python 3.8+ is required."
    exit 1
fi

print_success "Python $PYTHON_VERSION detected"

# Check if pip is installed
print_status "Checking pip installation..."
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed. Please install pip."
    exit 1
fi

print_success "pip3 is available"

# Create virtual environment
print_status "Creating virtual environment..."
if [ -d "venv" ]; then
    print_warning "Virtual environment already exists. Skipping creation."
else
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
python3 -m pip install --upgrade pip

# Install requirements
print_status "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_success "Dependencies installed successfully"
else
    print_error "requirements.txt not found!"
    exit 1
fi

# Create .env file if it doesn't exist
print_status "Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
# FastAPI PDF Chat Configuration
# Copy this file to .env and fill in your actual API keys

# Required API Keys
PAPR_MEMORY_API_KEY=your_papr_memory_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Optional Configuration
LOG_LEVEL=INFO
MAX_FILE_SIZE=10485760
ENVIRONMENT=development

# CORS Configuration (for production)
# CORS_ORIGINS=["https://yourdomain.com"]
EOF
    print_success ".env file created with template"
    print_warning "⚠️  Please edit .env file and add your actual API keys!"
else
    print_warning ".env file already exists. Skipping creation."
fi

# Create .gitignore if it doesn't exist
print_status "Setting up .gitignore..."
if [ ! -f ".gitignore" ]; then
    cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environment
venv/
env/
ENV/

# Environment Variables
.env
.env.local
.env.production
.env.development

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Application Specific
documents_store.json
*.log
uploads/
temp/

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Documentation
docs/_build/
EOF
    print_success ".gitignore created"
else
    print_warning ".gitignore already exists. Skipping creation."
fi

# Verify installation
print_status "Verifying installation..."

# Check if all required packages are installed
python3 -c "
import fastapi
import papr_memory
import openai
import fitz  # PyMuPDF
import pydantic
import uvicorn
print('✅ All required packages are installed')
" 2>/dev/null || {
    print_error "Some packages failed to install correctly"
    exit 1
}

print_success "Installation verification completed"

# Create a simple test script
print_status "Creating test script..."
cat > test_setup.py << 'EOF'
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
EOF

print_success "Test script created (test_setup.py)"

# Final instructions
echo ""
print_success "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your API keys:"
echo "   - Get Papr Memory API key: https://papr.ai"
echo "   - Get OpenAI API key: https://platform.openai.com"
echo ""
echo "2. Test your setup:"
echo "   python3 test_setup.py"
echo ""
echo "3. Start the application:"
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "4. Open your browser:"
echo "   http://localhost:8000"
echo ""
print_warning "⚠️  Don't forget to edit .env file with your actual API keys!"
echo ""
echo "For more information, see README.md"

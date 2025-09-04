# Contributing to FastAPI PDF Chat

Thank you for your interest in contributing to the FastAPI PDF Chat application! This project demonstrates best practices for integrating Papr Memory SDK with FastAPI and OpenAI.

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Papr Memory API Key ([Get one here](https://papr.ai))
- OpenAI API Key ([Get one here](https://platform.openai.com))

### Quick Setup
```bash
git clone https://github.com/Papr-ai/papr-fastapi-pdf-chat.git
cd papr-fastapi-pdf-chat
./setup.sh
```

## 🛠️ Development Environment

### 1. Set up virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run the application
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📋 How to Contribute

### Reporting Issues
- Use the [issue tracker](../../issues) to report bugs
- Include detailed reproduction steps
- Provide error messages and logs
- Specify your environment (OS, Python version, etc.)

### Suggesting Features
- Open an issue with the "enhancement" label
- Describe the feature and its use case
- Explain how it would benefit users
- Consider implementation complexity

### Submitting Pull Requests

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Test thoroughly**
5. **Update documentation**
6. **Commit with clear messages**
   ```bash
   git commit -m "feat: add new PDF processing feature"
   ```
7. **Push and create PR**

## 🎯 Development Guidelines

### Code Style
- Follow PEP 8 for Python code
- Use type hints for all functions
- Add docstrings for public methods
- Keep functions focused and small

### Error Handling
```python
# Good: Specific error handling with logging
try:
    result = papr_service.add_document(content)
except PaprMemoryError as e:
    logger.error(f"Papr Memory error: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Document processing failed")
```

### Testing
- Test your changes locally
- Ensure all existing functionality works
- Add tests for new features
- Verify error scenarios

### Documentation
- Update README.md if needed
- Add API documentation for new endpoints
- Update TROUBLESHOOTING.md for new issues
- Include code examples

## 🏗️ Project Structure

```
app/
├── main.py                 # FastAPI application entry point
├── models/
│   └── schemas.py          # Pydantic models
├── routers/
│   ├── chat.py            # Chat endpoints
│   ├── documents.py       # Document management
│   └── upload_progress.py # Progress tracking
└── services/
    ├── chat_service.py    # Chat logic
    ├── llm_service.py     # OpenAI integration
    └── papr_service.py    # Papr Memory integration
```

## 🔍 Areas for Contribution

### High Priority
- **Performance optimizations** for large PDF processing
- **Additional file format support** (DOCX, TXT, etc.)
- **Enhanced error handling** and user feedback
- **UI/UX improvements** in the web interface

### Medium Priority
- **Testing framework** setup and test coverage
- **Docker improvements** for easier deployment
- **Configuration management** enhancements
- **Logging and monitoring** improvements

### Low Priority
- **Code refactoring** for better maintainability
- **Documentation improvements** and examples
- **CI/CD pipeline** setup
- **Additional deployment options**

## 🧪 Testing Your Changes

### Manual Testing
1. **Upload various PDF sizes** and formats
2. **Test chat functionality** with different queries
3. **Verify error handling** with invalid inputs
4. **Check progress tracking** during uploads
5. **Test cross-document search** capabilities

### Automated Testing
```bash
# Run the setup validation
python3 test_setup.py

# Test API endpoints
curl -X GET http://localhost:8000/health
curl -X GET http://localhost:8000/documents/list
```

## 📝 Commit Message Guidelines

Use conventional commits format:
- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation changes
- `style:` formatting changes
- `refactor:` code refactoring
- `test:` adding tests
- `chore:` maintenance tasks

Examples:
```bash
feat: add support for DOCX file uploads
fix: resolve progress tracking race condition
docs: update API reference for new endpoints
```

## 🔒 Security Guidelines

- **Never commit API keys** or sensitive data
- **Validate all user inputs** properly
- **Use environment variables** for configuration
- **Follow OWASP security practices**
- **Report security issues** privately

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Papr Memory Python SDK](https://github.com/Papr-ai/papr-pythonSDK)
- [OpenAI API Reference](https://platform.openai.com/docs)
- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/)

## 🤝 Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Documentation**: Check README.md and DEVELOPMENT.md
- **Troubleshooting**: See TROUBLESHOOTING.md for common issues

## 🎉 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- GitHub contributor graphs

Thank you for contributing to the FastAPI PDF Chat project! 🚀

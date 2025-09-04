# Development Guide

This guide provides detailed information for developers who want to contribute to or extend the FastAPI PDF Chat application.

## 🏗️ Architecture Deep Dive

### Service Layer Architecture

The application follows a clean architecture pattern with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Routers       │    │   Services      │    │   External      │
│   (FastAPI)     │────│   (Business     │────│   APIs          │
│                 │    │    Logic)       │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
│                      │                      │
├── chat.py           ├── chat_service.py    ├── Papr Memory
├── documents.py      ├── llm_service.py     ├── OpenAI API
└── upload_progress.py├── papr_service.py    └── PyMuPDF
                      └── document_store.py
```

### Key Design Patterns

#### 1. Dependency Injection
Services are injected into routers to maintain loose coupling:

```python
# In routers/chat.py
@router.post("/")
async def chat_endpoint(request: ChatRequest):
    papr_service = PaprService()
    chat_service = ChatService(papr_service)
    return await chat_service.chat_with_documents(...)
```

#### 2. Strategy Pattern for LLM Integration
The `LLMService` abstracts OpenAI interactions and can be extended for other providers:

```python
class LLMService:
    def __init__(self, papr_service: PaprService):
        self.client = OpenAI()
        self.papr_service = papr_service
        self.model = "gpt-5"  # Easily configurable
```

#### 3. Observer Pattern for Progress Tracking
Upload progress uses an observer-like pattern with callbacks:

```python
def progress_callback(completed: int, total: int, message: str):
    tracker.update_progress(completed, total, message)

papr_service.add_document(content, progress_callback=progress_callback)
```

## 🔧 Development Setup

### Prerequisites
- Python 3.8+
- Node.js (for frontend development tools, optional)
- Git

### Quick Start
```bash
# Clone and setup
git clone <repository-url>
cd fastapi-pdf-chat
./setup.sh

# Activate virtual environment
source venv/bin/activate

# Run in development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
```

### Development Environment Variables
Create `.env.development`:
```bash
ENVIRONMENT=development
LOG_LEVEL=DEBUG
PAPR_MEMORY_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

## 📝 Code Style & Standards

### Python Code Style
We follow PEP 8 with some modifications:

```python
# Good: Type hints for all functions
def process_document(content: str, filename: str) -> Dict[str, Any]:
    """Process a document and return metadata."""
    pass

# Good: Proper error handling
try:
    result = papr_service.add_document(content)
except Exception as e:
    logger.error(f"Failed to add document: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail="Document processing failed")

# Good: Descriptive variable names
document_upload_response = DocumentUploadResponse(
    document_id=document_id,
    chunks_created=len(chunks),
    total_chunks=len(chunks)
)
```

### Error Handling Patterns

#### Service Layer
```python
class PaprService:
    def add_document(self, content: str) -> str:
        try:
            response = self.client.memory.add(...)
            return response.data[0].memory_id
        except Exception as e:
            logger.error(f"Papr Memory error: {e}", exc_info=True)
            raise ServiceError(f"Failed to add document: {str(e)}")
```

#### Router Layer
```python
@router.post("/upload")
async def upload_document(file: UploadFile):
    try:
        result = papr_service.add_document(content)
        return {"status": "success", "document_id": result}
    except ServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

## 🧪 Testing Strategy

### Unit Tests Structure
```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures
├── unit/
│   ├── test_papr_service.py
│   ├── test_llm_service.py
│   └── test_chat_service.py
├── integration/
│   ├── test_document_upload.py
│   └── test_chat_flow.py
└── e2e/
    └── test_complete_workflow.py
```

### Example Test
```python
import pytest
from unittest.mock import Mock, patch
from app.services.papr_service import PaprService

class TestPaprService:
    @patch('app.services.papr_service.Papr')
    def test_add_document_success(self, mock_papr):
        # Arrange
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [Mock(memory_id="test-id")]
        mock_client.memory.add.return_value = mock_response
        mock_papr.return_value = mock_client
        
        service = PaprService()
        
        # Act
        result = service.add_document("test content", "test.pdf")
        
        # Assert
        assert result == "test-id"
        mock_client.memory.add.assert_called_once()
```

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/unit/test_papr_service.py -v
```

## 🔍 Debugging Guide

### Common Issues & Solutions

#### 1. Papr Memory Integration Issues

**Problem**: Authentication errors
```
This auth method has not been implemented yet
```

**Debug Steps**:
1. Check SDK version: `pip show papr-memory`
2. Verify environment variable: `echo $PAPR_MEMORY_API_KEY`
3. Test API key: `curl -H "x-api-key: $PAPR_MEMORY_API_KEY" https://api.papr.ai/health`

**Solution**: Update to latest SDK and verify API key format.

#### 2. Search Quality Issues

**Problem**: Search returns irrelevant results

**Debug Steps**:
1. Enable debug logging: `LOG_LEVEL=DEBUG`
2. Check search queries in logs
3. Verify metadata filters
4. Test with different query formats

**Solution**: Improve query quality following Papr Memory best practices.

#### 3. Upload Progress Not Working

**Problem**: Progress bar stuck at 0%

**Debug Steps**:
1. Check browser console for JavaScript errors
2. Verify progress endpoint: `curl http://localhost:8000/upload/progress/test-id`
3. Check background task execution
4. Verify progress_store updates

### Logging Configuration

```python
# app/main.py - Enhanced logging setup
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if os.getenv("ENVIRONMENT") == "development" else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("app.log") if os.getenv("ENVIRONMENT") == "production" else logging.NullHandler()
    ]
)

# Service-specific loggers
papr_logger = logging.getLogger("papr_service")
llm_logger = logging.getLogger("llm_service")
chat_logger = logging.getLogger("chat_service")
```

### Performance Profiling

```python
# Add to services for performance monitoring
import time
import functools

def timing_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger.info(f"{func.__name__} took {end - start:.2f} seconds")
        return result
    return wrapper

class PaprService:
    @timing_decorator
    def add_document(self, content: str) -> str:
        # Implementation
        pass
```

## 🚀 Deployment Guide

### Docker Development
```dockerfile
# Dockerfile.dev
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Development command
CMD ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    environment:
      - ENVIRONMENT=development
      - LOG_LEVEL=DEBUG
    env_file:
      - .env
```

### Production Deployment

#### Environment Configuration
```bash
# .env.production
ENVIRONMENT=production
LOG_LEVEL=WARNING
MAX_FILE_SIZE=52428800
CORS_ORIGINS=["https://yourdomain.com"]
```

#### Docker Production
```dockerfile
# Dockerfile.prod
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH
EXPOSE 8000

CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

#### Kubernetes Deployment
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-pdf-chat
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi-pdf-chat
  template:
    metadata:
      labels:
        app: fastapi-pdf-chat
    spec:
      containers:
      - name: app
        image: fastapi-pdf-chat:latest
        ports:
        - containerPort: 8000
        env:
        - name: PAPR_MEMORY_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: papr-memory-api-key
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai-api-key
```

## 🔧 Extension Points

### Adding New LLM Providers

1. Create a new service class:
```python
# app/services/anthropic_service.py
class AnthropicService:
    def __init__(self):
        self.client = anthropic.Client()
    
    def generate_response_with_tools(self, message: str, tools: List[Dict]) -> str:
        # Implementation
        pass
```

2. Update the factory pattern:
```python
# app/services/llm_factory.py
def create_llm_service(provider: str) -> LLMService:
    if provider == "openai":
        return OpenAIService()
    elif provider == "anthropic":
        return AnthropicService()
    else:
        raise ValueError(f"Unsupported provider: {provider}")
```

### Adding New Document Types

1. Create a document processor:
```python
# app/services/processors/docx_processor.py
class DocxProcessor:
    def extract_text(self, file_content: bytes) -> str:
        # Implementation using python-docx
        pass
```

2. Update the document service:
```python
# app/services/document_service.py
def get_processor(file_type: str):
    processors = {
        "pdf": PDFProcessor(),
        "docx": DocxProcessor(),
        "txt": TextProcessor()
    }
    return processors.get(file_type)
```

### Custom Metadata Fields

```python
# app/models/schemas.py
class DocumentMetadata(BaseModel):
    original_filename: str
    file_size: int
    content_type: str
    author: Optional[str] = None
    creation_date: Optional[datetime] = None
    tags: List[str] = []
    category: Optional[str] = None
```

## 📊 Monitoring & Observability

### Metrics Collection
```python
# app/middleware/metrics.py
from prometheus_client import Counter, Histogram, generate_latest

upload_counter = Counter('documents_uploaded_total', 'Total uploaded documents')
search_duration = Histogram('search_duration_seconds', 'Search duration')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    if request.url.path.startswith("/upload"):
        upload_counter.inc()
    elif request.url.path.startswith("/chat"):
        search_duration.observe(duration)
    
    return response
```

### Health Checks
```python
# app/routers/health.py
@router.get("/health")
async def health_check():
    checks = {
        "papr_memory": await check_papr_memory(),
        "openai": await check_openai(),
        "database": await check_database()
    }
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return JSONResponse(
        status_code=status_code,
        content={"status": "healthy" if all_healthy else "unhealthy", "checks": checks}
    )
```

## 🤝 Contributing Workflow

### 1. Development Process
```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and test
pytest
python test_setup.py

# Commit with conventional commits
git commit -m "feat: add new document processor for DOCX files"

# Push and create PR
git push origin feature/new-feature
```

### 2. Code Review Checklist
- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Error handling implemented
- [ ] Logging added for debugging
- [ ] Performance considerations addressed
- [ ] Security implications reviewed

### 3. Release Process
```bash
# Update version
bump2version patch  # or minor/major

# Tag release
git tag v1.0.0
git push origin v1.0.0

# Deploy to production
docker build -t fastapi-pdf-chat:v1.0.0 .
kubectl set image deployment/fastapi-pdf-chat app=fastapi-pdf-chat:v1.0.0
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Papr Memory SDK](https://github.com/Papr-ai/papr-pythonSDK)
- [OpenAI API Reference](https://platform.openai.com/docs)
- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)

---

Happy coding! 🎉

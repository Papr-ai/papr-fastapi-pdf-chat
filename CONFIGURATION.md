# Configuration Guide

This guide covers all configuration options for the FastAPI PDF Chat application, from basic setup to advanced production configurations.

## 📋 Environment Variables

### Required Variables

These variables must be set for the application to function:

```bash
# API Keys
PAPR_MEMORY_API_KEY=your_papr_memory_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### Optional Variables

```bash
# Application Settings
ENVIRONMENT=development                    # development, staging, production
LOG_LEVEL=INFO                            # DEBUG, INFO, WARNING, ERROR, CRITICAL
MAX_FILE_SIZE=10485760                    # Maximum upload size in bytes (10MB)
HOST=0.0.0.0                             # Server host
PORT=8000                                # Server port

# CORS Settings (Production)
CORS_ORIGINS=["https://yourdomain.com"]   # Allowed origins for CORS
CORS_ALLOW_CREDENTIALS=true               # Allow credentials in CORS
CORS_ALLOW_METHODS=["*"]                  # Allowed HTTP methods
CORS_ALLOW_HEADERS=["*"]                  # Allowed headers

# LLM Settings
OPENAI_MODEL=gpt-4o                       # OpenAI model to use
OPENAI_MAX_TOKENS=4000                    # Maximum tokens for responses
OPENAI_TEMPERATURE=0.2                    # Response creativity (0.0-1.0)

# Papr Memory Settings
PAPR_MAX_MEMORIES=50                      # Maximum memories per search
PAPR_CHUNK_SIZE=14000                     # Maximum bytes per memory chunk
PAPR_TOPICS=["document","pdf"]            # Default topics for filtering

# Performance Settings
WORKER_PROCESSES=4                        # Number of worker processes
WORKER_CONNECTIONS=1000                   # Max connections per worker
KEEPALIVE_TIMEOUT=5                       # Keep-alive timeout in seconds

# Storage Settings
UPLOAD_DIR=./uploads                      # Temporary upload directory
DOCUMENTS_STORE_PATH=./documents_store.json  # Local document metadata
```

## 🔧 Configuration Files

### 1. Environment-Specific Configuration

#### Development (.env.development)
```bash
ENVIRONMENT=development
LOG_LEVEL=DEBUG
HOST=0.0.0.0
PORT=8000
MAX_FILE_SIZE=10485760
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]
```

#### Staging (.env.staging)
```bash
ENVIRONMENT=staging
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
MAX_FILE_SIZE=52428800
CORS_ORIGINS=["https://staging.yourdomain.com"]
```

#### Production (.env.production)
```bash
ENVIRONMENT=production
LOG_LEVEL=WARNING
HOST=0.0.0.0
PORT=8000
MAX_FILE_SIZE=52428800
CORS_ORIGINS=["https://yourdomain.com"]
WORKER_PROCESSES=4
```

### 2. Application Configuration (config.py)

Create `app/config.py` for centralized configuration management:

```python
import os
from typing import List, Optional
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False)
    
    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # API Keys
    papr_memory_api_key: str = Field(..., env="PAPR_MEMORY_API_KEY")
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    
    # File Upload
    max_file_size: int = Field(default=10485760, env="MAX_FILE_SIZE")  # 10MB
    allowed_file_types: List[str] = Field(default=["application/pdf"])
    upload_dir: str = Field(default="./uploads", env="UPLOAD_DIR")
    
    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000"], 
        env="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: List[str] = Field(default=["*"], env="CORS_ALLOW_METHODS")
    cors_allow_headers: List[str] = Field(default=["*"], env="CORS_ALLOW_HEADERS")
    
    # OpenAI
    openai_model: str = Field(default="gpt-4o", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=4000, env="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.2, env="OPENAI_TEMPERATURE")
    
    # Papr Memory
    papr_max_memories: int = Field(default=50, env="PAPR_MAX_MEMORIES")
    papr_chunk_size: int = Field(default=14000, env="PAPR_CHUNK_SIZE")
    papr_topics: List[str] = Field(
        default=["document", "pdf"], 
        env="PAPR_TOPICS"
    )
    
    # Storage
    documents_store_path: str = Field(
        default="./documents_store.json", 
        env="DOCUMENTS_STORE_PATH"
    )
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Performance
    worker_processes: int = Field(default=1, env="WORKER_PROCESSES")
    worker_connections: int = Field(default=1000, env="WORKER_CONNECTIONS")
    keepalive_timeout: int = Field(default=5, env="KEEPALIVE_TIMEOUT")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

# Environment-specific overrides
if settings.environment == "development":
    settings.debug = True
    settings.log_level = "DEBUG"
elif settings.environment == "production":
    settings.debug = False
    settings.log_level = "WARNING"
```

### 3. Using Configuration in Services

```python
# app/services/papr_service.py
from app.config import settings

class PaprService:
    def __init__(self):
        self.client = Papr(x_api_key=settings.papr_memory_api_key)
        self.max_memories = settings.papr_max_memories
        self.chunk_size = settings.papr_chunk_size
        self.topics = settings.papr_topics
```

## 🚀 Deployment Configurations

### 1. Docker Configuration

#### Development Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Development command
CMD ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
```

#### Production Dockerfile
```dockerfile
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /home/app/.local

# Copy application
COPY . .
RUN chown -R app:app /app

# Switch to non-root user
USER app

# Set PATH
ENV PATH=/home/app/.local/bin:$PATH

# Create directories
RUN mkdir -p uploads

EXPOSE 8000

# Production command
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### 2. Docker Compose

#### Development (docker-compose.dev.yml)
```yaml
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
      - /app/venv  # Exclude venv from volume mount
    environment:
      - ENVIRONMENT=development
      - LOG_LEVEL=DEBUG
    env_file:
      - .env.development
    restart: unless-stopped

  # Optional: Add Redis for production-like caching
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
```

#### Production (docker-compose.prod.yml)
```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.prod
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=WARNING
    env_file:
      - .env.production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped
```

### 3. Kubernetes Configuration

#### Deployment (k8s-deployment.yaml)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-pdf-chat
  labels:
    app: fastapi-pdf-chat
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
        - name: ENVIRONMENT
          value: "production"
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
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### Service (k8s-service.yaml)
```yaml
apiVersion: v1
kind: Service
metadata:
  name: fastapi-pdf-chat-service
spec:
  selector:
    app: fastapi-pdf-chat
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

#### ConfigMap (k8s-configmap.yaml)
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "WARNING"
  MAX_FILE_SIZE: "52428800"
  OPENAI_MODEL: "gpt-4o"
  CORS_ORIGINS: '["https://yourdomain.com"]'
```

### 4. Nginx Configuration

```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream app {
        server app:8000;
    }

    server {
        listen 80;
        server_name yourdomain.com;
        
        # Redirect to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";

        # File upload size
        client_max_body_size 50M;

        # Proxy configuration
        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeout settings
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Static files (if served by nginx)
        location /static/ {
            alias /app/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

## 🔒 Security Configuration

### 1. API Key Management

#### Using Environment Variables
```bash
# Development
export PAPR_MEMORY_API_KEY="dev_key_here"
export OPENAI_API_KEY="dev_key_here"

# Production (use secrets management)
kubectl create secret generic api-keys \
  --from-literal=papr-memory-api-key="prod_key_here" \
  --from-literal=openai-api-key="prod_key_here"
```

#### Using AWS Secrets Manager
```python
import boto3
from botocore.exceptions import ClientError

def get_secret(secret_name: str, region_name: str = "us-west-2"):
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return response['SecretString']
    except ClientError as e:
        raise e

# Usage
papr_key = get_secret("prod/papr-memory-api-key")
openai_key = get_secret("prod/openai-api-key")
```

### 2. HTTPS Configuration

#### Let's Encrypt with Certbot
```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 3. Rate Limiting

```python
# app/middleware/rate_limit.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException

limiter = Limiter(key_func=get_remote_address)

# Apply to routes
@app.post("/documents/upload")
@limiter.limit("10/minute")
async def upload_document(request: Request, file: UploadFile):
    # Implementation
    pass

@app.post("/chat/")
@limiter.limit("30/minute")
async def chat(request: Request, chat_request: ChatRequest):
    # Implementation
    pass
```

## 📊 Monitoring Configuration

### 1. Logging Configuration

```python
# app/logging_config.py
import logging
import logging.handlers
import os
from app.config import settings

def setup_logging():
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format=settings.log_format,
        handlers=[
            logging.StreamHandler(),
            logging.handlers.RotatingFileHandler(
                "logs/app.log",
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
        ]
    )
    
    # Configure specific loggers
    loggers = {
        "papr_service": logging.getLogger("papr_service"),
        "llm_service": logging.getLogger("llm_service"),
        "chat_service": logging.getLogger("chat_service"),
    }
    
    for name, logger in loggers.items():
        logger.setLevel(getattr(logging, settings.log_level.upper()))
        
        # Add file handler for each service
        handler = logging.handlers.RotatingFileHandler(
            f"logs/{name}.log",
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        handler.setFormatter(logging.Formatter(settings.log_format))
        logger.addHandler(handler)

# Call during app startup
setup_logging()
```

### 2. Health Check Configuration

```python
# app/routers/health.py
from fastapi import APIRouter, HTTPException
from app.services.papr_service import PaprService
import openai
import time

router = APIRouter()

@router.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    start_time = time.time()
    
    checks = {
        "status": "healthy",
        "timestamp": time.time(),
        "checks": {}
    }
    
    # Check Papr Memory
    try:
        papr_service = PaprService()
        # Simple search to verify connection
        response = papr_service.client.memory.search(
            query="health check",
            metadata={"external_user_id": "health_check"},
            max_memories=1
        )
        checks["checks"]["papr_memory"] = {
            "status": "healthy",
            "response_time_ms": (time.time() - start_time) * 1000
        }
    except Exception as e:
        checks["checks"]["papr_memory"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        checks["status"] = "unhealthy"
    
    # Check OpenAI
    try:
        client = openai.OpenAI()
        response = client.models.list()
        checks["checks"]["openai"] = {
            "status": "healthy",
            "models_available": len(response.data)
        }
    except Exception as e:
        checks["checks"]["openai"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        checks["status"] = "unhealthy"
    
    # Check disk space
    import shutil
    total, used, free = shutil.disk_usage("/")
    free_gb = free // (1024**3)
    
    checks["checks"]["disk_space"] = {
        "status": "healthy" if free_gb > 1 else "warning",
        "free_gb": free_gb
    }
    
    checks["response_time_ms"] = (time.time() - start_time) * 1000
    
    status_code = 200 if checks["status"] == "healthy" else 503
    return JSONResponse(status_code=status_code, content=checks)

@router.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe"""
    return {"status": "ready"}

@router.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"status": "alive"}
```

### 3. Metrics Collection

```python
# app/middleware/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time

# Metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

active_uploads = Gauge(
    'active_uploads',
    'Number of active uploads'
)

document_count = Gauge(
    'documents_total',
    'Total number of documents'
)

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## 🔧 Performance Tuning

### 1. Uvicorn Configuration

```python
# gunicorn_config.py
import multiprocessing
from app.config import settings

# Server socket
bind = f"{settings.host}:{settings.port}"
backlog = 2048

# Worker processes
workers = settings.worker_processes or multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = settings.worker_connections
max_requests = 1000
max_requests_jitter = 50

# Timeouts
timeout = 30
keepalive = settings.keepalive_timeout

# Logging
accesslog = "-"
errorlog = "-"
loglevel = settings.log_level.lower()

# Process naming
proc_name = "fastapi-pdf-chat"

# Worker recycling
max_requests = 1000
max_requests_jitter = 100
preload_app = True
```

### 2. Database Connection Pooling (if using database)

```python
# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### 3. Caching Configuration

```python
# app/cache.py
import redis
from functools import wraps
import json
import hashlib

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)

def cache_result(ttl: int = 300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key
            key_data = f"{func.__name__}:{args}:{kwargs}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Try to get from cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            
            return result
        return wrapper
    return decorator

# Usage
@cache_result(ttl=600)  # Cache for 10 minutes
async def get_document_summary(document_id: str):
    # Implementation
    pass
```

---

This configuration guide provides comprehensive setup options for all deployment scenarios. Adjust settings based on your specific requirements and infrastructure.

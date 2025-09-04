# API Reference

This document provides comprehensive documentation for all API endpoints in the FastAPI PDF Chat application.

## Base URL
```
http://localhost:8000
```

## Authentication
Currently, the application uses a demo user system. In production, implement proper authentication and replace `external_user_id: "demo_user"` with actual user identification.

## Error Responses

All endpoints return errors in the following format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid input)
- `422`: Validation Error (Pydantic validation failed)
- `500`: Internal Server Error

## Endpoints

### 1. Root Endpoint

#### `GET /`
Serves the main HTML application.

**Response:**
- Content-Type: `text/html`
- Returns the main application interface

**Example:**
```bash
curl http://localhost:8000/
```

---

### 2. Document Management

#### `POST /documents/upload`
Upload a PDF document for processing and storage.

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form data with file upload

**Parameters:**
- `file` (required): PDF file to upload
  - Type: `UploadFile`
  - Max size: 10MB (configurable via `MAX_FILE_SIZE`)
  - Allowed types: PDF only

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.pdf",
  "chunks_created": 15,
  "total_chunks": 15,
  "message": "Document uploaded and processed successfully"
}
```

**Response Schema:** `DocumentUploadResponse`
- `document_id`: Unique identifier for the uploaded document
- `filename`: Original filename of the uploaded document
- `chunks_created`: Number of chunks successfully created
- `total_chunks`: Total number of chunks the document was split into
- `message`: Success message

**Example:**
```bash
curl -X POST \
  http://localhost:8000/documents/upload \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

**Error Responses:**
- `400`: File type not supported (non-PDF)
- `400`: File too large
- `500`: Document processing failed

---

#### `GET /documents/list`
Retrieve all documents uploaded by the current user.

**Response:**
```json
{
  "documents": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "document.pdf",
      "uploaded_at": "2024-01-15T10:30:00.000Z",
      "chunks_created": 15,
      "total_chunks": 15,
      "file_size": 1048576,
      "metadata": {
        "original_filename": "document.pdf",
        "file_size": 1048576,
        "content_type": "application/pdf"
      }
    }
  ],
  "count": 1,
  "user_id": "demo_user"
}
```

**Response Schema:** `DocumentListResponse`
- `documents`: Array of document objects
  - `id`: Document unique identifier
  - `filename`: Original filename
  - `uploaded_at`: ISO timestamp of upload
  - `chunks_created`: Number of chunks created
  - `total_chunks`: Total chunks in document
  - `file_size`: File size in bytes
  - `metadata`: Additional document metadata
- `count`: Total number of documents
- `user_id`: User identifier

**Example:**
```bash
curl http://localhost:8000/documents/list
```

---

### 3. Upload Progress Tracking

#### `POST /upload/with-progress/{upload_id}`
Upload a document with real-time progress tracking.

**Path Parameters:**
- `upload_id`: Unique identifier for tracking this upload

**Request:**
- Content-Type: `multipart/form-data`
- Body: Form data with file upload

**Parameters:**
- `file` (required): PDF file to upload

**Response:**
```json
{
  "upload_id": "upload-123",
  "status": "started",
  "message": "Upload started successfully"
}
```

**Example:**
```bash
curl -X POST \
  http://localhost:8000/upload/with-progress/upload-123 \
  -F "file=@document.pdf"
```

---

#### `GET /upload/progress/{upload_id}`
Get the current progress of an upload.

**Path Parameters:**
- `upload_id`: Upload identifier to check progress for

**Response:**
```json
{
  "upload_id": "upload-123",
  "status": "processing",
  "progress": 65,
  "message": "Processing chunk 13 of 20",
  "total_chunks": 20,
  "completed_chunks": 13
}
```

**Response Schema:** `ProgressResponse`
- `upload_id`: Upload identifier
- `status`: Current status (`pending`, `processing`, `completed`, `failed`)
- `progress`: Progress percentage (0-100)
- `message`: Human-readable progress message
- `total_chunks`: Total number of chunks to process
- `completed_chunks`: Number of chunks completed

**Example:**
```bash
curl http://localhost:8000/upload/progress/upload-123
```

**Status Values:**
- `pending`: Upload not yet started
- `processing`: Currently processing chunks
- `completed`: All chunks processed successfully
- `failed`: Processing failed

---

### 4. Chat Interface

#### `POST /chat/`
Chat with uploaded documents using AI.

**Request:**
```json
{
  "message": "What are the main revenue figures?",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "max_sources": 10
}
```

**Request Schema:** `ChatRequest`
- `message` (required): User's question or message
- `document_id` (optional): Specific document to search within
- `max_sources` (optional): Maximum number of source chunks to retrieve (default: 10, min: 10, max: 50)

**Response:**
```json
{
  "response": "Based on the uploaded documents, the main revenue figures show...",
  "sources": [
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "annual-report.pdf",
      "content_preview": "Revenue for the fiscal year was $648.7 billion...",
      "relevance_score": 0.95
    }
  ],
  "document_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response Schema:** `ChatResponse`
- `response`: AI-generated response to the user's question
- `sources`: Array of source documents used to generate the response
  - `document_id`: Source document identifier
  - `filename`: Source document filename
  - `content_preview`: Preview of relevant content (first 200 characters)
  - `relevance_score`: Relevance score from semantic search (0-1)
- `document_id`: Document ID from the request (if provided)

**Example:**
```bash
curl -X POST \
  http://localhost:8000/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the key financial metrics?",
    "document_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

**Chat Behavior:**
- If `document_id` is provided, search is limited to that specific document
- If `document_id` is omitted, search across all user documents
- The AI uses OpenAI's function calling to intelligently search for relevant information
- Responses include citations and source information for transparency

---

## WebSocket Endpoints (Future Enhancement)

### `WS /ws/chat`
Real-time chat interface (not currently implemented).

**Future Implementation:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat');
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
```

---

## Data Models

### DocumentUploadResponse
```python
class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    chunks_created: int
    total_chunks: int
    message: str
```

### DocumentListResponse
```python
class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo]
    count: int
    user_id: str

class DocumentInfo(BaseModel):
    id: str
    filename: str
    uploaded_at: str
    chunks_created: int
    total_chunks: int
    file_size: int
    metadata: Dict[str, Any]
```

### ChatRequest
```python
class ChatRequest(BaseModel):
    message: str
    document_id: Optional[str] = None
    max_sources: Optional[int] = 10
```

### ChatResponse
```python
class ChatResponse(BaseModel):
    response: str
    sources: List[SourceInfo]
    document_id: Optional[str] = None

class SourceInfo(BaseModel):
    document_id: str
    filename: str
    content_preview: str
    relevance_score: Optional[float] = None
```

### ProgressResponse
```python
class ProgressResponse(BaseModel):
    upload_id: str
    status: str
    progress: int
    message: str
    total_chunks: int
    completed_chunks: int
```

---

## Rate Limits

Currently, no rate limiting is implemented. For production deployment, consider implementing:

- **Upload endpoint**: 10 requests per minute per IP
- **Chat endpoint**: 30 requests per minute per user
- **Progress endpoint**: 60 requests per minute per IP

Example implementation:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/chat/")
@limiter.limit("30/minute")
async def chat_endpoint(request: Request, chat_request: ChatRequest):
    # Implementation
    pass
```

---

## Error Handling

### Common Error Scenarios

#### 1. File Upload Errors
```json
{
  "detail": "File size exceeds maximum allowed size of 10MB"
}
```

#### 2. Document Processing Errors
```json
{
  "detail": "Failed to extract text from PDF. The file may be corrupted or password-protected."
}
```

#### 3. Search/Chat Errors
```json
{
  "detail": "No documents found. Please upload a document first."
}
```

#### 4. API Integration Errors
```json
{
  "detail": "External service temporarily unavailable. Please try again later."
}
```

### Error Response Format
All errors follow FastAPI's standard error format:
```json
{
  "detail": "Human-readable error message"
}
```

For validation errors (422), the response includes field-specific details:
```json
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## OpenAPI/Swagger Documentation

The API automatically generates interactive documentation available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

These interfaces provide:
- Interactive API testing
- Request/response examples
- Schema validation
- Authentication testing (when implemented)

---

## SDK Usage Examples

### Python Client Example
```python
import requests
import json

class PDFChatClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def upload_document(self, file_path: str):
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{self.base_url}/documents/upload",
                files={"file": f}
            )
        return response.json()
    
    def chat(self, message: str, document_id: str = None):
        payload = {"message": message}
        if document_id:
            payload["document_id"] = document_id
        
        response = requests.post(
            f"{self.base_url}/chat/",
            json=payload
        )
        return response.json()

# Usage
client = PDFChatClient()
doc_result = client.upload_document("report.pdf")
chat_result = client.chat("What are the key findings?", doc_result["document_id"])
print(chat_result["response"])
```

### JavaScript Client Example
```javascript
class PDFChatClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async uploadDocument(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${this.baseUrl}/documents/upload`, {
            method: 'POST',
            body: formData
        });
        
        return response.json();
    }
    
    async chat(message, documentId = null) {
        const payload = { message };
        if (documentId) payload.document_id = documentId;
        
        const response = await fetch(`${this.baseUrl}/chat/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        return response.json();
    }
}

// Usage
const client = new PDFChatClient();
const fileInput = document.getElementById('file-input');
const file = fileInput.files[0];

client.uploadDocument(file)
    .then(result => client.chat("Summarize this document", result.document_id))
    .then(response => console.log(response.response));
```

---

## Performance Considerations

### Response Times
- **Document Upload**: 2-10 seconds depending on file size and content complexity
- **Chat Queries**: 1-5 seconds depending on search complexity and LLM processing
- **Document List**: <100ms (cached locally)
- **Progress Check**: <50ms

### Optimization Strategies
1. **Caching**: Implement Redis for frequently accessed documents
2. **Async Processing**: Use Celery for background document processing
3. **CDN**: Serve static assets via CDN
4. **Database Indexing**: Index document metadata for faster queries

### Scaling Considerations
- **Horizontal Scaling**: Multiple FastAPI instances behind load balancer
- **Database Scaling**: Separate read/write databases
- **File Storage**: Use cloud storage (S3, GCS) for document files
- **Memory Management**: Implement proper cleanup for large file processing

---

This API reference provides comprehensive documentation for integrating with the FastAPI PDF Chat application. For additional examples and advanced usage patterns, see the `DEVELOPMENT.md` guide.

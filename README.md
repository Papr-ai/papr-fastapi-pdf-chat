# FastAPI PDF Chat Application

A modern web application that allows users to upload PDF documents and chat with their content using AI. Built with FastAPI, Papr Memory SDK, and OpenAI's GPT-4.

## 🚀 Features

- **PDF Upload & Processing**: Upload multiple PDF documents with real-time progress tracking
- **AI-Powered Chat**: Chat with your documents using OpenAI's GPT-5 with intelligent context retrieval
- **Document Management**: View and manage uploaded documents with metadata (file size, upload date, chunk count)
- **Semantic plus graph Search**: Powered by Papr Memory for accurate document content retrieval
- **Modern UI**: Clean, responsive interface built with vanilla HTML/CSS/JavaScript and Tailwind CSS
- **Real-time Progress**: Live progress bars showing upload and processing status

## 🛠️ Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **Papr Memory SDK**: Document storage and semantic graph search
- **OpenAI API**: GPT-5 for chat responses with tool calling
- **PyMuPDF (fitz)**: High-quality PDF text extraction
- **Pydantic**: Data validation and serialization

### Frontend
- **Vanilla JavaScript**: Simple, dependency-free frontend
- **Tailwind CSS**: Utility-first CSS framework via CDN
- **HTML5**: Modern web standards

### Storage & Memory
- **Papr Memory**: Cloud-based semantic memory storage
- **Local JSON Store**: Document metadata caching for improved performance

## 📋 Prerequisites

- Python 3.8+
- Papr Memory API Key ([Get one here](https://papr.ai))
- OpenAI API Key ([Get one here](https://platform.openai.com))

## 🔧 Installation & Setup

### 1. Clone the Repository

   ```bash
git clone <repository-url>
   cd fastapi-pdf-chat
   ```

### 2. Create Virtual Environment

   ```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

### 3. Install Dependencies

   ```bash
   pip install -r requirements.txt
   ```

### 4. Environment Configuration

Create a `.env` file in the project root:

   ```bash
# Required API Keys
PAPR_MEMORY_API_KEY=your_papr_memory_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Optional Configuration
LOG_LEVEL=INFO
MAX_FILE_SIZE=10485760  # 10MB in bytes
```

### 5. Run the Application

   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

The application will be available at: `http://localhost:8000`

## 📖 Usage Guide

### Uploading Documents

1. **Access the Application**: Navigate to `http://localhost:8000`
2. **Select PDF**: Click "Choose File" and select your PDF document
3. **Upload**: Click "Upload Document" and monitor the progress bar
4. **View Documents**: Uploaded documents appear in the left sidebar

### Chatting with Documents

1. **Select Document**: Click on any document in the sidebar (optional - you can chat across all documents)
2. **Ask Questions**: Type your question in the chat input
3. **Get Answers**: The AI will search your documents and provide contextual answers
4. **View Sources**: Each response includes source information showing which documents were referenced

### Example Questions

- "What are the main revenue figures for Amazon?"
- "Summarize the key findings in this report"
- "What does the document say about AWS performance?"
- "Find information about quarterly earnings"

## 🏗️ Architecture Overview

### Core Components

```
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── models/
│   │   └── schemas.py          # Pydantic models for API validation
│   ├── routers/
│   │   ├── chat.py            # Chat endpoints
│   │   ├── documents.py       # Document management endpoints
│   │   └── upload_progress.py # Upload progress tracking
│   └── services/
│       ├── chat_service.py    # Chat logic and orchestration
│       ├── document_store.py  # Local document metadata storage
│       ├── llm_service.py     # OpenAI integration with function calling
│       └── papr_service.py    # Papr Memory SDK integration
├── static/
│   └── index.html             # Frontend application
└── requirements.txt           # Python dependencies
```

### Data Flow

1. **PDF Upload**: User uploads PDF → PyMuPDF extracts text → Content chunked → Stored in Papr Memory
2. **Chat Query**: User asks question → LLM decides to search → Papr Memory retrieves relevant chunks → LLM generates response
3. **Document Management**: Metadata stored locally for quick access, with Papr Memory as fallback

## 🔍 Key Technical Insights

### 1. Content Chunking Strategy

**Challenge**: Papr Memory has a 14,000 byte limit per memory item.

**Solution**: Implemented intelligent chunking in `papr_service.py`:
```python
def _chunk_content(self, content: str, max_size: int = 14000) -> List[str]:
    """Split content into chunks that fit within Papr Memory limits"""
    chunks = []
    current_chunk = ""
    
    for paragraph in content.split('\n\n'):
        if len(current_chunk) + len(paragraph) > max_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                # Handle very long paragraphs
                words = paragraph.split()
                for word in words:
                    if len(current_chunk) + len(word) > max_size:
                        chunks.append(current_chunk.strip())
                        current_chunk = word
                    else:
                        current_chunk += " " + word
        else:
            current_chunk += "\n\n" + paragraph
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks
```

### 2. OpenAI Function Calling Integration

**Challenge**: LLM needs to intelligently decide when and how to search documents.

**Solution**: Implemented OpenAI function calling with proper JSON schema:
```python
tools = [{
    "type": "function",
    "function": {
        "name": "search_memory",
        "description": "Search through uploaded documents for specific information",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Detailed, specific search query following best practices..."
                },
                "document_id": {
                    "type": "string",
                    "description": "Optional: specific document ID to search within"
                },
                "max_results": {
                    "type": "integer",
                    "minimum": 10,
                    "maximum": 50,
                    "default": 25
                }
            },
            "required": ["query"]
        }
    }
}]
```

### 3. Query Optimization for Papr Memory

**Key Insight**: Papr Memory works best with detailed, contextual queries rather than keywords.

**Best Practices**:
- ✅ "Find Amazon's total revenue figures and financial performance data from their annual report, including breakdowns by business segments like AWS"
- ❌ "revenue"
- ✅ Use 2-3 sentences with specific context
- ✅ Include relevant terms, dates, and technical details
- ✅ Provide context about why you're searching

### 4. Metadata Strategy

**Structure**: Used Papr Memory's metadata system effectively:
```python
metadata = {
    "external_user_id": "demo_user",  # User isolation
    "topics": ["document", "pdf"],    # Content categorization
    "custom_metadata": {              # Custom fields
        "document_id": str(uuid.uuid4()),
        "filename": filename,
        "chunk_index": i,
        "total_chunks": len(chunks),
        "upload_timestamp": datetime.utcnow().isoformat()
    }
}
```

### 5. Hybrid Storage Approach

**Problem**: Papr Memory doesn't have a "get all documents" API.

**Solution**: Hybrid approach with local JSON cache:
- **Primary**: Local `documents_store.json` for quick document listing
- **Fallback**: Papr Memory search with broad query for reliability
- **Benefits**: Fast UI loading + data redundancy

### 6. Progress Tracking Implementation

**Challenge**: Users need real-time feedback during PDF processing.

**Solution**: Background task with progress callbacks:
```python
class ProgressTracker:
    def __init__(self):
        self.status = "pending"
        self.progress = 0
        self.message = "Initializing..."
        self.total_chunks = 0
        self.completed_chunks = 0

    def update_progress(self, completed: int, total: int, message: str):
        self.completed_chunks = completed
        self.total_chunks = total
        self.progress = int((completed / total) * 100) if total > 0 else 0
        self.message = message
        self.status = "completed" if completed >= total else "processing"
```

## 🐛 Common Issues & Solutions

### 1. Authentication Errors

**Error**: `This auth method has not been implemented yet`

**Solution**: Ensure you're using the latest Papr Memory SDK (>=2.14.0) and correct environment variable:
```bash
pip install --upgrade papr-memory>=2.14.0
```

### 2. Search Returns Wrong Results

**Symptoms**: Always getting cover page or irrelevant content

**Causes & Solutions**:
- **Missing Topics Filter**: Ensure `topics: ["document", "pdf"]` is set in metadata filters
- **Query Quality**: Use detailed, contextual queries instead of keywords

### 3. Upload Progress Not Showing

**Issue**: Progress bar stays at 0% or doesn't update

**Debug Steps**:
1. Check browser console for JavaScript errors
2. Verify `/upload/progress/{upload_id}` endpoint returns data
3. Ensure `progress_store` is being updated in background tasks

### 4. Memory Limit Errors

**Error**: `Error code: 404 - There was an error adding the memory item`

**Solution**: Content too large - chunking is working if you see this error rarely, but check chunk sizes:
```python
MAX_CHUNK_SIZE = 14000  # Papr Memory limit
```

## 🔒 Security Considerations

### Environment Variables
- Never commit `.env` files to version control
- Use strong, unique API keys
- Rotate keys regularly

### File Upload Security
- File type validation (PDF only)
- File size limits (10MB default)
- Virus scanning (recommended for production)

### User Isolation
- All memories tagged with `external_user_id`
- Implement proper authentication for multi-user scenarios

## 🚀 Production Deployment

### Environment Setup
```bash
# Production environment variables
ENVIRONMENT=production
LOG_LEVEL=WARNING
MAX_FILE_SIZE=52428800  # 50MB
CORS_ORIGINS=["https://yourdomain.com"]
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Performance Optimizations
- Use Redis for progress tracking instead of in-memory dict
- Implement caching for frequently accessed documents
- Add rate limiting for API endpoints
- Use CDN for static assets

## 📊 Monitoring & Logging

The application includes comprehensive logging:
- Upload progress and errors
- Search queries and results
- LLM interactions and tool calls
- Performance metrics

Key log locations:
- Upload processing: `papr_service.py`
- Search operations: `papr_service.py` and `llm_service.py`
- Chat interactions: `chat_service.py`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Commit your changes: `git commit -am 'Add new feature'`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add type hints to all functions
- Include docstrings for public methods
- Write tests for new features
- Update documentation for API changes

## 📝 License

[Add your chosen license here]

## 🙏 Acknowledgments

- [Papr Memory](https://platform.papr.ai) for semantic graph memory storage
- [OpenAI](https://openai.com) for GPT-5 API
- [FastAPI](https://fastapi.tiangolo.com) for the excellent web framework
- [PyMuPDF](https://pymupdf.readthedocs.io) for PDF processing

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section above
- Review the logs for detailed error information

---

**Built with ❤️ for the open source community**
# Troubleshooting Guide

This guide covers common issues encountered during development and deployment of the FastAPI PDF Chat application, along with their solutions.

## 🚨 Critical Issues

### 1. Authentication Errors with Papr Memory

#### **Error**: `This auth method has not been implemented yet`

**Symptoms:**
- Upload fails immediately after file selection
- Error appears in browser console and server logs
- No document processing occurs

**Root Cause:**
- Outdated Papr Memory SDK version
- Incorrect API key configuration
- Wrong client initialization parameters

**Solution:**
```bash
# Update to latest SDK
pip install --upgrade papr-memory>=2.14.0

# Verify environment variable
echo $PAPR_MEMORY_API_KEY

# Check client initialization in papr_service.py
client = Papr(x_api_key=os.environ.get("PAPR_MEMORY_API_KEY"))
```

**Prevention:**
- Always use the latest SDK version
- Validate API keys before deployment
- Monitor SDK changelog for breaking changes

---

### 2. Search Returns Wrong/Irrelevant Results

#### **Error**: AI always returns "I couldn't find information about..."

**Symptoms:**
- Search consistently returns cover page or irrelevant content
- Even exact number searches fail
- Only getting 1 chunk when document has 20+ chunks

**Root Cause:**
- Missing or incorrect metadata filters
- Document chunking/indexing issues during upload
- Search query quality problems

**Solution:**

1. **Restore Metadata Filters:**
```python
# In papr_service.py - search_memories method
metadata_filter: MemoryMetadataParam = {
    "external_user_id": external_user_id,
    "topics": ["document", "pdf"]  # Critical for filtering
}
```

2. **Re-upload Documents:**
```bash
# Delete problematic document via UI
# Re-upload to fix indexing issues
```

3. **Improve Query Quality:**
```python
# Bad query
"revenue"

# Good query
"Find Amazon's total revenue figures and financial performance data from their annual report, including breakdowns by business segments like AWS for the most recent fiscal year"
```

**Prevention:**
- Always include topics filter in searches
- Test uploads with small documents first
- Use detailed, contextual search queries

---

### 3. Upload Progress Not Displaying

#### **Error**: Progress bar stuck at 0% or shows generic error

**Symptoms:**
- Upload completes but progress never updates
- JavaScript console shows `Cannot create property 'textContent' on string`
- Progress endpoint returns no data

**Root Cause:**
- JavaScript DOM manipulation errors
- Background task not updating progress store
- Polling mechanism not working

**Solution:**

1. **Fix JavaScript DOM Error:**
```javascript
// Bad - trying to set textContent on string
const progressElement = "progress-" + uploadId;
progressElement.textContent = "50%";

// Good - get DOM element first
const progressElement = document.getElementById("progress-" + uploadId);
progressElement.textContent = "50%";
```

2. **Debug Progress Store:**
```python
# Add logging to progress tracker
def update_progress(self, completed: int, total: int, message: str):
    logger.info(f"Progress update: {completed}/{total} - {message}")
    self.completed_chunks = completed
    # ... rest of implementation
```

3. **Test Progress Endpoint:**
```bash
curl http://localhost:8000/upload/progress/test-id
```

**Prevention:**
- Test progress tracking with small files first
- Add comprehensive logging to progress updates
- Validate DOM element existence before manipulation

---

## 🔧 Setup & Configuration Issues

### 4. Virtual Environment Problems

#### **Error**: `externally-managed-environment` or `command not found: pip`

**Symptoms:**
- Cannot install packages
- Python/pip commands not found
- Permission errors during installation

**Solution:**
```bash
# Create proper virtual environment
python3 -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Upgrade pip within venv
python3 -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

**Verification:**
```bash
# Check you're in virtual environment
which python3  # Should show path to venv
pip list        # Should show installed packages
```

---

### 5. Environment Variable Issues

#### **Error**: API keys not loading or showing as default values

**Symptoms:**
- `.env` file exists but variables not loaded
- API calls fail with authentication errors
- Variables show as `your_api_key_here`

**Solution:**

1. **Check File Location:**
```bash
# .env should be in project root
ls -la .env
```

2. **Verify File Format:**
```bash
# .env file should have no spaces around =
PAPR_MEMORY_API_KEY=actual_key_here
OPENAI_API_KEY=actual_key_here
```

3. **Test Loading:**
```python
from dotenv import load_dotenv
import os

load_dotenv()
print(f"Papr Key: {os.getenv('PAPR_MEMORY_API_KEY')}")
print(f"OpenAI Key: {os.getenv('OPENAI_API_KEY')}")
```

**Prevention:**
- Use `.env.example` template
- Add `.env` to `.gitignore`
- Validate environment variables on startup

---

## 🐛 Runtime Errors

### 6. PDF Processing Failures

#### **Error**: `Error code: 404 - There was an error adding the memory item`

**Symptoms:**
- Large PDFs fail to upload
- Success with small files, failure with large ones
- Memory items not created

**Root Cause:**
- Content exceeds Papr Memory's 14,000 byte limit per item
- Chunking not working properly

**Solution:**

1. **Verify Chunking Logic:**
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

2. **Test Chunk Sizes:**
```python
chunks = self._chunk_content(content)
for i, chunk in enumerate(chunks):
    print(f"Chunk {i}: {len(chunk)} bytes")
    if len(chunk) > 14000:
        print(f"WARNING: Chunk {i} exceeds limit!")
```

**Prevention:**
- Test with various PDF sizes
- Monitor chunk sizes during processing
- Implement proper error handling for oversized content

---

### 7. SDK Version Compatibility Issues

#### **Error**: `'MemoryResource' object has no attribute 'add_document'` or parameter mismatches

**Symptoms:**
- Method not found errors
- Parameter name mismatches (`api_key` vs `x_api_key`)
- Response structure changes

**Solution:**

1. **Check SDK Version:**
```bash
pip show papr-memory
```

2. **Update to Latest:**
```bash
pip install --upgrade papr-memory>=2.14.0
```

3. **Verify Method Names:**
```python
# Correct method for adding documents
response = self.client.memory.add(
    content=content,
    metadata=metadata
)

# Access response data correctly
memory_id = response.data[0].memory_id
```

4. **Check Parameter Names:**
```python
# Correct client initialization
client = Papr(x_api_key=os.environ.get("PAPR_MEMORY_API_KEY"))
```

**Prevention:**
- Pin SDK versions in requirements.txt
- Test after SDK updates
- Monitor SDK documentation for changes

---

### 8. OpenAI Function Calling Issues

#### **Error**: LLM not using tools or tools returning no results

**Symptoms:**
- AI responds without searching documents
- Tool calls made but return empty results
- Function schema validation errors

**Solution:**

1. **Verify Tool Schema:**
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
                    "description": "Detailed, specific search query..."
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

2. **Check Tool Execution:**
```python
# Add logging to tool execution
logger.info(f"Tool call: {tool_call.function.name}")
logger.info(f"Tool args: {tool_call.function.arguments}")

# Verify tool results
logger.info(f"Tool results: {len(memories)} memories found")
```

3. **Test Content Limits:**
```python
# Increase content limit for better context
result = {
    "content": content[:120000],  # ~30K tokens
    "metadata": memory.get("metadata", {}),
    "score": memory.get("score", 0)
}
```

**Prevention:**
- Test tool calls with simple queries first
- Validate JSON schema syntax
- Monitor OpenAI API changes

---

## 🔍 Debugging Strategies

### General Debugging Approach

1. **Enable Debug Logging:**
```python
# In main.py or service files
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
```

2. **Add Comprehensive Error Handling:**
```python
try:
    result = risky_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    raise HTTPException(status_code=500, detail=str(e))
```

3. **Test Individual Components:**
```python
# Test Papr Memory connection
response = client.memory.search(query="test", metadata={"external_user_id": "test"})
print(f"Search works: {len(response.data.memories)} results")

# Test OpenAI connection  
response = openai_client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}]
)
print(f"OpenAI works: {response.choices[0].message.content}")
```

### Performance Debugging

1. **Add Timing Decorators:**
```python
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

@timing_decorator
def search_memories(self, query: str):
    # Implementation
    pass
```

2. **Monitor Memory Usage:**
```python
import psutil
import os

def log_memory_usage():
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    logger.info(f"Memory usage: {memory_mb:.1f} MB")
```

### Network Debugging

1. **Test API Endpoints:**
```bash
# Test health
curl -v http://localhost:8000/

# Test document list
curl -v http://localhost:8000/documents/list

# Test with invalid data
curl -X POST http://localhost:8000/chat/ \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}'
```

2. **Check External API Connectivity:**
```bash
# Test Papr Memory API
curl -H "x-api-key: $PAPR_MEMORY_API_KEY" https://api.papr.ai/health

# Test OpenAI API
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

---

## 🚀 Production Issues

### 9. CORS Configuration

#### **Error**: Cross-origin requests blocked

**Solution:**
```python
# In main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 10. File Upload Size Limits

#### **Error**: `413 Request Entity Too Large`

**Solution:**
```python
# In main.py
app.add_middleware(
    middleware_class=...,
    max_request_size=50 * 1024 * 1024  # 50MB
)

# Also configure reverse proxy (nginx)
client_max_body_size 50M;
```

### 11. Memory Leaks

#### **Symptoms**: Application memory usage grows over time

**Solution:**
```python
# Proper cleanup after processing
try:
    # Process document
    result = process_large_pdf(content)
finally:
    # Clean up large variables
    del content
    gc.collect()
```

---

## 🔧 Quick Fixes

### Common Quick Solutions

1. **Restart Services:**
```bash
# Kill existing process
pkill -f uvicorn

# Restart application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. **Clear Application State:**
```bash
# Remove local document store
rm documents_store.json

# Clear Python cache
find . -type d -name "__pycache__" -delete
```

3. **Reset Virtual Environment:**
```bash
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

4. **Validate Configuration:**
```bash
python3 test_setup.py
```

---

## 📞 Getting Help

### Before Asking for Help

1. **Check Logs:**
   - Application logs in terminal
   - Browser console for frontend issues
   - Network tab for API issues

2. **Reproduce Issue:**
   - Create minimal reproduction case
   - Note exact error messages
   - Document steps to reproduce

3. **Gather Information:**
   - Python version: `python3 --version`
   - Package versions: `pip list`
   - OS information: `uname -a`
   - Environment variables (redacted)

### Creating Bug Reports

Include:
- **Environment**: OS, Python version, package versions
- **Steps to Reproduce**: Exact steps that cause the issue
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Logs**: Relevant log output (with sensitive data removed)
- **Configuration**: Relevant configuration (API keys redacted)

### Community Resources

- GitHub Issues: Report bugs and feature requests
- Documentation: README.md, DEVELOPMENT.md, API_REFERENCE.md
- Code Examples: See `examples/` directory (if available)

---

This troubleshooting guide covers the most common issues encountered during development. For additional help, consult the other documentation files or create an issue on GitHub.

import os
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from .models.schemas import HealthResponse, ErrorResponse
from .routers import documents, chat, upload_progress

# Load environment variables
# Load .env.local first (takes precedence), then .env
load_dotenv(".env.local")  # Local development overrides
load_dotenv()  # Default .env file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="PDF Chat API with Papr Memory",
    description="A FastAPI application that allows users to upload PDFs and chat with their documents using Papr Memory's context-aware system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(upload_progress.router)

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            code=str(exc.status_code)
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc),
            code="500"
        ).dict()
    )

# Root endpoints
@app.get("/")
async def root():
    """
    Serve the main chat interface.
    """
    return FileResponse("static/index.html")

@app.get("/api", response_model=HealthResponse)
async def api_info():
    """
    API information endpoint.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version="1.0.0"
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint - verifies that the API and its dependencies are working.
    """
    try:
        # Check if required environment variables are set
        required_env_vars = ["PAPR_API_KEY", "PAPR_MEMORY_API_KEY"]
        missing_vars = [var for var in required_env_vars if not (os.getenv("PAPR_API_KEY") or os.getenv("PAPR_MEMORY_API_KEY"))]
        # Only report missing if neither variable is set
        if not (os.getenv("PAPR_API_KEY") or os.getenv("PAPR_MEMORY_API_KEY")):
            missing_vars = ["PAPR_API_KEY or PAPR_MEMORY_API_KEY"]
        else:
            missing_vars = []
        
        if missing_vars:
            raise HTTPException(
                status_code=503,
                detail=f"Missing required environment variables: {', '.join(missing_vars)}"
            )
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now(),
            version="1.0.0"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """
    Application startup event - initialize services and check configuration.
    """
    logger.info("Starting PDF Chat API with Papr Memory...")
    
    # Check required environment variables
    if not (os.getenv("PAPR_API_KEY") or os.getenv("PAPR_MEMORY_API_KEY")):
        missing_vars = ["PAPR_API_KEY or PAPR_MEMORY_API_KEY"]
    else:
        missing_vars = []
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please check your .env file and ensure all required variables are set")
    else:
        logger.info("All required environment variables are set")
    
    # Ensure upload directory exists
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    logger.info(f"Upload directory ensured: {upload_dir}")
    
    logger.info("PDF Chat API startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event - cleanup resources.
    """
    logger.info("Shutting down PDF Chat API...")
    # Add any cleanup logic here if needed
    logger.info("Shutdown complete")

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
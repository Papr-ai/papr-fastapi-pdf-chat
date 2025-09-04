import asyncio
import json
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from ..services.pdf_service import PDFService
from ..services.papr_service import PaprMemoryService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["upload"])

# Global store for progress tracking - persists across requests
progress_store: Dict[str, Dict[str, Any]] = {}

# Add some debugging
import atexit
def cleanup_progress_store():
    logger.info(f"Shutting down with {len(progress_store)} active uploads")
atexit.register(cleanup_progress_store)

class ProgressTracker:
    def __init__(self, upload_id: str):
        self.upload_id = upload_id
        self.progress_store = progress_store
        
    def update_progress(self, current: int, total: int, message: str):
        """Update progress for this upload"""
        percent = (current / total * 100) if total > 0 else 0
        self.progress_store[self.upload_id] = {
            "current": current,
            "total": total,
            "percent": percent,
            "message": message,
            "status": "processing"
        }
        logger.info(f"Progress updated for {self.upload_id}: {percent}% - {message}")
        logger.info(f"Progress store now contains: {list(self.progress_store.keys())}")
        
    def complete(self, result: Dict[str, Any]):
        """Mark upload as complete"""
        self.progress_store[self.upload_id] = {
            "current": result.get("chunks_created", 0),
            "total": result.get("total_chunks", 0),
            "percent": 100,
            "message": f"Complete! Created {result.get('chunks_created', 0)} chunks",
            "status": "complete",
            "result": result
        }
        logger.info(f"Upload {self.upload_id} marked as complete")
        logger.info(f"Progress store after completion: {list(self.progress_store.keys())}")
        
        # Keep completed uploads for 5 minutes so frontend can read them
        import threading
        import time
        def cleanup_later():
            time.sleep(300)  # 5 minutes
            if self.upload_id in self.progress_store:
                del self.progress_store[self.upload_id]
                logger.info(f"Cleaned up expired upload {self.upload_id}")
        
        threading.Thread(target=cleanup_later, daemon=True).start()
        
    def error(self, error_message: str):
        """Mark upload as failed"""
        self.progress_store[self.upload_id] = {
            "current": 0,
            "total": 0,
            "percent": 0,
            "message": f"Error: {error_message}",
            "status": "error"
        }

@router.post("/with-progress/{upload_id}")
async def upload_document_with_progress(
    upload_id: str,
    file: UploadFile = File(..., description="PDF file to upload")
):
    """
    Upload a PDF document with progress tracking
    """
    try:
        logger.info(f"Starting upload with progress tracking: {upload_id}")
        logger.info(f"Progress store before initialization: {list(progress_store.keys())}")
        
        # Initialize progress tracker
        tracker = ProgressTracker(upload_id)
        tracker.update_progress(0, 100, "Starting upload...")
        logger.info(f"Progress store after initialization: {list(progress_store.keys())}")
        
        # Initialize services
        pdf_service = PDFService()
        papr_service = PaprMemoryService()
        
        # Process PDF
        tracker.update_progress(10, 100, "Processing PDF...")
        file_path, extracted_text = await pdf_service.process_pdf(file)
        
        # Add to Papr Memory with progress callback
        tracker.update_progress(30, 100, "Uploading to memory system...")
        
        def progress_callback(current_chunk: int, total_chunks: int, message: str):
            # Calculate progress: 30% base + 70% for chunks
            base_progress = 30
            chunk_progress = (current_chunk / total_chunks) * 70 if total_chunks > 0 else 0
            total_progress = int(base_progress + chunk_progress)
            
            # Update the progress tracker with current chunk info
            detailed_message = f"{message} ({current_chunk}/{total_chunks} chunks)"
            tracker.update_progress(total_progress, 100, detailed_message)
            
            logger.info(f"Progress update: {total_progress}% - {detailed_message}")
        
        result = papr_service.add_document(
            content=extracted_text,
            filename=file.filename or "unknown.pdf",
            external_user_id="demo_user",
            metadata={
                "original_filename": file.filename,
                "file_size": len(extracted_text),
                "content_type": "application/pdf"
            },
            progress_callback=progress_callback
        )
        
        # Clean up
        pdf_service.cleanup_file(file_path)
        
        # Mark as complete
        tracker.complete(result)
        
        return {"status": "success", "upload_id": upload_id}
        
    except Exception as e:
        logger.error(f"Upload failed for {upload_id}: {str(e)}")
        tracker = ProgressTracker(upload_id)
        tracker.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/progress/{upload_id}")
async def get_upload_progress(upload_id: str):
    """
    Get current progress for an upload
    """
    logger.info(f"Progress requested for {upload_id}. Available IDs: {list(progress_store.keys())}")
    
    if upload_id not in progress_store:
        logger.warning(f"Upload ID {upload_id} not found in progress store")
        raise HTTPException(status_code=404, detail="Upload not found")
    
    progress_data = progress_store[upload_id]
    logger.info(f"Returning progress for {upload_id}: {progress_data}")
    return progress_data

@router.get("/progress-stream/{upload_id}")
async def stream_upload_progress(upload_id: str):
    """
    Stream upload progress using Server-Sent Events
    """
    async def event_stream():
        while upload_id not in progress_store:
            await asyncio.sleep(0.1)
        
        while True:
            if upload_id in progress_store:
                progress_data = progress_store[upload_id]
                yield f"data: {json.dumps(progress_data)}\n\n"
                
                # Stop streaming when complete or error
                if progress_data.get("status") in ["complete", "error"]:
                    break
            
            await asyncio.sleep(0.2)  # Update every 200ms
    
    return StreamingResponse(
        event_stream(), 
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

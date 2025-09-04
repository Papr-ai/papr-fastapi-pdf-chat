import os
import logging
import aiofiles
from typing import Tuple
import fitz  # PyMuPDF
from fastapi import UploadFile, HTTPException

logger = logging.getLogger(__name__)


class PDFService:
    """Service for handling PDF file operations"""
    
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = upload_dir
        self.max_file_size = int(os.getenv("MAX_FILE_SIZE_MB", "50")) * 1024 * 1024  # Convert MB to bytes
        self.allowed_extensions = os.getenv("ALLOWED_EXTENSIONS", "pdf").split(",")
        
        # Ensure upload directory exists
        os.makedirs(upload_dir, exist_ok=True)
        logger.info(f"PDF service initialized with upload dir: {upload_dir}")
    
    def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file"""
        # Check file extension
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_extension = file.filename.split(".")[-1].lower()
        if file_extension not in self.allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"File type not allowed. Allowed types: {', '.join(self.allowed_extensions)}"
            )
        
        # Check file size (this is a rough check, actual size will be checked during read)
        if hasattr(file, 'size') and file.size and file.size > self.max_file_size:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size: {self.max_file_size // 1024 // 1024}MB"
            )
    
    async def save_file(self, file: UploadFile) -> str:
        """Save uploaded file to disk"""
        self._validate_file(file)
        
        # Generate unique filename
        import uuid
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(self.upload_dir, unique_filename)
        
        try:
            # Read and save file
            content = await file.read()
            
            # Check actual file size
            if len(content) > self.max_file_size:
                raise HTTPException(
                    status_code=413, 
                    detail=f"File too large. Maximum size: {self.max_file_size // 1024 // 1024}MB"
                )
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            logger.info(f"File saved: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            # Clean up partial file if it exists
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text content from PDF file using PyMuPDF"""
        try:
            # Open the PDF document
            doc = fitz.open(file_path)
            
            if doc.page_count == 0:
                doc.close()
                raise HTTPException(status_code=400, detail="PDF file appears to be empty")
            
            text_content = []
            for page_num in range(doc.page_count):
                try:
                    page = doc[page_num]
                    # Extract text with better formatting preservation
                    page_text = page.get_text("text")  # "text" mode preserves layout better
                    
                    if page_text.strip():  # Only add non-empty pages
                        text_content.append(f"[Page {page_num + 1}]\n{page_text}")
                    else:
                        # Try to extract from images if no text found (basic fallback)
                        logger.warning(f"Page {page_num + 1} contains no extractable text")
                        
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num + 1}: {str(e)}")
                    continue
            
            doc.close()  # Always close the document
            
            if not text_content:
                raise HTTPException(status_code=400, detail="No readable text found in PDF")
            
            full_text = "\n\n".join(text_content)
            logger.info(f"Extracted {len(full_text)} characters from {len(text_content)} pages in PDF: {file_path}")
            return full_text
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    
    async def process_pdf(self, file: UploadFile) -> Tuple[str, str]:
        """
        Process uploaded PDF file
        
        Returns:
            Tuple of (file_path, extracted_text)
        """
        # Save file
        file_path = await self.save_file(file)
        
        try:
            # Extract text
            text_content = self.extract_text_from_pdf(file_path)
            return file_path, text_content
            
        except Exception as e:
            # Clean up file if text extraction fails
            if os.path.exists(file_path):
                os.remove(file_path)
            raise
    
    def cleanup_file(self, file_path: str) -> None:
        """Remove file from disk"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up file: {file_path}")
        except Exception as e:
            logger.warning(f"Error cleaning up file {file_path}: {str(e)}")
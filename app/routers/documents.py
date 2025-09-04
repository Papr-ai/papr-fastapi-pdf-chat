import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any

from ..models.schemas import DocumentUploadResponse, DocumentStatusResponse, ErrorResponse
from ..services.pdf_service import PDFService
from ..services.papr_service import PaprMemoryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

# Dependency injection
def get_pdf_service():
    return PDFService()

def get_papr_service():
    return PaprMemoryService()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(..., description="PDF file to upload"),
    pdf_service: PDFService = Depends(get_pdf_service),
    papr_service: PaprMemoryService = Depends(get_papr_service)
):
    """
    Upload a PDF document and add it to Papr Memory for chat interactions.
    
    - **file**: PDF file to upload (max 50MB by default)
    
    Returns the document ID that can be used for chat interactions.
    """
    try:
        logger.info(f"Starting upload for file: {file.filename}")
        
        # Process PDF file
        file_path, extracted_text = await pdf_service.process_pdf(file)
        
        try:
            # Add document to Papr Memory
            # TODO: In a real app, get external_user_id from authentication
            external_user_id = "demo_user"  # For now, use a default user
            
            result = papr_service.add_document(
                content=extracted_text,
                filename=file.filename or "unknown.pdf",
                external_user_id=external_user_id,
                metadata={
                    "original_filename": file.filename,
                    "file_size": len(extracted_text),
                    "content_type": "application/pdf"
                }
            )
            
            document_id = result["document_id"]
            chunks_created = result["chunks_created"]
            total_chunks = result["total_chunks"]
            
            # Clean up the temporary file
            pdf_service.cleanup_file(file_path)
            
            logger.info(f"Successfully processed document: {document_id}")
            
            return DocumentUploadResponse(
                document_id=document_id,
                filename=file.filename or "unknown.pdf",
                status="success",
                message=f"Document uploaded and processed successfully ({chunks_created} chunks created)",
                chunks_created=chunks_created,
                total_chunks=total_chunks
            )
            
        except Exception as e:
            # Clean up file if Papr Memory addition fails
            pdf_service.cleanup_file(file_path)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to add document to memory system: {str(e)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during document upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get("/list")
async def list_user_documents(
    papr_service: PaprMemoryService = Depends(get_papr_service)
):
    """
    Get all documents for the current user
    
    Returns:
        List of user's documents with metadata
    """
    try:
        logger.info("Fetching user documents")
        
        # TODO: In a real app, get external_user_id from authentication
        external_user_id = "demo_user"  # For now, use a default user
        
        documents = papr_service.get_user_documents(external_user_id)
        
        logger.info(f"Retrieved {len(documents)} documents for user")
        
        return {
            "documents": documents,
            "count": len(documents),
            "user_id": external_user_id
        }
        
    except Exception as e:
        logger.error(f"Error fetching user documents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch documents: {str(e)}"
        )


@router.get("/status/{document_id}", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: str,
    papr_service: PaprMemoryService = Depends(get_papr_service)
):
    """
    Get the processing status of a document.
    
    - **document_id**: The ID of the document to check
    
    Returns the current processing status and details.
    """
    try:
        status_info = papr_service.get_document_status(document_id)
        
        return DocumentStatusResponse(
            document_id=document_id,
            status=status_info.get("status", "unknown"),
            processing_details=status_info
        )
        
    except Exception as e:
        logger.error(f"Error getting document status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving document status: {str(e)}"
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    papr_service: PaprMemoryService = Depends(get_papr_service)
):
    """
    Delete a document from the memory system.
    
    - **document_id**: The ID of the document to delete
    
    Returns confirmation of deletion.
    """
    try:
        success = papr_service.delete_document(document_id)
        
        if success:
            return JSONResponse(
                content={
                    "message": f"Document {document_id} deleted successfully",
                    "document_id": document_id,
                    "status": "deleted"
                }
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to delete document"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting document: {str(e)}"
        )
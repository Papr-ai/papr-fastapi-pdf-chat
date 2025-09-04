import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any

from ..models.schemas import ChatMessage, ChatResponse, ErrorResponse
from ..services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Dependency injection
def get_chat_service():
    return ChatService()


@router.post("/", response_model=ChatResponse)
async def chat_with_documents(
    chat_message: ChatMessage,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Chat with your uploaded documents.
    
    - **message**: Your question or message
    - **document_id**: Optional - specify a particular document to search within
    
    Returns an AI response based on the content of your documents.
    """
    try:
        logger.info(f"Processing chat message: {chat_message.message[:100]}...")
        
        # Process the chat message
        result = await chat_service.chat_with_documents(
            message=chat_message.message,
            document_id=chat_message.document_id,
            max_sources=3
        )
        
        return ChatResponse(
            response=result["response"],
            sources=result.get("sources", []),
            document_id=result.get("document_id")
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat message: {str(e)}"
        )


@router.post("/summary/{document_id}")
async def get_document_summary(
    document_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Get a summary of a specific document.
    
    - **document_id**: The ID of the document to summarize
    
    Returns a summary of the document content.
    """
    try:
        logger.info(f"Generating summary for document: {document_id}")
        
        summary_result = await chat_service.get_document_summary(document_id)
        
        return {
            "document_id": document_id,
            "summary": summary_result.get("summary"),
            "metadata": {
                "filename": summary_result.get("filename"),
                "content_length": summary_result.get("content_length"),
                "sections_found": summary_result.get("sections_found")
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating document summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating document summary: {str(e)}"
        )


@router.get("/health")
async def chat_health_check():
    """
    Check if the chat service is healthy and can connect to Papr Memory.
    """
    try:
        # Try to initialize the chat service to test connectivity
        chat_service = ChatService()
        
        return {
            "status": "healthy",
            "message": "Chat service is operational",
            "papr_connection": "connected"
        }
        
    except Exception as e:
        logger.error(f"Chat service health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Chat service unavailable: {str(e)}"
        )
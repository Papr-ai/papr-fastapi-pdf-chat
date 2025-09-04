from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ChatMessage(BaseModel):
    message: str = Field(..., description="The user's chat message")
    document_id: Optional[str] = Field(None, description="Optional document ID to chat with specific document")


class ChatResponse(BaseModel):
    response: str = Field(..., description="The AI's response")
    sources: Optional[List[Dict[str, Any]]] = Field(None, description="Source references from the documents")
    document_id: Optional[str] = Field(None, description="Document ID used for the chat")


class DocumentUploadResponse(BaseModel):
    document_id: str = Field(..., description="Unique identifier for the uploaded document")
    filename: str = Field(..., description="Name of the uploaded file")
    status: str = Field(..., description="Upload status")
    message: str = Field(..., description="Status message")
    chunks_created: int = Field(..., description="Number of chunks created")
    total_chunks: int = Field(..., description="Total number of chunks")


class DocumentStatusResponse(BaseModel):
    document_id: str = Field(..., description="Document identifier")
    status: str = Field(..., description="Processing status")
    filename: Optional[str] = Field(None, description="Original filename")
    upload_time: Optional[datetime] = Field(None, description="When the document was uploaded")
    processing_details: Optional[Dict[str, Any]] = Field(None, description="Additional processing information")


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    code: Optional[str] = Field(None, description="Error code")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(..., description="Current timestamp")
    version: str = Field(..., description="API version")
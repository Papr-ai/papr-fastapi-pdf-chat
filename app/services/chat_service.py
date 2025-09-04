import logging
from typing import List, Dict, Any, Optional
from .papr_service import PaprMemoryService
from .llm_service import LLMService

logger = logging.getLogger(__name__)


class ChatService:
    """Service for handling chat interactions with documents"""
    
    def __init__(self):
        self.papr_service = PaprMemoryService()
        self.llm_service = LLMService(papr_service=self.papr_service)  # Inject Papr service
        logger.info("Chat service initialized")
    
    def _format_context_from_memories(self, memories: List[Dict[str, Any]]) -> str:
        """Format retrieved memories into context for the response"""
        if not memories:
            return "No relevant information found in the documents."
        
        context_parts = []
        for i, memory in enumerate(memories, 1):
            content = memory.get('content', '')
            metadata = memory.get('metadata', {})
            filename = metadata.get('filename', 'Unknown document')
            
            # Truncate very long content
            if len(content) > 500:
                content = content[:500] + "..."
            
            context_parts.append(f"Source {i} (from {filename}):\n{content}")
        
        return "\n\n".join(context_parts)
    
    async def _generate_response(
        self, 
        query: str, 
        memories: List[Dict[str, Any]], 
        document_name: Optional[str] = None
    ) -> str:
        """Generate a response using LLM based on the query and retrieved memories"""
        if not memories:
            return "I couldn't find relevant information in your documents to answer that question. Please try rephrasing your question or upload more relevant documents."
        
        # Use LLM to generate response with context
        response = await self.llm_service.generate_response_with_context(
            user_message=query,
            context_memories=memories,
            document_name=document_name
        )
        
        return response
    
    async def chat_with_documents(
        self, 
        message: str, 
        document_id: Optional[str] = None,
        max_sources: int = 15
    ) -> Dict[str, Any]:
        """
        Process a chat message and return a response with sources
        
        Args:
            message: User's chat message
            document_id: Optional specific document to search within
            max_sources: Maximum number of source documents to include
            
        Returns:
            Dictionary with response, sources, and metadata
        """
        try:
            # Use the new tool-based approach for more intelligent responses
            # TODO: In a real app, get external_user_id from authentication
            external_user_id = "demo_user"  # For now, use a default user
            
            # Generate response using LLM with tool calls
            response = await self.llm_service.generate_response_with_tools(
                user_message=message,
                document_id=document_id,
                external_user_id=external_user_id
            )
            
            # For backwards compatibility, also search for sources to display
            memories = self.papr_service.search_memories(
                query=message,
                external_user_id=external_user_id,
                document_id=document_id,
                max_results=min(max_sources, 15)  # Limit for UI display
            )
            
            # Format sources for the response
            sources = []
            for memory in memories:
                metadata = memory.get('metadata', {})
                sources.append({
                    "document_id": memory.get('id'),
                    "filename": metadata.get('filename', 'Unknown'),
                    "content_preview": memory.get('content', '')[:200] + "..." if len(memory.get('content', '')) > 200 else memory.get('content', ''),
                    "relevance_score": memory.get('score')
                })
            
            result = {
                "response": response,
                "sources": sources,
                "document_id": document_id,
                "query": message,
                "total_sources": len(sources)
            }
            
            logger.info(f"Generated chat response with {len(sources)} sources")
            return result
            
        except Exception as e:
            logger.error(f"Error in chat service: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                "response": f"I apologize, but I encountered an error while processing your question. Error: {str(e)}",
                "sources": [],
                "document_id": document_id,
                "query": message,
                "error": str(e)
            }
    
    async def get_document_summary(self, document_id: str) -> Dict[str, Any]:
        """
        Get a summary of a specific document
        
        Args:
            document_id: Document ID to summarize
            
        Returns:
            Dictionary with document summary information
        """
        try:
            # Search for content from the specific document
            # TODO: In a real app, get external_user_id from authentication
            external_user_id = "demo_user"  # For now, use a default user
            
            memories = self.papr_service.search_memories(
                query="Provide a summary of this document including key topics and main points",
                external_user_id=external_user_id,
                document_id=document_id,
                max_results=10
            )
            
            if not memories:
                return {
                    "summary": "No content found for this document.",
                    "document_id": document_id,
                    "key_topics": []
                }
            
            # Get document metadata
            metadata = {}
            if memories:
                metadata = memories[0].get('metadata', {})
            
            document_name = metadata.get('filename', 'Unknown Document')
            
            # Generate summary using LLM
            summary = await self.llm_service.generate_summary(
                context_memories=memories,
                document_name=document_name
            )
            
            return {
                "summary": summary,
                "document_id": document_id,
                "filename": document_name,
                "sections_found": len(memories)
            }
            
        except Exception as e:
            logger.error(f"Error generating document summary: {str(e)}")
            return {
                "summary": "Error generating summary for this document.",
                "document_id": document_id,
                "error": str(e)
            }
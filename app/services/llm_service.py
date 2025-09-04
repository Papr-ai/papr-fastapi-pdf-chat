import os
import logging
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMService:
    """Service for handling LLM interactions with OpenAI"""
    
    def __init__(self, papr_service=None):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o"  # Use the more powerful model
        self.papr_service = papr_service  # Inject Papr service for tool calls
        logger.info("LLM service initialized with OpenAI")
    
    async def generate_response_with_context(
        self,
        user_message: str,
        context_memories: List[Dict[str, Any]],
        document_name: Optional[str] = None
    ) -> str:
        """
        Generate a response using LLM with context from Papr Memory
        
        Args:
            user_message: The user's query
            context_memories: A list of relevant memories (chunks) from Papr Memory
            document_name: The name of the document being chatted with
            
        Returns:
            The LLM's generated response
        """
        try:
            if not context_memories:
                return "I couldn't find relevant information in your documents to answer that question. Please try rephrasing your question or upload more relevant documents."
            
            # Format context from memories
            context_text = self._format_context_from_memories(context_memories)
            
            # Create system and user prompts
            system_prompt = self._create_system_prompt(document_name)
            user_prompt = self._create_user_prompt(user_message, context_text)
            
            # Generate response
            chat_completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=1000
            )
            
            response_content = chat_completion.choices[0].message.content
            logger.info(f"LLM generated response for query: {user_message}")
            return response_content
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}")
            return "I apologize, but I encountered an error while trying to generate a response."
    
    async def generate_summary(
        self,
        context_memories: List[Dict[str, Any]],
        document_name: Optional[str] = None
    ) -> str:
        """
        Generate a summary of the document content using the LLM
        
        Args:
            context_memories: A list of relevant memories (chunks) from Papr Memory
            document_name: The name of the document to summarize
            
        Returns:
            The LLM's generated summary
        """
        try:
            if not context_memories:
                return "No content found to summarize."
            
            # Format context from memories
            context_text = self._format_context_from_memories(context_memories)
            
            system_prompt = f"""You are a helpful AI assistant specialized in summarizing documents.
Provide a comprehensive summary of the following document content, highlighting:
1. Main topics and themes
2. Key findings or insights
3. Important data or statistics
4. Conclusions or recommendations

Document: {document_name or 'Uploaded Document'}"""
            
            user_prompt = f"""Please provide a comprehensive summary of this document content:

{context_text}

Focus on the most important information and present it in a clear, organized manner."""
            
            # Generate summary
            chat_completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=1500
            )
            
            summary_content = chat_completion.choices[0].message.content
            logger.info(f"LLM generated summary for document: {document_name}")
            return summary_content
            
        except Exception as e:
            logger.error(f"Error generating LLM summary: {str(e)}")
            return "I apologize, but I encountered an error while trying to generate a summary."
    
    def _format_context_from_memories(self, memories: List[Dict[str, Any]]) -> str:
        """Format memories into context text for the LLM"""
        if not memories:
            return ""
        
        context_parts = []
        for i, memory in enumerate(memories, 1):
            content = memory.get('content', '')
            metadata = memory.get('metadata', {})
            
            # Add chunk information if available
            chunk_info = ""
            if 'chunk_index' in metadata:
                chunk_info = f" (Chunk {metadata['chunk_index'] + 1})"
            
            context_parts.append(f"[Context {i}{chunk_info}]\n{content}\n")
        
        return "\n".join(context_parts)
    
    def _create_system_prompt(self, document_name: Optional[str] = None) -> str:
        """Create system prompt for the LLM"""
        doc_context = f" about the document '{document_name}'" if document_name else ""
        
        return f"""You are a helpful AI assistant specialized in answering questions{doc_context} based on the provided context.

Instructions:
1. Answer questions using ONLY the information provided in the context
2. If the context doesn't contain enough information to answer the question, clearly state this
3. Be precise and cite specific details from the context when possible
4. If asked about something not in the context, explain that you can only answer based on the provided document content
5. Keep responses informative but concise
6. Use a friendly, professional tone

Remember: You can only reference information that appears in the provided context from the document."""
    
    def _create_user_prompt(self, user_message: str, context_text: str) -> str:
        """Create user prompt with context and question"""
        return f"""Context from the document:
{context_text}

User Question: {user_message}

Please answer the user's question based on the context provided above."""
    
    async def generate_response_with_tools(
        self,
        user_message: str,
        document_id: Optional[str] = None,
        external_user_id: str = "demo_user"
    ) -> str:
        """
        Generate a response using OpenAI tool calls with Papr Memory search
        
        Args:
            user_message: The user's query
            document_id: Optional document ID to search within
            external_user_id: External user ID for memory filtering
            
        Returns:
            The LLM's generated response using tool calls
        """
        if not self.papr_service:
            return "I apologize, but the memory search service is not available."
        
        # Define the tool schema for Papr Memory search
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_memory",
                    "description": "Search through uploaded documents and memories to find relevant information using semantic search",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Detailed, specific search query (2-3 sentences) describing what information to find. Include specific names, dates, technical terms, and context. Example: 'Find financial revenue data and performance metrics from Amazon's annual reports, focusing on total revenue figures and AWS segment contributions for the most recent fiscal year.'"
                            },
                            "document_id": {
                                "type": "string",
                                "description": "Optional document ID to search within a specific document"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results to return (10-50)",
                                "minimum": 10,
                                "maximum": 50,
                                "default": 25
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
        
        # Initial system message with Papr Memory best practices
        system_message = (
            "You are an AI assistant that helps users understand and analyze their uploaded documents. "
            "You have access to a search_memory tool that can find relevant information from their documents. "
            "When using the search tool, ALWAYS create detailed, specific queries following these best practices:\n"
            "- Use 2-3 sentences that clearly describe what you're looking for\n"
            "- Include specific details such as names, dates, or technical terms from the user's question\n"
            "- Provide context about why you're searching for this information\n"
            "- Specify time frames when relevant (e.g., 'recent', 'quarterly', 'annual')\n"
            "- Avoid single keywords or short phrases\n\n"
            "Example: Instead of 'revenue', use 'Find Amazon's total revenue figures and financial performance data from their annual report, including breakdowns by business segments like AWS.'\n\n"
            "After searching, provide a comprehensive answer based on the search results and always cite specific information from the documents."
        )
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        try:
            # Make the initial request with tools
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.2,
                max_tokens=4000  # Increased for more comprehensive responses
            )
            
            assistant_message = response.choices[0].message
            
            # Check if the model wants to use tools
            if assistant_message.tool_calls:
                # Add the assistant message to conversation
                messages.append(assistant_message)
                
                # Process each tool call
                for tool_call in assistant_message.tool_calls:
                    if tool_call.function.name == "search_memory":
                        try:
                            # Parse the function arguments
                            args = json.loads(tool_call.function.arguments)
                            search_query = args.get("query", user_message)
                            search_document_id = args.get("document_id", document_id)
                            max_results = args.get("max_results", 15)
                            
                            logger.info(f"LLM requested memory search: '{search_query}' (max_results: {max_results})")
                            
                            # Call Papr Memory search
                            memories = self.papr_service.search_memories(
                                query=search_query,
                                external_user_id=external_user_id,
                                document_id=search_document_id,
                                max_results=max_results
                            )
                            
                            # Format the search results
                            search_results = []
                            for i, memory in enumerate(memories[:10]):  # Limit to avoid token overflow
                                content = memory.get("content", "")
                                logger.info(f"Memory {i}: content_length={len(content)}, content_preview='{content[:100]}...'")
                                
                                # Use much larger content limit - roughly 30K tokens worth of characters
                                result = {
                                    "content": content[:120000],  # ~30K tokens (4 chars per token average)
                                    "metadata": memory.get("metadata", {}),
                                    "score": memory.get("score", 0)
                                }
                                search_results.append(result)
                            
                            # Add tool result to conversation
                            tool_result = {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps({
                                    "search_query": search_query,
                                    "results_count": len(search_results),
                                    "results": search_results
                                })
                            }
                            messages.append(tool_result)
                            
                            logger.info(f"Memory search returned {len(search_results)} results")
                            logger.info(f"Tool result content length: {len(tool_result['content'])}")
                            
                        except Exception as e:
                            logger.error(f"Error executing search_memory tool: {str(e)}")
                            # Add error result
                            error_result = {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps({
                                    "error": f"Search failed: {str(e)}",
                                    "results": []
                                })
                            }
                            messages.append(error_result)
                
                # Generate final response with tool results
                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.2,
                    max_tokens=4000  # Increased for more comprehensive responses
                )
                
                return final_response.choices[0].message.content
            else:
                # No tool calls needed, return direct response
                return assistant_message.content
                
        except Exception as e:
            logger.error(f"Error generating response with tools: {str(e)}")
            return "I apologize, but I encountered an error while processing your request. Please try again."

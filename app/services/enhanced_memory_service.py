"""
Enhanced Memory Service for intelligent document processing with LLM-generated metadata
"""
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from openai import OpenAI
from .papr_service import PaprMemoryService
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class EnhancedMemoryService:
    """Service for processing documents with LLM-enhanced metadata generation"""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.papr_service = PaprMemoryService()
        self.model = "gpt-4o-mini"
    
    async def process_document_enhanced(
        self,
        content: str,
        filename: str,
        external_user_id: str,
        metadata: Dict[str, Any],
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Process document with enhanced LLM-generated metadata for each chunk
        """
        try:
            logger.info(f"Starting enhanced processing for {filename}")
            
            # Split content into chunks
            chunks = self._chunk_content(content)
            total_chunks = len(chunks)
            
            if progress_callback:
                progress_callback(0, total_chunks, f"Starting enhanced processing of {total_chunks} chunks...")
            
            # Process each chunk with LLM enhancement
            enhanced_chunks = []
            for i, chunk in enumerate(chunks):
                logger.info(f"Processing chunk {i+1}/{total_chunks} with LLM enhancement")
                
                try:
                    # Generate enhanced metadata for this chunk
                    enhanced_metadata = await self._generate_enhanced_metadata(
                        chunk_text=chunk,
                        filename=filename,
                        chunk_index=i,
                        total_chunks=total_chunks,
                        base_metadata=metadata
                    )
                    
                    enhanced_chunks.append({
                        "content": chunk,
                        "metadata": enhanced_metadata
                    })
                    
                    if progress_callback:
                        # First phase: LLM enhancement (0-80% of total progress)
                        progress_callback(
                            i + 1, 
                            total_chunks, 
                            f"Enhanced chunk {i+1}/{total_chunks} with AI metadata"
                        )
                        
                except Exception as e:
                    logger.error(f"Error enhancing chunk {i}: {e}")
                    # Fallback to basic metadata if LLM enhancement fails
                    fallback_metadata = self._create_fallback_metadata(
                        filename, i, total_chunks, metadata
                    )
                    enhanced_chunks.append({
                        "content": chunk,
                        "metadata": fallback_metadata
                    })
            
            # Now add all enhanced chunks to Papr Memory
            logger.info(f"Starting to upload {len(enhanced_chunks)} enhanced chunks to Papr Memory")
            document_id = self._generate_document_id()
            memory_ids = []
            
            for i, enhanced_chunk in enumerate(enhanced_chunks):
                try:
                    logger.info(f"Uploading enhanced chunk {i+1}/{len(enhanced_chunks)} to Papr Memory")
                    # Add to Papr Memory with enhanced metadata
                    memory_id = self.papr_service.add_memory_with_metadata(
                        content=enhanced_chunk["content"],
                        external_user_id=external_user_id,
                        metadata=enhanced_chunk["metadata"]
                    )
                    memory_ids.append(memory_id)
                    logger.info(f"Successfully uploaded chunk {i+1}, memory_id: {memory_id}")
                    
                    if progress_callback:
                        # Second phase: Upload to memory (80-100% of total progress)
                        # This should update the progress in the router's callback
                        progress_callback(
                            len(enhanced_chunks) + i + 1,  # Add offset for second phase
                            total_chunks * 2,  # Double total to account for two phases
                            f"Uploaded enhanced chunk {i+1}/{total_chunks} to memory"
                        )
                        
                except Exception as e:
                    logger.error(f"Error uploading enhanced chunk {i}: {e}")
                    raise
            
            logger.info(f"Successfully processed {filename} with {len(memory_ids)} enhanced chunks")
            logger.info(f"About to return result for {filename}")
            
            return {
                "document_id": document_id,
                "filename": filename,
                "chunks_created": len(memory_ids),
                "total_chunks": total_chunks,
                "memory_ids": memory_ids,
                "enhanced": True
            }
            
        except Exception as e:
            logger.error(f"Enhanced processing failed for {filename}: {e}")
            raise
    
    async def _generate_enhanced_metadata(
        self,
        chunk_text: str,
        filename: str,
        chunk_index: int,
        total_chunks: int,
        base_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use LLM to generate enhanced metadata for a chunk
        """
        
        # Define the tool for the LLM to call
        tools = [{
            "type": "function",
            "function": {
                "name": "create_enhanced_metadata",
                "description": "Generate comprehensive metadata for a document chunk including summary, keywords, entities, topics, and hierarchical structure",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Main title or heading for this chunk content"
                        },
                        "heading_hierarchy": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Hierarchical structure like ['Chapter 1', 'Section 1.2', 'Subsection 1.2.1']"
                        },
                        "summary": {
                            "type": "string",
                            "description": "Concise summary of the chunk content (2-3 sentences)"
                        },
                        "keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Key terms and concepts mentioned in this chunk"
                        },
                        "entities": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Named entities like people, organizations, dates, locations"
                        },
                        "topic_tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "High-level topic categories like 'machine_learning', 'finance', 'research'"
                        },
                        "content_type": {
                            "type": "string",
                            "enum": ["introduction", "methodology", "results", "discussion", "conclusion", "reference", "data", "analysis", "other"],
                            "description": "Type of content this chunk represents"
                        },
                        "language": {
                            "type": "string",
                            "description": "Language code (e.g., 'en', 'es', 'fr')"
                        },
                        "complexity_level": {
                            "type": "string",
                            "enum": ["basic", "intermediate", "advanced", "expert"],
                            "description": "Complexity level of the content"
                        },
                        "key_concepts": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Main concepts or ideas discussed in this chunk"
                        }
                    },
                    "required": ["title", "summary", "keywords", "topic_tags", "content_type", "language"]
                }
            }
        }]
        
        # System message for the LLM
        system_message = (
            "You are an expert document analyzer specializing in creating rich, searchable metadata. "
            "Your goal is to extract meaningful information that enables precise semantic search and content discovery.\n\n"
            "ANALYSIS GUIDELINES:\n"
            "• Extract specific, actionable keywords (not generic terms)\n"
            "• Identify clear hierarchical structure from headings/sections\n"
            "• Create concise but informative summaries (2-3 sentences max)\n"
            "• Detect named entities with proper context\n"
            "• Assign relevant topic tags that reflect the actual content domain\n"
            "• Classify content type based on its function in the document\n"
            "• Assess complexity level based on technical depth and prerequisites\n\n"
            "QUALITY STANDARDS:\n"
            "• Be specific over generic (e.g., 'transformer attention mechanisms' vs 'machine learning')\n"
            "• Focus on searchable terms users would actually query\n"
            "• Ensure hierarchical structure reflects document organization\n"
            "• Make summaries standalone and informative\n\n"
            "EXAMPLES:\n"
            "Good keywords: ['quarterly revenue growth', 'EBITDA margins', 'market expansion strategy']\n"
            "Poor keywords: ['business', 'numbers', 'growth']\n\n"
            "Good topic_tags: ['financial_analysis', 'quarterly_earnings', 'market_strategy']\n"
            "Poor topic_tags: ['business', 'document', 'report']\n\n"
            "Good title: 'Q3 2024 Revenue Analysis and Market Performance'\n"
            "Poor title: 'Financial Information'"
        )
        
        # User message with the chunk content
        user_message = f"""
Analyze this document chunk and generate comprehensive, searchable metadata:

**Document Context:**
- Filename: {filename}
- Chunk: {chunk_index + 1} of {total_chunks}
- Position: {"Beginning" if chunk_index < 3 else "Middle" if chunk_index < total_chunks - 3 else "End"} of document

**Content to Analyze:**
{chunk_text[:4000]}  # Limit content to avoid token limits

**Instructions:**
1. Extract a descriptive title that captures the main topic/section
2. Identify hierarchical structure (chapters, sections, subsections)
3. Create a concise summary focusing on key information
4. List specific keywords that users might search for
5. Identify named entities (people, organizations, dates, locations)
6. Assign topic tags that reflect the content domain
7. Classify the content type and complexity level

Focus on making this content discoverable through semantic search.
"""
        
        try:
            # Call OpenAI with function calling
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "create_enhanced_metadata"}},
                temperature=0.3,
                max_tokens=2000,
                timeout=30  # 30 second timeout
            )
            
            # Extract the function call result
            if response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                enhanced_data = json.loads(tool_call.function.arguments)
                
                # Combine with base metadata
                final_metadata = {
                    **base_metadata,
                    "document_id": self._generate_document_id(),
                    "chunk_index": chunk_index,
                    "total_chunks": total_chunks,
                    "created_at": datetime.utcnow().isoformat(),
                    "enhanced": True,
                    "source_url": filename,  # Add source_url field with PDF filename
                    **enhanced_data
                }
                
                logger.info(f"Generated enhanced metadata for chunk {chunk_index}: {enhanced_data.get('title', 'No title')}")
                return final_metadata
            else:
                logger.warning(f"No tool call in LLM response for chunk {chunk_index}")
                return self._create_fallback_metadata(filename, chunk_index, total_chunks, base_metadata)
                
        except Exception as e:
            logger.error(f"Error generating enhanced metadata for chunk {chunk_index}: {e}")
            return self._create_fallback_metadata(filename, chunk_index, total_chunks, base_metadata)
    
    def _create_fallback_metadata(
        self,
        filename: str,
        chunk_index: int,
        total_chunks: int,
        base_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create fallback metadata when LLM enhancement fails"""
        return {
            **base_metadata,
            "document_id": self._generate_document_id(),
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "title": f"Chunk {chunk_index + 1} from {filename}",
            "summary": f"Content chunk {chunk_index + 1} of {total_chunks} from {filename}",
            "keywords": [filename.replace('.pdf', '').replace('_', ' ')],
            "topic_tags": ["document"],
            "content_type": "other",
            "language": "en",
            "enhanced": False,
            "source_url": filename,  # Add source_url field with PDF filename
            "created_at": datetime.utcnow().isoformat()
        }
    
    def _chunk_content(self, content: str, max_size: int = 12000) -> List[str]:
        """Split content into chunks (smaller size for enhanced processing)"""
        chunks = []
        current_chunk = ""
        
        # Split by paragraphs first
        paragraphs = content.split('\n\n')
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) > max_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = paragraph
                else:
                    # Handle very long paragraphs
                    words = paragraph.split()
                    for word in words:
                        if len(current_chunk) + len(word) > max_size:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                                current_chunk = word
                            else:
                                # Single word is too long, truncate it
                                chunks.append(word[:max_size])
                        else:
                            current_chunk += " " + word if current_chunk else word
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _generate_document_id(self) -> str:
        """Generate a unique document ID"""
        import uuid
        return str(uuid.uuid4())

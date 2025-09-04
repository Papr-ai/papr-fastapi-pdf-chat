import os
import logging
from typing import List, Dict, Any, Optional
from papr_memory import Papr
from papr_memory.types import MemoryMetadata, MemoryType, AddMemoryResponse, SearchResponse, UserResponse
from .document_store import DocumentStore

logger = logging.getLogger(__name__)


class PaprMemoryService:
    """Service class for interacting with Papr Memory API"""
    
    def __init__(self):
        self.api_key = os.getenv("PAPR_API_KEY") or os.getenv("PAPR_MEMORY_API_KEY")
        self.base_url = os.getenv("PAPR_BASE_URL")
        
        if not self.api_key:
            raise ValueError("PAPR_API_KEY or PAPR_MEMORY_API_KEY environment variable is required")
        
        # Initialize the Papr client with proper configuration
        client_kwargs = {"x_api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
            
        self.client = Papr(**client_kwargs)
        self.document_store = DocumentStore()  # Initialize local document store
        logger.info("Papr Memory service initialized with SDK and local document store")
    
    def _ensure_user_exists(self, external_user_id: str, email: str = None) -> None:
        """Ensure a user exists in Papr Memory, create if needed"""
        try:
            # Try to create the user (will fail if already exists)
            user_response: UserResponse = self.client.user.create(
                external_id=external_user_id,
                email=email or f"{external_user_id}@example.com"
            )
            logger.info(f"User created: {user_response.external_id}")
        except Exception as e:
            # User likely already exists, which is fine
            if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                logger.debug(f"User {external_user_id} already exists")
            else:
                logger.warning(f"User creation failed: {e}")

    def _chunk_content(self, content: str, max_chunk_size: int = 14000) -> List[str]:
        """Split content into chunks that fit within Papr Memory's size limit"""
        if len(content.encode('utf-8')) <= max_chunk_size:
            return [content]
        
        chunks = []
        words = content.split()
        current_chunk = []
        current_size = 0
        
        for word in words:
            word_size = len((word + ' ').encode('utf-8'))
            if current_size + word_size > max_chunk_size and current_chunk:
                # Finish current chunk
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_size = word_size
            else:
                current_chunk.append(word)
                current_size += word_size
        
        # Add the last chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks

    def add_document(
        self, 
        content: str, 
        filename: str,
        external_user_id: str = "demo_user",
        metadata: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Add a document to Papr Memory with proper SDK types
        
        Args:
            content: The document content (extracted text from PDF)
            filename: Original filename
            external_user_id: External user identifier for memory isolation
            metadata: Additional custom metadata for the document
            progress_callback: Optional callback function to report progress
            
        Returns:
            Dictionary with document_id, chunks_created, and total_chunks
        """
        try:
            # Ensure user exists first
            self._ensure_user_exists(external_user_id)
            
            # Add a small delay to ensure user is fully created
            import time
            time.sleep(0.5)
            
            # Prepare custom metadata using allowed types
            custom_metadata: Dict[str, str | float | bool | List[str]] = {}
            if metadata:
                # Filter metadata to match allowed types
                for key, value in metadata.items():
                    if isinstance(value, (str, float, bool)) or (isinstance(value, list) and all(isinstance(x, str) for x in value)):
                        custom_metadata[key] = value
                    else:
                        custom_metadata[key] = str(value)  # Convert to string as fallback
            
            # Add our standard metadata
            custom_metadata.update({
                "filename": filename,
                "source": "fastapi-pdf-chat",
                "content_type": "pdf"
            })
            
            # Generate a document ID for grouping chunks
            import uuid
            document_group_id = str(uuid.uuid4())
            
            # Split content into chunks that fit within Papr Memory's 15KB limit
            content_chunks = self._chunk_content(content)
            logger.info(f"Split document into {len(content_chunks)} chunks")
            
            # Report initial progress
            if progress_callback:
                progress_callback(0, len(content_chunks), "Starting chunk upload...")
            
            chunk_ids = []
            for i, chunk in enumerate(content_chunks):
                # Add chunk-specific metadata
                chunk_metadata = custom_metadata.copy()
                chunk_metadata.update({
                    "document_id": document_group_id,
                    "chunk_index": i,
                    "total_chunks": len(content_chunks),
                    "chunk_size": len(chunk)
                })
                
                # Create properly typed metadata using SDK types
                papr_metadata: MemoryMetadataParam = {
                    "external_user_id": external_user_id,
                    "topics": ["document", "pdf"],
                    "custom_metadata": chunk_metadata
                }
                
                logger.info(f"Adding chunk {i+1}/{len(content_chunks)} ({len(chunk)} chars)")
                
                response: AddMemoryResponse = self.client.memory.add(
                    content=chunk,
                    metadata=papr_metadata,
                    type="document"  # MemoryType literal
                )
                
                # Extract memory_id from the response data
                if response.data and len(response.data) > 0:
                    chunk_id = response.data[0].memory_id
                    chunk_ids.append(chunk_id)
                    logger.info(f"Chunk {i+1} added with ID: {chunk_id}")
                    
                    # Report progress after each chunk
                    if progress_callback:
                        progress_percent = ((i + 1) / len(content_chunks)) * 100
                        progress_callback(i + 1, len(content_chunks), f"Uploaded chunk {i+1}/{len(content_chunks)}")
                else:
                    raise ValueError(f"No data returned for chunk {i+1}")
            
            # Save to local document store
            self.document_store.add_document(
                document_id=document_group_id,
                filename=filename,
                external_user_id=external_user_id,
                chunks_created=len(chunk_ids),
                total_chunks=len(content_chunks),
                file_size=len(content),
                metadata=metadata
            )

            logger.info(f"Document '{filename}' successfully added as {len(chunk_ids)} chunks with group ID: {document_group_id}")
            return {
                "document_id": document_group_id,
                "chunks_created": len(chunk_ids),
                "total_chunks": len(content_chunks)
            }
            
        except Exception as e:
            logger.error(f"Error adding document to Papr Memory: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            # Add more detailed error information
            if hasattr(e, 'response'):
                logger.error(f"Response status: {getattr(e.response, 'status_code', 'unknown')}")
                logger.error(f"Response text: {getattr(e.response, 'text', 'unknown')}")
            raise
    
    def search_memories(
        self, 
        query: str, 
        external_user_id: str = "demo_user",
        document_id: Optional[str] = None,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search memories in Papr Memory for a specific external user
        
        Args:
            query: Search query
            external_user_id: External user identifier to filter memories
            document_id: Optional specific document ID to search within
            max_results: Maximum number of results to return
            
        Returns:
            List of relevant memory items
        """
        try:
            # Use direct query for better semantic matching
            search_query = query
            
            # Build metadata filter using proper SDK types
            metadata_filter: MemoryMetadataParam = {
                "external_user_id": external_user_id
            }
            
            # Add document_id filter when specifically requested
            if document_id:
                metadata_filter["custom_metadata"] = {
                    "document_id": document_id
                }
            
            logger.info(f"Papr Memory search - Query: '{search_query}'")
            logger.info(f"Papr Memory search - Metadata filter: {metadata_filter}")
            # Increase max_memories when filtering by document_id to get more chunks from the same document
            if document_id:
                max_memories = min(max(max_results, 20), 50)  # Higher limit for document-specific searches
            else:
                max_memories = min(max(max_results, 10), 50)
                
            logger.info(f"Papr Memory search - Max memories: {max_memories}")
            
            response: SearchResponse = self.client.memory.search(
                query=search_query,
                metadata=metadata_filter,
                max_memories=max_memories
            )
            
            logger.info(f"Papr Memory search response - Status: {response.status}")
            logger.info(f"Papr Memory search response - Data exists: {response.data is not None}")
            if response.data:
                logger.info(f"Papr Memory search response - Memories count: {len(response.data.memories) if response.data.memories else 0}")
                # Debug: Log first few items to understand structure
                if response.data.memories:
                    for i, item in enumerate(response.data.memories[:2]):  # Log first 2 items
                        logger.debug(f"Item {i}: id={item.id}, external_user_id={getattr(item, 'external_user_id', 'NONE')}, topics={getattr(item, 'topics', 'NONE')}")
            
            memories = []
            
            # Get memories from SearchResponse.data.memories
            items = []
            if response.data and response.data.memories:
                items = response.data.memories
            
            for item in items:
                # Extract custom metadata from the DataMemory structure
                # Note: custom_metadata is aliased as "customMetadata" in the SDK
                custom_metadata = {}
                if hasattr(item, 'custom_metadata') and item.custom_metadata:
                    custom_metadata = item.custom_metadata
                
                # Debug: Log what we're getting from each item
                logger.info(f"Processing item {item.id}: content_preview='{item.content[:100]}...', custom_metadata={custom_metadata}")
                
                # Document filtering is now done at the API level via metadata filters
                
                memories.append({
                    "id": item.id,
                    "content": item.content,
                    "metadata": custom_metadata,  # Use our custom metadata
                    "external_user_id": getattr(item, 'external_user_id', None),
                    "score": getattr(item, 'score', None)
                })
            
            logger.info(f"Retrieved {len(memories)} memories for query: {query}")
            return memories
            
        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            raise
    
    def get_user_documents(self, external_user_id: str = "demo_user") -> List[Dict[str, Any]]:
        """
        Get all documents for a specific user
        Uses local document store as primary source with Papr Memory as fallback
        
        Args:
            external_user_id: External user identifier
            
        Returns:
            List of document information with metadata
        """
        try:
            # First, try to get documents from local store
            local_documents = self.document_store.get_user_documents(external_user_id)
            
            if local_documents:
                logger.info(f"Retrieved {len(local_documents)} documents from local store for user {external_user_id}")
                return local_documents
            
            # Fallback: Try to get from Papr Memory if local store is empty
            logger.info("Local store empty, attempting to retrieve from Papr Memory")
            response: SearchResponse = self.client.memory.search(
                query="document pdf content text",  # Broad query to match document content
                metadata={
                    "external_user_id": external_user_id,
                    "topics": ["document", "pdf"]
                },
                max_memories=50  # Papr Memory API: min 10, max 50
            )
            
            # Group chunks by document_id
            documents_map = {}
            
            # Get memories from SearchResponse.data.memories
            items = []
            if response.data and response.data.memories:
                items = response.data.memories
            
            for item in items:
                if hasattr(item, 'metadata') and item.metadata:
                    custom_metadata = item.custom_metadata if hasattr(item, 'custom_metadata') and item.custom_metadata else {}
                    document_id = custom_metadata.get('document_id')
                    
                    if document_id:
                        if document_id not in documents_map:
                            # Create new document entry
                            documents_map[document_id] = {
                                "id": document_id,
                                "filename": custom_metadata.get('filename', 'Unknown Document'),
                                "chunks": [],
                                "total_chunks": custom_metadata.get('total_chunks', 0),
                                "file_size": custom_metadata.get('file_size', 0),
                                "content_type": custom_metadata.get('content_type', 'pdf'),
                                "source": custom_metadata.get('source', 'unknown'),
                                "created_at": None  # We'll try to extract this from the first chunk
                            }
                        
                        # Add chunk info
                        chunk_info = {
                            "chunk_index": custom_metadata.get('chunk_index', 0),
                            "chunk_size": custom_metadata.get('chunk_size', len(item.content)),
                            "memory_id": item.id
                        }
                        documents_map[document_id]["chunks"].append(chunk_info)
            
            # Convert to list and sort chunks
            documents = []
            for doc_id, doc_info in documents_map.items():
                # Sort chunks by index
                doc_info["chunks"].sort(key=lambda x: x.get("chunk_index", 0))
                doc_info["chunks_created"] = len(doc_info["chunks"])
                
                # Estimate upload date (we don't have exact date, so we'll use a placeholder)
                doc_info["uploaded_at"] = "Recently"  # Could be enhanced with actual timestamps
                
                documents.append(doc_info)
            
            # Sort documents by filename
            documents.sort(key=lambda x: x["filename"])
            
            logger.info(f"Retrieved {len(documents)} documents for user {external_user_id}")
            return documents
            
        except Exception as e:
            logger.error(f"Error retrieving user documents: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            # Fallback: Try a different search query approach
            try:
                logger.info("Trying alternative search approach for retrieving documents")
                response: SearchResponse = self.client.memory.search(
                    query="pdf",  # Simple query to match documents
                    metadata={
                        "external_user_id": external_user_id,
                        "topics": ["document", "pdf"]
                    },
                    max_memories=50  # Papr Memory API: min 10, max 50
                )
                
                # Group chunks by document_id (same logic as above)
                documents_map = {}
                
                # Get memories from SearchResponse.data.memories
                items = []
                if response.data and response.data.memories:
                    items = response.data.memories
                
                for item in items:
                    custom_metadata = item.custom_metadata if hasattr(item, 'custom_metadata') and item.custom_metadata else {}
                    document_id = custom_metadata.get('document_id')
                    
                    if document_id:
                        if document_id not in documents_map:
                            documents_map[document_id] = {
                                "id": document_id,
                                "filename": custom_metadata.get('filename', 'Unknown Document'),
                                "chunks": [],
                                "total_chunks": custom_metadata.get('total_chunks', 0),
                                "file_size": custom_metadata.get('file_size', 0),
                                "content_type": custom_metadata.get('content_type', 'pdf'),
                                "source": custom_metadata.get('source', 'unknown'),
                                "created_at": None
                            }
                        
                        chunk_info = {
                            "chunk_index": custom_metadata.get('chunk_index', 0),
                            "chunk_size": custom_metadata.get('chunk_size', len(item.content)),
                            "memory_id": item.id
                        }
                        documents_map[document_id]["chunks"].append(chunk_info)
                
                # Convert to list and sort
                documents = []
                for doc_id, doc_info in documents_map.items():
                    doc_info["chunks"].sort(key=lambda x: x.get("chunk_index", 0))
                    doc_info["chunks_created"] = len(doc_info["chunks"])
                    doc_info["uploaded_at"] = "Recently"
                    documents.append(doc_info)
                
                documents.sort(key=lambda x: x["filename"])
                logger.info(f"Retrieved {len(documents)} documents using fallback search")
                return documents
                
            except Exception as fallback_e:
                logger.error(f"Fallback search also failed: {str(fallback_e)}")
                return []  # Return empty list on error rather than raising
    
    def get_document_status(self, document_id: str) -> Dict[str, Any]:
        """
        Get the processing status of a document
        
        Args:
            document_id: Document ID to check
            
        Returns:
            Document status information
        """
        try:
            response = self.client.memory.get_document_status(document_id)
            return {
                "document_id": document_id,
                "status": response.get("processing_status", "unknown"),
                "chunk_count": response.get("chunk_count", 0),
                "error": response.get("error"),
                "last_updated": response.get("last_updated")
            }
        except Exception as e:
            logger.error(f"Error getting document status: {str(e)}")
            raise
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from Papr Memory
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            True if successful
        """
        try:
            self.client.memory.delete(document_id)
            logger.info(f"Document {document_id} deleted from Papr Memory")
            return True
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise

    def add_memory_with_metadata(
        self,
        content: str,
        external_user_id: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Add a single memory item with comprehensive metadata
        """
        try:
            # Debug: Log the metadata being processed
            logger.info(f"Processing enhanced metadata: {metadata}")
            
            # Convert heading_hierarchy to hierarchical_structures (root level field)
            hierarchical_structures = None
            if "heading_hierarchy" in metadata and metadata["heading_hierarchy"]:
                # Join hierarchy with " > " separator
                hierarchical_structures = " > ".join(metadata["heading_hierarchy"])
            
            # Extract topics from topic_tags array
            topics = metadata.get("topic_tags", ["document"])
            
            # Create custom_metadata by excluding standard fields that go in root
            standard_fields = {
                "topic_tags", "external_user_id", "created_at", 
                "document_id", "chunk_index", "total_chunks", "enhanced",
                "heading_hierarchy",  # This goes to hierarchical_structures instead
                "source_url"  # This goes to root level
            }
            custom_metadata = {
                key: value for key, value in metadata.items() 
                if key not in standard_fields
            }
            
            # Create the memory metadata structure
            memory_metadata = MemoryMetadata(
                external_user_id=external_user_id,
                topics=topics,
                customMetadata=custom_metadata,  # Use correct alias
                createdAt=metadata.get("created_at"),  # Use correct alias
                hierarchical_structures=hierarchical_structures,
                sourceUrl=metadata.get("source_url")  # Use correct alias
            )
            
            logger.info(f"Created MemoryMetadata:")
            logger.info(f"  - external_user_id: {external_user_id}")
            logger.info(f"  - topics: {topics}")
            logger.info(f"  - hierarchical_structures: {hierarchical_structures}")
            logger.info(f"  - source_url: {metadata.get('source_url')}")
            logger.info(f"  - custom_metadata keys: {list(custom_metadata.keys())}")
            logger.info(f"  - custom_metadata values: {custom_metadata}")
            logger.info(f"  - created_at: {metadata.get('created_at')}")
            
            # Verify the MemoryMetadata object was created correctly
            logger.info(f"MemoryMetadata verification:")
            logger.info(f"  - memory_metadata.custom_metadata: {memory_metadata.custom_metadata}")
            logger.info(f"  - memory_metadata.topics: {memory_metadata.topics}")
            logger.info(f"  - memory_metadata.hierarchical_structures: {memory_metadata.hierarchical_structures}")
            
            # Add to Papr Memory
            response = self.client.memory.add(
                content=content,
                metadata=memory_metadata,
                type="text"
            )
            
            memory_id = response.data[0].memory_id
            logger.info(f"Added enhanced memory with ID: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Error adding enhanced memory: {e}", exc_info=True)
            logger.error(f"Failed metadata structure: {memory_metadata}")
            logger.error(f"Failed custom_metadata: {custom_metadata}")
            raise
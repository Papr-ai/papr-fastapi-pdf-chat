import json
import os
import logging
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class DocumentStore:
    """Simple local storage for document metadata to track user's uploaded documents"""
    
    def __init__(self, storage_file: str = "documents_store.json"):
        self.storage_file = storage_file
        self.documents = self._load_documents()
    
    def _load_documents(self) -> Dict[str, Dict[str, Any]]:
        """Load documents from JSON file"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading documents store: {str(e)}")
            return {}
    
    def _save_documents(self):
        """Save documents to JSON file"""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.documents, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving documents store: {str(e)}")
    
    def add_document(
        self, 
        document_id: str, 
        filename: str, 
        external_user_id: str = "demo_user",
        chunks_created: int = 0,
        total_chunks: int = 0,
        file_size: int = 0,
        metadata: Dict[str, Any] = None
    ):
        """Add a document to the local store"""
        try:
            if external_user_id not in self.documents:
                self.documents[external_user_id] = {}
            
            self.documents[external_user_id][document_id] = {
                "id": document_id,
                "filename": filename,
                "uploaded_at": datetime.now().isoformat(),
                "chunks_created": chunks_created,
                "total_chunks": total_chunks,
                "file_size": file_size,
                "metadata": metadata or {}
            }
            
            self._save_documents()
            logger.info(f"Added document {filename} to local store for user {external_user_id}")
            
        except Exception as e:
            logger.error(f"Error adding document to store: {str(e)}")
    
    def get_user_documents(self, external_user_id: str = "demo_user") -> List[Dict[str, Any]]:
        """Get all documents for a user from local store"""
        try:
            user_docs = self.documents.get(external_user_id, {})
            documents = list(user_docs.values())
            
            # Sort by upload date (newest first)
            documents.sort(key=lambda x: x.get('uploaded_at', ''), reverse=True)
            
            logger.info(f"Retrieved {len(documents)} documents from local store for user {external_user_id}")
            return documents
            
        except Exception as e:
            logger.error(f"Error retrieving documents from store: {str(e)}")
            return []
    
    def remove_document(self, document_id: str, external_user_id: str = "demo_user"):
        """Remove a document from the local store"""
        try:
            if external_user_id in self.documents and document_id in self.documents[external_user_id]:
                del self.documents[external_user_id][document_id]
                self._save_documents()
                logger.info(f"Removed document {document_id} from local store")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing document from store: {str(e)}")
            return False
    
    def document_exists(self, document_id: str, external_user_id: str = "demo_user") -> bool:
        """Check if a document exists in the store"""
        return (external_user_id in self.documents and 
                document_id in self.documents[external_user_id])

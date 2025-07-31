from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
import os
import logging
from datetime import datetime
from fastapi import HTTPException

from langchain_community.document_loaders import (
    PyPDFLoader, 
    TextLoader, 
    JSONLoader, 
    CSVLoader,
    Docx2txtLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import numpy as np

from app.models.knowledge_base import (
    KnowledgeBase,
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseList
)
from app.core.config import settings

logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    def __init__(self):
        # Try to get Supabase client, but don't fail if it's not available
        try:
            from app.core.dependencies import get_supabase_client
            self.supabase = get_supabase_client()
            logger.info(f"Supabase client initialized. Has table method: {hasattr(self.supabase, 'table')}")
            if self.supabase:
                available_methods = [attr for attr in dir(self.supabase) if not attr.startswith('_') and callable(getattr(self.supabase, attr))]
                logger.info(f"Available Supabase client methods: {available_methods}")
        except Exception as e:
            logger.error(f"Could not initialize Supabase client: {e}", exc_info=True)
            self.supabase = None
            
        self.embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        self.storage_bucket = "knowledge-bases"
        
        
        # Ensure storage bucket exists (only if storage is available)
        try:
            if self.supabase and hasattr(self.supabase, 'storage'):
                self._ensure_bucket_exists()
        except Exception as e:
            logger.warning(f"Could not ensure storage bucket exists: {e}")
    
    def _ensure_bucket_exists(self):
        """Ensure the knowledge-bases bucket exists in Supabase storage"""
        try:
            buckets = self.supabase.storage.list_buckets()
            bucket_names = [b.name for b in buckets]
            
            if self.storage_bucket not in bucket_names:
                self.supabase.storage.create_bucket(
                    self.storage_bucket,
                    {"public": False}
                )
                logger.info(f"Created storage bucket: {self.storage_bucket}")
        except Exception as e:
            logger.error(f"Error ensuring bucket exists: {e}")
    
    def _get_loader(self, file_path: str, file_type: str):
        """Get the appropriate document loader based on file type"""
        loaders = {
            "pdf": PyPDFLoader,
            "txt": TextLoader,
            "json": JSONLoader,
            "csv": CSVLoader,
            "docx": Docx2txtLoader
        }
        
        loader_class = loaders.get(file_type)
        if not loader_class:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        if file_type == "json":
            return loader_class(file_path, jq_schema=".", text_content=False)
        else:
            return loader_class(file_path)
    
    async def list_knowledge_bases(
        self,
        organization_id: UUID,
        project_id: Optional[UUID] = None,
        department_id: Optional[UUID] = None,
        agent_type: Optional[str] = None,
        user_id: Optional[UUID] = None
    ) -> List[KnowledgeBaseList]:
        """List knowledge bases for a given scope"""
        try:
            # Database is required
            if not self.supabase or not hasattr(self.supabase, 'table'):
                raise HTTPException(
                    status_code=503,
                    detail="Database service is not available. Please check your Supabase configuration."
                )
                
            query = self.supabase.table("knowledge_bases").select("*")
            query = query.eq("organization_id", str(organization_id))
            query = query.eq("is_active", True)
            
            if project_id:
                query = query.eq("project_id", str(project_id))
            if department_id:
                query = query.eq("department_id", str(department_id))
            if agent_type:
                query = query.eq("agent_type", agent_type)
            
            response = query.execute()
            data = response.data
            
            # Add scope level to each knowledge base
            kb_list = []
            for kb in data:
                kb_dict = dict(kb)
                if kb.get("agent_type") and kb.get("department_id"):
                    kb_dict["scope_level"] = "agent_department"
                elif kb.get("agent_type") and kb.get("project_id"):
                    kb_dict["scope_level"] = "agent_project"
                elif kb.get("department_id"):
                    kb_dict["scope_level"] = "department"
                elif kb.get("project_id"):
                    kb_dict["scope_level"] = "project"
                else:
                    kb_dict["scope_level"] = "organization"
                
                kb_list.append(KnowledgeBaseList(**kb_dict))
            
            return kb_list
        except Exception as e:
            logger.error(f"Error listing knowledge bases: {e}", exc_info=True)
            return []
    
    async def get_knowledge_base(
        self,
        knowledge_base_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Optional[KnowledgeBase]:
        """Get a specific knowledge base"""
        try:
            response = self.supabase.table("knowledge_bases").select("*").eq(
                "id", str(knowledge_base_id)
            ).single().execute()
            
            if response.data:
                return KnowledgeBase(**response.data)
            return None
        except Exception as e:
            logger.error(f"Error getting knowledge base: {e}")
            return None
    
    async def create_knowledge_base(
        self,
        kb_create: KnowledgeBaseCreate,
        file_content: bytes,
        user_id: UUID
    ) -> KnowledgeBase:
        """Create a new knowledge base with file upload and indexing"""
        try:
            # Generate unique file path
            file_id = uuid4()
            file_path = f"{kb_create.organization_id}/{file_id}_{kb_create.file_name}"
            
            # For text content, store it locally as a temporary workaround
            # Check if this is text content from the API
            if kb_create.file_type == 'txt' and kb_create.file_name.endswith('.txt'):
                # Store text content locally temporarily
                import tempfile
                temp_dir = tempfile.gettempdir()
                local_path = os.path.join(temp_dir, f"kb_{file_id}.txt")
                with open(local_path, 'wb') as f:
                    f.write(file_content)
                logger.info(f"Created text-based knowledge base locally: {kb_create.name} at {local_path}")
            else:
                # Upload file to Supabase storage (only if storage is available)
                try:
                    if hasattr(self.supabase, 'storage'):
                        response = self.supabase.storage.from_(self.storage_bucket).upload(
                            file_path,
                            file_content,
                            {
                                "content-type": self._get_content_type(kb_create.file_type),
                                "cache-control": "3600"
                            }
                        )
                    else:
                        # Fallback: store locally
                        import tempfile
                        temp_dir = tempfile.gettempdir()
                        local_path = os.path.join(temp_dir, f"kb_{file_id}_{kb_create.file_name}")
                        with open(local_path, 'wb') as f:
                            f.write(file_content)
                        logger.warning(f"Storage not available, stored file locally at {local_path}")
                except Exception as e:
                    logger.error(f"Error uploading to storage: {e}")
                    # Fallback: store locally
                    import tempfile
                    temp_dir = tempfile.gettempdir()
                    local_path = os.path.join(temp_dir, f"kb_{file_id}_{kb_create.file_name}")
                    with open(local_path, 'wb') as f:
                        f.write(file_content)
                    logger.warning(f"Storage error, stored file locally at {local_path}")
            
            # Ensure we have a valid user_id
            if not user_id:
                raise ValueError("User ID is required to create knowledge base")
            
            # Create database record
            kb_data = {
                **kb_create.model_dump(),
                "file_path": file_path,
                "created_by": str(user_id),
                "id": str(file_id),
                "is_active": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Database is required - no fallback to in-memory
            if not self.supabase or not hasattr(self.supabase, 'table'):
                raise HTTPException(
                    status_code=503,
                    detail="Database service is not available. Please check your Supabase configuration."
                )
            
            try:
                response = self.supabase.table("knowledge_bases").insert(kb_data).execute()
                kb = KnowledgeBase(**response.data[0])
            except Exception as e:
                logger.error(f"Failed to persist to database: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create knowledge base: {str(e)}"
                )
            
            # Process and index the file
            await self._index_knowledge_base(kb, file_content)
            
            return kb
        except Exception as e:
            logger.error(f"Error creating knowledge base: {e}", exc_info=True)
            raise
    
    async def update_knowledge_base(
        self,
        knowledge_base_id: UUID,
        update: KnowledgeBaseUpdate,
        user_id: UUID
    ) -> Optional[KnowledgeBase]:
        """Update knowledge base metadata"""
        try:
            update_data = update.dict(exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow().isoformat()
            
            response = self.supabase.table("knowledge_bases").update(
                update_data
            ).eq("id", str(knowledge_base_id)).execute()
            
            if response.data:
                return KnowledgeBase(**response.data[0])
            return None
        except Exception as e:
            logger.error(f"Error updating knowledge base: {e}")
            return None
    
    async def delete_knowledge_base(
        self,
        knowledge_base_id: UUID,
        user_id: UUID
    ) -> bool:
        """Delete a knowledge base"""
        try:
            # Get knowledge base to find file path
            kb = await self.get_knowledge_base(knowledge_base_id)
            if not kb:
                return False
            
            # Delete from storage
            self.supabase.storage.from_(self.storage_bucket).remove([kb.file_path])
            
            # Delete embeddings
            self.supabase.table("knowledge_base_embeddings").delete().eq(
                "knowledge_base_id", str(knowledge_base_id)
            ).execute()
            
            # Delete knowledge base record
            self.supabase.table("knowledge_bases").delete().eq(
                "id", str(knowledge_base_id)
            ).execute()
            
            return True
        except Exception as e:
            logger.error(f"Error deleting knowledge base: {e}")
            return False
    
    async def reindex_knowledge_base(
        self,
        knowledge_base_id: UUID,
        user_id: UUID
    ) -> bool:
        """Reindex a knowledge base"""
        try:
            kb = await self.get_knowledge_base(knowledge_base_id)
            if not kb:
                return False
            
            # Download file from storage
            file_content = self.supabase.storage.from_(self.storage_bucket).download(
                kb.file_path
            )
            
            # Delete existing embeddings
            self.supabase.table("knowledge_base_embeddings").delete().eq(
                "knowledge_base_id", str(knowledge_base_id)
            ).execute()
            
            # Reindex
            await self._index_knowledge_base(kb, file_content)
            
            return True
        except Exception as e:
            logger.error(f"Error reindexing knowledge base: {e}")
            return False
    
    async def get_applicable_knowledge_bases(
        self,
        organization_id: UUID,
        project_id: Optional[UUID] = None,
        department_id: Optional[UUID] = None,
        agent_type: Optional[str] = None,
        user_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get all applicable knowledge bases for a given context"""
        try:
            # Call the database function
            response = self.supabase.rpc(
                "get_applicable_knowledge_bases",
                {
                    "p_organization_id": str(organization_id),
                    "p_project_id": str(project_id) if project_id else None,
                    "p_department_id": str(department_id) if department_id else None,
                    "p_agent_type": agent_type
                }
            ).execute()
            
            return response.data
        except Exception as e:
            logger.error(f"Error getting applicable knowledge bases: {e}")
            return []
    
    async def _index_knowledge_base(self, kb: KnowledgeBase, file_content: bytes):
        """Process and index a knowledge base file"""
        try:
            # Save file temporarily
            temp_path = f"/tmp/{kb.id}_{kb.file_name}"
            with open(temp_path, "wb") as f:
                f.write(file_content)
            
            # Load and split documents
            loader = self._get_loader(temp_path, kb.file_type)
            documents = loader.load()
            texts = self.text_splitter.split_documents(documents)
            
            # Generate embeddings
            embeddings_data = []
            for idx, doc in enumerate(texts):
                embedding = self.embeddings.embed_query(doc.page_content)
                embeddings_data.append({
                    "knowledge_base_id": str(kb.id),
                    "chunk_index": idx,
                    "chunk_text": doc.page_content,
                    "embedding_vector": embedding,
                    "metadata": doc.metadata
                })
            
            # Store embeddings in database
            if embeddings_data:
                self.supabase.table("knowledge_base_embeddings").insert(
                    embeddings_data
                ).execute()
            
            # Create FAISS index
            vector_store = FAISS.from_documents(texts, self.embeddings)
            vector_store_id = f"faiss_{kb.id}"
            vector_store.save_local(f"/tmp/{vector_store_id}")
            
            # Update knowledge base with vector store ID
            self.supabase.table("knowledge_bases").update({
                "vector_store_id": vector_store_id
            }).eq("id", str(kb.id)).execute()
            
            # Clean up temp file
            os.remove(temp_path)
            
            logger.info(f"Successfully indexed knowledge base {kb.id} with {len(texts)} chunks")
        except Exception as e:
            logger.error(f"Error indexing knowledge base: {e}")
            raise
    
    def _get_content_type(self, file_type: str) -> str:
        """Get content type for file type"""
        content_types = {
            "pdf": "application/pdf",
            "txt": "text/plain",
            "json": "application/json",
            "csv": "text/csv",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }
        return content_types.get(file_type, "application/octet-stream")

    async def search_knowledge_bases(
        self,
        query: str,
        knowledge_base_ids: List[UUID],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search across multiple knowledge bases"""
        try:
            all_results = []
            
            for kb_id in knowledge_base_ids:
                # Get embeddings from database
                response = self.supabase.table("knowledge_base_embeddings").select(
                    "chunk_text, embedding_vector, metadata"
                ).eq("knowledge_base_id", str(kb_id)).execute()
                
                if not response.data:
                    continue
                
                # Convert to numpy arrays
                embeddings = np.array([doc["embedding_vector"] for doc in response.data])
                texts = [doc["chunk_text"] for doc in response.data]
                
                # Generate query embedding
                query_embedding = np.array(self.embeddings.embed_query(query))
                
                # Calculate cosine similarities
                similarities = np.dot(embeddings, query_embedding) / (
                    np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_embedding)
                )
                
                # Get top k results
                top_indices = np.argsort(similarities)[-top_k:][::-1]
                
                for idx in top_indices:
                    all_results.append({
                        "knowledge_base_id": str(kb_id),
                        "chunk_text": texts[idx],
                        "score": float(similarities[idx]),
                        "metadata": response.data[idx].get("metadata", {})
                    })
            
            # Sort all results by score
            all_results.sort(key=lambda x: x["score"], reverse=True)
            
            return all_results[:top_k]
        except Exception as e:
            logger.error(f"Error searching knowledge bases: {e}")
            return []
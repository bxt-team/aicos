"""
Enhanced Knowledge Base Manager
Integrates multi-level knowledge bases with agents
"""
import os
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import numpy as np

from app.services.knowledge_base_service import KnowledgeBaseService

logger = logging.getLogger(__name__)

class EnhancedKnowledgeBaseManager:
    """Manages knowledge bases with multi-level hierarchy support"""
    
    _instance: Optional['EnhancedKnowledgeBaseManager'] = None
    _vector_stores: Dict[str, FAISS] = {}
    _embeddings: Optional[OpenAIEmbeddings] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.kb_service = KnowledgeBaseService()
        self.supabase = get_supabase_client()
    
    def initialize(self, openai_api_key: str):
        """Initialize the embeddings"""
        if self._embeddings is None:
            self._embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
            logger.info("Enhanced knowledge base manager initialized")
    
    async def get_agent_knowledge_bases(
        self,
        agent_type: str,
        organization_id: UUID,
        project_id: Optional[UUID] = None,
        department_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get all applicable knowledge bases for an agent"""
        return await self.kb_service.get_applicable_knowledge_bases(
            organization_id=organization_id,
            project_id=project_id,
            department_id=department_id,
            agent_type=agent_type
        )
    
    async def load_agent_vector_stores(
        self,
        agent_type: str,
        organization_id: UUID,
        project_id: Optional[UUID] = None,
        department_id: Optional[UUID] = None
    ) -> Optional[FAISS]:
        """Load and merge all applicable vector stores for an agent"""
        try:
            # Get applicable knowledge bases
            kb_list = await self.get_agent_knowledge_bases(
                agent_type=agent_type,
                organization_id=organization_id,
                project_id=project_id,
                department_id=department_id
            )
            
            if not kb_list:
                logger.warning(f"No knowledge bases found for agent {agent_type}")
                return None
            
            # Collect all embeddings
            all_texts = []
            all_embeddings = []
            all_metadatas = []
            
            for kb in kb_list:
                kb_id = kb['id']
                
                # Check if we have cached vector store
                cache_key = str(kb_id)
                if cache_key in self._vector_stores:
                    logger.info(f"Using cached vector store for {kb_id}")
                    cached_store = self._vector_stores[cache_key]
                    # Extract texts and embeddings from cached store
                    # This is a simplified approach - in production you'd want proper extraction
                    continue
                
                # Load embeddings from database
                response = self.supabase.table("knowledge_base_embeddings").select(
                    "chunk_text, embedding_vector, metadata"
                ).eq("knowledge_base_id", str(kb_id)).execute()
                
                if response.data:
                    for doc in response.data:
                        all_texts.append(doc["chunk_text"])
                        all_embeddings.append(doc["embedding_vector"])
                        all_metadatas.append({
                            **doc.get("metadata", {}),
                            "knowledge_base_id": str(kb_id),
                            "knowledge_base_name": kb['name'],
                            "scope_level": kb.get('scope_level', 'unknown')
                        })
            
            if not all_texts:
                logger.warning(f"No embeddings found for agent {agent_type}")
                return None
            
            # Create merged FAISS index
            embeddings_array = np.array(all_embeddings)
            vector_store = FAISS.from_embeddings(
                text_embeddings=list(zip(all_texts, embeddings_array.tolist())),
                embedding=self._embeddings,
                metadatas=all_metadatas
            )
            
            # Cache the merged store
            cache_key = f"{agent_type}_{organization_id}_{project_id}_{department_id}"
            self._vector_stores[cache_key] = vector_store
            
            logger.info(
                f"Loaded {len(all_texts)} documents for agent {agent_type} "
                f"from {len(kb_list)} knowledge bases"
            )
            
            return vector_store
        except Exception as e:
            logger.error(f"Error loading vector stores for agent {agent_type}: {e}")
            return None
    
    async def search_agent_knowledge(
        self,
        agent_type: str,
        query: str,
        organization_id: UUID,
        project_id: Optional[UUID] = None,
        department_id: Optional[UUID] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search knowledge bases for an agent"""
        try:
            # Get or load vector store
            vector_store = await self.load_agent_vector_stores(
                agent_type=agent_type,
                organization_id=organization_id,
                project_id=project_id,
                department_id=department_id
            )
            
            if not vector_store:
                return []
            
            # Search
            docs = vector_store.similarity_search_with_score(query, k=top_k)
            
            results = []
            for doc, score in docs:
                results.append({
                    "content": doc.page_content,
                    "score": float(score),
                    "metadata": doc.metadata
                })
            
            return results
        except Exception as e:
            logger.error(f"Error searching knowledge for agent {agent_type}: {e}")
            return []
    
    def clear_cache(self, agent_type: Optional[str] = None):
        """Clear cached vector stores"""
        if agent_type:
            # Clear specific agent caches
            keys_to_remove = [k for k in self._vector_stores.keys() if k.startswith(agent_type)]
            for key in keys_to_remove:
                del self._vector_stores[key]
            logger.info(f"Cleared cache for agent {agent_type}")
        else:
            # Clear all caches
            self._vector_stores.clear()
            logger.info("Cleared all vector store caches")
    
    def get_embeddings(self) -> OpenAIEmbeddings:
        """Get the shared embeddings instance"""
        if self._embeddings is None:
            raise RuntimeError("Knowledge base not initialized. Call initialize() first.")
        return self._embeddings

# Global instance
enhanced_kb_manager = EnhancedKnowledgeBaseManager()
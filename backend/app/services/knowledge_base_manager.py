"""
Shared Knowledge Base Manager
Manages a single instance of the knowledge base embeddings to be shared across all agents
"""
import os
from typing import Optional
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import logging

logger = logging.getLogger(__name__)


class KnowledgeBaseManager:
    """Singleton manager for shared knowledge base embeddings"""
    
    _instance: Optional['KnowledgeBaseManager'] = None
    _vector_store: Optional[FAISS] = None
    _embeddings: Optional[OpenAIEmbeddings] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def initialize(self, openai_api_key: str, knowledge_base_path: str = "knowledge/20250607_7Cycles of Life_Ebook.pdf"):
        """Initialize the shared knowledge base embeddings"""
        if self._vector_store is not None:
            logger.info("Knowledge base already initialized, skipping...")
            return
            
        logger.info("Initializing shared knowledge base embeddings...")
        
        # Initialize embeddings
        self._embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        
        # Check if knowledge base file exists
        if not os.path.exists(knowledge_base_path):
            logger.error(f"Knowledge base file not found: {knowledge_base_path}")
            raise FileNotFoundError(f"Knowledge base file not found: {knowledge_base_path}")
        
        # Load and process the PDF
        loader = PyPDFLoader(knowledge_base_path)
        documents = loader.load()
        
        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        texts = text_splitter.split_documents(documents)
        
        # Create vector store ONCE
        self._vector_store = FAISS.from_documents(texts, self._embeddings)
        
        logger.info(f"Successfully loaded {len(texts)} document sections into shared vector store")
    
    def get_vector_store(self) -> FAISS:
        """Get the shared vector store"""
        if self._vector_store is None:
            raise RuntimeError("Knowledge base not initialized. Call initialize() first.")
        return self._vector_store
    
    def get_embeddings(self) -> OpenAIEmbeddings:
        """Get the shared embeddings instance"""
        if self._embeddings is None:
            raise RuntimeError("Knowledge base not initialized. Call initialize() first.")
        return self._embeddings
    
    def is_initialized(self) -> bool:
        """Check if the knowledge base is initialized"""
        return self._vector_store is not None


# Global instance
knowledge_base_manager = KnowledgeBaseManager()
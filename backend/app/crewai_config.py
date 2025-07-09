"""
CrewAI Configuration Module
Handles CrewAI setup, memory configuration, vector stores, etc.
"""

import os
from typing import Dict, Any
from crewai import Crew
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# Base configuration paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(BASE_DIR, "app", "agents", "config")
KNOWLEDGE_DIR = os.path.join(BASE_DIR, "knowledge")

# CrewAI settings
CREW_CONFIG = {
    "verbose": True,
    "memory": True,
    "max_iter": 3,
    "max_execution_time": 300,
}

# Vector store configuration
VECTOR_STORE_CONFIG = {
    "chunk_size": 1000,
    "chunk_overlap": 200,
}

# Model configurations
DEFAULT_LLM_MODEL = "gpt-4o-mini"
DEFAULT_EMBEDDING_MODEL = "text-embedding-ada-002"

def get_embeddings(api_key: str):
    """Get OpenAI embeddings instance"""
    return OpenAIEmbeddings(openai_api_key=api_key)

def initialize_vector_store(embeddings):
    """Initialize FAISS vector store"""
    # This can be expanded to load from persistent storage
    return None

# Crew templates configuration
CREW_TEMPLATES = {
    "content_generation": {
        "name": "Content Generation Crew",
        "description": "Crew for generating various types of content"
    },
    "instagram_analysis": {
        "name": "Instagram Analysis Crew", 
        "description": "Crew for analyzing Instagram content and trends"
    },
    "affirmations": {
        "name": "Affirmations Generation Crew",
        "description": "Crew for generating 7 Cycles affirmations"
    }
}
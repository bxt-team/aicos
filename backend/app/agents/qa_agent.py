from crewai import Agent, Task, Crew
from crewai.llm import LLM
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import os
from typing import List, Dict, Any
import json
from app.agents.crews.base_crew import BaseCrew
from app.services.knowledge_base_manager import knowledge_base_manager

class QAAgent(BaseCrew):
    def __init__(self, openai_api_key: str):
        super().__init__()
        self.openai_api_key = openai_api_key
        # Use shared embeddings and vector store
        self.embeddings = knowledge_base_manager.get_embeddings()
        self.vector_store = knowledge_base_manager.get_vector_store()
        self.llm = LLM(model="gpt-4o-mini", api_key=openai_api_key)
        
        # Create the Q&A agent from YAML config
        self.qa_agent = self.create_agent("qa_agent", llm=self.llm)
    
    
    def _get_relevant_context(self, question: str, k: int = 5) -> str:
        """Retrieve relevant context for the question"""
        if not self.vector_store:
            return "Wissensdatenbank nicht verfügbar"
        
        try:
            # Retrieve relevant documents
            docs = self.vector_store.similarity_search(question, k=k)
            
            # Combine context
            context = "\n\n".join([doc.page_content for doc in docs])
            return context
            
        except Exception as e:
            print(f"Fehler beim Abrufen des Kontexts: {e}")
            return "Fehler beim Abrufen des Kontexts"
    
    def answer_question(self, question: str) -> Dict[str, Any]:
        """Answer a question using the knowledge base"""
        try:
            # Get relevant context
            context = self._get_relevant_context(question)
            
            # Create task from YAML config
            task = self.create_task(
                "answer_question_task",
                self.qa_agent,
                question=question,
                context=context
            )
            
            # Create and execute crew
            crew = self.create_crew(
                "qa_crew",
                agents=[self.qa_agent],
                tasks=[task]
            )
            
            result = crew.kickoff()
            
            return {
                "success": True,
                "answer": str(result),
                "context_used": context[:500] + "..." if len(context) > 500 else context
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "answer": "Entschuldigung, beim Verarbeiten Ihrer Frage ist ein Fehler aufgetreten."
            }
    
    def get_knowledge_overview(self) -> Dict[str, Any]:
        """Get an overview of the knowledge base"""
        try:
            if not self.vector_store:
                return {"success": False, "error": "Wissensdatenbank nicht verfügbar"}
            
            # Get sample content to understand structure
            sample_docs = self.vector_store.similarity_search("7 cycles", k=3)
            sample_content = chr(10).join([doc.page_content for doc in sample_docs])
            
            # Create task from YAML config
            task = self.create_task(
                "knowledge_overview_task",
                self.qa_agent,
                sample_content=sample_content
            )
            
            # Create and execute crew
            crew = self.create_crew(
                "qa_crew",
                agents=[self.qa_agent],
                tasks=[task]
            )
            
            result = crew.kickoff()
            
            return {
                "success": True,
                "overview": str(result)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Check if the Q&A agent is properly initialized"""
        try:
            is_ready = self.vector_store is not None
            documents_loaded = False
            index_size = 0
            
            if self.vector_store:
                # Get vector store statistics without executing searches
                try:
                    # Check if FAISS index exists and has vectors
                    if hasattr(self.vector_store, 'index') and hasattr(self.vector_store.index, 'ntotal'):
                        index_size = self.vector_store.index.ntotal
                        documents_loaded = index_size > 0
                    else:
                        # Fallback: check if docstore has documents
                        if hasattr(self.vector_store, 'docstore') and hasattr(self.vector_store.docstore, '_dict'):
                            documents_loaded = len(self.vector_store.docstore._dict) > 0
                except:
                    documents_loaded = False
                    index_size = 0
            
            return {
                "is_ready": is_ready,
                "documents_loaded": documents_loaded,
                "index_size": index_size,
                "message": "Q&A agent is ready" if is_ready else "Q&A agent not initialized properly"
            }
            
        except Exception as e:
            return {
                "is_ready": False,
                "documents_loaded": False,
                "index_size": 0,
                "message": f"Health check failed: {str(e)}"
            }
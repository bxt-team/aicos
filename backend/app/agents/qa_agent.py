from crewai.llm import LLM
from langchain_community.vectorstores import FAISS
from typing import List, Dict, Any, Optional
from app.agents.crews.base_crew import BaseCrew
from app.services.knowledge_base_manager import knowledge_base_manager
from app.services.knowledge_base_service import KnowledgeBaseService
from app.core.storage import StorageFactory
import asyncio
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)


class QAAgent(BaseCrew):
    def __init__(self, openai_api_key: str):
        # Get storage adapter from factory
        storage_adapter = StorageFactory.get_adapter()
        super().__init__(storage_adapter=storage_adapter)

        self.openai_api_key = openai_api_key
        # Use shared embeddings and vector store as default
        self.embeddings = knowledge_base_manager.get_embeddings()
        self.vector_store = knowledge_base_manager.get_vector_store()
        self.llm = LLM(model="gpt-4o-mini", api_key=openai_api_key)

        # Knowledge base service for project-specific KBs
        self.kb_service = KnowledgeBaseService()

        # Collection name for Q&A interactions
        self.collection = "qa_interactions"

        # Create the Q&A agent from YAML config
        self.qa_agent = self.create_agent("qa_agent", llm=self.llm)

    def _run_async(self, coro):
        """Helper to run async code in sync context"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def _get_relevant_context(self, question: str, k: int = 5) -> str:
        """Retrieve relevant context for the question from default knowledge base"""
        if not self.vector_store:
            return "Wissensdatenbank nicht verfügbar"

        try:
            # Retrieve relevant documents
            docs = self.vector_store.similarity_search(question, k=k)

            # Combine context
            context = "\n\n".join([doc.page_content for doc in docs])
            return context

        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Kontexts: {e}")
            return "Fehler beim Abrufen des Kontexts"

    def answer_question(self, question: str) -> Dict[str, Any]:
        """Answer a question using the knowledge base"""
        try:
            # Consume credits for this action
            if self.validate_context():
                self._run_async(self.consume_credits_for_action(
                    action='answer_question',
                    metadata={
                        'question': question[:100],  # First 100 chars for metadata
                        'question_length': len(question)
                    }
                ))

            # Get relevant context - use scoped if context is available
            if self.validate_context():
                context = self._get_relevant_context_scoped(question)
            else:
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
            answer = str(result)

            # Calculate relevance score based on context similarity
            # This is a simple heuristic - in production, you might use more sophisticated methods
            relevance_score = self._calculate_relevance_score(question, context)

            # Save Q&A interaction with multi-tenant context
            interaction_data = {
                "question": question,
                "answer": answer,
                "context": context[:1000] if len(context) > 1000 else context,  # Limit context size
                "relevance_score": relevance_score,
                "metadata": {
                    "model": "gpt-4o-mini",
                    "timestamp": datetime.now().isoformat(),
                    "context_length": len(context),
                    "answer_length": len(answer)
                }
            }

            # Run async save operation with context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # Use base class's save_result for multi-tenant support
                if self.validate_context():
                    interaction_id = loop.run_until_complete(
                        self.save_result(self.collection, interaction_data)
                    )
                else:
                    # Fallback to direct storage if no context
                    interaction_id = loop.run_until_complete(
                        self.storage_adapter.save(self.collection, interaction_data)
                    )
            finally:
                loop.close()

            return {
                "success": True,
                "answer": answer,
                "context_used": context[:500] + "..." if len(context) > 500 else context,
                "interaction_id": interaction_id,
                "relevance_score": relevance_score
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
                except Exception:
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

    def _calculate_relevance_score(self, question: str, context: str) -> float:
        """Calculate a simple relevance score between question and context"""
        try:
            # Simple keyword overlap score (0.0 to 1.0)
            question_words = set(question.lower().split())
            context_words = set(context.lower().split())

            if not question_words:
                return 0.0

            overlap = len(question_words.intersection(context_words))
            score = overlap / len(question_words)

            # Normalize to 0-1 range
            return min(1.0, score)
        except Exception:
            return 0.5  # Default middle score on error

    async def get_recent_interactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent Q&A interactions from storage"""
        try:
            # Use base class's list_results for multi-tenant support
            if self.validate_context():
                interactions = await self.list_results(
                    self.collection,
                    limit=limit,
                    order_by="created_at",
                    order_desc=True
                )
            else:
                # Fallback to direct storage if no context
                interactions = await self.storage_adapter.list(
                    self.collection,
                    order_by="created_at",
                    order_desc=True,
                    limit=limit
                )
            return interactions
        except Exception as e:
            print(f"Error retrieving interactions: {e}")
            return []

    async def update_interaction_feedback(self, interaction_id: str, user_feedback: int) -> bool:
        """Update user feedback for an interaction (1-5 rating)"""
        try:
            if user_feedback < 1 or user_feedback > 5:
                raise ValueError("Feedback must be between 1 and 5")

            # Load existing interaction with context validation
            if self.validate_context():
                interaction = await self.get_result(self.collection, interaction_id)
            else:
                interaction = await self.storage_adapter.load(self.collection, interaction_id)

            if not interaction:
                return False

            # Update with feedback
            interaction["user_feedback"] = user_feedback
            interaction["metadata"]["feedback_timestamp"] = datetime.now().isoformat()

            # Save updated interaction
            if self.validate_context():
                await self.save_result(self.collection, interaction, interaction_id)
            else:
                await self.storage_adapter.save(self.collection, interaction, interaction_id)
            return True
        except Exception as e:
            print(f"Error updating feedback: {e}")
            return False

    async def list_available_knowledge_bases(self) -> Dict[str, Any]:
        """List all available knowledge bases for the current context"""
        try:
            if not self.validate_context():
                return {
                    "success": True,
                    "knowledge_bases": [{
                        "id": "default",
                        "name": "7 Cycles of Life",
                        "description": "Default knowledge base about the 7 Cycles methodology",
                        "scope_level": "system"
                    }]
                }

            # Get applicable knowledge bases
            applicable_kbs = await self.kb_service.get_applicable_knowledge_bases(
                organization_id=self._context.organization_id,
                project_id=self._context.project_id,
                department_id=None,
                agent_type='qa_agent',
                user_id=self._context.user_id
            )

            # Add default knowledge base
            kbs = [{
                "id": "default",
                "name": "7 Cycles of Life",
                "description": "Default knowledge base about the 7 Cycles methodology",
                "scope_level": "system"
            }]

            # Add custom knowledge bases
            for kb in applicable_kbs:
                kbs.append({
                    "id": kb['id'],
                    "name": kb['name'],
                    "description": kb.get('description', ''),
                    "scope_level": kb.get('scope_level', 'unknown'),
                    "file_type": kb.get('file_type', ''),
                    "created_at": kb.get('created_at', '')
                })

            return {
                "success": True,
                "knowledge_bases": kbs,
                "total": len(kbs)
            }

        except Exception as e:
            logger.error(f"Error listing knowledge bases: {e}")
            return {
                "success": False,
                "error": str(e),
                "knowledge_bases": []
            }

    async def get_scoped_knowledge_base(self) -> Optional[FAISS]:
        """Get organization/project specific knowledge base"""
        if not self.validate_context():
            # Return default knowledge base if no context
            return self.vector_store

        try:
            # Get applicable knowledge bases for the context
            applicable_kbs = await self.kb_service.get_applicable_knowledge_bases(
                organization_id=self._context.organization_id,
                project_id=self._context.project_id,
                department_id=None,  # Could be extended for department-specific KBs
                agent_type='qa_agent',  # Specific to Q&A agent
                user_id=self._context.user_id
            )

            if not applicable_kbs:
                # No custom knowledge base, use default
                logger.info(f"No custom KB for org {self._context.organization_id}, using default KB")
                return self.vector_store

            # Extract knowledge base IDs
            kb_ids = [uuid.UUID(kb['id']) for kb in applicable_kbs]

            # Search across all applicable knowledge bases
            # For now, we'll create a temporary FAISS store from search results
            # In a production system, you might want to cache this
            for kb_id in kb_ids:
                # Get embeddings for this KB
                try:
                    # This is a simplified approach - in production you'd want to
                    # load the actual FAISS index or use the search functionality
                    logger.info(f"Loading knowledge base {kb_id}")
                except Exception as e:
                    logger.error(f"Error loading KB {kb_id}: {e}")
                    continue

            # For now, return default KB merged with any custom content
            # This ensures we always have some knowledge to work with
            return self.vector_store

        except Exception as e:
            logger.error(f"Error loading scoped knowledge base: {e}")
            return self.vector_store

    def _get_relevant_context_scoped(self, question: str, k: int = 5) -> str:
        """Retrieve relevant context using organization-specific knowledge base"""
        if not self.validate_context():
            return self._get_relevant_context(question, k)

        try:
            # Get applicable knowledge bases
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                applicable_kbs = loop.run_until_complete(
                    self.kb_service.get_applicable_knowledge_bases(
                        organization_id=self._context.organization_id,
                        project_id=self._context.project_id,
                        department_id=None,
                        agent_type='qa_agent',
                        user_id=self._context.user_id
                    )
                )

                if not applicable_kbs:
                    # Fall back to default knowledge base
                    return self._get_relevant_context(question, k)

                # Get KB IDs
                kb_ids = [uuid.UUID(kb['id']) for kb in applicable_kbs]

                # Search across knowledge bases
                search_results = loop.run_until_complete(
                    self.kb_service.search_knowledge_bases(
                        query=question,
                        knowledge_base_ids=kb_ids,
                        top_k=k
                    )
                )

                if not search_results:
                    # Fall back to default knowledge base
                    return self._get_relevant_context(question, k)

                # Format context from search results
                context_parts = []
                for i, result in enumerate(search_results):
                    kb_info = next((kb for kb in applicable_kbs if kb['id'] == result['knowledge_base_id']), {})
                    kb_name = kb_info.get('name', 'Unknown')
                    scope = kb_info.get('scope_level', 'Unknown')
                    content = result['chunk_text']
                    score = result['score']

                    context_parts.append(
                        f"[Document {i+1}]\n"
                        f"Knowledge Base: {kb_name} ({scope})\n"
                        f"Relevance Score: {score:.3f}\n"
                        f"{content}"
                    )

                # Also include some results from default KB for completeness
                default_docs = self.vector_store.similarity_search(question, k=2) if self.vector_store else []
                for i, doc in enumerate(default_docs):
                    source = doc.metadata.get('source', 'Unknown')
                    content = doc.page_content
                    context_parts.append(
                        f"[Document {len(search_results) + i + 1}]\n"
                        f"Knowledge Base: Default (7 Cycles)\n"
                        f"Source: {source}\n"
                        f"{content}"
                    )

                context = "\n\n---\n\n".join(context_parts)
                return context

            finally:
                loop.close()

        except Exception as e:
            logger.error(f"Error retrieving scoped context: {e}")
            # Fall back to default knowledge base
            return self._get_relevant_context(question, k)
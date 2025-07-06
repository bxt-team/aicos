from crewai import Agent, Task, Crew
from crewai.agent import Agent
from crewai.llm import LLM
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import os
from typing import List, Dict, Any
import json

class QAAgent:
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.vector_store = None
        self.llm = LLM(model="gpt-4o-mini", api_key=openai_api_key)
        
        # Initialize knowledge base
        self._load_knowledge_base()
        
        # Create the Q&A agent
        self.qa_agent = Agent(
            role="7 Lebenszyklen Wissensexperte",
            goal="Beantworte Fragen über das 7 Lebenszyklen-Konzept basierend auf der bereitgestellten Wissensdatenbank",
            backstory="""Du bist ein Experte für die 7 Lebenszyklen-Philosophie und -Methodik. 
            Du verfügst über tiefgreifendes Wissen darüber, wie das Leben in zyklischen Mustern funktioniert 
            und wie das Verständnis dieser Zyklen Menschen helfen kann, ihre Energie, Kreativität und ihren Erfolg zu optimieren. 
            Du gibst klare, aufschlussreiche Antworten basierend auf der Wissensdatenbank. WICHTIG: Antworte IMMER auf Deutsch!""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
    
    def _load_knowledge_base(self):
        """Load and process the PDF knowledge base"""
        try:
            pdf_path = os.path.join(os.path.dirname(__file__), "../../knowledge_files/20250607_7Cycles of Life_Ebook.pdf")
            
            # Load PDF
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            
            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )
            
            texts = text_splitter.split_documents(documents)
            
            # Create vector store
            self.vector_store = FAISS.from_documents(texts, self.embeddings)
            
            print(f"Erfolgreich {len(texts)} Dokumentenabschnitte in den Vektorspeicher geladen")
            
        except Exception as e:
            print(f"Fehler beim Laden der Wissensdatenbank: {e}")
            self.vector_store = None
    
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
            
            # Create task
            task = Task(
                description=f"""
                Beantworte die folgende Frage über die 7 Lebenszyklen basierend auf dem bereitgestellten Kontext.
                
                Frage: {question}
                
                Kontext aus der Wissensdatenbank:
                {context}
                
                Anweisungen:
                - Gib eine klare, umfassende Antwort basierend auf dem Kontext
                - Wenn die Frage anhand des Kontexts nicht beantwortet werden kann, sage das deutlich
                - Beziehe dich spezifisch auf das 7-Zyklen-Konzept, wenn relevant
                - Halte die Antwort fokussiert und praktisch
                - Formatiere die Antwort klar und gut lesbar
                - WICHTIG: Antworte IMMER auf Deutsch, auch wenn die Frage auf Englisch gestellt wurde
                """,
                expected_output="Eine klare, gut strukturierte Antwort auf die Frage basierend auf der 7 Lebenszyklen Wissensdatenbank",
                agent=self.qa_agent
            )
            
            # Execute task
            crew = Crew(
                agents=[self.qa_agent],
                tasks=[task],
                verbose=True
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
            
            task = Task(
                description=f"""
                Erstelle eine umfassende Übersicht über die 7 Lebenszyklen Wissensdatenbank.
                
                Beispielinhalt:
                {chr(10).join([doc.page_content for doc in sample_docs])}
                
                Anweisungen:
                - Fasse die Hauptkonzepte und Prinzipien zusammen
                - Liste die verschiedenen behandelten Zyklen auf
                - Erkläre, wie dieses Wissen angewendet werden kann
                - Halte es prägnant aber informativ
                - WICHTIG: Erstelle die Übersicht auf Deutsch
                """,
                expected_output="Eine umfassende Übersicht über die 7 Lebenszyklen Wissensdatenbank",
                agent=self.qa_agent
            )
            
            crew = Crew(
                agents=[self.qa_agent],
                tasks=[task],
                verbose=True
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
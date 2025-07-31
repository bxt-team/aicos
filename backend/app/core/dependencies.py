"""Application dependencies and agent initialization"""

from typing import Optional
from app.services.flows.content_generation_wrapper import ContentGenerationWrapper
from app.services.tools.image_generator import ImageGenerator
from app.agents.qa_agent import QAAgent
from app.agents.affirmations_agent import AffirmationsAgent
from app.agents.write_hashtag_research_agent import WriteHashtagResearchAgent
from app.agents.instagram_ai_prompt_agent import InstagramAIPromptAgent
from app.agents.instagram_poster_agent import InstagramPosterAgent
from app.agents.instagram_analyzer_agent import InstagramAnalyzerAgent
from app.agents.content_workflow_agent import ContentWorkflowAgent
from app.agents.post_composition_agent import PostCompositionAgent
from app.agents.video_generation_agent import VideoGenerationAgent
from app.agents.background_video_agent import BackgroundVideoAgent
from app.agents.app_testing_agent import AppTestingAgent
from app.agents.voice_over_agent import VoiceOverAgent
from app.agents.app_store_analyst import AppStoreAnalystAgent
from app.agents.play_store_analyst import PlayStoreAnalystAgent
from app.agents.meta_ads_analyst import MetaAdsAnalystAgent
from app.agents.google_analytics_expert import GoogleAnalyticsExpertAgent
from app.agents.threads_analysis_agent import ThreadsAnalysisAgent
from app.agents.content_strategy_agent import ContentStrategyAgent
from app.agents.post_generator_agent import PostGeneratorAgent
from app.agents.approval_agent import ApprovalAgent
from app.agents.scheduler_agent import SchedulerAgent
from app.agents.x_analysis_agent import XAnalysisAgent
from app.agents.x_content_strategy_agent import XContentStrategyAgent
from app.agents.x_post_generator_agent import XPostGeneratorAgent
from app.agents.x_approval_agent import XApprovalAgent
from app.agents.x_scheduler_agent import XSchedulerAgent
from app.agents.crews.organization_goal_crew import OrganizationGoalCrew
from app.agents.crews.department_structure_crew import DepartmentStructureCrew
from app.agents.crews.project_description_crew import ProjectDescriptionCrew
from app.agents.crews.project_task_crew import ProjectTaskCrew
from app.services.supabase_client import SupabaseClient
from app.services.knowledge_base_manager import knowledge_base_manager
from app.services.knowledge_base_service import KnowledgeBaseService
from .config import settings
import logging
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# Global Supabase client instance
_supabase_client: Optional[Client] = None

def get_supabase_client() -> Client:
    """Get or create Supabase client instance"""
    global _supabase_client
    if _supabase_client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
            raise ValueError("Supabase URL and service key must be set in environment variables")
        
        # Create client without options to get default behavior
        _supabase_client = create_client(
            settings.SUPABASE_URL, 
            settings.SUPABASE_SERVICE_KEY
        )
        
        # Log client attributes for debugging
        logger.info(f"Supabase client created successfully")
        
        # Verify that table method exists
        if not hasattr(_supabase_client, 'table'):
            logger.error(f"Supabase client missing table method. Available methods: {[attr for attr in dir(_supabase_client) if not attr.startswith('_')]}")
            raise ValueError("Supabase client is not properly initialized - missing table method")
        
    return _supabase_client

# Global agent instances
image_generator: Optional[ImageGenerator] = None
qa_agent: Optional[QAAgent] = None
affirmations_agent: Optional[AffirmationsAgent] = None
write_hashtag_agent: Optional[WriteHashtagResearchAgent] = None
instagram_ai_prompt_agent: Optional[InstagramAIPromptAgent] = None
instagram_poster_agent: Optional[InstagramPosterAgent] = None
instagram_analyzer_agent: Optional[InstagramAnalyzerAgent] = None
content_wrapper: Optional[ContentGenerationWrapper] = None
workflow_agent: Optional[ContentWorkflowAgent] = None
post_composition_agent: Optional[PostCompositionAgent] = None
video_generation_agent: Optional[VideoGenerationAgent] = None
background_video_agent: Optional[BackgroundVideoAgent] = None
app_testing_agent: Optional[AppTestingAgent] = None
voice_over_agent: Optional[VoiceOverAgent] = None
app_store_analyst_agent: Optional[AppStoreAnalystAgent] = None
play_store_analyst_agent: Optional[PlayStoreAnalystAgent] = None
meta_ads_analyst_agent: Optional[MetaAdsAnalystAgent] = None
google_analytics_expert_agent: Optional[GoogleAnalyticsExpertAgent] = None
threads_analysis_agent: Optional[ThreadsAnalysisAgent] = None
content_strategy_agent: Optional[ContentStrategyAgent] = None
post_generator_agent: Optional[PostGeneratorAgent] = None
approval_agent: Optional[ApprovalAgent] = None
scheduler_agent: Optional[SchedulerAgent] = None
x_analysis_agent: Optional[XAnalysisAgent] = None
x_content_strategy_agent: Optional[XContentStrategyAgent] = None
x_post_generator_agent: Optional[XPostGeneratorAgent] = None
x_approval_agent: Optional[XApprovalAgent] = None
x_scheduler_agent: Optional[XSchedulerAgent] = None
organization_goal_crew: Optional[OrganizationGoalCrew] = None
department_structure_crew: Optional[DepartmentStructureCrew] = None
project_description_crew: Optional[ProjectDescriptionCrew] = None
project_task_crew: Optional[ProjectTaskCrew] = None
supabase_client: Optional[SupabaseClient] = None

# Storage
content_storage = {}

def initialize_agents():
    """Initialize all agent instances"""
    global image_generator, qa_agent, affirmations_agent, write_hashtag_agent
    global instagram_ai_prompt_agent, instagram_poster_agent, instagram_analyzer_agent
    global content_wrapper, workflow_agent, post_composition_agent
    global video_generation_agent, instagram_reel_agent, app_testing_agent, voice_over_agent
    global app_store_analyst_agent, play_store_analyst_agent, meta_ads_analyst_agent, google_analytics_expert_agent
    global threads_analysis_agent, content_strategy_agent, post_generator_agent, approval_agent, scheduler_agent
    global x_analysis_agent, x_content_strategy_agent, x_post_generator_agent, x_approval_agent, x_scheduler_agent, supabase_client
    global background_video_agent, organization_goal_crew, department_structure_crew, project_description_crew, project_task_crew
    
    logger.info(f"[INIT] OPENAI_API_KEY present: {bool(settings.OPENAI_API_KEY)}")
    logger.info(f"[INIT] OPENAI_API_KEY length: {len(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else 0}")
    
    # Initialize Supabase client FIRST (before any agents that depend on it)
    logger.info("[SUPABASE_CLIENT] Initializing...")
    try:
        supabase_client = SupabaseClient()
        # Add mock activities if running without real Supabase
        if not supabase_client.client:
            supabase_client.add_mock_activities()
        logger.info("[SUPABASE_CLIENT] Initialized successfully")
    except Exception as e:
        logger.error(f"[SUPABASE_CLIENT] Failed to initialize: {str(e)}")
        supabase_client = None
    
    if settings.OPENAI_API_KEY:
        # Initialize shared knowledge base first
        logger.info("[KNOWLEDGE_BASE] Initializing shared knowledge base...")
        try:
            knowledge_base_manager.initialize(settings.OPENAI_API_KEY)
            logger.info("[KNOWLEDGE_BASE] Shared knowledge base initialized successfully")
        except Exception as e:
            logger.error(f"[KNOWLEDGE_BASE] Failed to initialize: {str(e)}")
            raise
        logger.info("[IMAGE_GENERATOR] Initializing...")
        image_generator = ImageGenerator(settings.OPENAI_API_KEY)
        logger.info("[IMAGE_GENERATOR] Initialized successfully")
        
        logger.info("[QA_AGENT] Initializing...")
        qa_agent = QAAgent(settings.OPENAI_API_KEY)
        logger.info("[QA_AGENT] Initialized successfully")
        try:
            logger.info("[AFFIRMATIONS_AGENT] Attempting to initialize...")
            affirmations_agent = AffirmationsAgent(settings.OPENAI_API_KEY)
            logger.info(f"[AFFIRMATIONS_AGENT] Initialized successfully: {affirmations_agent is not None}")
        except Exception as e:
            logger.error(f"[AFFIRMATIONS_AGENT] Failed to initialize: {str(e)}")
            logger.error(f"[AFFIRMATIONS_AGENT] Full error details: ", exc_info=True)
            affirmations_agent = None
        logger.info("[WRITE_HASHTAG_AGENT] Initializing...")
        write_hashtag_agent = WriteHashtagResearchAgent(settings.OPENAI_API_KEY)
        logger.info("[WRITE_HASHTAG_AGENT] Initialized successfully")
        
        logger.info("[INSTAGRAM_AI_PROMPT_AGENT] Initializing...")
        instagram_ai_prompt_agent = InstagramAIPromptAgent(settings.OPENAI_API_KEY)
        logger.info("[INSTAGRAM_AI_PROMPT_AGENT] Initialized successfully")
        
        logger.info("[INSTAGRAM_POSTER_AGENT] Initializing...")
        instagram_poster_agent = InstagramPosterAgent(
            settings.OPENAI_API_KEY, 
            settings.INSTAGRAM_ACCESS_TOKEN, 
            settings.INSTAGRAM_BUSINESS_ACCOUNT_ID
        )
        logger.info("[INSTAGRAM_POSTER_AGENT] Initialized successfully")
        
        logger.info("[INSTAGRAM_ANALYZER_AGENT] Initializing...")
        instagram_analyzer_agent = InstagramAnalyzerAgent(settings.OPENAI_API_KEY)
        logger.info("[INSTAGRAM_ANALYZER_AGENT] Initialized successfully")
        
        logger.info("[CONTENT_WRAPPER] Initializing...")
        content_wrapper = ContentGenerationWrapper()
        logger.info("[CONTENT_WRAPPER] Initialized successfully")
        
        # Initialize new agents
        logger.info("[WORKFLOW_AGENT] Initializing...")
        workflow_agent = ContentWorkflowAgent(
            settings.OPENAI_API_KEY, 
            settings.PEXELS_API_KEY, 
            settings.INSTAGRAM_ACCESS_TOKEN
        )
        logger.info("[WORKFLOW_AGENT] Initialized successfully")
        
        logger.info("[POST_COMPOSITION_AGENT] Initializing...")
        post_composition_agent = PostCompositionAgent(settings.OPENAI_API_KEY)
        logger.info("[POST_COMPOSITION_AGENT] Initialized successfully")
        
        logger.info("[VIDEO_GENERATION_AGENT] Initializing...")
        video_generation_agent = VideoGenerationAgent(settings.OPENAI_API_KEY)
        logger.info("[VIDEO_GENERATION_AGENT] Initialized successfully")
        
        # Initialize Voice Over agent
        logger.info("[VOICE_OVER_AGENT] Initializing...")
        voice_over_agent = VoiceOverAgent(settings.OPENAI_API_KEY, settings.ELEVENLABS_API_KEY)
        logger.info("[VOICE_OVER_AGENT] Initialized successfully")
        
        # Initialize App Testing agent (unified iOS and Android)
        logger.info("[APP_TESTING_AGENT] Initializing...")
        try:
            app_testing_agent = AppTestingAgent()
            logger.info("[APP_TESTING_AGENT] Initialized successfully")
        except Exception as e:
            logger.error(f"[APP_TESTING_AGENT] Failed to initialize: {str(e)}")
            app_testing_agent = None
        
        # Initialize App Store Analyst agent
        logger.info("[APP_STORE_ANALYST] Initializing...")
        try:
            app_store_analyst_agent = AppStoreAnalystAgent()
            logger.info("[APP_STORE_ANALYST] Initialized successfully")
        except Exception as e:
            logger.error(f"[APP_STORE_ANALYST] Failed to initialize: {str(e)}")
            app_store_analyst_agent = None
        
        # Initialize Play Store Analyst agent
        logger.info("[PLAY_STORE_ANALYST] Initializing...")
        try:
            play_store_analyst_agent = PlayStoreAnalystAgent()
            logger.info("[PLAY_STORE_ANALYST] Initialized successfully")
        except Exception as e:
            logger.error(f"[PLAY_STORE_ANALYST] Failed to initialize: {str(e)}")
            play_store_analyst_agent = None
        
        # Initialize Meta Ads Analyst agent
        logger.info("[META_ADS_ANALYST] Initializing...")
        try:
            meta_ads_analyst_agent = MetaAdsAnalystAgent()
            logger.info("[META_ADS_ANALYST] Initialized successfully")
        except Exception as e:
            logger.error(f"[META_ADS_ANALYST] Failed to initialize: {str(e)}")
            meta_ads_analyst_agent = None
        
        # Initialize Google Analytics Expert agent
        logger.info("[GOOGLE_ANALYTICS_EXPERT] Initializing...")
        try:
            google_analytics_expert_agent = GoogleAnalyticsExpertAgent()
            logger.info("[GOOGLE_ANALYTICS_EXPERT] Initialized successfully")
        except Exception as e:
            logger.error(f"[GOOGLE_ANALYTICS_EXPERT] Failed to initialize: {str(e)}")
            google_analytics_expert_agent = None
        
        # Initialize Background Video Agent (after Supabase client)
        logger.info("[BACKGROUND_VIDEO_AGENT] Initializing...")
        background_video_agent = BackgroundVideoAgent(
            settings.OPENAI_API_KEY, 
            settings.KLINGAI_API_KEY,
            settings.KLINGAI_PROVIDER,
            supabase_client
        )
        logger.info("[BACKGROUND_VIDEO_AGENT] Initialized successfully")
        
        # Initialize Threads agents
        logger.info("[THREADS_ANALYSIS_AGENT] Initializing...")
        try:
            threads_analysis_agent = ThreadsAnalysisAgent(settings.OPENAI_API_KEY)
            logger.info("[THREADS_ANALYSIS_AGENT] Initialized successfully")
        except Exception as e:
            logger.error(f"[THREADS_ANALYSIS_AGENT] Failed to initialize: {str(e)}")
            threads_analysis_agent = None
        
        logger.info("[CONTENT_STRATEGY_AGENT] Initializing...")
        try:
            content_strategy_agent = ContentStrategyAgent(settings.OPENAI_API_KEY, supabase_client)
            logger.info("[CONTENT_STRATEGY_AGENT] Initialized successfully")
        except Exception as e:
            logger.error(f"[CONTENT_STRATEGY_AGENT] Failed to initialize: {str(e)}")
            content_strategy_agent = None
        
        logger.info("[POST_GENERATOR_AGENT] Initializing...")
        try:
            post_generator_agent = PostGeneratorAgent(settings.OPENAI_API_KEY, supabase_client)
            logger.info("[POST_GENERATOR_AGENT] Initialized successfully")
        except Exception as e:
            logger.error(f"[POST_GENERATOR_AGENT] Failed to initialize: {str(e)}")
            post_generator_agent = None
        
        logger.info("[APPROVAL_AGENT] Initializing...")
        try:
            approval_agent = ApprovalAgent(settings.OPENAI_API_KEY, supabase_client)
            logger.info("[APPROVAL_AGENT] Initialized successfully")
        except Exception as e:
            logger.error(f"[APPROVAL_AGENT] Failed to initialize: {str(e)}")
            approval_agent = None
        
        logger.info("[SCHEDULER_AGENT] Initializing...")
        try:
            scheduler_agent = SchedulerAgent(settings.OPENAI_API_KEY, supabase_client)
            logger.info("[SCHEDULER_AGENT] Initialized successfully")
        except Exception as e:
            logger.error(f"[SCHEDULER_AGENT] Failed to initialize: {str(e)}")
            scheduler_agent = None
        
        # Initialize X (Twitter) agents
        logger.info("[X_ANALYSIS_AGENT] Initializing...")
        try:
            x_analysis_agent = XAnalysisAgent()
            logger.info("[X_ANALYSIS_AGENT] Initialized successfully")
        except Exception as e:
            logger.error(f"[X_ANALYSIS_AGENT] Failed to initialize: {str(e)}")
            x_analysis_agent = None
        
        logger.info("[X_CONTENT_STRATEGY_AGENT] Initializing...")
        try:
            x_content_strategy_agent = XContentStrategyAgent()
            logger.info("[X_CONTENT_STRATEGY_AGENT] Initialized successfully")
        except Exception as e:
            logger.error(f"[X_CONTENT_STRATEGY_AGENT] Failed to initialize: {str(e)}")
            x_content_strategy_agent = None
        
        logger.info("[X_POST_GENERATOR_AGENT] Initializing...")
        try:
            x_post_generator_agent = XPostGeneratorAgent()
            logger.info("[X_POST_GENERATOR_AGENT] Initialized successfully")
        except Exception as e:
            logger.error(f"[X_POST_GENERATOR_AGENT] Failed to initialize: {str(e)}")
            x_post_generator_agent = None
        
        logger.info("[X_APPROVAL_AGENT] Initializing...")
        try:
            x_approval_agent = XApprovalAgent()
            logger.info("[X_APPROVAL_AGENT] Initialized successfully")
        except Exception as e:
            logger.error(f"[X_APPROVAL_AGENT] Failed to initialize: {str(e)}")
            x_approval_agent = None
        
        logger.info("[X_SCHEDULER_AGENT] Initializing...")
        try:
            x_scheduler_agent = XSchedulerAgent()
            logger.info("[X_SCHEDULER_AGENT] Initialized successfully")
        except Exception as e:
            logger.error(f"[X_SCHEDULER_AGENT] Failed to initialize: {str(e)}")
            x_scheduler_agent = None
        
        # Initialize organizational management agents
        logger.info("[ORGANIZATION_GOAL_CREW] Initializing...")
        try:
            organization_goal_crew = OrganizationGoalCrew()
            logger.info("[ORGANIZATION_GOAL_CREW] Initialized successfully")
        except Exception as e:
            logger.error(f"[ORGANIZATION_GOAL_CREW] Failed to initialize: {str(e)}")
            organization_goal_crew = None
            
        logger.info("[DEPARTMENT_STRUCTURE_CREW] Initializing...")
        try:
            department_structure_crew = DepartmentStructureCrew()
            logger.info("[DEPARTMENT_STRUCTURE_CREW] Initialized successfully")
        except Exception as e:
            logger.error(f"[DEPARTMENT_STRUCTURE_CREW] Failed to initialize: {str(e)}")
            department_structure_crew = None
            
        logger.info("[PROJECT_DESCRIPTION_CREW] Initializing...")
        try:
            project_description_crew = ProjectDescriptionCrew()
            logger.info("[PROJECT_DESCRIPTION_CREW] Initialized successfully")
        except Exception as e:
            logger.error(f"[PROJECT_DESCRIPTION_CREW] Failed to initialize: {str(e)}")
            project_description_crew = None
            
        logger.info("[PROJECT_TASK_CREW] Initializing...")
        try:
            project_task_crew = ProjectTaskCrew()
            logger.info("[PROJECT_TASK_CREW] Initialized successfully")
        except Exception as e:
            logger.error(f"[PROJECT_TASK_CREW] Failed to initialize: {str(e)}")
            project_task_crew = None
    else:
        logger.warning("OpenAI API key not found. Agents not initialized.")

def cleanup_agents():
    """Cleanup agent resources"""
    if app_testing_agent:
        try:
            # Clean up any active tests
            for test in app_testing_agent.list_tests():
                app_testing_agent.cleanup_test(test['id'])
            logger.info("[APP_TESTING_AGENT] Cleaned up successfully")
        except Exception as e:
            logger.error(f"[APP_TESTING_AGENT] Error cleaning up: {e}")

def get_agent(agent_name: str):
    """Get a specific agent instance"""
    agents = {
        'image_generator': image_generator,
        'qa_agent': qa_agent,
        'affirmations_agent': affirmations_agent,
        'write_hashtag_agent': write_hashtag_agent,
        'instagram_ai_prompt_agent': instagram_ai_prompt_agent,
        'instagram_poster_agent': instagram_poster_agent,
        'instagram_analyzer_agent': instagram_analyzer_agent,
        'content_wrapper': content_wrapper,
        'workflow_agent': workflow_agent,
        'post_composition_agent': post_composition_agent,
        'video_generation_agent': video_generation_agent,
        'background_video_agent': background_video_agent,
        'app_testing': app_testing_agent,
        'voice_over_agent': voice_over_agent,
        'app_store_analyst': app_store_analyst_agent,
        'play_store_analyst': play_store_analyst_agent,
        'meta_ads_analyst': meta_ads_analyst_agent,
        'google_analytics_expert': google_analytics_expert_agent,
        'threads_analysis': threads_analysis_agent,
        'content_strategy': content_strategy_agent,
        'post_generator': post_generator_agent,
        'approval': approval_agent,
        'scheduler': scheduler_agent,
        'x_analysis': x_analysis_agent,
        'x_strategy': x_content_strategy_agent,
        'x_generator': x_post_generator_agent,
        'x_approval': x_approval_agent,
        'x_scheduler': x_scheduler_agent,
        'organization_goal': organization_goal_crew,
        'department_structure': department_structure_crew,
        'project_description': project_description_crew,
        'project_task': project_task_crew,
    }
    return agents.get(agent_name)

# Dependency getters for Threads agents
def get_threads_analysis_agent():
    """Get ThreadsAnalysisAgent instance"""
    if not threads_analysis_agent:
        raise RuntimeError("ThreadsAnalysisAgent not initialized")
    return threads_analysis_agent

def get_content_strategy_agent():
    """Get ContentStrategyAgent instance"""
    if not content_strategy_agent:
        raise RuntimeError("ContentStrategyAgent not initialized")
    return content_strategy_agent

def get_post_generator_agent():
    """Get PostGeneratorAgent instance"""
    if not post_generator_agent:
        raise RuntimeError("PostGeneratorAgent not initialized")
    return post_generator_agent

def get_approval_agent():
    """Get ApprovalAgent instance"""
    if not approval_agent:
        raise RuntimeError("ApprovalAgent not initialized")
    return approval_agent

def get_scheduler_agent():
    """Get SchedulerAgent instance"""
    if not scheduler_agent:
        raise RuntimeError("SchedulerAgent not initialized")
    return scheduler_agent

def get_supabase_client():
    """Get SupabaseClient instance"""
    if not supabase_client:
        raise RuntimeError("SupabaseClient not initialized")
    return supabase_client

def get_knowledge_base_service():
    """Get KnowledgeBaseService instance"""
    return KnowledgeBaseService()

# Dependency getters for organizational management agents
def get_organization_goal_crew():
    """Get OrganizationGoalCrew instance"""
    if not organization_goal_crew:
        raise RuntimeError("OrganizationGoalCrew not initialized")
    return organization_goal_crew

def get_department_structure_crew():
    """Get DepartmentStructureCrew instance"""
    if not department_structure_crew:
        raise RuntimeError("DepartmentStructureCrew not initialized")
    return department_structure_crew

def get_project_description_crew():
    """Get ProjectDescriptionCrew instance"""
    if not project_description_crew:
        raise RuntimeError("ProjectDescriptionCrew not initialized")
    return project_description_crew

def get_project_task_crew():
    """Get ProjectTaskCrew instance"""
    if not project_task_crew:
        raise RuntimeError("ProjectTaskCrew not initialized")
    return project_task_crew
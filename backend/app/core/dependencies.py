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
from app.agents.instagram_reel_agent import InstagramReelAgent
from app.agents.android_testing_agent import AndroidTestingAgent
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
from app.services.supabase_client import SupabaseClient
from app.services.knowledge_base_manager import knowledge_base_manager
from .config import settings
import logging

logger = logging.getLogger(__name__)

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
instagram_reel_agent: Optional[InstagramReelAgent] = None
android_testing_agent: Optional[AndroidTestingAgent] = None
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
supabase_client: Optional[SupabaseClient] = None

# Storage
content_storage = {}

def initialize_agents():
    """Initialize all agent instances"""
    global image_generator, qa_agent, affirmations_agent, write_hashtag_agent
    global instagram_ai_prompt_agent, instagram_poster_agent, instagram_analyzer_agent
    global content_wrapper, workflow_agent, post_composition_agent
    global video_generation_agent, instagram_reel_agent, android_testing_agent, voice_over_agent
    global app_store_analyst_agent, play_store_analyst_agent, meta_ads_analyst_agent, google_analytics_expert_agent
    global threads_analysis_agent, content_strategy_agent, post_generator_agent, approval_agent, scheduler_agent
    global x_analysis_agent, x_content_strategy_agent, x_post_generator_agent, x_approval_agent, x_scheduler_agent, supabase_client
    
    logger.info(f"[INIT] OPENAI_API_KEY present: {bool(settings.OPENAI_API_KEY)}")
    logger.info(f"[INIT] OPENAI_API_KEY length: {len(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else 0}")
    
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
        
        logger.info("[INSTAGRAM_REEL_AGENT] Initializing...")
        instagram_reel_agent = InstagramReelAgent(
            settings.OPENAI_API_KEY, 
            settings.RUNWAY_API_KEY,
            settings.KLINGAI_API_KEY,
            settings.KLINGAI_PROVIDER
        )
        logger.info("[INSTAGRAM_REEL_AGENT] Initialized successfully")
        
        # Initialize Voice Over agent
        logger.info("[VOICE_OVER_AGENT] Initializing...")
        voice_over_agent = VoiceOverAgent(settings.OPENAI_API_KEY, settings.ELEVENLABS_API_KEY)
        logger.info("[VOICE_OVER_AGENT] Initialized successfully")
        
        # Initialize Android testing agent
        logger.info(f"[ANDROID_TESTING_AGENT] Initializing with adb_path: {settings.ADB_PATH}")
        try:
            android_testing_agent = AndroidTestingAgent(settings.OPENAI_API_KEY, settings.ADB_PATH)
            logger.info(f"[ANDROID_TESTING_AGENT] Initialized successfully: {android_testing_agent is not None}")
        except Exception as e:
            logger.error(f"[ANDROID_TESTING_AGENT] Failed to initialize: {str(e)}")
            android_testing_agent = None
        
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
        
        # Initialize Supabase client
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
    else:
        logger.warning("OpenAI API key not found. Agents not initialized.")

def cleanup_agents():
    """Cleanup agent resources"""
    if android_testing_agent:
        try:
            android_testing_agent.cleanup()
            logger.info("[ANDROID_TESTING_AGENT] Cleaned up successfully")
        except Exception as e:
            logger.error(f"[ANDROID_TESTING_AGENT] Error cleaning up: {e}")

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
        'instagram_reel_agent': instagram_reel_agent,
        'android_testing_agent': android_testing_agent,
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
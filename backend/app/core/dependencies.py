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

# Storage
content_storage = {}

def initialize_agents():
    """Initialize all agent instances"""
    global image_generator, qa_agent, affirmations_agent, write_hashtag_agent
    global instagram_ai_prompt_agent, instagram_poster_agent, instagram_analyzer_agent
    global content_wrapper, workflow_agent, post_composition_agent
    global video_generation_agent, instagram_reel_agent, android_testing_agent, voice_over_agent
    
    logger.info(f"[INIT] OPENAI_API_KEY present: {bool(settings.OPENAI_API_KEY)}")
    logger.info(f"[INIT] OPENAI_API_KEY length: {len(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else 0}")
    
    if settings.OPENAI_API_KEY:
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
    }
    return agents.get(agent_name)
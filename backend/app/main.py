"""
Refactored main application file for 7 Cycles Backend
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import os
import sys

# Import configuration and dependencies
from app.core.config import settings
from app.core.dependencies import initialize_agents, cleanup_agents

# Import routers
from app.api.routers import (
    health, content, affirmations, visual_posts, instagram,
    media, workflows, android_testing, feedback, qa, images, mobile_analytics
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # Force reconfiguration of logging
)
logger = logging.getLogger(__name__)

# Also configure the dependencies logger
deps_logger = logging.getLogger('app.core.dependencies')
deps_logger.setLevel(logging.INFO)

# Lifespan context manager for startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("[STARTUP] Starting 7 Cycles Backend...")
    initialize_agents()
    logger.info("[STARTUP] Agents initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("[SHUTDOWN] Shutting down 7 Cycles Backend...")
    cleanup_agents()
    logger.info("[SHUTDOWN] Cleanup completed")

# Create FastAPI app
app = FastAPI(
    title="7 Cycles AI Assistant API",
    version="2.0.0",
    description="""
## 7 Cycles AI Content Generation API

This API provides comprehensive AI-powered content generation for the "7 Cycles of Life" methodology.

### Features:
- 🎯 **Multi-agent AI System**: CrewAI-based agents for specialized tasks
- 📱 **Instagram Integration**: Create and post content directly to Instagram
- 🎨 **Visual Content**: Generate images with DALL-E 3 and stock photos
- 🎬 **Video Generation**: Create Instagram Reels with AI
- 🎙️ **Voice Over**: Generate voice narration with ElevenLabs
- 💭 **Q&A System**: Answer questions about the 7 Cycles philosophy
- ✨ **Affirmations**: Generate period-specific affirmations

### Documentation:
- Interactive API docs: [/docs](/docs)
- Alternative docs: [/redoc](/redoc)
- OpenAPI schema: [/openapi.json](/openapi.json)

### API Sections:
- **Content** (`/content/*`): Main content generation workflows
- **Q&A** (`/api/*`): Knowledge base queries and answers
- **Affirmations** (`/affirmations`, `/generate-affirmations`): Period-specific affirmations
- **Visual Posts** (`/visual-posts/*`, `/search-images`): Image generation and management
- **Instagram** (`/instagram-posts/*`): Instagram content creation and posting
- **Media** (`/api/*`): Voice over, video generation, captions
- **Workflows** (`/api/workflows/*`): Complex multi-step workflows

### Authentication:
Currently using API keys configured via environment variables.
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = "static"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routers
app.include_router(health.router)
app.include_router(content.router)
app.include_router(affirmations.router)
app.include_router(visual_posts.router)
app.include_router(instagram.router)
app.include_router(media.router)
app.include_router(workflows.router)
app.include_router(android_testing.router)
app.include_router(feedback.router)
app.include_router(qa.router)
app.include_router(images.router)
app.include_router(mobile_analytics.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
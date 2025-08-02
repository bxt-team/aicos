"""
Refactored main application file for 7 Cycles Backend
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
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
    media, workflows, app_testing, feedback, qa, images, mobile_analytics, threads, x, agent_prompts,
    background_video, auth, organizations, projects, departments, goals, tasks, agent_tasks,
    credits, billing, knowledge_bases, ai_agents, organization_management
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set to INFO to reduce noise
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Ensure logs go to stdout
    ],
    force=True  # Force reconfiguration of logging
)
logger = logging.getLogger(__name__)

# Also configure the dependencies logger
deps_logger = logging.getLogger('app.core.dependencies')
deps_logger.setLevel(logging.INFO)

# Configure organizations router logger
org_logger = logging.getLogger('app.api.routers.organizations')
org_logger.setLevel(logging.INFO)

# Suppress httpcore.http11 DEBUG logs
httpcore_logger = logging.getLogger('httpcore.http11')
httpcore_logger.setLevel(logging.WARNING)

# Suppress all httpcore logs
httpcore_base_logger = logging.getLogger('httpcore')
httpcore_base_logger.setLevel(logging.WARNING)

# Suppress hpack debug logs (HTTP/2 header compression)
hpack_logger = logging.getLogger('hpack')
hpack_logger.setLevel(logging.WARNING)

# Suppress httpx debug logs
httpx_logger = logging.getLogger('httpx')
httpx_logger.setLevel(logging.WARNING)

# Suppress h2 (HTTP/2) debug logs
h2_logger = logging.getLogger('h2')
h2_logger.setLevel(logging.WARNING)

# Lifespan context manager for startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("[STARTUP] Starting AI Company Backend...")
    initialize_agents()
    logger.info("[STARTUP] Agents initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("[SHUTDOWN] Shutting down AI Company Backend...")
    cleanup_agents()
    logger.info("[SHUTDOWN] Cleanup completed")

# Create FastAPI app
app = FastAPI(
    title="AI Company API",
    version="2.0.0",
    description="""
## AI Company Enterprise AI Platform

This API provides comprehensive AI-powered content generation and automation solutions. The "7 Cycles of Life" is one of our specialized projects.

### Features:
- 🎯 **Multi-agent AI System**: CrewAI-based agents for specialized tasks
- 📱 **Instagram Integration**: Create and post content directly to Instagram
- 🎨 **Visual Content**: Generate images with DALL-E 3 and stock photos
- 🎬 **Video Generation**: Create Instagram Reels with AI
- 🎙️ **Voice Over**: Generate voice narration with ElevenLabs
- 💭 **Q&A System**: Answer questions about various knowledge bases
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
- **JWT Authentication**: Secure user authentication with JWT tokens
- **Multi-Tenant Support**: Organization and project-based data isolation
- **API Keys**: Programmatic access with scoped permissions
- **Role-Based Access**: Owner, Admin, Member, and Viewer roles
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add multi-tenant middleware
from app.core.middleware import ContextMiddleware, MultiTenantMiddleware, AuditLoggingMiddleware

# Add in reverse order (last added is executed first)
app.add_middleware(AuditLoggingMiddleware)
app.add_middleware(MultiTenantMiddleware)
app.add_middleware(ContextMiddleware)

# Configure CORS - should be last so it executes first
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler to ensure CORS headers are always present
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all exceptions and ensure CORS headers are present"""
    import traceback
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Mount static files
static_dir = "static"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include routers
app.include_router(auth.router)  # Auth should be first
app.include_router(health.router)
app.include_router(content.router)
app.include_router(affirmations.router)
app.include_router(visual_posts.router)
app.include_router(instagram.router)
app.include_router(media.router)
app.include_router(workflows.router)
app.include_router(app_testing.router)
app.include_router(feedback.router)
app.include_router(qa.router)
app.include_router(images.router)
app.include_router(mobile_analytics.router)
app.include_router(threads.router)
app.include_router(x.router)
app.include_router(agent_prompts.router)
app.include_router(background_video.router)
app.include_router(organizations.router)  # Organization management
app.include_router(projects.router)  # Project management
app.include_router(departments.router)  # Department management
app.include_router(goals.router)  # Goals/Key Results
app.include_router(tasks.router)  # Task management
app.include_router(agent_tasks.router)  # Agent task management
app.include_router(credits.router)  # Credits management
app.include_router(billing.router)  # Billing and subscriptions
app.include_router(knowledge_bases.router)  # Knowledge base management
app.include_router(ai_agents.router)  # AI agents management
app.include_router(organization_management.router)  # Organization management AI agents

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
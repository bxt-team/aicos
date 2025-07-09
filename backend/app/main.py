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
    media, workflows, android_testing, feedback, qa, images
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lifespan context manager for startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting 7 Cycles Backend...")
    initialize_agents()
    logger.info("Agents initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down 7 Cycles Backend...")
    cleanup_agents()
    logger.info("Cleanup completed")

# Create FastAPI app
app = FastAPI(
    title="7 Cycles AI Assistant API",
    version="2.0.0",
    description="Refactored API for 7 Cycles of Life content generation and management",
    lifespan=lifespan
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
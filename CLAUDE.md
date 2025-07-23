# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AICOS is a comprehensive AI-powered business automation system for the "7 Cycles of Life" methodology. Where AI runs your business - it uses CrewAI for multi-agent orchestration to create social media content, visual posts, videos, and more.

## Essential Commands

### Development
```bash
# Install all dependencies (Python + Node)
npm run setup

# Run backend (FastAPI on port 8000)
npm run dev-backend
# Alternative: cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run frontend (React on port 3000)
npm run dev-frontend
# Alternative: cd frontend && npm start

# Build frontend for production
npm run build-frontend
```

### Testing
```bash
# Backend tests (from backend directory)
cd backend && pytest
# Run specific test: pytest tests/unit/agents/test_researcher.py
# Run with coverage: pytest --cov=app tests/
```

### Docker
```bash
docker-compose up  # Runs backend, frontend, and Redis
```

## Architecture

### Backend Structure
- **Main entry**: `backend/app/main.py` - FastAPI application with all routers
- **Agent system**: CrewAI-based agents in `backend/app/agents/`
  - Configuration: YAML files in `backend/app/agents/config/`
  - Base class: `backend/app/agents/crews/base_crew.py`
- **API routers**: `backend/app/api/routers/` - Each file corresponds to an API prefix
- **Dependencies**: `backend/app/core/dependencies.py` - Agent initialization and management

### Key API Endpoints
All endpoints have their respective prefix:
- `/api/ask-question` - Q&A agent queries (NOT `/content/ask-question`)
- `/api/qa-health` - Check Q&A agent status
- `/generate-affirmations` - Generate affirmations (NO prefix)
- `/affirmations` - List affirmations (NO prefix)
- `/periods` - Get periods info (NO prefix)
- `/content/generate` - Generate content (NOT `/generate-content`)
- `/content/approve` - Approve content (NOT `/approve-content`)
- `/visual-posts/*` - Create visual posts
- `/create-visual-post` - Create visual post (NO prefix, NOT `/create-affirmation-post`)
- `/instagram-posts/*` - Instagram posting
- `/prepare-instagram-content` - Prepare Instagram content (NO prefix)
- `/api/generate-instagram-reel` - Generate reel (NOT `/api/generate-reel`)
- `/api/videos` - List videos (NOT `/api/instagram-reels`)
- `/api/workflows/*` - Content workflow management

### Agent System
Agents are initialized on startup via `initialize_agents()` in dependencies.py. Each agent:
1. Extends `BaseCrew` class
2. Has YAML configuration in `agents/config/`
3. Is registered in `get_agent()` function
4. Has specific tools and LLM models configured

Common pattern for fixing agent issues:
1. Check if agent is properly initialized in `dependencies.py`
2. Verify YAML configuration exists
3. Ensure required methods are implemented (e.g., `health_check()`)
4. Check environment variables for API keys

### Frontend
- React app with TypeScript in `frontend/`
- Proxy configured to reach backend at localhost:8000
- Main components in `frontend/src/components/`

## Configuration

### Environment Variables (.env)
Critical variables:
- `OPENAI_API_KEY` - Required for all AI features
- `PEXELS_API_KEY` - For image search
- `ELEVENLABS_API_KEY` - For voice generation
- `RUNWAY_API_KEY` - For video generation
- `INSTAGRAM_ACCESS_TOKEN` & `INSTAGRAM_BUSINESS_ACCOUNT_ID` - For Instagram posting
- `ADB_PATH` - For Android testing

### YAML Configuration
Agents, tasks, crews, and tools are defined in `backend/app/agents/config/`:
- `agents.yaml` - Agent definitions with roles and backstories
- `tasks.yaml` - Task templates with descriptions
- `crews.yaml` - Crew compositions
- `tools.yaml` - Tool configurations

## Common Issues and Solutions

### Agent Not Found (404)
- Endpoints are prefixed (e.g., `/api/ask-question` not `/ask-question`)
- Check agent initialization in `dependencies.py`
- Verify agent is registered in `get_agent()` function

### Missing Methods
- Agents may need `health_check()` method if used in health endpoints
- Check router file for expected method signatures

### Static Files
- Directories auto-created: `static/`, `storage/`, etc.
- Served by FastAPI at `/static`

## Knowledge Base
- PDF knowledge base: `backend/knowledge/20250607_7Cycles of Life_Ebook.pdf`
- Loaded by QAAgent using FAISS vector store
- German language content about 7 life cycles

## Testing Approach
- Unit tests: `backend/tests/unit/` - Test individual agents
- Integration tests: `backend/tests/integration/` - Test workflows
- Always check if test infrastructure exists before assuming test commands

## Important Notes
- All agents use CrewAI framework with LangChain integration
- Most operations are async
- CORS configured for local development (ports 3000, 3001, 8000)
- Logs use German and English mixed (legacy from original development)
- Static file directories are created automatically if missing
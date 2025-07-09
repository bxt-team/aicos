# Backend Refactoring Guide

## Overview

The backend has been refactored from a single 2600+ line `main.py` file into a modular structure for better maintainability, testability, and scalability.

## New Structure

```
backend/
├── app.py                    # Main application file
├── api/
│   └── routers/             # API route modules
│       ├── health.py        # Health check endpoints
│       ├── content.py       # Content generation endpoints
│       ├── affirmations.py  # Affirmation endpoints
│       ├── visual_posts.py  # Visual post endpoints
│       ├── instagram.py     # Instagram-related endpoints
│       ├── media.py         # Voice, video, and caption endpoints
│       ├── workflows.py     # Workflow management endpoints
│       ├── android_testing.py # Android testing endpoints
│       ├── feedback.py      # Feedback and analytics endpoints
│       ├── qa.py           # Q&A and knowledge base endpoints
│       └── images.py       # Image search endpoints
├── core/
│   ├── config.py           # Configuration settings
│   └── dependencies.py     # Agent initialization and dependencies
├── schemas/                # Pydantic models
│   ├── content.py         # Content-related schemas
│   ├── instagram.py       # Instagram schemas
│   ├── visual_post.py     # Visual post schemas
│   ├── media.py           # Media processing schemas
│   └── workflow.py        # Workflow schemas
├── utils/                 # Utility functions
│   ├── file_helpers.py    # File handling utilities
│   └── image_helpers.py   # Image processing utilities
└── storage/              # Data storage directory

```

## Migration Steps

### 1. Install the refactored version

The new structure is backward compatible. You can run both versions side by side during migration.

### 2. Update imports in your code

All imports have been updated. The main.py file has been removed and replaced with the modular app.py structure.

### 3. Test the new application

Run the refactored version:
```bash
python app.py
```

Or with uvicorn:
```bash
uvicorn app:app --reload
```

### 4. Environment variables

All environment variables remain the same. The configuration is now centralized in `core/config.py`.

## Key Changes

### 1. Modular Routers

API endpoints are now organized by feature:
- `/api/routers/health.py` - Health checks
- `/api/routers/content.py` - Content generation
- `/api/routers/affirmations.py` - Affirmations
- `/api/routers/visual_posts.py` - Visual posts
- `/api/routers/instagram.py` - Instagram features

### 2. Centralized Configuration

All settings are in `core/config.py`:
```python
from core.config import settings

# Access settings
api_key = settings.OPENAI_API_KEY
```

### 3. Dependency Management

Agent initialization is handled in `core/dependencies.py`:
```python
from core.dependencies import get_agent

# Get a specific agent
qa_agent = get_agent('qa_agent')
```

### 4. Type-safe Schemas

All request/response models are in the `schemas/` directory with proper type hints.

### 5. Utility Functions

Common utilities are extracted to `utils/`:
- File operations: `utils.file_helpers`
- Image processing: `utils.image_helpers`

## Benefits

1. **Better Organization**: Code is organized by feature/domain
2. **Easier Testing**: Individual modules can be tested in isolation
3. **Improved Maintainability**: Changes to one feature don't affect others
4. **Type Safety**: Centralized schemas with type hints
5. **Reusability**: Utility functions can be reused across modules

## TODO

The following components have been migrated:
- [x] Media processing endpoints (voice, video, captions) - ✅ Completed in media.py
- [x] Workflow endpoints - ✅ Completed in workflows.py
- [x] Android testing endpoints - ✅ Completed in android_testing.py
- [x] Feedback and analytics endpoints - ✅ Completed in feedback.py
- [x] Q&A endpoints - ✅ Completed in qa.py
- [x] Image search endpoints - ✅ Completed in images.py
- [ ] Remaining utility functions (if any)

## Migration Complete

The refactoring is now complete. The main.py file has been removed and all functionality has been migrated to the modular structure. All endpoints are now available through the organized router system.

## Support

For questions or issues with the refactoring, please check:
1. The error logs for specific issues
2. The original `main.py` for reference
3. Individual module documentation
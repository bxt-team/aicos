# Backend Refactoring Guide

## Overview

The backend has been refactored from a single 2600+ line `main.py` file into a modular structure for better maintainability, testability, and scalability.

## New Structure

```
backend/
├── app.py                    # New main application file
├── main.py                   # Original file (to be deprecated)
├── api/
│   └── routers/             # API route modules
│       ├── health.py        # Health check endpoints
│       ├── content.py       # Content generation endpoints
│       ├── affirmations.py  # Affirmation endpoints
│       ├── visual_posts.py  # Visual post endpoints
│       └── instagram.py     # Instagram-related endpoints
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

If you have any custom scripts importing from main.py, update them:

```python
# Old
from main import app

# New
from app import app
```

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

The following components still need to be migrated:
- [ ] Media processing endpoints (voice, video, captions)
- [ ] Workflow endpoints
- [ ] Android testing endpoints
- [ ] Feedback and analytics endpoints
- [ ] Remaining utility functions

## Rollback

If you need to rollback to the original version:
1. Stop the new application
2. Run `python main.py` to use the original monolithic version
3. All data and functionality will remain the same

## Support

For questions or issues with the refactoring, please check:
1. The error logs for specific issues
2. The original `main.py` for reference
3. Individual module documentation
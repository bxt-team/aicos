# Supabase Migration Plan for 7cycles-ai

## Overview
This document outlines the strategy for migrating from JSON file-based storage to Supabase database storage. The migration will be done incrementally to ensure system stability and data integrity.

## Database Schema Design

### Agent-Specific Tables

#### 1. Affirmation Agent Tables
```sql
-- Generated affirmations
agent_affirmation_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  theme TEXT NOT NULL,
  period INTEGER NOT NULL,
  affirmation TEXT NOT NULL,
  language TEXT DEFAULT 'de',
  created_at TIMESTAMP DEFAULT NOW(),
  metadata JSONB,
  INDEX idx_period (period),
  INDEX idx_theme (theme)
);
```

#### 2. Visual Post Agent Tables
```sql
-- Visual posts created by the agent
agent_visual_posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  post_type TEXT NOT NULL, -- 'affirmation', 'quote', 'custom'
  image_url TEXT,
  image_path TEXT,
  text_content TEXT NOT NULL,
  period INTEGER,
  theme TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  metadata JSONB,
  INDEX idx_post_type (post_type),
  INDEX idx_period (period)
);
```

#### 3. Instagram Agent Tables
```sql
-- Instagram content and posting history
agent_instagram_posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content TEXT NOT NULL,
  hashtags TEXT[],
  post_type TEXT, -- 'feed', 'story', 'reel'
  status TEXT DEFAULT 'draft', -- 'draft', 'scheduled', 'posted', 'failed'
  scheduled_at TIMESTAMP,
  posted_at TIMESTAMP,
  instagram_post_id TEXT,
  engagement_data JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  metadata JSONB,
  INDEX idx_status (status),
  INDEX idx_posted_at (posted_at)
);

-- Instagram account analyses
agent_instagram_analyses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_username TEXT NOT NULL,
  analysis_type TEXT, -- 'profile', 'content', 'engagement'
  analysis_data JSONB NOT NULL,
  recommendations JSONB,
  analyzed_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_account (account_username),
  INDEX idx_analyzed_at (analyzed_at)
);

-- Instagram reels
agent_instagram_reels (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  script TEXT NOT NULL,
  video_url TEXT,
  video_path TEXT,
  duration INTEGER,
  status TEXT DEFAULT 'draft',
  created_at TIMESTAMP DEFAULT NOW(),
  metadata JSONB
);
```

#### 4. Content Agent Tables
```sql
-- General content generation
agent_content_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content_type TEXT NOT NULL, -- 'blog', 'social', 'email', etc.
  title TEXT,
  content TEXT NOT NULL,
  period INTEGER,
  theme TEXT,
  status TEXT DEFAULT 'draft',
  created_at TIMESTAMP DEFAULT NOW(),
  metadata JSONB,
  INDEX idx_content_type (content_type),
  INDEX idx_status (status)
);

-- Content approvals
agent_content_approvals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content_id UUID REFERENCES agent_content_items(id),
  approved BOOLEAN NOT NULL,
  approved_by TEXT,
  approval_notes TEXT,
  approved_at TIMESTAMP DEFAULT NOW()
);
```

#### 5. Video Agent Tables
```sql
-- Generated videos
agent_video_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  description TEXT,
  script TEXT,
  video_url TEXT,
  video_path TEXT,
  duration INTEGER,
  generation_status TEXT DEFAULT 'pending',
  generation_provider TEXT, -- 'runway', 'elevenlabs', etc.
  created_at TIMESTAMP DEFAULT NOW(),
  metadata JSONB,
  INDEX idx_status (generation_status)
);

-- Voice overs
agent_voice_overs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  text TEXT NOT NULL,
  voice_id TEXT,
  audio_url TEXT,
  audio_path TEXT,
  duration FLOAT,
  language TEXT DEFAULT 'de',
  created_at TIMESTAMP DEFAULT NOW(),
  metadata JSONB
);
```

#### 6. Social Media Analysis Agent Tables
```sql
-- X (Twitter) analysis
agent_x_analyses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_handle TEXT NOT NULL,
  analysis_data JSONB NOT NULL,
  strategy_recommendations JSONB,
  analyzed_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_account (account_handle)
);

-- X posts
agent_x_posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content TEXT NOT NULL,
  hashtags TEXT[],
  media_urls TEXT[],
  status TEXT DEFAULT 'draft',
  scheduled_at TIMESTAMP,
  posted_at TIMESTAMP,
  x_post_id TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  metadata JSONB
);

-- Threads analysis
agent_threads_analyses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_username TEXT NOT NULL,
  analysis_data JSONB NOT NULL,
  content_strategy JSONB,
  analyzed_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_account (account_username)
);

-- Threads posts
agent_threads_posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content TEXT NOT NULL,
  hashtags TEXT[],
  media_urls TEXT[],
  thread_parent_id UUID,
  status TEXT DEFAULT 'draft',
  scheduled_at TIMESTAMP,
  posted_at TIMESTAMP,
  threads_post_id TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  metadata JSONB
);
```

#### 7. Mobile Analytics Agent Tables
```sql
-- Play Store app analyses
agent_play_store_analyses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  app_id TEXT NOT NULL,
  app_name TEXT NOT NULL,
  analysis_type TEXT, -- 'reviews', 'ratings', 'competitors'
  analysis_data JSONB NOT NULL,
  insights JSONB,
  analyzed_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_app_id (app_id),
  INDEX idx_analyzed_at (analyzed_at)
);
```

#### 8. QA Agent Tables
```sql
-- Question-answer pairs for knowledge base
agent_qa_interactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  context TEXT,
  relevance_score FLOAT,
  user_feedback INTEGER, -- 1-5 rating
  created_at TIMESTAMP DEFAULT NOW(),
  metadata JSONB,
  INDEX idx_created_at (created_at)
);
```

### Shared/System Tables

```sql
-- Workflow executions
system_workflows (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_type TEXT NOT NULL,
  workflow_config JSONB,
  status TEXT DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
  result JSONB,
  error_message TEXT,
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_workflow_type (workflow_type),
  INDEX idx_status (status)
);

-- User feedback
system_feedback (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  resource_type TEXT NOT NULL,
  resource_id UUID,
  rating INTEGER CHECK (rating >= 1 AND rating <= 5),
  feedback_text TEXT,
  user_id TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_resource (resource_type, resource_id)
);

-- Cost tracking
system_cost_tracking (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  service_name TEXT NOT NULL, -- 'openai', 'runway', 'elevenlabs'
  operation_type TEXT NOT NULL,
  cost_amount DECIMAL(10, 6),
  usage_metrics JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_service (service_name),
  INDEX idx_created_at (created_at)
);

-- Generic storage for migration
system_generic_storage (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  storage_key TEXT NOT NULL UNIQUE,
  storage_type TEXT NOT NULL,
  data JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  INDEX idx_storage_type (storage_type)
);
```

## Storage Abstraction Layer

### 1. Base Storage Interface
```python
# backend/app/core/storage/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

class StorageAdapter(ABC):
    """Abstract base class for storage adapters"""
    
    @abstractmethod
    async def save(self, 
                   collection: str, 
                   data: Dict[str, Any], 
                   id: Optional[str] = None) -> str:
        """Save data to storage and return ID"""
        pass
    
    @abstractmethod
    async def load(self, 
                   collection: str, 
                   id: str) -> Optional[Dict[str, Any]]:
        """Load single item by ID"""
        pass
    
    @abstractmethod
    async def list(self, 
                   collection: str, 
                   filters: Optional[Dict] = None,
                   limit: Optional[int] = None,
                   offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """List items with optional filtering"""
        pass
    
    @abstractmethod
    async def update(self, 
                     collection: str, 
                     id: str, 
                     data: Dict[str, Any]) -> bool:
        """Update existing item"""
        pass
    
    @abstractmethod
    async def delete(self, 
                     collection: str, 
                     id: str) -> bool:
        """Delete item by ID"""
        pass
    
    @abstractmethod
    async def count(self, 
                    collection: str, 
                    filters: Optional[Dict] = None) -> int:
        """Count items in collection"""
        pass
```

### 2. Supabase Adapter Implementation
```python
# backend/app/core/storage/supabase_adapter.py
from supabase import create_client, Client
from .base import StorageAdapter

class SupabaseAdapter(StorageAdapter):
    def __init__(self, url: str, key: str):
        self.client: Client = create_client(url, key)
        self._table_mappings = {
            # Map collection names to table names
            'affirmations': 'agent_affirmation_items',
            'visual_posts': 'agent_visual_posts',
            'instagram_posts': 'agent_instagram_posts',
            # ... etc
        }
```

### 3. JSON Adapter (for backward compatibility)
```python
# backend/app/core/storage/json_adapter.py
import json
import os
from .base import StorageAdapter

class JSONAdapter(StorageAdapter):
    def __init__(self, base_path: str = "static"):
        self.base_path = base_path
```

### 4. Storage Factory
```python
# backend/app/core/storage/factory.py
from typing import Optional
from .base import StorageAdapter
from .supabase_adapter import SupabaseAdapter
from .json_adapter import JSONAdapter

class StorageFactory:
    @staticmethod
    def create_adapter(adapter_type: str = "json", **kwargs) -> StorageAdapter:
        if adapter_type == "supabase":
            return SupabaseAdapter(
                url=kwargs.get("url"),
                key=kwargs.get("key")
            )
        elif adapter_type == "json":
            return JSONAdapter(
                base_path=kwargs.get("base_path", "static")
            )
        else:
            raise ValueError(f"Unknown adapter type: {adapter_type}")
```

## Migration Strategy

### Phase 1: Preparation (Week 1)
1. **Set up Supabase project**
   - Create database
   - Configure authentication
   - Set up environment variables

2. **Implement storage abstraction layer**
   - Create base interface
   - Implement JSON adapter (current behavior)
   - Add storage factory

3. **Update configuration**
   ```python
   # backend/app/core/config.py
   STORAGE_ADAPTER = os.getenv("STORAGE_ADAPTER", "json")
   SUPABASE_URL = os.getenv("SUPABASE_URL")
   SUPABASE_KEY = os.getenv("SUPABASE_KEY")
   ```

### Phase 2: Implementation (Week 2-3)
1. **Implement Supabase adapter**
   - Create adapter class
   - Implement all interface methods
   - Add error handling and retries

2. **Create migration scripts**
   ```python
   # backend/scripts/migrate_to_supabase.py
   async def migrate_collection(collection_name: str):
       json_adapter = JSONAdapter()
       supabase_adapter = SupabaseAdapter()
       
       # Load all data from JSON
       items = await json_adapter.list(collection_name)
       
       # Save to Supabase
       for item in items:
           await supabase_adapter.save(collection_name, item)
   ```

3. **Update one agent as pilot**
   - Start with QA Agent (simpler data structure)
   - Replace direct file operations with storage adapter
   - Test thoroughly

### Phase 3: Gradual Migration (Week 4-6)
1. **Migrate agents in order of complexity**
   - Simple agents first (QA, Affirmation)
   - Complex agents later (Instagram, Video)
   - Test each migration thoroughly

2. **Implement dual-write mode**
   - Write to both JSON and Supabase
   - Read from JSON (safety)
   - Compare data integrity

3. **Switch read operations**
   - Start reading from Supabase
   - Keep JSON as backup
   - Monitor for issues

### Phase 4: Cleanup (Week 7)
1. **Remove JSON write operations**
2. **Archive JSON files**
3. **Update documentation**
4. **Remove old code**

## Implementation Checklist

- [ ] Create Supabase project and database
- [ ] Design and create all tables
- [ ] Implement storage abstraction layer
- [ ] Create JSON adapter (current behavior)
- [ ] Create Supabase adapter
- [ ] Implement storage factory
- [ ] Create migration scripts
- [ ] Set up environment configuration
- [ ] Migrate QA Agent (pilot)
- [ ] Migrate Affirmation Agent
- [ ] Migrate Visual Post Agent
- [ ] Migrate Content Agent
- [ ] Migrate Instagram Agent
- [ ] Migrate Video Agent
- [ ] Migrate Social Media Agents (X, Threads)
- [ ] Migrate Mobile Analytics Agent
- [ ] Implement monitoring and logging
- [ ] Create backup/restore procedures
- [ ] Update all documentation
- [ ] Remove deprecated code

## Benefits of Migration

1. **Scalability**: No file system limitations
2. **Performance**: Indexed queries instead of full file loads
3. **Concurrency**: Better handling of simultaneous operations
4. **Real-time**: Supabase's real-time subscriptions
5. **Security**: Row-level security policies
6. **Backup**: Automated database backups
7. **Analytics**: SQL queries for insights
8. **Integration**: Easy API access for frontend

## Risk Mitigation

1. **Data Loss Prevention**
   - Keep JSON files as backup during migration
   - Implement data validation after each migration
   - Create rollback procedures

2. **Performance Issues**
   - Test query performance before migration
   - Add appropriate indexes
   - Implement caching where needed

3. **Compatibility**
   - Use abstraction layer to maintain API compatibility
   - Gradual migration to minimize disruption
   - Extensive testing at each phase

## Success Criteria

1. All data successfully migrated to Supabase
2. No data loss during migration
3. Performance equal or better than JSON storage
4. All agents functioning correctly with new storage
5. Monitoring and backup procedures in place
6. Documentation updated
7. Team trained on new system

## Next Steps

1. Review and approve this plan
2. Set up Supabase project
3. Begin Phase 1 implementation
4. Schedule regular progress reviews
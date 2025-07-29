from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class KnowledgeBaseBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    organization_id: UUID
    project_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    agent_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    is_active: bool = True

class KnowledgeBaseCreate(KnowledgeBaseBase):
    file_type: str
    file_name: str
    file_size: int

class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class KnowledgeBase(KnowledgeBaseBase):
    id: UUID
    file_type: str
    file_name: str
    file_size: int
    file_path: str
    vector_store_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    
    class Config:
        from_attributes = True

class KnowledgeBaseList(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    file_type: str
    file_name: str
    file_size: int
    organization_id: UUID
    project_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    agent_type: Optional[str] = None
    is_active: bool
    created_at: datetime
    scope_level: Optional[str] = None
    
    class Config:
        from_attributes = True

class KnowledgeBaseEmbedding(BaseModel):
    id: UUID
    knowledge_base_id: UUID
    chunk_index: int
    chunk_text: str
    embedding_vector: Optional[list[float]] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: datetime
    
    class Config:
        from_attributes = True
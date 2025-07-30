from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import List, Optional, Dict, Any
from uuid import UUID
import os
import aiofiles
from datetime import datetime

from app.core.supabase_auth import get_current_user
from app.models.knowledge_base import (
    KnowledgeBase,
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseList
)
from app.services.knowledge_base_service import KnowledgeBaseService
from app.core.dependencies import get_knowledge_base_service

router = APIRouter(prefix="/api/knowledge-bases", tags=["knowledge-bases"])

@router.get("/", response_model=List[KnowledgeBaseList])
async def list_knowledge_bases(
    organization_id: UUID,
    project_id: Optional[UUID] = None,
    department_id: Optional[UUID] = None,
    agent_type: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_knowledge_base_service)
):
    """List all knowledge bases for a given scope"""
    return await kb_service.list_knowledge_bases(
        organization_id=organization_id,
        project_id=project_id,
        department_id=department_id,
        agent_type=agent_type,
        user_id=current_user.get('id')
    )

@router.get("/{knowledge_base_id}", response_model=KnowledgeBase)
async def get_knowledge_base(
    knowledge_base_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_knowledge_base_service)
):
    """Get a specific knowledge base"""
    kb = await kb_service.get_knowledge_base(knowledge_base_id, current_user.get('id'))
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb

@router.post("/", response_model=KnowledgeBase)
async def create_knowledge_base(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    organization_id: UUID = Form(...),
    project_id: Optional[UUID] = Form(None),
    department_id: Optional[UUID] = Form(None),
    agent_type: Optional[str] = Form(None),
    current_user: Dict[str, Any] = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_knowledge_base_service)
):
    """Upload a new knowledge base file"""
    # Validate file type
    allowed_types = {".pdf", ".txt", ".json", ".csv", ".docx"}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file_ext} not allowed. Allowed types: {', '.join(allowed_types)}"
        )
    
    # Read file content
    content = await file.read()
    
    kb_create = KnowledgeBaseCreate(
        name=name,
        description=description,
        organization_id=organization_id,
        project_id=project_id,
        department_id=department_id,
        agent_type=agent_type,
        file_type=file_ext[1:],  # Remove the dot
        file_name=file.filename,
        file_size=len(content)
    )
    
    return await kb_service.create_knowledge_base(
        kb_create=kb_create,
        file_content=content,
        user_id=current_user.get('id')
    )

@router.put("/{knowledge_base_id}", response_model=KnowledgeBase)
async def update_knowledge_base(
    knowledge_base_id: UUID,
    update: KnowledgeBaseUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_knowledge_base_service)
):
    """Update knowledge base metadata"""
    kb = await kb_service.update_knowledge_base(
        knowledge_base_id=knowledge_base_id,
        update=update,
        user_id=current_user.get('id')
    )
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb

@router.delete("/{knowledge_base_id}")
async def delete_knowledge_base(
    knowledge_base_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_knowledge_base_service)
):
    """Delete a knowledge base"""
    success = await kb_service.delete_knowledge_base(
        knowledge_base_id=knowledge_base_id,
        user_id=current_user.get('id')
    )
    if not success:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return {"message": "Knowledge base deleted successfully"}

@router.post("/{knowledge_base_id}/reindex")
async def reindex_knowledge_base(
    knowledge_base_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_knowledge_base_service)
):
    """Reindex a knowledge base (regenerate embeddings)"""
    success = await kb_service.reindex_knowledge_base(
        knowledge_base_id=knowledge_base_id,
        user_id=current_user.get('id')
    )
    if not success:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return {"message": "Knowledge base reindexing started"}

@router.get("/applicable/search")
async def get_applicable_knowledge_bases(
    organization_id: UUID,
    project_id: Optional[UUID] = None,
    department_id: Optional[UUID] = None,
    agent_type: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_knowledge_base_service)
):
    """Get all applicable knowledge bases for a given context"""
    return await kb_service.get_applicable_knowledge_bases(
        organization_id=organization_id,
        project_id=project_id,
        department_id=department_id,
        agent_type=agent_type,
        user_id=current_user.get('id')
    )
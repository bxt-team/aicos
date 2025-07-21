"""
Authentication models for multi-tenant system
"""
from typing import Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID


class OrganizationRole(str, Enum):
    """Organization membership roles"""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Permission(str, Enum):
    """System permissions"""
    # Organization permissions
    ORG_READ = "org:read"
    ORG_UPDATE = "org:update"
    ORG_DELETE = "org:delete"
    ORG_BILLING = "org:billing"
    
    # Project permissions
    PROJECT_CREATE = "project:create"
    PROJECT_READ = "project:read"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"
    
    # Agent permissions
    AGENT_USE = "agent:use"
    AGENT_CONFIGURE = "agent:configure"
    
    # Content permissions
    CONTENT_CREATE = "content:create"
    CONTENT_READ = "content:read"
    CONTENT_UPDATE = "content:update"
    CONTENT_DELETE = "content:delete"
    CONTENT_PUBLISH = "content:publish"


# Role-Permission Mapping
ROLE_PERMISSIONS = {
    OrganizationRole.OWNER: [Permission(p) for p in Permission],
    OrganizationRole.ADMIN: [
        Permission.ORG_READ, Permission.ORG_UPDATE,
        Permission.PROJECT_CREATE, Permission.PROJECT_READ, 
        Permission.PROJECT_UPDATE, Permission.PROJECT_DELETE,
        Permission.AGENT_USE, Permission.AGENT_CONFIGURE,
        Permission.CONTENT_CREATE, Permission.CONTENT_READ,
        Permission.CONTENT_UPDATE, Permission.CONTENT_DELETE,
        Permission.CONTENT_PUBLISH
    ],
    OrganizationRole.MEMBER: [
        Permission.ORG_READ,
        Permission.PROJECT_READ,
        Permission.AGENT_USE,
        Permission.CONTENT_CREATE, Permission.CONTENT_READ,
        Permission.CONTENT_UPDATE
    ],
    OrganizationRole.VIEWER: [
        Permission.ORG_READ,
        Permission.PROJECT_READ,
        Permission.CONTENT_READ
    ]
}


class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    """Signup request model"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str
    organization_name: str


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"
    organization: "OrganizationResponse"


class UserResponse(BaseModel):
    """User response model"""
    id: UUID
    email: str
    name: str
    avatar_url: Optional[str] = None
    created_at: datetime
    organizations: List["OrganizationMembership"] = []


class OrganizationResponse(BaseModel):
    """Organization response model"""
    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    subscription_tier: str
    created_at: datetime


class OrganizationMembership(BaseModel):
    """Organization membership model"""
    organization: OrganizationResponse
    role: OrganizationRole
    joined_at: datetime


class ProjectResponse(BaseModel):
    """Project response model"""
    id: UUID
    organization_id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime


class User(BaseModel):
    """Internal user model"""
    id: UUID
    email: str
    name: str
    avatar_url: Optional[str] = None
    email_verified: bool = False
    created_at: datetime
    updated_at: datetime


class RequestContext(BaseModel):
    """Request context for multi-tenant operations"""
    user_id: UUID
    organization_id: UUID
    project_id: Optional[UUID] = None
    permissions: List[Permission] = []
    role: OrganizationRole


class APIKeyCreate(BaseModel):
    """API key creation request"""
    name: str
    expires_in_days: Optional[int] = None
    permissions: List[Permission] = []
    project_id: Optional[UUID] = None


class APIKeyResponse(BaseModel):
    """API key response (only shown once)"""
    id: UUID
    key: str  # Only returned on creation
    name: str
    prefix: str
    created_at: datetime
    expires_at: Optional[datetime] = None


# Update forward references
TokenResponse.model_rebuild()
UserResponse.model_rebuild()
OrganizationMembership.model_rebuild()
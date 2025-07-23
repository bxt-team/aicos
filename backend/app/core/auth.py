"""
Core authentication utilities for JWT tokens and user management
"""
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.models.auth import User, RequestContext, Permission, OrganizationRole


# Configuration
SECRET_KEY = os.getenv("SUPABASE_JWT_SECRET")
if not SECRET_KEY:
    raise ValueError("SUPABASE_JWT_SECRET environment variable must be set")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token security
security = HTTPBearer()


class TokenData(BaseModel):
    """JWT token payload data"""
    sub: str  # user_id
    email: str
    organizations: List[Dict[str, Any]] = []
    permissions: List[str] = []
    exp: datetime
    iat: datetime
    token_type: str = "access"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(
    user_id: str,
    email: str,
    organizations: List[Dict[str, Any]],
    permissions: List[str],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token"""
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    
    to_encode = {
        "sub": user_id,
        "email": email,
        "organizations": organizations,
        "permissions": permissions,
        "exp": expire,
        "iat": datetime.utcnow(),
        "token_type": "access"
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(user_id: str, email: str) -> str:
    """Create a JWT refresh token"""
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow(),
        "token_type": "refresh"
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenData(**payload)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """Get current user from JWT token"""
    token = credentials.credentials
    token_data = decode_token(token)
    
    if token_data.token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data


async def get_current_user(
    request: Request,
    token_data: TokenData = Depends(get_current_user_token)
) -> User:
    """Get current user from token and database"""
    from app.core.dependencies import get_supabase_client
    
    # Get user from database
    supabase_client = get_supabase_client()
    supabase = supabase_client.client
    
    if not supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection not available"
        )
    
    result = supabase.table("users").select("*").eq("id", token_data.sub).single().execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    # Store user in request state for easy access
    user = User(**result.data)
    request.state.user = user
    
    return user


async def get_request_context(
    request: Request,
    user: User = Depends(get_current_user),
    token_data: TokenData = Depends(get_current_user_token)
) -> RequestContext:
    """Get request context with organization and project info"""
    # Extract organization from headers or URL
    org_id = request.headers.get("X-Organization-ID")
    project_id = request.headers.get("X-Project-ID")
    
    # Or extract from URL path if using path-based routing
    # e.g., /api/orgs/{org_id}/projects/{project_id}/...
    
    if not org_id:
        # Get default organization (first one user is member of)
        if token_data.organizations:
            org_id = token_data.organizations[0]["id"]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No organization context provided",
            )
    
    # Verify user has access to this organization
    org_membership = next(
        (org for org in token_data.organizations if org["id"] == org_id),
        None
    )
    
    if not org_membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this organization",
        )
    
    # Build context
    context = RequestContext(
        user_id=UUID(user.id),
        organization_id=UUID(org_id),
        project_id=UUID(project_id) if project_id else None,
        permissions=[Permission(p) for p in token_data.permissions],
        role=OrganizationRole(org_membership["role"])
    )
    
    # Store in request state
    request.state.context = context
    
    return context


def check_permission(required_permission: Permission):
    """Dependency to check if user has required permission"""
    async def permission_checker(
        context: RequestContext = Depends(get_request_context)
    ):
        if required_permission not in context.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {required_permission.value} required",
            )
        return True
    
    return permission_checker


def require_role(minimum_role: OrganizationRole):
    """Dependency to check if user has minimum role"""
    async def role_checker(
        context: RequestContext = Depends(get_request_context)
    ):
        role_hierarchy = {
            OrganizationRole.VIEWER: 0,
            OrganizationRole.MEMBER: 1,
            OrganizationRole.ADMIN: 2,
            OrganizationRole.OWNER: 3
        }
        
        if role_hierarchy.get(context.role, -1) < role_hierarchy.get(minimum_role, 999):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {minimum_role.value} or higher required",
            )
        return True
    
    return role_checker


class OptionalAuth:
    """Optional authentication - allows anonymous access"""
    async def __call__(
        self,
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> Optional[User]:
        if not credentials:
            return None
        
        try:
            token_data = decode_token(credentials.credentials)
            return await get_current_user(request, token_data)
        except HTTPException:
            return None


# Utility functions for API key authentication
def generate_api_key_prefix(key: str) -> str:
    """Generate a prefix for API key identification"""
    return key[:12] if len(key) >= 12 else key


async def validate_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    """Validate an API key and return associated context"""
    from app.core.security.api_keys import APIKeyManager
    
    manager = APIKeyManager()
    return await manager.validate_api_key(api_key)
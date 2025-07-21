"""
Authentication API endpoints
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer

from uuid import UUID
from app.models.auth import (
    LoginRequest, SignupRequest, TokenResponse, UserResponse,
    OrganizationResponse, OrganizationMembership, OrganizationRole,
    APIKeyCreate, APIKeyResponse, ROLE_PERMISSIONS
)
from app.core.auth import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, decode_token, get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from jose import JWTError
from app.core.dependencies import get_supabase_client
from app.core.security.api_keys import APIKeyManager


router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


@router.post("/signup", response_model=TokenResponse)
async def signup(request: SignupRequest):
    """Create new user and organization"""
    supabase_client = get_supabase_client()
    supabase = supabase_client.client
    
    if not supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection not available"
        )
    
    # Check if user already exists
    existing_user = supabase.table("users").select("id").eq("email", request.email).execute()
    if existing_user.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash the password
    password_hash = get_password_hash(request.password)
    
    try:
        # Create user using the register_user function
        user_result = supabase.rpc("register_user", {
            "p_email": request.email,
            "p_name": request.name,
            "p_password_hash": password_hash,
            "p_auth_provider": "email"
        }).execute()
        
        if not user_result.data or len(user_result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
            
        user_id = user_result.data[0]["user_id"]
        
        # Get the created user
        user_data = supabase.table("users").select("*").eq("id", user_id).single().execute()
        user = user_data.data
        
        # Create organization
        org_slug = request.organization_name.lower().replace(" ", "-")
        org_data = {
            "name": request.organization_name,
            "slug": org_slug,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        # Insert and then select the created organization
        supabase.table("organizations").insert(org_data).execute()
        
        # Fetch the created organization
        org_result = supabase.table("organizations").select("*").eq("slug", org_slug).single().execute()
        
        if not org_result.data:
            raise Exception(f"Failed to create organization")
            
        organization = org_result.data
        
        # Add user as owner of organization
        membership_data = {
            "organization_id": organization["id"],
            "user_id": str(user_id),
            "role": OrganizationRole.OWNER.value,
            "accepted_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        supabase.table("organization_members").insert(membership_data).execute()
        
        # Create default project for the organization
        project_id = uuid4()
        project_data = {
            "id": str(project_id),
            "organization_id": organization["id"],
            "name": "Default Project",
            "description": "Your first project - feel free to rename or create additional projects",
            "created_by": user["id"],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        supabase.table("projects").insert(project_data).execute()
        
        # Add user as project member
        project_membership_data = {
            "id": str(uuid4()),
            "project_id": str(project_id),
            "user_id": user["id"],
            "role": "admin",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        supabase.table("project_members").insert(project_membership_data).execute()
        
        # Create tokens
        permissions = [p.value for p in ROLE_PERMISSIONS[OrganizationRole.OWNER]]
        organizations = [{
            "id": organization["id"],
            "role": OrganizationRole.OWNER.value,
            "projects": []
        }]
        
        access_token = create_access_token(
            user_id=str(user_id),
            email=request.email,
            organizations=organizations,
            permissions=permissions
        )
        refresh_token = create_refresh_token(str(user_id), request.email)
        
        # Build response
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse(
                id=UUID(user["id"]),
                email=user["email"],
                name=user["name"],
                created_at=datetime.fromisoformat(user["created_at"].replace('Z', '+00:00')) if isinstance(user["created_at"], str) else user["created_at"],
                organizations=[
                    OrganizationMembership(
                        organization=OrganizationResponse(
                            id=UUID(organization["id"]),
                            name=organization["name"],
                            slug=organization["slug"],
                            subscription_tier=organization.get("subscription_tier", "free"),
                            created_at=datetime.fromisoformat(organization["created_at"].replace('Z', '+00:00')) if isinstance(organization["created_at"], str) else organization["created_at"]
                        ),
                        role=OrganizationRole.OWNER,
                        joined_at=datetime.fromisoformat(membership_data["created_at"].replace('Z', '+00:00')) if isinstance(membership_data["created_at"], str) else membership_data["created_at"]
                    )
                ]
            ),
            organization=OrganizationResponse(
                id=UUID(organization["id"]),
                name=organization["name"],
                slug=organization["slug"],
                subscription_tier=organization.get("subscription_tier", "free"),
                created_at=datetime.fromisoformat(organization["created_at"].replace('Z', '+00:00')) if isinstance(organization["created_at"], str) else organization["created_at"]
            )
        )
        
    except Exception as e:
        # Rollback on error
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        
        # Get detailed error info
        error_detail = str(e) if str(e) else f"Unknown error of type {type(e).__name__}"
        if hasattr(e, '__dict__'):
            error_detail += f" - Details: {e.__dict__}"
            
        logger.error(f"Signup error: {error_detail}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Try to clean up if user was created
        if 'user_id' in locals():
            try:
                supabase.table("users").delete().eq("id", user_id).execute()
            except:
                pass
                
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating account: {error_detail}"
        )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Authenticate user"""
    supabase_client = get_supabase_client()
    supabase = supabase_client.client
    
    if not supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection not available"
        )
    
    # Get user by email
    user_result = supabase.rpc("get_user_for_login", {
        "p_email": request.email
    }).execute()
    
    if not user_result.data or len(user_result.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    user = user_result.data[0]
    
    # Verify password
    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Get user's organizations
    memberships_result = supabase.table("organization_members").select(
        "*, organizations(*)"
    ).eq("user_id", user["id"]).execute()
    
    organizations = []
    all_permissions = set()
    
    for membership in memberships_result.data:
        org = membership["organizations"]
        role = OrganizationRole(membership["role"])
        
        # Get projects for this organization
        projects_result = supabase.table("projects").select("id").eq(
            "organization_id", org["id"]
        ).execute()
        project_ids = [p["id"] for p in projects_result.data]
        
        organizations.append({
            "id": org["id"],
            "role": role.value,
            "projects": project_ids
        })
        
        # Accumulate permissions
        all_permissions.update(p.value for p in ROLE_PERMISSIONS[role])
    
    # Create tokens
    access_token = create_access_token(
        user_id=user["id"],
        email=user["email"],
        organizations=organizations,
        permissions=list(all_permissions)
    )
    refresh_token = create_refresh_token(user["id"], user["email"])
    
    # Update last login
    supabase.table("users").update({
        "last_login_at": datetime.utcnow().isoformat()
    }).eq("id", user["id"]).execute()
    
    # Get first organization for response
    first_org = memberships_result.data[0]["organizations"] if memberships_result.data else None
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            avatar_url=user.get("avatar_url"),
            created_at=user["created_at"],
            organizations=[
                OrganizationMembership(
                    organization=OrganizationResponse(
                        id=m["organizations"]["id"],
                        name=m["organizations"]["name"],
                        slug=m["organizations"]["slug"],
                        subscription_tier=m["organizations"].get("subscription_tier", "free"),
                        created_at=m["organizations"]["created_at"]
                    ),
                    role=OrganizationRole(m["role"]),
                    joined_at=m["created_at"]
                )
                for m in memberships_result.data
            ]
        ),
        organization=OrganizationResponse(
            id=first_org["id"],
            name=first_org["name"],
            slug=first_org["slug"],
            subscription_tier=first_org.get("subscription_tier", "free"),
            created_at=first_org["created_at"]
        ) if first_org else None
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    """Refresh access token"""
    try:
        # Decode refresh token
        token_data = decode_token(refresh_token)
        
        if token_data.token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        # Get fresh user data and create new access token
        supabase_client = get_supabase_client()
        supabase = supabase_client.client
        
        if not supabase:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection not available"
            )
        
        user_result = supabase.table("users").select("*").eq("id", token_data.sub).single().execute()
        
        if not user_result.data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Re-fetch organizations and permissions
        # (Similar to login logic)
        # ... (abbreviated for brevity)
        
        # For now, return a simple response
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Refresh token endpoint not fully implemented"
        )
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout")
async def logout(current_user = Depends(get_current_user)):
    """Invalidate user session"""
    # In a stateless JWT system, logout is typically handled client-side
    # by removing the token. For server-side invalidation, you would:
    # 1. Add token to a blacklist
    # 2. Or store tokens in database and mark as revoked
    
    return {"message": "Logged out successfully"}


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    request: APIKeyCreate,
    current_user = Depends(get_current_user)
):
    """Create a new API key"""
    # TODO: Verify user has permission to create API keys for the organization
    
    key, key_data = await APIKeyManager.create_api_key(
        organization_id=request.organization_id,  # Get from context
        name=request.name,
        created_by=current_user.id,
        project_id=request.project_id,
        expires_in_days=request.expires_in_days,
        permissions={p.value: True for p in request.permissions}
    )
    
    return APIKeyResponse(
        id=key_data["id"],
        key=key,  # Only shown once!
        name=key_data["name"],
        prefix=key_data["key_prefix"],
        created_at=key_data["created_at"],
        expires_at=key_data.get("expires_at")
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information"""
    supabase_client = get_supabase_client()
    supabase = supabase_client.client
    
    if not supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection not available"
        )
    
    # Get user's organizations
    memberships_result = supabase.table("organization_members").select(
        "*, organizations(*)"
    ).eq("user_id", current_user.id).execute()
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        avatar_url=current_user.avatar_url,
        created_at=current_user.created_at,
        organizations=[
            OrganizationMembership(
                organization=OrganizationResponse(
                    id=m["organizations"]["id"],
                    name=m["organizations"]["name"],
                    slug=m["organizations"]["slug"],
                    subscription_tier=m["organizations"].get("subscription_tier", "free"),
                    created_at=m["organizations"]["created_at"]
                ),
                role=OrganizationRole(m["role"]),
                joined_at=m["created_at"]
            )
            for m in memberships_result.data
        ]
    )
"""
Example router showing how to use Supabase Auth
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from app.core.supabase_auth import (
    get_current_user,
    get_current_user_optional,
    require_mfa,
    get_user_from_supabase,
)

router = APIRouter(
    prefix="/api/supabase",
    tags=["Supabase Auth Examples"],
)


@router.get("/me")
async def get_current_user_info(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current user information from Supabase JWT"""
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "role": user["role"],
        "aal": user["aal"],
        "auth_methods": user["amr"],
        "metadata": user["user_metadata"],
    }


@router.get("/profile")
async def get_user_profile(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed user profile from Supabase"""
    user_details = await get_user_from_supabase(user["user_id"])
    
    if not user_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    return user_details


@router.get("/public")
async def public_endpoint(
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
) -> Dict[str, Any]:
    """Public endpoint that works with or without authentication"""
    if user:
        return {
            "message": f"Hello {user['email']}!",
            "authenticated": True,
        }
    else:
        return {
            "message": "Hello anonymous user!",
            "authenticated": False,
        }


@router.get("/secure")
async def secure_endpoint(
    user: Dict[str, Any] = Depends(require_mfa)
) -> Dict[str, Any]:
    """Endpoint that requires MFA to access"""
    return {
        "message": "This is a highly secure endpoint",
        "user_id": user["user_id"],
        "mfa_verified": True,
    }


@router.post("/migrate-to-supabase")
async def migrate_user_to_supabase(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Example endpoint showing how to migrate existing users to use Supabase auth
    This would typically involve:
    1. Creating a Supabase user if they don't exist
    2. Linking existing data to the Supabase user ID
    3. Migrating user preferences and settings
    """
    # This is just an example - actual implementation would depend on your needs
    logger.info(f"Migrating user {user['email']} to Supabase auth")
    
    return {
        "message": "User migration initiated",
        "user_id": user["user_id"],
        "email": user["email"],
        "next_steps": [
            "Link existing content to Supabase user ID",
            "Migrate user preferences",
            "Update related records",
        ]
    }
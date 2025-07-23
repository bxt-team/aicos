"""
Auth adapter to support both legacy JWT and Supabase auth during migration
"""
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError, jwt
from loguru import logger

from app.core.auth import get_current_user as get_legacy_user
from app.core.supabase_auth import supabase_auth_optional
from app.models.user import User


class AuthAdapter:
    """Adapter to support both authentication methods during migration"""
    
    @staticmethod
    async def get_current_user_hybrid(
        request: Request,
        supabase_user: Optional[Dict[str, Any]] = Depends(supabase_auth_optional),
    ) -> Optional[User]:
        """
        Try Supabase auth first, fall back to legacy auth if needed
        Returns User model for compatibility with existing code
        """
        # First, try Supabase auth
        if supabase_user:
            logger.info(f"Authenticated via Supabase: {supabase_user['email']}")
            # Convert Supabase user to legacy User model
            return User(
                id=supabase_user["user_id"],
                email=supabase_user["email"],
                # Map other fields as needed
                created_at=None,  # Would need to fetch from Supabase
                updated_at=None,
            )
        
        # Fall back to legacy auth
        try:
            # Check if we have a legacy JWT token
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # Try legacy auth
                from app.core.dependencies import get_current_user_dependency
                legacy_user = await get_current_user_dependency(
                    authorization=auth_header
                )
                if legacy_user:
                    logger.info(f"Authenticated via legacy JWT: {legacy_user.email}")
                    return legacy_user
        except Exception as e:
            logger.debug(f"Legacy auth failed: {str(e)}")
        
        # No authentication found
        return None
    
    @staticmethod
    async def require_authenticated_user(
        user: Optional[User] = Depends(get_current_user_hybrid)
    ) -> User:
        """Require an authenticated user from either auth system"""
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    
    @staticmethod
    def create_supabase_compatible_token(user: User) -> str:
        """
        Create a token that mimics Supabase JWT structure for legacy users
        This helps with gradual migration
        """
        from datetime import datetime, timedelta
        from app.core.config import settings
        
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": "authenticated",
            "aal": "aal1",
            "amr": [{"method": "password", "timestamp": int(datetime.now().timestamp())}],
            "session_id": str(user.id),  # Mock session ID
            "iat": datetime.now(),
            "exp": datetime.now() + timedelta(days=7),
            "user_metadata": {},
            "app_metadata": {"provider": "email"},
        }
        
        # Sign with the same secret for now
        token = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm="HS256"
        )
        
        return token


# Dependency functions for gradual migration
get_current_user_hybrid = AuthAdapter.get_current_user_hybrid
require_authenticated_user = AuthAdapter.require_authenticated_user


def migrate_endpoint_to_supabase(legacy_dependency):
    """
    Decorator to migrate endpoints from legacy auth to Supabase auth
    Usage:
    
    @router.get("/endpoint")
    @migrate_endpoint_to_supabase(get_current_user)
    async def my_endpoint(user: User):
        ...
    """
    async def wrapper(
        user: User = Depends(require_authenticated_user)
    ):
        return user
    
    return wrapper
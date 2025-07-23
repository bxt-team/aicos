"""
Supabase Auth middleware for validating Supabase JWTs
"""
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import httpx
from datetime import datetime
import os
from loguru import logger

from app.core.config import settings


class SupabaseAuth(HTTPBearer):
    """Supabase JWT authentication handler"""
    
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        self.supabase_url = settings.SUPABASE_URL
        self.supabase_anon_key = settings.SUPABASE_ANON_KEY
        self.jwt_secret = settings.SUPABASE_JWT_SECRET
        
        if not self.jwt_secret:
            logger.warning("SUPABASE_JWT_SECRET not set - JWT verification will fail")
            raise ValueError("SUPABASE_JWT_SECRET (JWT_SECRET_KEY in .env) is required for JWT verification")
        
    async def __call__(self, request: Request) -> Optional[Dict[str, Any]]:
        """Validate the authorization header and extract user info"""
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        
        if not credentials:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authorization header missing",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None
            
        # Extract and verify the JWT token
        token = credentials.credentials
        
        try:
            # Decode and verify the JWT token
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=["HS256"],
                options={"verify_aud": False}  # Supabase doesn't use audience claim
            )
            
            logger.debug("JWT successfully verified")
            
            # Check if token is expired
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.now():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Extract user information
            user_id = payload.get("sub")
            email = payload.get("email")
            role = payload.get("role", "authenticated")
            aal = payload.get("aal", "aal1")  # Auth Assurance Level for MFA
            amr = payload.get("amr", [])  # Auth methods used
            user_metadata = payload.get("user_metadata", {})
            app_metadata = payload.get("app_metadata", {})
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing user ID",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Return user info
            return {
                "user_id": user_id,
                "email": email,
                "role": role,
                "aal": aal,
                "amr": amr,
                "user_metadata": user_metadata,
                "app_metadata": app_metadata,
                "token": token,
            }
            
        except JWTError as e:
            logger.error(f"JWT validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication error",
            )


class SupabaseAuthOptional(SupabaseAuth):
    """Optional Supabase JWT authentication - doesn't raise error if no token"""
    
    def __init__(self):
        super().__init__(auto_error=False)


# Dependency functions
supabase_auth = SupabaseAuth()
supabase_auth_optional = SupabaseAuthOptional()


async def get_current_user(user_info: Dict[str, Any] = Depends(supabase_auth)) -> Dict[str, Any]:
    """Get the current authenticated user"""
    return user_info


async def get_current_user_optional(
    user_info: Optional[Dict[str, Any]] = Depends(supabase_auth_optional)
) -> Optional[Dict[str, Any]]:
    """Get the current user if authenticated, otherwise None"""
    return user_info


async def require_mfa(user_info: Dict[str, Any] = Depends(supabase_auth)) -> Dict[str, Any]:
    """Require that the user has completed MFA (aal2)"""
    if user_info.get("aal") != "aal2":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Multi-factor authentication required",
        )
    return user_info


async def get_user_from_supabase(user_id: str) -> Optional[Dict[str, Any]]:
    """Fetch user details from Supabase Admin API"""
    try:
        headers = {
            "apikey": settings.SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.SUPABASE_URL}/auth/v1/admin/users/{user_id}",
                headers=headers,
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to fetch user {user_id}: {response.status_code}")
                return None
                
    except Exception as e:
        logger.error(f"Error fetching user from Supabase: {str(e)}")
        return None
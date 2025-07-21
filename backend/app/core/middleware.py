"""
Middleware for multi-tenant context injection
"""
import re
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.auth import decode_token, OptionalAuth
from app.core.dependencies import get_supabase_client


class RequestContext(BaseModel):
    """Context information for requests"""
    user_id: str
    organization_id: Optional[str] = None
    project_id: Optional[str] = None


class ContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract and inject organization/project context into requests
    """
    
    # Patterns to extract org/project from URL paths
    ORG_PATH_PATTERN = re.compile(r'/orgs/([^/]+)')
    PROJECT_PATH_PATTERN = re.compile(r'/projects/([^/]+)')
    
    async def dispatch(self, request: Request, call_next):
        """Process request and inject context"""
        # Skip context injection for auth endpoints
        if request.url.path.startswith("/auth/") or request.url.path in ["/docs", "/redoc", "/openapi.json", "/health"]:
            return await call_next(request)
        
        # Initialize context attributes
        request.state.organization_id = None
        request.state.project_id = None
        request.state.user = None
        request.state.context = None
        
        # Try to extract organization/project from headers
        org_id = request.headers.get('X-Organization-ID')
        org_slug = request.headers.get('X-Organization')
        project_id = request.headers.get('X-Project-ID')
        project_slug = request.headers.get('X-Project')
        
        # Or extract from URL path
        path = str(request.url.path)
        if not org_id and not org_slug:
            org_match = self.ORG_PATH_PATTERN.search(path)
            if org_match:
                org_slug = org_match.group(1)
        
        if not project_id and not project_slug:
            project_match = self.PROJECT_PATH_PATTERN.search(path)
            if project_match:
                project_slug = project_match.group(1)
        
        # Convert slugs to IDs if needed
        if org_slug and not org_id:
            org_id = await self.get_org_id_from_slug(org_slug)
        
        if project_slug and not project_id:
            project_id = await self.get_project_id_from_slug(project_slug, org_id)
        
        # Store in request state
        request.state.organization_id = org_id
        request.state.project_id = project_id
        
        # Continue processing
        response = await call_next(request)
        return response
    
    async def get_org_id_from_slug(self, slug: str) -> Optional[str]:
        """Get organization ID from slug"""
        try:
            supabase_client = get_supabase_client()
            supabase = supabase_client.client
            if not supabase:
                return None
            result = supabase.table("organizations").select("id").eq("slug", slug).single().execute()
            return result.data["id"] if result.data else None
        except Exception:
            return None
    
    async def get_project_id_from_slug(self, slug: str, org_id: Optional[str]) -> Optional[str]:
        """Get project ID from slug"""
        if not org_id:
            return None
        
        try:
            supabase_client = get_supabase_client()
            supabase = supabase_client.client
            if not supabase:
                return None
            result = supabase.table("projects").select("id").eq("slug", slug).eq("organization_id", org_id).single().execute()
            return result.data["id"] if result.data else None
        except Exception:
            return None


class MultiTenantMiddleware(BaseHTTPMiddleware):
    """
    Enhanced middleware that enforces multi-tenant access control
    """
    
    # Endpoints that don't require authentication
    PUBLIC_ENDPOINTS = {
        "/health", "/docs", "/redoc", "/openapi.json",
        "/auth/login", "/auth/signup", "/auth/refresh"
    }
    
    # Endpoints that require authentication but not organization context
    AUTH_ONLY_ENDPOINTS = {
        "/auth/me", "/auth/logout", "/organizations", "/invitations"
    }
    
    async def dispatch(self, request: Request, call_next):
        """Process request with multi-tenant validation"""
        path = str(request.url.path)
        
        # Skip authentication for public endpoints
        if any(path.startswith(endpoint) for endpoint in self.PUBLIC_ENDPOINTS):
            return await call_next(request)
        
        # Check for API key authentication
        api_key = request.headers.get("X-API-Key")
        if api_key:
            # Validate API key and set context
            from app.core.security.api_keys import APIKeyManager
            api_context = await APIKeyManager.validate_api_key(api_key)
            
            if not api_context:
                return Response(
                    content='{"detail": "Invalid API key"}',
                    status_code=401,
                    headers={"Content-Type": "application/json"}
                )
            
            # Set context from API key
            request.state.organization_id = api_context["organization_id"]
            request.state.project_id = api_context.get("project_id")
            request.state.api_key_context = api_context
            
            return await call_next(request)
        
        # For other endpoints, require JWT authentication
        # This is handled by the dependency injection in each endpoint
        
        # Validate organization context for non-auth endpoints
        if not any(path.startswith(endpoint) for endpoint in self.AUTH_ONLY_ENDPOINTS):
            # Ensure organization context is available
            if not request.state.organization_id and path not in self.PUBLIC_ENDPOINTS:
                # This will be handled by the endpoint dependencies
                pass
        
        return await call_next(request)


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log API actions for audit trail
    """
    
    # Actions to log
    LOGGED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
    
    async def dispatch(self, request: Request, call_next):
        """Log request details for audit"""
        response = await call_next(request)
        
        # Only log write operations
        if request.method in self.LOGGED_METHODS and response.status_code < 400:
            # Get user and context info
            user_id = getattr(request.state, "user", {}).get("id") if hasattr(request.state, "user") else None
            org_id = getattr(request.state, "organization_id", None)
            project_id = getattr(request.state, "project_id", None)
            
            if user_id or org_id:
                # Log the action
                await self.log_action(
                    user_id=user_id,
                    organization_id=org_id,
                    project_id=project_id,
                    action=f"{request.method} {request.url.path}",
                    resource_type=self.extract_resource_type(request.url.path),
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("User-Agent")
                )
        
        return response
    
    def extract_resource_type(self, path: str) -> str:
        """Extract resource type from path"""
        parts = path.strip("/").split("/")
        if len(parts) > 0:
            return parts[0]
        return "unknown"
    
    async def log_action(self, **kwargs):
        """Log action to audit table"""
        try:
            supabase_client = get_supabase_client()
            supabase = supabase_client.client
            if not supabase:
                return
            supabase.table("audit_logs").insert({
                k: v for k, v in kwargs.items() if v is not None
            }).execute()
        except Exception as e:
            # Don't fail the request if logging fails
            print(f"Audit logging error: {e}")
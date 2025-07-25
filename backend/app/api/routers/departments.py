from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime
from supabase import create_client, Client
import os

from ...core.supabase_auth import get_current_user
# from ...core.dependencies import get_organization_member  # TODO: Implement this

router = APIRouter(prefix="/api/departments", tags=["departments"])


def get_supabase() -> Client:
    """Get the actual Supabase client."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        raise ValueError("Supabase credentials not configured")
    
    return create_client(url, key)


class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class Department(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    employee_count: Optional[int] = 0


@router.get("", response_model=List[Department])
async def list_departments(
    organization_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List all departments in the organization."""
    supabase = get_supabase()
    
    try:
        # Get departments
        response = supabase.table('departments').select('*').eq(
            'organization_id', str(organization_id)
        ).order('name').execute()
            
        departments = []
        for dept in response.data:
            dept_dict = dict(dept)
            # TODO: Get actual employee count in a separate query
            dept_dict['employee_count'] = 0
            departments.append(Department(**dept_dict))
        return departments
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list departments: {str(e)}"
        )


@router.post("", response_model=Department, status_code=status.HTTP_201_CREATED)
async def create_department(
    organization_id: UUID,
    department: DepartmentCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new department. Requires admin or owner role."""
    # TODO: Implement proper role checking
    # For now, allow any authenticated user to create departments
    
    supabase = get_supabase()
    
    try:
        response = supabase.table('departments').insert({
            'organization_id': str(organization_id),
            'name': department.name,
            'description': department.description
        }).execute()
        
        dept_dict = dict(response.data[0])
        dept_dict['employee_count'] = 0
        return Department(**dept_dict)
    except Exception as e:
        if 'duplicate key' in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A department with this name already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create department: {str(e)}"
        )


@router.get("/{department_id}", response_model=Department)
async def get_department(
    organization_id: UUID,
    department_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get a specific department."""
    supabase = get_supabase()
    
    try:
        response = supabase.table('departments').select('*').eq(
            'id', str(department_id)
        ).eq('organization_id', str(organization_id)).single().execute()
        
        dept_dict = dict(response.data)
        
        # Get employee count
        count_response = supabase.table('employees').select(
            'id', count='exact'
        ).eq('department_id', str(department_id)).execute()
        
        dept_dict['employee_count'] = count_response.count or 0
        return Department(**dept_dict)
    except Exception as e:
        if 'No rows found' in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get department: {str(e)}"
        )


@router.patch("/{department_id}", response_model=Department)
async def update_department(
    organization_id: UUID,
    department_id: UUID,
    department: DepartmentUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update a department. Requires admin or owner role."""
    # TODO: Implement proper role checking
    # For now, allow any authenticated user to update departments
    
    supabase = get_supabase()
    
    update_data = {}
    if department.name is not None:
        update_data['name'] = department.name
    if department.description is not None:
        update_data['description'] = department.description
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    try:
        response = supabase.table('departments').update(update_data).eq(
            'id', str(department_id)
        ).eq('organization_id', str(organization_id)).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found"
            )
        
        dept_dict = dict(response.data[0])
        dept_dict['employee_count'] = 0
        return Department(**dept_dict)
    except HTTPException:
        raise
    except Exception as e:
        if 'duplicate key' in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A department with this name already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update department: {str(e)}"
        )


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    organization_id: UUID,
    department_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a department. Requires admin or owner role."""
    # TODO: Implement proper role checking
    # For now, allow any authenticated user to delete departments
    
    supabase = get_supabase()
    
    try:
        # Check if department has employees
        count_response = supabase.table('employees').select(
            'id', count='exact'
        ).eq('department_id', str(department_id)).execute()
        
        if count_response.count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete department with employees. Please reassign or remove employees first."
            )
        
        response = supabase.table('departments').delete().eq(
            'id', str(department_id)
        ).eq('organization_id', str(organization_id)).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete department: {str(e)}"
        )
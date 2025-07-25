from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from supabase import create_client, Client
import os

from ...core.supabase_auth import get_current_user
# from ...core.dependencies import get_organization_member  # TODO: Implement this

router = APIRouter(prefix="/api/employees", tags=["employees"])


def get_supabase() -> Client:
    """Get the actual Supabase client."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        raise ValueError("Supabase credentials not configured")
    
    return create_client(url, key)


class EmployeeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    department_id: Optional[UUID] = None
    role: Optional[str] = Field(None, max_length=100)
    user_id: Optional[UUID] = None  # Link to existing user account


class EmployeeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    department_id: Optional[UUID] = None
    role: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class Employee(BaseModel):
    id: UUID
    organization_id: UUID
    user_id: Optional[UUID]
    department_id: Optional[UUID]
    name: str
    email: str
    role: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    department_name: Optional[str] = None


@router.get("", response_model=List[Employee])
async def list_employees(
    organization_id: UUID,
    department_id: Optional[UUID] = None,
    is_active: Optional[bool] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List all employees in the organization."""
    supabase = get_supabase()
    
    try:
        query = supabase.table('employees').select(
            '*, departments!left(name)'
        ).eq('organization_id', str(organization_id))
        
        if department_id:
            query = query.eq('department_id', str(department_id))
        if is_active is not None:
            query = query.eq('is_active', is_active)
        
        response = query.order('name').execute()
        
        employees = []
        for emp in response.data:
            emp_dict = dict(emp)
            if emp.get('departments'):
                emp_dict['department_name'] = emp['departments']['name']
                del emp_dict['departments']
            employees.append(Employee(**emp_dict))
        
        return employees
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list employees: {str(e)}"
        )


@router.post("", response_model=Employee, status_code=status.HTTP_201_CREATED)
async def create_employee(
    organization_id: UUID,
    employee: EmployeeCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new employee. Requires admin or owner role."""
    # TODO: Implement proper role checking
    # For now, allow any authenticated user to create employees
    
    supabase = get_supabase()
    
    # Validate department if provided
    if employee.department_id:
        try:
            dept_response = supabase.table('departments').select('id').eq(
                'id', str(employee.department_id)
            ).eq('organization_id', str(organization_id)).single().execute()
        except:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found"
            )
    
    # Validate user if provided
    if employee.user_id:
        try:
            user_response = supabase.table('users').select('id').eq(
                'id', str(employee.user_id)
            ).single().execute()
        except:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
    
    try:
        employee_data = {
            'organization_id': str(organization_id),
            'name': employee.name,
            'email': employee.email,
            'role': employee.role
        }
        
        if employee.department_id:
            employee_data['department_id'] = str(employee.department_id)
        if employee.user_id:
            employee_data['user_id'] = str(employee.user_id)
        
        response = supabase.table('employees').insert(employee_data).execute()
        
        # Get with department name
        created_id = response.data[0]['id']
        emp_response = supabase.table('employees').select(
            '*, departments!left(name)'
        ).eq('id', created_id).single().execute()
        
        emp_dict = dict(emp_response.data)
        if emp_dict.get('departments'):
            emp_dict['department_name'] = emp_dict['departments']['name']
            del emp_dict['departments']
        
        return Employee(**emp_dict)
    except Exception as e:
        if 'duplicate key' in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An employee with this email already exists in the organization"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create employee: {str(e)}"
        )


@router.get("/{employee_id}", response_model=Employee)
async def get_employee(
    organization_id: UUID,
    employee_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get a specific employee."""
    supabase = get_supabase()
    
    try:
        response = supabase.table('employees').select(
            '*, departments!left(name)'
        ).eq('id', str(employee_id)).eq(
            'organization_id', str(organization_id)
        ).single().execute()
        
        emp_dict = dict(response.data)
        if emp_dict.get('departments'):
            emp_dict['department_name'] = emp_dict['departments']['name']
            del emp_dict['departments']
        
        return Employee(**emp_dict)
    except Exception as e:
        if 'No rows found' in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get employee: {str(e)}"
        )


@router.patch("/{employee_id}", response_model=Employee)
async def update_employee(
    organization_id: UUID,
    employee_id: UUID,
    employee: EmployeeUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update an employee. Requires admin or owner role."""
    # TODO: Implement proper role checking
    # For now, allow any authenticated user to update employees
    
    supabase = get_supabase()
    
    # Validate department if provided
    if employee.department_id is not None:
        try:
            dept_response = supabase.table('departments').select('id').eq(
                'id', str(employee.department_id)
            ).eq('organization_id', str(organization_id)).single().execute()
        except:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found"
            )
    
    update_data = {}
    if employee.name is not None:
        update_data['name'] = employee.name
    if employee.email is not None:
        update_data['email'] = employee.email
    if employee.department_id is not None:
        update_data['department_id'] = str(employee.department_id)
    if employee.role is not None:
        update_data['role'] = employee.role
    if employee.is_active is not None:
        update_data['is_active'] = employee.is_active
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    try:
        response = supabase.table('employees').update(update_data).eq(
            'id', str(employee_id)
        ).eq('organization_id', str(organization_id)).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
        
        # Get with department name
        emp_response = supabase.table('employees').select(
            '*, departments!left(name)'
        ).eq('id', str(employee_id)).single().execute()
        
        emp_dict = dict(emp_response.data)
        if emp_dict.get('departments'):
            emp_dict['department_name'] = emp_dict['departments']['name']
            del emp_dict['departments']
        
        return Employee(**emp_dict)
    except HTTPException:
        raise
    except Exception as e:
        if 'duplicate key' in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An employee with this email already exists in the organization"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update employee: {str(e)}"
        )


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    organization_id: UUID,
    employee_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete an employee. Requires admin or owner role."""
    # TODO: Implement proper role checking
    # For now, allow any authenticated user to delete employees
    
    supabase = get_supabase()
    
    try:
        response = supabase.table('employees').delete().eq(
            'id', str(employee_id)
        ).eq('organization_id', str(organization_id)).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete employee: {str(e)}"
        )
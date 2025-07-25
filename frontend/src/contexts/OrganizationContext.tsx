import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useSupabaseAuth } from './SupabaseAuthContext';
import { apiService } from '../services/api';

interface Organization {
  id: string;
  name: string;
  description?: string;
  website?: string;
  created_at: string;
  updated_at: string;
  subscription_tier: string;
  owner_id: string;
}

interface OrganizationMember {
  id: string;
  user_id: string;
  organization_id: string;
  role: 'owner' | 'admin' | 'member' | 'viewer';
  joined_at: string;
  email: string;
  name?: string;
  is_current_user?: boolean;
}

interface OrganizationContextType {
  organizations: Organization[];
  currentOrganization: Organization | null;
  members: OrganizationMember[];
  currentUserRole: 'owner' | 'admin' | 'member' | 'viewer' | null;
  loading: boolean;
  error: string | null;
  
  // Actions
  setCurrentOrganization: (org: Organization | null) => void;
  loadOrganizations: () => Promise<void>;
  createOrganization: (data: { name: string; description?: string }) => Promise<Organization>;
  updateOrganization: (id: string, data: Partial<Organization>) => Promise<void>;
  deleteOrganization: (id: string) => Promise<void>;
  loadMembers: () => Promise<void>;
  inviteMember: (email: string, role: string) => Promise<void>;
  removeMember: (memberId: string) => Promise<void>;
  updateMemberRole: (memberId: string, role: string) => Promise<void>;
  createProject: (data: { name: string; description?: string; organization_id: string }) => Promise<any>;
}

const OrganizationContext = createContext<OrganizationContextType | undefined>(undefined);

export const useOrganization = () => {
  const context = useContext(OrganizationContext);
  if (!context) {
    throw new Error('useOrganization must be used within OrganizationProvider');
  }
  return context;
};

interface OrganizationProviderProps {
  children: ReactNode;
}

export const OrganizationProvider: React.FC<OrganizationProviderProps> = ({ children }) => {
  const { user } = useSupabaseAuth();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [currentOrganization, setCurrentOrganization] = useState<Organization | null>(null);
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingPromise, setLoadingPromise] = useState<Promise<void> | null>(null);

  // Load organizations when user changes
  useEffect(() => {
    if (user) {
      loadOrganizations();
    } else {
      setOrganizations([]);
      setCurrentOrganization(null);
      setMembers([]);
    }
  }, [user]);

  // Load current organization from localStorage
  useEffect(() => {
    const orgId = localStorage.getItem('currentOrganizationId');
    if (orgId && organizations.length > 0) {
      const org = organizations.find(o => o.id === orgId);
      if (org) {
        setCurrentOrganization(org);
      }
    } else if (organizations.length > 0 && !currentOrganization) {
      // Set first organization as current if none selected
      setCurrentOrganization(organizations[0]);
      localStorage.setItem('currentOrganizationId', organizations[0].id);
    }
  }, [organizations]);

  // Load members when current organization changes
  useEffect(() => {
    if (currentOrganization) {
      loadMembers();
    } else {
      setMembers([]);
    }
  }, [currentOrganization]);

  const loadOrganizations = async () => {
    if (!user) return;
    
    // Return existing promise if already loading
    if (loadingPromise) {
      return loadingPromise;
    }
    
    const promise = (async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await apiService.organizations.list();
        const orgs = response.data.organizations || [];
        setOrganizations(orgs);
      } catch (err: any) {
        console.error('Failed to load organizations:', err);
        setError(err.response?.data?.detail || 'Failed to load organizations');
      } finally {
        setLoading(false);
        setLoadingPromise(null);
      }
    })();
    
    setLoadingPromise(promise);
    return promise;
  };

  const createOrganization = async (data: { name: string; description?: string }) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiService.organizations.create(data);
      const newOrg = response.data.organization;
      
      // Update the organizations list
      const updatedOrgs = [...organizations, newOrg];
      setOrganizations(updatedOrgs);
      
      // Automatically set as current organization
      setCurrentOrganization(newOrg);
      localStorage.setItem('currentOrganizationId', newOrg.id);
      
      return newOrg;
    } catch (err: any) {
      console.error('Failed to create organization:', err);
      setError(err.response?.data?.detail || 'Failed to create organization');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const updateOrganization = async (id: string, data: Partial<Organization>) => {
    setLoading(true);
    setError(null);
    
    try {
      await apiService.organizations.update(id, data);
      
      // Update local state
      setOrganizations(orgs => 
        orgs.map(org => org.id === id ? { ...org, ...data } : org)
      );
      
      if (currentOrganization?.id === id) {
        setCurrentOrganization({ ...currentOrganization, ...data });
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update organization');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const deleteOrganization = async (id: string) => {
    setLoading(true);
    setError(null);
    
    try {
      await apiService.organizations.delete(id);
      
      // Update local state
      setOrganizations(orgs => orgs.filter(org => org.id !== id));
      
      if (currentOrganization?.id === id) {
        const remainingOrgs = organizations.filter(org => org.id !== id);
        if (remainingOrgs.length > 0) {
          setCurrentOrganization(remainingOrgs[0]);
          localStorage.setItem('currentOrganizationId', remainingOrgs[0].id);
        } else {
          setCurrentOrganization(null);
          localStorage.removeItem('currentOrganizationId');
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete organization');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const loadMembers = async () => {
    if (!currentOrganization) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiService.organizations.getMembers(currentOrganization.id);
      const membersList = response.data.members || [];
      setMembers(membersList);
    } catch (err: any) {
      console.error('Failed to load members:', err);
      setError(err.response?.data?.detail || 'Failed to load members');
    } finally {
      setLoading(false);
    }
  };

  const inviteMember = async (email: string, role: string) => {
    if (!currentOrganization) throw new Error('No organization selected');
    
    setLoading(true);
    setError(null);
    
    try {
      await apiService.organizations.inviteMember(currentOrganization.id, { email, role });
      await loadMembers(); // Reload members list
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to invite member');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const removeMember = async (memberId: string) => {
    if (!currentOrganization) throw new Error('No organization selected');
    
    setLoading(true);
    setError(null);
    
    try {
      await apiService.organizations.removeMember(currentOrganization.id, memberId);
      await loadMembers(); // Reload members list
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to remove member');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const updateMemberRole = async (memberId: string, role: string) => {
    if (!currentOrganization) throw new Error('No organization selected');
    
    setLoading(true);
    setError(null);
    
    try {
      await apiService.organizations.updateMemberRole(currentOrganization.id, memberId, { role });
      await loadMembers(); // Reload members list
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update member role');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const createProject = async (data: { name: string; description?: string; organization_id: string }) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiService.projects.create(data);
      return response.data.project;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create project');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const handleSetCurrentOrganization = (org: Organization | null) => {
    setCurrentOrganization(org);
    if (org) {
      localStorage.setItem('currentOrganizationId', org.id);
    } else {
      localStorage.removeItem('currentOrganizationId');
    }
  };

  // Compute current user's role in the current organization
  const currentUserRole = React.useMemo(() => {
    if (!currentOrganization || !user) return null;
    
    // Check if user is the owner
    if (currentOrganization.owner_id === user.id) {
      return 'owner';
    }
    
    // Find user in members list
    const currentMember = members.find(member => member.user_id === user.id);
    return currentMember?.role || null;
  }, [currentOrganization, user, members]);

  const value: OrganizationContextType = {
    organizations,
    currentOrganization,
    members,
    currentUserRole,
    loading,
    error,
    setCurrentOrganization: handleSetCurrentOrganization,
    loadOrganizations,
    createOrganization,
    updateOrganization,
    deleteOrganization,
    loadMembers,
    inviteMember,
    removeMember,
    updateMemberRole,
    createProject,
  };

  return (
    <OrganizationContext.Provider value={value}>
      {children}
    </OrganizationContext.Provider>
  );
};
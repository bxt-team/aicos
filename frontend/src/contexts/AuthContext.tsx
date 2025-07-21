import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import axios from 'axios';

interface OrganizationMembership {
  organization?: Organization;
  role: string;
  joined_at?: string;
}

interface User {
  id: string;
  email: string;
  name: string;
  default_organization_id?: string;
  avatar_url?: string;
  created_at: string;
  organizations?: (Organization | OrganizationMembership)[];
}

export interface Organization {
  id: string;
  name: string;
  role: string;
  created_at: string;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  organization_id: string;
  role?: string;
  created_at: string;
}

interface AuthContextType {
  user: User | null;
  accessToken: string | null;
  currentOrganization: Organization | null;
  currentProject: Project | null;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string, rememberMe?: boolean) => Promise<void>;
  signup: (email: string, password: string, name: string, organizationName: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  setCurrentOrganization: (org: Organization | null) => void;
  setCurrentProject: (project: Project | null) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [currentOrganization, setCurrentOrganization] = useState<Organization | null>(null);
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load token from localStorage or sessionStorage on mount
  useEffect(() => {
    const loadAuthState = async () => {
      try {
        // Check localStorage first (remember me), then sessionStorage
        const token = localStorage.getItem('accessToken') || sessionStorage.getItem('accessToken');
        
        if (token) {
          setAccessToken(token);
          await fetchUserInfo(token);
        } else {
          setIsLoading(false);
        }
      } catch (error) {
        console.error('Failed to restore auth state:', error);
        setIsLoading(false);
      }
    };
    
    loadAuthState();
  }, []);

  // Set axios default headers when token changes
  useEffect(() => {
    if (accessToken) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [accessToken]);

  // Set organization/project headers
  useEffect(() => {
    if (currentOrganization) {
      axios.defaults.headers.common['X-Organization-ID'] = currentOrganization.id;
    } else {
      delete axios.defaults.headers.common['X-Organization-ID'];
    }

    if (currentProject) {
      axios.defaults.headers.common['X-Project-ID'] = currentProject.id;
    } else {
      delete axios.defaults.headers.common['X-Project-ID'];
    }
  }, [currentOrganization, currentProject]);

  const fetchUserInfo = async (token: string) => {
    try {
      const baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      console.log('AuthContext: Fetching user info from:', `${baseURL}/auth/me`);
      const response = await axios.get(`${baseURL}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      console.log('AuthContext: User info response:', response.data);
      setUser(response.data);
      
      // Restore saved organization or set default
      const savedOrgId = localStorage.getItem('currentOrganizationId');
      if (savedOrgId && response.data.organizations) {
        const savedOrgMembership = response.data.organizations.find((membership: any) => {
          const org = membership.organization || membership;
          return org.id === savedOrgId;
        });
        if (savedOrgMembership) {
          const org = savedOrgMembership.organization || savedOrgMembership;
          setCurrentOrganization({
            id: org.id,
            name: org.name,
            role: savedOrgMembership.role || org.role,
            created_at: org.created_at
          });
        } else if (response.data.organizations.length > 0) {
          const firstOrgMembership = response.data.organizations[0];
          const org = firstOrgMembership.organization || firstOrgMembership;
          setCurrentOrganization({
            id: org.id,
            name: org.name,
            role: firstOrgMembership.role || org.role,
            created_at: org.created_at
          });
        }
      } else if (response.data.organizations && response.data.organizations.length > 0) {
        const firstOrgMembership = response.data.organizations[0];
        const org = firstOrgMembership.organization || firstOrgMembership;
        setCurrentOrganization({
          id: org.id,
          name: org.name,
          role: firstOrgMembership.role || org.role,
          created_at: org.created_at
        });
      }
    } catch (err) {
      console.error('Failed to fetch user info:', err);
      setAccessToken(null);
      // Clear from both storages
      localStorage.removeItem('accessToken');
      sessionStorage.removeItem('accessToken');
      localStorage.removeItem('currentOrganizationId');
      localStorage.removeItem('currentProjectId');
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string, rememberMe: boolean = true) => {
    setError(null);
    try {
      const baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await axios.post(`${baseURL}/auth/login`, { email, password });
      console.log('AuthContext: Login response:', response.data);
      const { access_token, user: userData } = response.data;
      
      setAccessToken(access_token);
      setUser(userData);
      
      // Store token based on remember me preference
      if (rememberMe) {
        localStorage.setItem('accessToken', access_token);
        // Clear from sessionStorage if it exists
        sessionStorage.removeItem('accessToken');
      } else {
        sessionStorage.setItem('accessToken', access_token);
        // Clear from localStorage if it exists
        localStorage.removeItem('accessToken');
      }
      
      // Set default organization
      if (userData.organizations && userData.organizations.length > 0) {
        // Handle both nested and flat organization structure
        const firstOrgMembership = userData.organizations[0];
        const org = firstOrgMembership.organization || firstOrgMembership;
        handleSetCurrentOrganization({
          id: org.id,
          name: org.name,
          role: firstOrgMembership.role || org.role,
          created_at: org.created_at
        });
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Login failed';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  };

  const signup = async (email: string, password: string, name: string, organizationName: string) => {
    setError(null);
    try {
      const baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await axios.post(`${baseURL}/auth/signup`, {
        email,
        password,
        name,
        organization_name: organizationName
      });
      
      const { access_token, user: userData, organization } = response.data;
      
      setAccessToken(access_token);
      setUser(userData);
      // Default to remembering signup tokens
      localStorage.setItem('accessToken', access_token);
      
      // Set the new organization as current
      if (userData.organizations && userData.organizations.length > 0) {
        // Handle the organization structure from signup response
        const firstOrgMembership = userData.organizations[0];
        const org = firstOrgMembership.organization || organization || firstOrgMembership;
        handleSetCurrentOrganization({
          id: org.id,
          name: org.name,
          role: firstOrgMembership.role || 'owner',
          created_at: org.created_at
        });
      } else if (organization) {
        // Fallback to the organization object directly
        handleSetCurrentOrganization({
          id: organization.id,
          name: organization.name,
          role: 'owner',
          created_at: organization.created_at
        });
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Signup failed';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  };

  const logout = async () => {
    try {
      const baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      await axios.post(`${baseURL}/auth/logout`);
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      setUser(null);
      setAccessToken(null);
      setCurrentOrganization(null);
      setCurrentProject(null);
      // Clear from both storages
      localStorage.removeItem('accessToken');
      sessionStorage.removeItem('accessToken');
      localStorage.removeItem('currentOrganizationId');
      localStorage.removeItem('currentProjectId');
      delete axios.defaults.headers.common['Authorization'];
      delete axios.defaults.headers.common['X-Organization-ID'];
      delete axios.defaults.headers.common['X-Project-ID'];
    }
  };

  const refreshToken = async () => {
    try {
      const baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await axios.post(`${baseURL}/auth/refresh`);
      const { access_token } = response.data;
      setAccessToken(access_token);
      // Store in the same storage type as current token
      const hasLocalStorage = localStorage.getItem('accessToken') !== null;
      if (hasLocalStorage) {
        localStorage.setItem('accessToken', access_token);
      } else {
        sessionStorage.setItem('accessToken', access_token);
      }
    } catch (err) {
      console.error('Token refresh failed:', err);
      logout();
    }
  };

  // Wrapped setters to persist to localStorage
  const handleSetCurrentOrganization = (org: Organization | null) => {
    setCurrentOrganization(org);
    if (org) {
      localStorage.setItem('currentOrganizationId', org.id);
    } else {
      localStorage.removeItem('currentOrganizationId');
    }
  };

  const handleSetCurrentProject = (project: Project | null) => {
    setCurrentProject(project);
    if (project) {
      localStorage.setItem('currentProjectId', project.id);
    } else {
      localStorage.removeItem('currentProjectId');
    }
  };

  const value = {
    user,
    accessToken,
    currentOrganization,
    currentProject,
    isLoading,
    error,
    login,
    signup,
    logout,
    refreshToken,
    setCurrentOrganization: handleSetCurrentOrganization,
    setCurrentProject: handleSetCurrentProject
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
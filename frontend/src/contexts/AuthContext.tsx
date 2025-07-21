import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import axios from 'axios';

interface User {
  id: string;
  email: string;
  name: string;
  default_organization_id: string;
  created_at: string;
  organizations?: Organization[];
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
  login: (email: string, password: string) => Promise<void>;
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

  // Load token from localStorage on mount
  useEffect(() => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      setAccessToken(token);
      fetchUserInfo(token);
    } else {
      setIsLoading(false);
    }
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
      const response = await axios.get('/auth/me', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(response.data);
      
      // Set default organization if available
      if (response.data.organizations && response.data.organizations.length > 0) {
        setCurrentOrganization(response.data.organizations[0]);
      }
    } catch (err) {
      console.error('Failed to fetch user info:', err);
      setAccessToken(null);
      localStorage.removeItem('accessToken');
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    setError(null);
    try {
      const response = await axios.post('/auth/login', { email, password });
      const { access_token, user: userData } = response.data;
      
      setAccessToken(access_token);
      setUser(userData);
      localStorage.setItem('accessToken', access_token);
      
      // Set default organization
      if (userData.organizations && userData.organizations.length > 0) {
        setCurrentOrganization(userData.organizations[0]);
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
      const response = await axios.post('/auth/signup', {
        email,
        password,
        name,
        organization_name: organizationName
      });
      
      const { access_token, user: userData, organization } = response.data;
      
      setAccessToken(access_token);
      setUser(userData);
      localStorage.setItem('accessToken', access_token);
      
      // Set the new organization as current
      setCurrentOrganization({
        id: organization.id,
        name: organization.name,
        role: 'owner',
        created_at: organization.created_at
      });
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Signup failed';
      setError(errorMessage);
      throw new Error(errorMessage);
    }
  };

  const logout = async () => {
    try {
      await axios.post('/auth/logout');
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      setUser(null);
      setAccessToken(null);
      setCurrentOrganization(null);
      setCurrentProject(null);
      localStorage.removeItem('accessToken');
      delete axios.defaults.headers.common['Authorization'];
      delete axios.defaults.headers.common['X-Organization-ID'];
      delete axios.defaults.headers.common['X-Project-ID'];
    }
  };

  const refreshToken = async () => {
    try {
      const response = await axios.post('/auth/refresh');
      const { access_token } = response.data;
      setAccessToken(access_token);
      localStorage.setItem('accessToken', access_token);
    } catch (err) {
      console.error('Token refresh failed:', err);
      logout();
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
    setCurrentOrganization,
    setCurrentProject
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
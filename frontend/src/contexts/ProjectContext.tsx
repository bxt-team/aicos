import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { useOrganization } from './OrganizationContext';
import { apiService } from '../services/api';

interface Project {
  id: string;
  name: string;
  description?: string;
  organization_id: string;
  created_at: string;
  updated_at: string;
}

interface ProjectContextType {
  projects: Project[];
  currentProject: Project | null;
  loading: boolean;
  error: string | null;
  
  // Actions
  setCurrentProject: (project: Project | null) => void;
  loadProjects: () => Promise<void>;
  createProject: (data: { name: string; description?: string }) => Promise<Project>;
  updateProject: (id: string, data: Partial<Project>) => Promise<void>;
  deleteProject: (id: string) => Promise<void>;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export const useProject = () => {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error('useProject must be used within ProjectProvider');
  }
  return context;
};

interface ProjectProviderProps {
  children: ReactNode;
}

// Cache for projects data
const projectsCache = new Map<string, { data: Project[], timestamp: number }>();
const CACHE_DURATION = 2 * 60 * 1000; // 2 minutes

export const ProjectProvider: React.FC<ProjectProviderProps> = ({ children }) => {
  const { currentOrganization } = useOrganization();
  const [projects, setProjects] = useState<Project[]>([]);
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingPromise, setLoadingPromise] = useState<Promise<void> | null>(null);

  // Load projects when organization changes
  useEffect(() => {
    if (currentOrganization) {
      loadProjects();
    } else {
      setProjects([]);
      setCurrentProject(null);
    }
  }, [currentOrganization]);

  // Load current project from localStorage
  useEffect(() => {
    const projectId = localStorage.getItem('currentProjectId');
    if (projectId && projects.length > 0) {
      const project = projects.find(p => p.id === projectId);
      if (project) {
        setCurrentProject(project);
      }
    } else if (projects.length > 0 && !currentProject) {
      // Set first project as current if none selected
      handleSetCurrentProject(projects[0]);
    }
  }, [projects]);

  const loadProjects = useCallback(async () => {
    if (!currentOrganization) return;
    
    // Return existing promise if already loading
    if (loadingPromise) {
      return loadingPromise;
    }
    
    // Check cache first
    const cacheKey = currentOrganization.id;
    const cached = projectsCache.get(cacheKey);
    const now = Date.now();
    
    if (cached && (now - cached.timestamp) < CACHE_DURATION) {
      setProjects(cached.data);
      return;
    }
    
    const promise = (async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await apiService.projects.list(currentOrganization.id);
        const projectList = response.data.projects || [];
        setProjects(projectList);
        
        // Update cache
        projectsCache.set(cacheKey, { data: projectList, timestamp: now });
      } catch (error) {
        console.error('Failed to load projects:', error);
        setError('Failed to load projects');
      } finally {
        setLoading(false);
        setLoadingPromise(null);
      }
    })();
    
    setLoadingPromise(promise);
    return promise;
  }, [currentOrganization, loadingPromise]);

  const createProject = async (data: { name: string; description?: string }) => {
    if (!currentOrganization) throw new Error('No organization selected');
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiService.projects.create({
        ...data,
        organization_id: currentOrganization.id
      });
      
      const newProject = response.data.project;
      setProjects([...projects, newProject]);
      handleSetCurrentProject(newProject);
      
      // Invalidate cache
      projectsCache.delete(currentOrganization.id);
      
      return newProject;
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create project');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const updateProject = async (id: string, data: Partial<Project>) => {
    setLoading(true);
    setError(null);
    
    try {
      await apiService.projects.update(id, data);
      
      // Update local state
      setProjects(projs => 
        projs.map(proj => proj.id === id ? { ...proj, ...data } : proj)
      );
      
      if (currentProject?.id === id) {
        setCurrentProject({ ...currentProject, ...data });
      }
      
      // Invalidate cache
      if (currentOrganization) {
        projectsCache.delete(currentOrganization.id);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update project');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const deleteProject = async (id: string) => {
    setLoading(true);
    setError(null);
    
    try {
      await apiService.projects.delete(id);
      
      // Update local state
      setProjects(projs => projs.filter(proj => proj.id !== id));
      
      if (currentProject?.id === id) {
        const remainingProjects = projects.filter(proj => proj.id !== id);
        if (remainingProjects.length > 0) {
          handleSetCurrentProject(remainingProjects[0]);
        } else {
          handleSetCurrentProject(null);
        }
      }
      
      // Invalidate cache
      if (currentOrganization) {
        projectsCache.delete(currentOrganization.id);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete project');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const handleSetCurrentProject = (project: Project | null) => {
    setCurrentProject(project);
    if (project) {
      localStorage.setItem('currentProjectId', project.id);
    } else {
      localStorage.removeItem('currentProjectId');
    }
    
    // Dispatch custom event for other components to listen to
    window.dispatchEvent(new CustomEvent('projectChanged', { detail: project }));
  };

  const value: ProjectContextType = {
    projects,
    currentProject,
    loading,
    error,
    setCurrentProject: handleSetCurrentProject,
    loadProjects,
    createProject,
    updateProject,
    deleteProject,
  };

  return (
    <ProjectContext.Provider value={value}>
      {children}
    </ProjectContext.Provider>
  );
};
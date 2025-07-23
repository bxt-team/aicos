import React, { useEffect, useState } from 'react';
import { useOrganization } from '../contexts/OrganizationContext';
import { useSupabaseAuth } from '../contexts/SupabaseAuthContext';
import OnboardingWizard from './OnboardingWizard';
import LoadingScreen from './LoadingScreen';
import { apiService } from '../services/api';

interface OnboardingCheckProps {
  children: React.ReactNode;
}

const OnboardingCheck: React.FC<OnboardingCheckProps> = ({ children }) => {
  const { user } = useSupabaseAuth();
  const { organizations, currentOrganization, loadOrganizations, loading: orgLoading } = useOrganization();
  const [currentProject, setCurrentProject] = useState<any>(null);
  const [loadingProjects, setLoadingProjects] = useState(true);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [onboardingInProgress, setOnboardingInProgress] = useState(false);

  useEffect(() => {
    const checkOnboardingStatus = async () => {
      console.log('OnboardingCheck: Starting check', { user: !!user, orgLoading, organizations: organizations.length });
      
      if (!user || orgLoading) {
        console.log('OnboardingCheck: Waiting for user or orgs to load');
        setIsInitializing(false);
        setLoadingProjects(false);
        return;
      }

      try {
        // Don't interrupt onboarding if it's in progress
        if (onboardingInProgress) {
          console.log('OnboardingCheck: Onboarding in progress, not interrupting');
          setIsInitializing(false);
          setLoadingProjects(false);
          return;
        }
        
        // Check if user has any organizations
        if (organizations.length === 0) {
          console.log('OnboardingCheck: No organizations found, showing onboarding');
          setShowOnboarding(true);
          setOnboardingInProgress(true);
          setIsInitializing(false);
          setLoadingProjects(false);
          return;
        }

        // Check if current organization has projects
        if (currentOrganization) {
          console.log('OnboardingCheck: Checking projects for org', currentOrganization.id);
          setLoadingProjects(true);
          try {
            const response = await apiService.projects.list(currentOrganization.id);
            const projects = response.data.projects || [];
            console.log('OnboardingCheck: Found projects', projects.length);
            
            if (projects.length > 0) {
              // Set first project as current if none selected
              const savedProjectId = localStorage.getItem('currentProjectId');
              const project = projects.find((p: any) => p.id === savedProjectId) || projects[0];
              setCurrentProject(project);
              localStorage.setItem('currentProjectId', project.id);
              setShowOnboarding(false);
            } else {
              // Organization exists but no projects
              console.log('OnboardingCheck: No projects found, showing onboarding');
              setShowOnboarding(true);
              setOnboardingInProgress(true);
            }
          } catch (error) {
            console.error('Failed to load projects:', error);
            setShowOnboarding(false); // Don't block on error
          } finally {
            setLoadingProjects(false);
          }
        } else {
          console.log('OnboardingCheck: No current organization set');
          setLoadingProjects(false);
        }
      } catch (error) {
        console.error('Failed to check onboarding status:', error);
        setShowOnboarding(false); // Don't block on error
      } finally {
        setIsInitializing(false);
      }
    };

    checkOnboardingStatus();
  }, [user, orgLoading, organizations.length, currentOrganization, onboardingInProgress]);

  const handleOnboardingComplete = () => {
    console.log('OnboardingCheck: Onboarding completed');
    setShowOnboarding(false);
    setOnboardingInProgress(false);
    // Don't reload - just let the app continue normally
    // The project ID should already be set in localStorage by the wizard
  };

  console.log('OnboardingCheck: Render state', { isInitializing, loadingProjects, showOnboarding, orgLoading });
  
  if (isInitializing || loadingProjects || orgLoading) {
    return <LoadingScreen />;
  }

  if (showOnboarding) {
    return <OnboardingWizard onComplete={handleOnboardingComplete} />;
  }

  return <>{children}</>;
};

export default OnboardingCheck;
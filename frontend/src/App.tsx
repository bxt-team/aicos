import React from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { MenuProvider } from './contexts/MenuContext';
import { SupabaseAuthProvider } from './contexts/SupabaseAuthContext';
import { OrganizationProvider } from './contexts/OrganizationContext';
import { ProjectProvider } from './contexts/ProjectContext';
import { ThemeProvider } from './contexts/ThemeContext';
import './App.css';
import './i18n/i18n';
import LoadingScreen from './components/LoadingScreen';
import { useLoadingScreen } from './hooks/useLoadingScreen';
import ContentGenerator from './components/ContentGenerator';
import ContentViewer from './components/ContentViewer';
import QAInterface from './components/QAInterface';
import AffirmationsInterface from './components/AffirmationsInterface';
import VisualPostsInterface from './components/VisualPostsInterface';
import InstagramPostsInterface from './components/InstagramPostsInterface';
import InstagramPostingInterface from './components/InstagramPostingInterface';
import InstagramAnalyzerInterface from './components/InstagramAnalyzerInterface';
import WorkflowManagement from './components/WorkflowManagement';
import PostCompositionInterface from './components/PostCompositionInterface';
import VideoGenerationInterface from './components/VideoGenerationInterface';
import InstagramReelInterface from './components/InstagramReelInterface';
import AppTestInterface from './components/AppTestInterface';
import VoiceOverInterface from './components/VoiceOverInterface';
import MobileAnalyticsInterface from './components/MobileAnalyticsInterface';
import DebugAuth from './components/DebugAuth';
import ThreadsInterface from './components/ThreadsInterface';
import XInterface from './components/XInterface';
import AgentManagement from './components/AgentManagement';
import AgentPromptsDisplay from './components/AgentPromptsDisplay';
import Header from './components/Header';
import ProjectDetail from './components/ProjectDetail';
import IdeaBoard from './components/IdeaBoard';
import IdeaAssistant from './components/IdeaAssistant';
import ProjectKnowledgeBase from './components/ProjectKnowledgeBase';
import ProjectTasks from './components/ProjectTasks';
import ProjectGoals from './components/ProjectGoals';
import SideMenu from './components/SideMenu';
import { BrandedSupabaseLogin } from './components/auth/BrandedSupabaseLogin';
import { BrandedSupabaseSignup } from './components/auth/BrandedSupabaseSignup';
import { BrandedForgotPassword } from './components/auth/BrandedForgotPassword';
import { BrandedResetPassword } from './components/auth/BrandedResetPassword';
import { AuthCallback } from './components/auth/AuthCallback';
import { MFAChallenge } from './components/auth/MFAChallenge';
import { AccountSettings } from './components/auth/AccountSettings';
import { AuthDebug } from './components/auth/AuthDebug';
import Profile from './components/Profile';
import OrganizationSettings from './components/OrganizationSettings';
import OrganizationDebug from './components/OrganizationDebug';
import ProtectedRoute from './components/auth/ProtectedRoute';
import AppHeader from './components/AppHeader';
import { useSupabaseAuth } from './contexts/SupabaseAuthContext';
import OnboardingCheck from './components/OnboardingCheck';
import MainDashboard from './components/MainDashboard';

function AppContent() {
  const { user, loading } = useSupabaseAuth();
  const location = useLocation();
  const { showLoadingScreen, fadeOut } = useLoadingScreen(loading);
  
  // Check if we're on an auth page
  const isAuthPage = ['/login', '/signup', '/forgot-password', '/reset-password', '/auth/callback', '/mfa-challenge'].includes(location.pathname);
  
  // Show loading screen while checking auth state
  if (showLoadingScreen) {
    return <LoadingScreen fadeOut={fadeOut} />;
  }
  
  // Wrap with OnboardingCheck only if user is logged in and not on auth pages
  const appContent = (
    <MenuProvider>
      <div className="App">
        {user && !isAuthPage && <SideMenu />}
        <div className={`app-container ${isAuthPage ? 'auth-page' : ''}`}>
          {/* Only show header if not on auth pages */}
          {!isAuthPage && (user ? <AppHeader /> : <Header />)}
          <main className="main-content" style={{ marginTop: (user && !isAuthPage) ? '48px' : '0' }}>
            <Routes>
            {/* Public routes */}
            <Route path="/login" element={<BrandedSupabaseLogin />} />
            <Route path="/signup" element={<BrandedSupabaseSignup />} />
            <Route path="/forgot-password" element={<BrandedForgotPassword />} />
            <Route path="/reset-password" element={<BrandedResetPassword />} />
            <Route path="/auth/callback" element={<AuthCallback />} />
            <Route path="/mfa-challenge" element={<MFAChallenge />} />
            <Route path="/auth-debug" element={<AuthDebug />} />
            <Route path="/account-settings" element={<ProtectedRoute><AccountSettings /></ProtectedRoute>} />
            
            {/* Protected routes */}
            <Route path="/" element={<ProtectedRoute><MainDashboard /></ProtectedRoute>} />
            <Route path="/qa" element={<ProtectedRoute><QAInterface /></ProtectedRoute>} />
            <Route path="/affirmations" element={<ProtectedRoute><AffirmationsInterface /></ProtectedRoute>} />
            <Route path="/instagram-posts" element={<ProtectedRoute><InstagramPostsInterface /></ProtectedRoute>} />
            <Route path="/instagram-posting" element={<InstagramPostingInterface />} />
            <Route path="/instagram-analyzer" element={<InstagramAnalyzerInterface />} />
            <Route path="/visual-posts" element={<ProtectedRoute><VisualPostsInterface /></ProtectedRoute>} />
            <Route path="/workflows" element={<ProtectedRoute><WorkflowManagement /></ProtectedRoute>} />
            <Route path="/post-composition" element={<PostCompositionInterface />} />
            <Route path="/video-generation" element={<VideoGenerationInterface />} />
            <Route path="/instagram-reel" element={<InstagramReelInterface apiBaseUrl="http://localhost:8000" />} />
            <Route path="/app-test" element={<AppTestInterface />} />
            <Route path="/voice-over" element={<VoiceOverInterface apiBaseUrl="http://localhost:8000" />} />
            <Route path="/mobile-analytics" element={<MobileAnalyticsInterface />} />
            <Route path="/debug-auth" element={<ProtectedRoute><DebugAuth /></ProtectedRoute>} />
            <Route path="/threads" element={<ThreadsInterface />} />
            <Route path="/x-twitter" element={<XInterface />} />
            <Route path="/agent-prompts" element={<AgentPromptsDisplay />} />
            <Route path="/agent-dashboard" element={<ProtectedRoute><AgentManagement /></ProtectedRoute>} />
            <Route path="/content-generator" element={<ProtectedRoute><ContentGenerator /></ProtectedRoute>} />
            <Route path="/content/:contentId" element={<ContentViewer />} />
            <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
            <Route path="/organization-settings" element={<ProtectedRoute><OrganizationSettings /></ProtectedRoute>} />
            <Route path="/organization-settings/:tab" element={<ProtectedRoute><OrganizationSettings /></ProtectedRoute>} />
            <Route path="/organization-debug" element={<ProtectedRoute><OrganizationDebug /></ProtectedRoute>} />
            <Route path="/projects/:projectId" element={<ProtectedRoute><ProjectDetail /></ProtectedRoute>} />
            <Route path="/projects/:projectId/goals" element={<ProtectedRoute><ProjectGoals /></ProtectedRoute>} />
            <Route path="/projects/:projectId/tasks" element={<ProtectedRoute><ProjectTasks /></ProtectedRoute>} />
            <Route path="/projects/:projectId/knowledgebase" element={<ProtectedRoute><ProjectKnowledgeBase /></ProtectedRoute>} />
            <Route path="/ideas" element={<ProtectedRoute><IdeaBoard /></ProtectedRoute>} />
            <Route path="/ideas/new" element={<ProtectedRoute><IdeaAssistant /></ProtectedRoute>} />
            <Route path="/ideas/:ideaId" element={<ProtectedRoute><IdeaAssistant /></ProtectedRoute>} />
            </Routes>
          </main>
          </div>
        </div>
      </MenuProvider>
  );
  
  // If user is logged in and not on auth page, check for onboarding
  if (user && !isAuthPage) {
    return <OnboardingCheck>{appContent}</OnboardingCheck>;
  }
  
  return appContent;
}

function App() {
  return (
    <Router>
      <ThemeProvider>
        <SupabaseAuthProvider>
          <OrganizationProvider>
            <ProjectProvider>
              <AppContent />
            </ProjectProvider>
          </OrganizationProvider>
        </SupabaseAuthProvider>
      </ThemeProvider>
    </Router>
  );
}

export default App;

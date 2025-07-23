import React from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { MenuProvider } from './contexts/MenuContext';
import { SupabaseAuthProvider } from './contexts/SupabaseAuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import './App.css';
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
import SideMenu from './components/SideMenu';
import { BrandedSupabaseLogin } from './components/auth/BrandedSupabaseLogin';
import { BrandedSupabaseSignup } from './components/auth/BrandedSupabaseSignup';
import { BrandedForgotPassword } from './components/auth/BrandedForgotPassword';
import { BrandedResetPassword } from './components/auth/BrandedResetPassword';
import { AuthCallback } from './components/auth/AuthCallback';
import { MFAChallenge } from './components/auth/MFAChallenge';
import { AccountSettings } from './components/auth/AccountSettings';
import { AuthDebug } from './components/auth/AuthDebug';
import ProtectedRoute from './components/auth/ProtectedRoute';
import AppHeader from './components/AppHeader';
import { useSupabaseAuth } from './contexts/SupabaseAuthContext';
import UserProfile from './components/UserProfile';
import OrganizationSettings from './components/OrganizationSettings';
import ProjectManagement from './components/ProjectManagement';

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
  
  return (
    <MenuProvider>
      <div className="App">
        {user && !isAuthPage && <SideMenu />}
        <div className={`app-container ${isAuthPage ? 'auth-page' : ''}`}>
          {/* Only show header if not on auth pages */}
          {!isAuthPage && (user ? <AppHeader /> : <Header />)}
          <main className="main-content" style={{ marginTop: (user && !isAuthPage) ? '64px' : '0' }}>
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
            <Route path="/" element={<ProtectedRoute><AgentManagement /></ProtectedRoute>} />
            <Route path="/agents" element={<ProtectedRoute><AgentManagement /></ProtectedRoute>} />
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
            <Route path="/content-generator" element={<ProtectedRoute><ContentGenerator /></ProtectedRoute>} />
            <Route path="/content/:contentId" element={<ContentViewer />} />
            <Route path="/profile" element={<ProtectedRoute><UserProfile /></ProtectedRoute>} />
            <Route path="/organization-settings" element={<ProtectedRoute><OrganizationSettings /></ProtectedRoute>} />
            <Route path="/projects" element={<ProtectedRoute><ProjectManagement /></ProtectedRoute>} />
            </Routes>
          </main>
          </div>
        </div>
      </MenuProvider>
  );
}

function App() {
  return (
    <Router>
      <ThemeProvider>
        <SupabaseAuthProvider>
          <AppContent />
        </SupabaseAuthProvider>
      </ThemeProvider>
    </Router>
  );
}

export default App;

import React from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { MenuProvider } from './contexts/MenuContext';
import { AuthProvider } from './contexts/AuthContext';
import './App.css';
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
import ThreadsInterface from './components/ThreadsInterface';
import XInterface from './components/XInterface';
import AgentManagement from './components/AgentManagement';
import AgentPromptsDisplay from './components/AgentPromptsDisplay';
import Header from './components/Header';
import SideMenu from './components/SideMenu';
import Login from './components/auth/Login';
import Signup from './components/auth/Signup';
import ProtectedRoute from './components/auth/ProtectedRoute';
import AppHeader from './components/AppHeader';
import { useAuth } from './contexts/AuthContext';
import UserProfile from './components/UserProfile';
import OrganizationSettings from './components/OrganizationSettings';
import ProjectManagement from './components/ProjectManagement';

function AppContent() {
  const { user } = useAuth();
  const location = useLocation();
  
  // Check if we're on an auth page (login or signup)
  const isAuthPage = ['/login', '/signup'].includes(location.pathname);
  
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
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            
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
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  );
}

export default App;

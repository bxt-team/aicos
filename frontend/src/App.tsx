import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
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
import AndroidTestInterface from './components/AndroidTestInterface';
import VoiceOverInterface from './components/VoiceOverInterface';
import MobileAnalyticsInterface from './components/MobileAnalyticsInterface';
import ThreadsInterface from './components/ThreadsInterface';
import XInterface from './components/XInterface';
import AgentManagement from './components/AgentManagement';
import AgentPromptsDisplay from './components/AgentPromptsDisplay';
import Header from './components/Header';
import SideMenu from './components/SideMenu';

function App() {
  return (
    <Router>
      <div className="App">
        <SideMenu />
        <div className="app-container">
          <Header />
          <main className="main-content">
            <Routes>
            <Route path="/" element={<AgentManagement />} />
            <Route path="/agents" element={<AgentManagement />} />
            <Route path="/qa" element={<QAInterface />} />
            <Route path="/affirmations" element={<AffirmationsInterface />} />
            <Route path="/instagram-posts" element={<InstagramPostsInterface />} />
            <Route path="/instagram-posting" element={<InstagramPostingInterface />} />
            <Route path="/instagram-analyzer" element={<InstagramAnalyzerInterface />} />
            <Route path="/visual-posts" element={<VisualPostsInterface />} />
            <Route path="/workflows" element={<WorkflowManagement />} />
            <Route path="/post-composition" element={<PostCompositionInterface />} />
            <Route path="/video-generation" element={<VideoGenerationInterface />} />
            <Route path="/instagram-reel" element={<InstagramReelInterface apiBaseUrl="http://localhost:8000" />} />
            <Route path="/android-test" element={<AndroidTestInterface />} />
            <Route path="/voice-over" element={<VoiceOverInterface apiBaseUrl="http://localhost:8000" />} />
            <Route path="/mobile-analytics" element={<MobileAnalyticsInterface />} />
            <Route path="/threads" element={<ThreadsInterface />} />
            <Route path="/x-twitter" element={<XInterface />} />
            <Route path="/agent-prompts" element={<AgentPromptsDisplay />} />
            <Route path="/content-generator" element={<ContentGenerator />} />
            <Route path="/content/:contentId" element={<ContentViewer />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;

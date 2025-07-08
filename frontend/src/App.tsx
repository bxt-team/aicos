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
import AgentManagement from './components/AgentManagement';
import Header from './components/Header';

function App() {
  return (
    <Router>
      <div className="App">
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
            <Route path="/content-generator" element={<ContentGenerator />} />
            <Route path="/content/:contentId" element={<ContentViewer />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;

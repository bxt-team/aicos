import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import ContentGenerator from './components/ContentGenerator';
import ContentViewer from './components/ContentViewer';
import Header from './components/Header';

function App() {
  return (
    <Router>
      <div className="App">
        <Header />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<ContentGenerator />} />
            <Route path="/content/:contentId" element={<ContentViewer />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;

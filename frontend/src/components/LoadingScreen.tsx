import React from 'react';
import './LoadingScreen.css';

interface LoadingScreenProps {
  fadeOut?: boolean;
}

const LoadingScreen: React.FC<LoadingScreenProps> = ({ fadeOut = false }) => {
  return (
    <div className={`loading-screen ${fadeOut ? 'fade-out' : ''}`}>
      <div className="loading-content">
        <div className="logo-container">
          <img src="/logo.svg" alt="AICOS" className="loading-logo" />
        </div>
        <div className="loading-text">Loading AICOS...</div>
        <div className="loading-dots">
          <span className="dot"></span>
          <span className="dot"></span>
          <span className="dot"></span>
        </div>
      </div>
    </div>
  );
};

export default LoadingScreen;
import React from 'react';
import { Link } from 'react-router-dom';
import { useMenu } from '../contexts/MenuContext';
import './Header.css';

const Header: React.FC = () => {
  const { toggleMenu, isMobile } = useMenu();
  
  return (
    <header className="header">
      <div className="header-container">
        {isMobile && (
          <button 
            className="hamburger-menu"
            onClick={toggleMenu}
            aria-label="Toggle menu"
          >
            <span className="hamburger-line"></span>
            <span className="hamburger-line"></span>
            <span className="hamburger-line"></span>
          </button>
        )}
        <Link to="/" className="header-title">
          <div className="title-content">
            <span className="title-icon">🌀</span>
            <h1>7 Lebenszyklen KI-Assistent</h1>
          </div>
        </Link>
      </div>
    </header>
  );
};

export default Header;
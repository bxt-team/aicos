import React from 'react';
import { Link } from 'react-router-dom';
import { useMenu } from '../contexts/MenuContext';
import ThemeToggle from './ThemeToggle';
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
          <div className="title-content aicos-brand">
            <img src="/logo.svg" alt="AICOS Logo" className="aicos-logo" />
            <h1>AICOS</h1>
          </div>
        </Link>
        <ThemeToggle />
      </div>
    </header>
  );
};

export default Header;
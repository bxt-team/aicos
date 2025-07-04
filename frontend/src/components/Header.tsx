import React from 'react';
import { Link } from 'react-router-dom';
import './Header.css';

const Header: React.FC = () => {
  return (
    <header className="header">
      <div className="header-container">
        <Link to="/" className="header-title">
          <h1>Instagram Content Generator</h1>
        </Link>
        <nav className="header-nav">
          <Link to="/" className="nav-link">Generate</Link>
        </nav>
      </div>
    </header>
  );
};

export default Header;
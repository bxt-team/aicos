import React from 'react';
import { Link } from 'react-router-dom';
import './Header.css';

const Header: React.FC = () => {
  return (
    <header className="header">
      <div className="header-container">
        <Link to="/" className="header-title">
          <h1>7 Lebenszyklen KI-Assistent</h1>
        </Link>
        <nav className="header-nav">
          <Link to="/qa" className="nav-link">Fragen & Antworten</Link>
          <Link to="/affirmations" className="nav-link">Affirmationen</Link>
          <Link to="/content-generator" className="nav-link">Inhalts-Generator</Link>
        </nav>
      </div>
    </header>
  );
};

export default Header;
import React from 'react';
import { Link } from 'react-router-dom';
import './Header.css';

const Header: React.FC = () => {
  return (
    <header className="header">
      <div className="header-container">
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
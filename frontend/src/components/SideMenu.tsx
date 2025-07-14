import React, { useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { getEnabledAgents, getAgentsByCategory, getAgentByRoute } from '../config/agents';
import { useMenu } from '../contexts/MenuContext';
import './SideMenu.css';

const SideMenu: React.FC = () => {
  const { isMenuOpen: isExpanded, toggleMenu, isMobile } = useMenu();
  const location = useLocation();

  // Close menu on route change for mobile
  useEffect(() => {
    if (isMobile && isExpanded) {
      toggleMenu();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]);

  // Prevent body scroll when menu is open on mobile
  useEffect(() => {
    if (isMobile && isExpanded) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isMobile, isExpanded]);

  const handleOverlayClick = () => {
    if (isMobile && isExpanded) {
      toggleMenu();
    }
  };

  const agents = getEnabledAgents();
  const agentsByCategory = getAgentsByCategory();
  const categories = Object.keys(agentsByCategory);
  
  const getCurrentAgent = () => {
    return getAgentByRoute(location.pathname);
  };

  const currentAgent = getCurrentAgent();

  const handleToggleClick = () => {
    toggleMenu();
  };

  return (
    <>
      {/* Mobile overlay */}
      {isMobile && isExpanded && (
        <div className="menu-overlay" onClick={handleOverlayClick} />
      )}
      
      <aside className={`side-menu ${isExpanded ? 'expanded' : 'collapsed'} ${isMobile ? 'mobile' : ''}`}>
      <div className="side-menu-header">
        <button 
          className="menu-toggle"
          onClick={handleToggleClick}
          aria-label={isExpanded ? 'Menü einklappen' : 'Menü ausklappen'}
        >
          {isExpanded ? '◀' : '▶'}
        </button>
        {isExpanded && (
          <div className="menu-title">
            <h3>🤖 AI Agenten</h3>
            <p className="agent-count">{agents.length} verfügbar</p>
            {isMobile && (
              <button 
                className="menu-close"
                onClick={handleToggleClick}
                aria-label="Menü schließen"
              >
                ✕
              </button>
            )}
          </div>
        )}
      </div>

      <nav className="side-menu-nav">
        {isExpanded ? (
          <>
            {categories.map(category => (
              <div key={category} className="menu-category">
                <h4 className="category-title">{category}</h4>
                <ul className="agents-list">
                  {agentsByCategory[category].map(agent => (
                    <li key={agent.id}>
                      <Link
                        to={agent.route}
                        className={`menu-item ${location.pathname === agent.route ? 'active' : ''}`}
                        title={agent.description}
                      >
                        <span className="agent-icon">{agent.icon}</span>
                        <div className="agent-info">
                          <span className="agent-name">{agent.name}</span>
                          <span className="agent-description">{agent.description}</span>
                        </div>
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </>
        ) : (
          <ul className="agents-list-collapsed">
            {agents.map(agent => (
              <li key={agent.id}>
                <Link
                  to={agent.route}
                  className={`menu-item-collapsed ${location.pathname === agent.route ? 'active' : ''}`}
                  title={agent.name}
                >
                  <span className="agent-icon">{agent.icon}</span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </nav>
    </aside>
    </>
  );
};

export default SideMenu;
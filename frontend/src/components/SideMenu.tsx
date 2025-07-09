import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { getEnabledAgents, getAgentsByCategory, getAgentByRoute } from '../config/agents';
import './SideMenu.css';

const SideMenu: React.FC = () => {
  const [isExpanded, setIsExpanded] = useState(true);
  const location = useLocation();

  const agents = getEnabledAgents();
  const agentsByCategory = getAgentsByCategory();
  const categories = Object.keys(agentsByCategory);
  
  const getCurrentAgent = () => {
    return getAgentByRoute(location.pathname);
  };

  const currentAgent = getCurrentAgent();

  const toggleMenu = () => {
    setIsExpanded(!isExpanded);
  };

  return (
    <aside className={`side-menu ${isExpanded ? 'expanded' : 'collapsed'}`}>
      <div className="side-menu-header">
        <button 
          className="menu-toggle"
          onClick={toggleMenu}
          aria-label={isExpanded ? 'Menü einklappen' : 'Menü ausklappen'}
        >
          {isExpanded ? '◀' : '▶'}
        </button>
        {isExpanded && (
          <div className="menu-title">
            <h3>🤖 AI Agenten</h3>
            <p className="agent-count">{agents.length} verfügbar</p>
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
  );
};

export default SideMenu;
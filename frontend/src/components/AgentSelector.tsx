import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { getEnabledAgents, getAgentsByCategory, getAgentByRoute } from '../config/agents';
import './AgentSelector.css';

const AgentSelector: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();

  const agents = getEnabledAgents();
  const agentsByCategory = getAgentsByCategory();
  const categories = Object.keys(agentsByCategory);
  
  const getCurrentAgent = () => {
    return getAgentByRoute(location.pathname);
  };

  const currentAgent = getCurrentAgent();

  const toggleDropdown = () => {
    setIsOpen(!isOpen);
  };

  const closeDropdown = () => {
    setIsOpen(false);
  };

  return (
    <div className="agent-selector">
      <button 
        className="agent-selector-trigger"
        onClick={toggleDropdown}
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        <div className="current-agent">
          <span className="agent-icon">
            {currentAgent?.icon || '🏠'}
          </span>
          <span className="agent-name">
            {currentAgent?.name || 'Dashboard'}
          </span>
        </div>
        <span className={`dropdown-arrow ${isOpen ? 'open' : ''}`}>
          ▼
        </span>
      </button>

      {isOpen && (
        <>
          <div className="dropdown-overlay" onClick={closeDropdown} />
          <div className="agent-dropdown">
            <div className="dropdown-header">
              <h3>🤖 AI Agenten wählen</h3>
              <p>Wähle einen Agenten für deine Aufgabe</p>
            </div>
            
            {categories.map(category => (
              <div key={category} className="agent-category">
                <h4 className="category-title">{category}</h4>
                <div className="agents-list">
                  {agentsByCategory[category].map(agent => (
                    <Link
                      key={agent.id}
                      to={agent.route}
                      className={`agent-item ${location.pathname === agent.route ? 'active' : ''}`}
                      onClick={closeDropdown}
                    >
                      <div className="agent-icon">{agent.icon}</div>
                      <div className="agent-info">
                        <div className="agent-title">{agent.name}</div>
                        <div className="agent-description">{agent.description}</div>
                        <div className="agent-features">
                          {agent.features.slice(0, 2).map((feature, index) => (
                            <span key={index} className="feature-tag">{feature}</span>
                          ))}
                        </div>
                      </div>
                      {location.pathname === agent.route && (
                        <div className="active-indicator">✓</div>
                      )}
                    </Link>
                  ))}
                </div>
              </div>
            ))}
            
            <div className="dropdown-footer">
              <div className="agent-count">
                {agents.length} Agenten verfügbar
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default AgentSelector;
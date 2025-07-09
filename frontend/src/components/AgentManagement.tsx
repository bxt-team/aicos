import React, { useState, useEffect, useCallback } from 'react';
import { agentConfigs, futureAgents, AgentConfig } from '../config/agents';
import './AgentManagement.css';

const AgentManagement: React.FC = () => {
  const [agents] = useState<AgentConfig[]>(agentConfigs);
  const [upcoming] = useState<Partial<AgentConfig>[]>(futureAgents);
  const [healthStatus, setHealthStatus] = useState<{ [key: string]: boolean }>({});
  const [loading, setLoading] = useState(false);

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const checkAgentHealth = useCallback(async () => {
    setLoading(true);
    const status: { [key: string]: boolean } = {};

    for (const agent of agents) {
      if (agent.apiHealthCheck) {
        try {
          const response = await fetch(`${API_BASE_URL}${agent.apiHealthCheck}`);
          status[agent.id] = response.ok;
        } catch {
          status[agent.id] = false;
        }
      } else {
        status[agent.id] = true; // Assume healthy if no health check endpoint
      }
    }

    setHealthStatus(status);
    setLoading(false);
  }, [agents, API_BASE_URL]);

  useEffect(() => {
    checkAgentHealth();
  }, [checkAgentHealth]);

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return 'Unbekannt';
    return new Date(timestamp).toLocaleString('de-DE');
  };

  const getStatusIcon = (agentId: string) => {
    if (loading) return '🔄';
    return healthStatus[agentId] ? '✅' : '❌';
  };

  const getStatusText = (agentId: string) => {
    if (loading) return 'Überprüfung...';
    return healthStatus[agentId] ? 'Online' : 'Offline';
  };

  const getCategoryColor = (category: string) => {
    const colors: { [key: string]: string } = {
      'Wissen & Forschung': '#667eea',
      'Persönlichkeitsentwicklung': '#48bb78',
      'Social Media Marketing': '#ed8936',
      'Visual Content': '#9f7aea',
      'Content Creation': '#38b2ac',
      'E-Mail Marketing': '#f56565',
      'Video Content': '#ec4899',
      'Bildung': '#3182ce',
      'Analytics': '#319795',
      'Quality Assurance': '#059669',
      'System Management': '#4b5563'
    };
    return colors[category] || '#718096';
  };

  return (
    <div className="agent-management">
      <div className="management-header">
        <h2>🤖 Agent Management Dashboard</h2>
        <p>Übersicht und Status aller verfügbaren AI-Agenten</p>
        <button 
          className="refresh-button"
          onClick={checkAgentHealth}
          disabled={loading}
        >
          {loading ? '🔄 Überprüfung...' : '🔄 Status aktualisieren'}
        </button>
      </div>

      <div className="agents-overview">
        <div className="overview-stats">
          <div className="stat-card">
            <div className="stat-number">{agents.filter(a => a.enabled).length}</div>
            <div className="stat-label">Aktive Agenten</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{Object.values(healthStatus).filter(Boolean).length}</div>
            <div className="stat-label">Online</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{upcoming.length}</div>
            <div className="stat-label">Geplant</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{Array.from(new Set(agents.map(a => a.category))).length}</div>
            <div className="stat-label">Kategorien</div>
          </div>
        </div>
      </div>

      <div className="agents-section">
        <h3>✅ Aktive Agenten</h3>
        <div className="agents-grid">
          {agents
            .filter(agent => agent.enabled)
            .map(agent => (
            <div key={agent.id} className="agent-card">
              <div className="card-header">
                <div className="agent-title-section">
                  <span className="agent-icon">{agent.icon}</span>
                  <div>
                    <h4>{agent.name}</h4>
                    <span 
                      className="category-badge"
                      style={{ backgroundColor: getCategoryColor(agent.category) }}
                    >
                      {agent.category}
                    </span>
                  </div>
                </div>
                <div className="status-section">
                  <div className="status-indicator">
                    <span className="status-icon">{getStatusIcon(agent.id)}</span>
                    <span className="status-text">{getStatusText(agent.id)}</span>
                  </div>
                  {agent.version && (
                    <div className="version">v{agent.version}</div>
                  )}
                </div>
              </div>

              <div className="card-content">
                <p className="agent-description">{agent.description}</p>
                
                <div className="features-section">
                  <h5>Features:</h5>
                  <div className="features-list">
                    {agent.features.map((feature, index) => (
                      <span key={index} className="feature-chip">{feature}</span>
                    ))}
                  </div>
                </div>

                <div className="card-actions">
                  <a 
                    href={agent.route} 
                    className="action-button primary"
                  >
                    🚀 Agent öffnen
                  </a>
                  {agent.apiHealthCheck && (
                    <button 
                      className="action-button secondary"
                      onClick={() => window.open(`${API_BASE_URL}${agent.apiHealthCheck}`, '_blank')}
                    >
                      🔗 API testen
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="upcoming-section">
        <h3>🚧 Geplante Agenten</h3>
        <div className="upcoming-grid">
          {upcoming.map((agent, index) => (
            <div key={agent.id || index} className="upcoming-card">
              <div className="upcoming-header">
                <span className="upcoming-icon">{agent.icon}</span>
                <div>
                  <h4>{agent.name}</h4>
                  <span 
                    className="category-badge upcoming"
                    style={{ backgroundColor: getCategoryColor(agent.category || '') }}
                  >
                    {agent.category}
                  </span>
                </div>
                <div className="coming-soon">Bald verfügbar</div>
              </div>
              <p className="upcoming-description">{agent.description}</p>
              {agent.features && (
                <div className="upcoming-features">
                  {agent.features.slice(0, 3).map((feature, fIndex) => (
                    <span key={fIndex} className="feature-chip upcoming">{feature}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="system-info">
        <h3>📊 System Information</h3>
        <div className="info-grid">
          <div className="info-item">
            <strong>Backend URL:</strong> {API_BASE_URL}
          </div>
          <div className="info-item">
            <strong>Letzte Überprüfung:</strong> {formatTimestamp(new Date().toISOString())}
          </div>
          <div className="info-item">
            <strong>Frontend Version:</strong> 1.0.0
          </div>
          <div className="info-item">
            <strong>Agent Framework:</strong> CrewAI + FastAPI
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentManagement;
import React, { useState, useEffect } from 'react';
import { agentConfigs, AgentConfig } from '../config/agents';
import axios from 'axios';
import './AgentManagement.css';

interface AgentPrompt {
  name: string;
  role: string;
  goal: string;
  backstory: string;
  settings: {
    verbose: boolean;
    allow_delegation: boolean;
    max_iter: number;
    max_execution_time: number;
  };
}

const AgentManagement: React.FC = () => {
  const [agents] = useState<AgentConfig[]>(agentConfigs);
  // Removed health status - all agents are assumed to be always up
  const [expandedAgents, setExpandedAgents] = useState<Set<string>>(new Set());
  const [agentPrompts, setAgentPrompts] = useState<{ [key: string]: AgentPrompt }>({});
  const [loadingPrompts, setLoadingPrompts] = useState<Set<string>>(new Set());

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  // Removed health check - all agents are assumed to be always up

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return 'Unknown';
    return new Date(timestamp).toLocaleString('en-US');
  };

  const getStatusIcon = (agentId: string) => {
    return '✅';
  };

  const getStatusText = (agentId: string) => {
    return 'Online';
  };

  const getCategoryColor = (category: string) => {
    const colors: { [key: string]: string } = {
      'Knowledge & Research': '#667eea',
      'Personal Development': '#48bb78',
      'Social Media Marketing': '#ed8936',
      'Visual Content': '#9f7aea',
      'Content Creation': '#38b2ac',
      'Email Marketing': '#f56565',
      'Video Content': '#ec4899',
      'Education': '#3182ce',
      'Analytics': '#319795',
      'Quality Assurance': '#059669',
      'System Management': '#4b5563'
    };
    return colors[category] || '#718096';
  };

  // Get CSS class for category instead of inline style
  const getCategoryClass = (category: string) => {
    const categoryMap: { [key: string]: string } = {
      'Knowledge & Research': 'category-knowledge',
      'Personal Development': 'category-personality',
      'Social Media Marketing': 'category-social',
      'Visual Content': 'category-visual',
      'Content Creation': 'category-content',
      'Email Marketing': 'category-email',
      'Video Content': 'category-video',
      'Education': 'category-education',
      'Analytics': 'category-analytics',
      'Quality Assurance': 'category-qa',
      'System Management': 'category-system'
    };
    return categoryMap[category] || 'category-default';
  };

  const loadAgentPrompt = async (agentId: string) => {
    // Map frontend agent IDs to backend agent IDs
    const agentIdMap: { [key: string]: string } = {
      'qa': 'qa_agent',
      'affirmations': 'affirmations_agent',
      'instagram-posts': 'instagram_ai_prompt_agent',
      'visual-posts': 'visual_post_creator_agent',
      'instagram-poster': 'instagram_poster_agent',
      'instagram-analyzer': 'instagram_analyzer_agent',
      'workflows': 'content_workflow_agent',
      'post-composition': 'post_composition_agent',
      'video-generation': 'video_generation_agent',
      'instagram-reel': 'instagram_reel_agent',
      'android-test': 'android_testing_agent',
      'voice-over': 'voice_over_agent',
      'mobile-analytics': 'mobile_analytics_agent',
      'threads': 'threads_analysis_agent',
      'x-twitter': 'x_analysis_agent'
    };

    const backendAgentId = agentIdMap[agentId];
    if (!backendAgentId) return;

    setLoadingPrompts(prev => new Set(prev).add(agentId));
    
    try {
      const response = await axios.get(`${API_BASE_URL}/api/agent-prompts/${backendAgentId}`);
      if (response.data.success) {
        setAgentPrompts(prev => ({
          ...prev,
          [agentId]: response.data.agent
        }));
      }
    } catch (error) {
      console.error(`Error loading prompt for agent ${agentId}:`, error);
    } finally {
      setLoadingPrompts(prev => {
        const newSet = new Set(prev);
        newSet.delete(agentId);
        return newSet;
      });
    }
  };

  const toggleAgentExpansion = async (agentId: string) => {
    const newExpanded = new Set(expandedAgents);
    if (newExpanded.has(agentId)) {
      newExpanded.delete(agentId);
    } else {
      newExpanded.add(agentId);
      // Load prompts if not already loaded
      if (!agentPrompts[agentId] && !loadingPrompts.has(agentId)) {
        await loadAgentPrompt(agentId);
      }
    }
    setExpandedAgents(newExpanded);
  };

  const formatBackstory = (backstory: string) => {
    return backstory.split('\n').map((line, index) => {
      if (line.trim().startsWith('-')) {
        return <li key={index}>{line.trim().substring(1).trim()}</li>;
      }
      if (line.trim() === '') {
        return <br key={index} />;
      }
      return <p key={index}>{line}</p>;
    });
  };

  return (
    <div className="agent-management">
      <div className="management-header">
        <h2>🤖 Agent Management Dashboard</h2>
        <p>Overview and status of all available AI agents</p>
        {/* Removed refresh button - all agents are always up */}
      </div>

      <div className="agents-overview">
        <div className="overview-stats">
          <div className="stat-card">
            <div className="stat-number">{agents.filter(a => a.enabled).length}</div>
            <div className="stat-label">Active Agents</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">{Array.from(new Set(agents.map(a => a.category))).length}</div>
            <div className="stat-label">Categories</div>
          </div>
        </div>
      </div>

      <div className="agents-section">
        <h3>✅ Active Agents</h3>
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
                      className={`category-badge ${getCategoryClass(agent.category)}`}
                    >
                      {agent.category}
                    </span>
                  </div>
                </div>
                {/* Status and version info hidden */}
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
                    🚀 Open Agent
                  </a>
                  <button 
                    className="action-button secondary"
                    onClick={() => toggleAgentExpansion(agent.id)}
                    disabled={loadingPrompts.has(agent.id)}
                  >
                    {loadingPrompts.has(agent.id) ? '⏳' : expandedAgents.has(agent.id) ? '📖 Hide Prompts' : '📋 Show Prompts'}
                  </button>
                </div>

                {expandedAgents.has(agent.id) && agentPrompts[agent.id] && (
                  <div className="agent-prompt-section">
                    <div className="prompt-divider"></div>
                    <h5>🤖 Agent Configuration</h5>
                    
                    <div className="prompt-item">
                      <h6>Role:</h6>
                      <p>{agentPrompts[agent.id].role}</p>
                    </div>

                    <div className="prompt-item">
                      <h6>Goal:</h6>
                      <p>{agentPrompts[agent.id].goal}</p>
                    </div>

                    <div className="prompt-item">
                      <h6>Background & Instructions:</h6>
                      <div className="backstory-content">
                        {formatBackstory(agentPrompts[agent.id].backstory)}
                      </div>
                    </div>

                    <div className="prompt-item">
                      <h6>Settings:</h6>
                      <div className="settings-grid">
                        <div className="setting-item">
                          <span className="setting-label">Verbose:</span>
                          <span className={`setting-value ${agentPrompts[agent.id].settings.verbose ? 'true' : 'false'}`}>
                            {agentPrompts[agent.id].settings.verbose ? 'Yes' : 'No'}
                          </span>
                        </div>
                        <div className="setting-item">
                          <span className="setting-label">Allow Delegation:</span>
                          <span className={`setting-value ${agentPrompts[agent.id].settings.allow_delegation ? 'true' : 'false'}`}>
                            {agentPrompts[agent.id].settings.allow_delegation ? 'Yes' : 'No'}
                          </span>
                        </div>
                        <div className="setting-item">
                          <span className="setting-label">Max Iterations:</span>
                          <span className="setting-value">{agentPrompts[agent.id].settings.max_iter}</span>
                        </div>
                        <div className="setting-item">
                          <span className="setting-label">Max Execution Time:</span>
                          <span className="setting-value">{agentPrompts[agent.id].settings.max_execution_time}s</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
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
            <strong>Last Check:</strong> {formatTimestamp(new Date().toISOString())}
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
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ChevronDown, ChevronUp, Info, Settings, Bot } from 'lucide-react';
import './AgentPromptsDisplay.css';

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

interface AgentPromptsResponse {
  success: boolean;
  agents: { [key: string]: AgentPrompt };
  total_agents: number;
}

const AgentPromptsDisplay: React.FC = () => {
  const [agents, setAgents] = useState<{ [key: string]: AgentPrompt }>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedAgents, setExpandedAgents] = useState<Set<string>>(new Set());

  const API_BASE = 'http://localhost:8000';

  useEffect(() => {
    loadAgentPrompts();
  }, []);

  const loadAgentPrompts = async () => {
    try {
      setLoading(true);
      const response = await axios.get<AgentPromptsResponse>(`${API_BASE}/api/agent-prompts`);
      
      if (response.data.success) {
        setAgents(response.data.agents);
      } else {
        setError('Failed to load agent prompts');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error loading agent prompts');
    } finally {
      setLoading(false);
    }
  };

  const toggleAgent = (agentKey: string) => {
    const newExpanded = new Set(expandedAgents);
    if (newExpanded.has(agentKey)) {
      newExpanded.delete(agentKey);
    } else {
      newExpanded.add(agentKey);
    }
    setExpandedAgents(newExpanded);
  };

  const formatBackstory = (backstory: string) => {
    // Split by newlines and format
    return backstory.split('\n').map((line, index) => {
      // Check if line starts with a dash (list item)
      if (line.trim().startsWith('-')) {
        return <li key={index}>{line.trim().substring(1).trim()}</li>;
      }
      // Check if line is empty
      if (line.trim() === '') {
        return <br key={index} />;
      }
      // Regular paragraph
      return <p key={index}>{line}</p>;
    });
  };

  const getCategoryColor = (agentKey: string) => {
    // Map agent types to colors
    const colorMap: { [key: string]: string } = {
      'qa_agent': '#3b82f6',
      'affirmations_agent': '#8b5cf6',
      'image_search_agent': '#ef4444',
      'visual_post_creator_agent': '#f59e0b',
      'post_composition_agent': '#10b981',
      'instagram_ai_prompt_agent': '#ec4899',
      'write_hashtag_research_agent': '#6366f1',
      'instagram_analyzer_agent': '#14b8a6',
      'content_workflow_agent': '#f97316',
      'video_generation_agent': '#84cc16',
      'instagram_reel_agent': '#a855f7',
      'android_testing_agent': '#0ea5e9',
      'voice_over_agent': '#eab308',
      'instagram_poster_agent': '#06b6d4'
    };
    return colorMap[agentKey] || '#6b7280';
  };

  if (loading) {
    return (
      <div className="agent-prompts-loading">
        <div className="spinner" />
        <p>Loading agent configurations...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="agent-prompts-error">
        <p>Error: {error}</p>
        <button onClick={loadAgentPrompts}>Retry</button>
      </div>
    );
  }

  return (
    <div className="agent-prompts-display">
      <div className="agent-prompts-header">
        <h1>
          <Bot className="inline-icon" />
          AI Agent Configurations
        </h1>
        <p>Overview of all AI agents and their prompts in the 7cycles system</p>
      </div>

      <div className="agents-grid">
        {Object.entries(agents).map(([agentKey, agent]) => {
          const isExpanded = expandedAgents.has(agentKey);
          const categoryColor = getCategoryColor(agentKey);

          return (
            <div 
              key={agentKey} 
              className={`agent-card ${isExpanded ? 'expanded' : ''}`}
              style={{ borderTopColor: categoryColor }}
            >
              <div 
                className="agent-header"
                onClick={() => toggleAgent(agentKey)}
              >
                <div className="agent-title">
                  <h3>{agent.name}</h3>
                  <span className="agent-role">{agent.role}</span>
                </div>
                <button className="expand-button">
                  {isExpanded ? <ChevronUp /> : <ChevronDown />}
                </button>
              </div>

              <div className="agent-content">
                <div className="agent-goal">
                  <Info className="section-icon" />
                  <div>
                    <h4>Goal</h4>
                    <p>{agent.goal}</p>
                  </div>
                </div>

                {isExpanded && (
                  <>
                    <div className="agent-backstory">
                      <h4>Backstory & Instructions</h4>
                      <div className="backstory-content">
                        {formatBackstory(agent.backstory)}
                      </div>
                    </div>

                    <div className="agent-settings">
                      <Settings className="section-icon" />
                      <div>
                        <h4>Settings</h4>
                        <div className="settings-grid">
                          <div className="setting-item">
                            <span className="setting-label">Verbose:</span>
                            <span className={`setting-value ${agent.settings.verbose ? 'true' : 'false'}`}>
                              {agent.settings.verbose ? 'Yes' : 'No'}
                            </span>
                          </div>
                          <div className="setting-item">
                            <span className="setting-label">Allow Delegation:</span>
                            <span className={`setting-value ${agent.settings.allow_delegation ? 'true' : 'false'}`}>
                              {agent.settings.allow_delegation ? 'Yes' : 'No'}
                            </span>
                          </div>
                          <div className="setting-item">
                            <span className="setting-label">Max Iterations:</span>
                            <span className="setting-value">{agent.settings.max_iter}</span>
                          </div>
                          <div className="setting-item">
                            <span className="setting-label">Max Execution Time:</span>
                            <span className="setting-value">{agent.settings.max_execution_time}s</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default AgentPromptsDisplay;
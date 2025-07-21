import React, { useState, useEffect, useCallback } from 'react';
import ProjectRequired from './ProjectRequired';
import { apiService } from '../services/api';
import './WorkflowManagement.css';

interface WorkflowTemplate {
  name: string;
  description: string;
  steps: string[];
  default_options: {
    [key: string]: any;
  };
}

interface Workflow {
  id: string;
  period: string;
  workflow_type: string;
  options: { [key: string]: any };
  status: string;
  started_at?: string;
  completed_at?: string;
  steps?: WorkflowStep[];
  results?: { [key: string]: any };
  error?: string;
}

interface WorkflowStep {
  step: string;
  success: boolean;
  message?: string;
  error?: string;
  data?: any;
}

interface WorkflowExecutionStatus {
  workflow_id: string;
  type: string;
  status: string;
  period: string;
  workflow_type: string;
  created_at: string;
  last_updated?: string;
  workflow_result?: Workflow;
}

const WorkflowManagement: React.FC = () => {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [templates, setTemplates] = useState<{ [key: string]: WorkflowTemplate }>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('full');
  const [selectedPeriod, setSelectedPeriod] = useState<string>('');
  const [customOptions, setCustomOptions] = useState<{ [key: string]: any }>({});
  const [activeTab, setActiveTab] = useState<'create' | 'manage' | 'templates'>('create');
  const [runningWorkflows, setRunningWorkflows] = useState<{ [key: string]: WorkflowExecutionStatus }>({});
  const [autoRefresh, setAutoRefresh] = useState(true);

  const periods = [
    'Image', 'Veränderung', 'Energie', 'Kreativität', 
    'Erfolg', 'Entspannung', 'Umsicht'
  ];

  useEffect(() => {
    loadTemplates();
    loadWorkflows();
  }, []);

  const loadTemplates = async () => {
    try {
      const response = await apiService.workflows.getTemplates();
      if (response.data.success) {
        setTemplates(response.data.templates);
      }
    } catch (err: any) {
      console.error('Error loading templates:', err);
    }
  };

  const loadWorkflows = async () => {
    try {
      const response = await apiService.workflows.list();
      if (response.data.success) {
        setWorkflows(response.data.workflows);
      }
    } catch (err: any) {
      console.error('Error loading workflows:', err);
    }
  };

  const checkRunningWorkflows = useCallback(async () => {
    const workflowsToCheck = Object.keys(runningWorkflows).filter(
      id => runningWorkflows[id].status === 'starting' || runningWorkflows[id].status === 'executing'
    );

    for (const workflowId of workflowsToCheck) {
      try {
        const response = await apiService.workflows.get(workflowId);
        if (response.data.workflow_id) {
          setRunningWorkflows(prev => ({
            ...prev,
            [workflowId]: response.data
          }));

          // If workflow completed, refresh the workflows list
          if (response.data.status === 'completed' || response.data.status === 'failed') {
            loadWorkflows();
          }
        }
      } catch (err) {
        console.error(`Error checking workflow ${workflowId}:`, err);
      }
    }
  }, [runningWorkflows]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (autoRefresh) {
      interval = setInterval(() => {
        checkRunningWorkflows();
      }, 5000); // Check every 5 seconds
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh, runningWorkflows, checkRunningWorkflows]);

  const createWorkflow = async () => {
    if (!selectedPeriod) {
      setError('Bitte wählen Sie eine Periode aus');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const templateOptions = templates[selectedTemplate]?.default_options || {};
      const finalOptions = { ...templateOptions, ...customOptions };

      const response = await apiService.workflows.create({
        period: selectedPeriod,
        workflow_type: selectedTemplate,
        options: finalOptions
      });

      if (response.data.workflow_id) {
        // Add to running workflows
        setRunningWorkflows(prev => ({
          ...prev,
          [response.data.workflow_id]: {
            workflow_id: response.data.workflow_id,
            type: 'workflow',
            status: 'starting',
            period: selectedPeriod,
            workflow_type: selectedTemplate,
            created_at: new Date().toISOString()
          }
        }));

        setSelectedPeriod('');
        setCustomOptions({});
        setActiveTab('manage');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Fehler beim Erstellen des Workflows');
    } finally {
      setLoading(false);
    }
  };

  const deleteWorkflow = async (workflowId: string) => {
    if (!window.confirm('Sind Sie sicher, dass Sie diesen Workflow löschen möchten?')) {
      return;
    }

    try {
      await apiService.workflows.delete(workflowId);
      loadWorkflows();
      
      // Remove from running workflows if present
      setRunningWorkflows(prev => {
        const updated = { ...prev };
        delete updated[workflowId];
        return updated;
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Fehler beim Löschen des Workflows');
    }
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'completed': return '#4CAF50';
      case 'failed': return '#f44336';
      case 'executing': return '#2196F3';
      case 'starting': return '#FF9800';
      default: return '#757575';
    }
  };

  const getStatusText = (status: string): string => {
    switch (status) {
      case 'completed': return 'Abgeschlossen';
      case 'failed': return 'Fehlgeschlagen';
      case 'executing': return 'Wird ausgeführt';
      case 'starting': return 'Startet';
      default: return status;
    }
  };

  const renderWorkflowSteps = (workflow: Workflow | WorkflowExecutionStatus) => {
    let steps: WorkflowStep[] | undefined;
    
    if ('workflow_result' in workflow && workflow.workflow_result) {
      steps = workflow.workflow_result.steps;
    } else if ('steps' in workflow) {
      steps = workflow.steps;
    }
    
    if (!steps || steps.length === 0) {
      return <p>Keine Schritte verfügbar</p>;
    }

    return (
      <div className="workflow-steps">
        {steps.map((step: WorkflowStep, index: number) => (
          <div key={index} className={`workflow-step ${step.success ? 'success' : 'pending'}`}>
            <div className="step-icon">
              {step.success ? '✅' : '⏳'}
            </div>
            <div className="step-content">
              <h4>{step.step}</h4>
              <p>{step.message}</p>
              {step.error && <p className="error">{step.error}</p>}
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderCreateTab = () => (
    <div className="create-workflow">
      <h3>Neuen Workflow erstellen</h3>
      
      <div className="form-group">
        <label>Periode:</label>
        <select 
          value={selectedPeriod} 
          onChange={(e) => setSelectedPeriod(e.target.value)}
          disabled={loading}
        >
          <option value="">Periode auswählen...</option>
          {periods.map(period => (
            <option key={period} value={period}>{period}</option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label>Workflow-Template:</label>
        <select 
          value={selectedTemplate} 
          onChange={(e) => setSelectedTemplate(e.target.value)}
          disabled={loading}
        >
          {Object.entries(templates).map(([key, template]) => (
            <option key={key} value={key}>{template.name}</option>
          ))}
        </select>
      </div>

      {templates[selectedTemplate] && (
        <div className="template-info">
          <h4>{templates[selectedTemplate].name}</h4>
          <p>{templates[selectedTemplate].description}</p>
          
          <div className="template-steps">
            <h5>Schritte:</h5>
            <ul>
              {templates[selectedTemplate].steps.map((step, index) => (
                <li key={index}>{step}</li>
              ))}
            </ul>
          </div>

          <div className="template-options">
            <h5>Optionen:</h5>
            {Object.entries(templates[selectedTemplate].default_options).map(([key, value]) => (
              <div key={key} className="option-input">
                <label>{key}:</label>
                <input
                  type={typeof value === 'boolean' ? 'checkbox' : typeof value === 'number' ? 'number' : 'text'}
                  checked={typeof value === 'boolean' ? customOptions[key] ?? value : undefined}
                  value={typeof value !== 'boolean' ? customOptions[key] ?? value : undefined}
                  onChange={(e) => {
                    const newValue = typeof value === 'boolean' 
                      ? e.target.checked 
                      : typeof value === 'number' 
                        ? Number(e.target.value) 
                        : e.target.value;
                    setCustomOptions(prev => ({ ...prev, [key]: newValue }));
                  }}
                  disabled={loading}
                />
              </div>
            ))}
          </div>
        </div>
      )}

      <button 
        onClick={createWorkflow}
        disabled={loading || !selectedPeriod}
        className="create-button"
      >
        {loading ? 'Erstelle Workflow...' : 'Workflow erstellen'}
      </button>
    </div>
  );

  const renderManageTab = () => (
    <div className="manage-workflows">
      <div className="workflows-header">
        <h3>Workflows verwalten</h3>
        <div className="header-controls">
          <label>
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            Auto-Refresh
          </label>
          <button onClick={loadWorkflows} className="refresh-button">🔄 Aktualisieren</button>
        </div>
      </div>

      {/* Running Workflows */}
      {Object.keys(runningWorkflows).length > 0 && (
        <div className="running-workflows">
          <h4>Laufende Workflows</h4>
          {Object.values(runningWorkflows).map((workflow) => (
            <div key={workflow.workflow_id} className="workflow-card running">
              <div className="workflow-header">
                <h4>{workflow.period} - {workflow.workflow_type}</h4>
                <span 
                  className="status"
                  style={{ color: getStatusColor(workflow.status) }}
                >
                  {getStatusText(workflow.status)}
                </span>
              </div>
              <p>Gestartet: {new Date(workflow.created_at).toLocaleString()}</p>
              {workflow.last_updated && (
                <p>Letzte Aktualisierung: {new Date(workflow.last_updated).toLocaleString()}</p>
              )}
              {renderWorkflowSteps(workflow)}
            </div>
          ))}
        </div>
      )}

      {/* Completed Workflows */}
      <div className="completed-workflows">
        <h4>Abgeschlossene Workflows</h4>
        {workflows.length === 0 ? (
          <p>Keine Workflows gefunden</p>
        ) : (
          workflows.map((workflow) => (
            <div key={workflow.id} className="workflow-card">
              <div className="workflow-header">
                <h4>{workflow.period} - {workflow.workflow_type}</h4>
                <div className="workflow-actions">
                  <span 
                    className="status"
                    style={{ color: getStatusColor(workflow.status) }}
                  >
                    {getStatusText(workflow.status)}
                  </span>
                  <button 
                    onClick={() => deleteWorkflow(workflow.id)}
                    className="delete-button"
                  >
                    🗑️
                  </button>
                </div>
              </div>
              
              <div className="workflow-meta">
                {workflow.started_at && (
                  <p>Gestartet: {new Date(workflow.started_at).toLocaleString()}</p>
                )}
                {workflow.completed_at && (
                  <p>Abgeschlossen: {new Date(workflow.completed_at).toLocaleString()}</p>
                )}
              </div>

              {workflow.error && (
                <div className="error-message">
                  <strong>Fehler:</strong> {workflow.error}
                </div>
              )}

              {renderWorkflowSteps(workflow)}

              {workflow.results && (
                <div className="workflow-results">
                  <h5>Ergebnisse:</h5>
                  {workflow.results.affirmations && (
                    <p>Affirmationen: {workflow.results.affirmations.length}</p>
                  )}
                  {workflow.results.visual_posts && (
                    <p>Visuelle Posts: {workflow.results.visual_posts.length}</p>
                  )}
                  {workflow.results.reels && (
                    <p>Reels: {workflow.results.reels.length}</p>
                  )}
                  {workflow.results.social_content && (
                    <p>Social Content: {workflow.results.social_content.length}</p>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );

  const renderTemplatesTab = () => (
    <div className="templates-overview">
      <h3>Verfügbare Workflow-Templates</h3>
      
      {Object.entries(templates).map(([key, template]) => (
        <div key={key} className="template-card">
          <h4>{template.name}</h4>
          <p>{template.description}</p>
          
          <div className="template-details">
            <div className="template-steps">
              <h5>Schritte:</h5>
              <ol>
                {template.steps.map((step, index) => (
                  <li key={index}>{step}</li>
                ))}
              </ol>
            </div>
            
            <div className="template-options">
              <h5>Standard-Optionen:</h5>
              <ul>
                {Object.entries(template.default_options).map(([option, value]) => (
                  <li key={option}>
                    <strong>{option}:</strong> {JSON.stringify(value)}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      ))}
    </div>
  );

  return (
    <ProjectRequired>
    <div className="workflow-management">
      <div className="header">
        <h2>🔄 Workflow Management</h2>
        <p>Orchestriere komplette Content-Workflows von Affirmationen bis zu geplanten Posts und Reels</p>
      </div>

      {error && (
        <div className="error-banner">
          <strong>Fehler:</strong> {error}
          <button onClick={() => setError(null)}>✖</button>
        </div>
      )}

      <div className="tabs">
        <button 
          className={activeTab === 'create' ? 'active' : ''}
          onClick={() => setActiveTab('create')}
        >
          Workflow erstellen
        </button>
        <button 
          className={activeTab === 'manage' ? 'active' : ''}
          onClick={() => setActiveTab('manage')}
        >
          Workflows verwalten
        </button>
        <button 
          className={activeTab === 'templates' ? 'active' : ''}
          onClick={() => setActiveTab('templates')}
        >
          Templates
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'create' && renderCreateTab()}
        {activeTab === 'manage' && renderManageTab()}
        {activeTab === 'templates' && renderTemplatesTab()}
      </div>
    </div>
    </ProjectRequired>
  );
};

export default WorkflowManagement;
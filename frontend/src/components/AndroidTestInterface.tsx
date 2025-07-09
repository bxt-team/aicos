import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Upload, Play, FileSearch, AlertTriangle, CheckCircle, XCircle, Smartphone, Activity, Eye, Zap, Copy, ChevronDown, ChevronUp, X, Info, Trash2, Clock, ChevronLeft, ChevronRight } from 'lucide-react';
import './AndroidTestInterface.css';

interface TestResult {
  test_id: string;
  package_name: string;
  timestamp: string;
  app_launches: boolean;
  errors: string[];
  performance: {
    metrics: {
      startup_time_ms?: number;
      cpu_usage_percent?: number;
      memory_usage_mb?: number;
      janky_frames?: number;
    };
    issues: Array<{
      type: string;
      severity: string;
      value: number;
      threshold?: number;
      description: string;
    }>;
  };
  navigation: {
    actions_performed: number;
    crashes_detected: number;
    screens_accessed: number;
  };
  accessibility: {
    accessible: boolean;
    score: number;
    issues: Array<{
      type: string;
      severity: string;
      description: string;
      count?: number;
      elements?: Array<{
        id?: string;
        class?: string;
        bounds?: string;
        text?: string;
      }>;
    }>;
  };
  ux_recommendations: Array<{
    category: string;
    priority: string;
    title: string;
    description: string;
  }>;
  screenshots: {
    initial?: string;
    action_count?: number;
  };
}

interface TestSummary {
  test_id: string;
  package_name: string;
  timestamp: string;
  success: boolean;
  crash_count: number;
  startup_time_seconds?: number;
}

const AndroidTestInterface: React.FC = () => {
  const [apkPath, setApkPath] = useState('');
  const [apkFile, setApkFile] = useState<File | null>(null);
  const [testActions, setTestActions] = useState<string[]>(['tap_all_buttons', 'scroll_all_views', 'input_text_fields']);
  const [targetApiLevel, setTargetApiLevel] = useState<number | null>(null);
  const [avdName, setAvdName] = useState('');
  const [availableAvds, setAvailableAvds] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [testId, setTestId] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [recentTests, setRecentTests] = useState<TestSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [polling, setPolling] = useState(false);
  const [screenshots, setScreenshots] = useState<Array<{
    name: string;
    url: string;
    action?: string;
    description?: string;
    ui_elements?: {
      input_fields?: Array<{type: string; text: string; hint: string; filled: boolean}>;
      buttons?: Array<{type: string; text: string}>;
      total_elements?: number;
    };
  }>>([]);
  const [selectedScreenshot, setSelectedScreenshot] = useState<number | null>(null);
  const [copiedPrompt, setCopiedPrompt] = useState<string | null>(null);
  const [expandedIssues, setExpandedIssues] = useState<Set<string>>(new Set());
  const [modalData, setModalData] = useState<{
    isOpen: boolean;
    type: string;
    issue: any;
    prompt: string;
  }>({ isOpen: false, type: '', issue: null, prompt: '' });
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const API_BASE = 'http://localhost:8000';

  // Load recent tests and available AVDs on mount
  useEffect(() => {
    loadRecentTests();
    loadAvailableAvds();
  }, []);

  // Poll for test results when test is running
  useEffect(() => {
    if (testId && polling) {
      const interval = setInterval(async () => {
        try {
          const response = await axios.get(`${API_BASE}/api/android-test/${testId}`);
          setTestResult(response.data);
          setPolling(false);
          loadScreenshots(testId);
        } catch (err: any) {
          if (err.response?.status !== 404) {
            console.error('Error polling test results:', err);
          }
        }
      }, 2000);

      return () => clearInterval(interval);
    }
  }, [testId, polling]);

  const loadRecentTests = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/android-tests`);
      if (response.data.success) {
        setRecentTests(response.data.data);
      }
    } catch (err) {
      console.error('Error loading recent tests:', err);
    }
  };

  const loadAvailableAvds = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/android-avds`);
      if (response.data.success && response.data.avds.length > 0) {
        setAvailableAvds(response.data.avds);
        // Set first AVD as default if none selected
        if (!avdName && response.data.avds.length > 0) {
          setAvdName(response.data.avds[0]);
        }
      }
    } catch (err) {
      console.error('Error loading available AVDs:', err);
    }
  };

  const loadScreenshots = async (testId: string) => {
    try {
      const response = await axios.get(`${API_BASE}/api/android-test/${testId}/screenshots`);
      if (response.data.success) {
        setScreenshots(response.data.screenshots);
      }
    } catch (err) {
      console.error('Error loading screenshots:', err);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.name.endsWith('.apk')) {
      setApkFile(file);
      setApkPath(file.name);
      setError(null);
    } else if (file) {
      setError('Please select a valid APK file');
    }
  };

  const startTest = async () => {
    if (!apkPath && !apkFile) {
      setError('Please select an APK file');
      return;
    }

    setLoading(true);
    setError(null);
    setTestResult(null);
    setScreenshots([]);

    try {
      let apkPathToUse = apkPath;
      
      // If a file was selected through the file input, upload it first
      if (apkFile) {
        setLoadingMessage('APK-Datei wird hochgeladen...');
        const formData = new FormData();
        formData.append('file', apkFile);
        
        try {
          const uploadResponse = await axios.post(`${API_BASE}/api/android-test/upload-apk`, formData, {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          });
          
          if (uploadResponse.data.success) {
            apkPathToUse = uploadResponse.data.file_path;
          } else {
            throw new Error('Failed to upload APK file');
          }
        } catch (uploadErr: any) {
          setError(uploadErr.response?.data?.detail || 'Failed to upload APK file');
          setLoading(false);
          setLoadingMessage('');
          return;
        }
      }
      
      // Now start the test with the correct APK path
      setLoadingMessage('Test wird gestartet...');
      const response = await axios.post(`${API_BASE}/api/android-test`, {
        apk_path: apkPathToUse,
        test_actions: testActions.length > 0 ? testActions : null,
        target_api_level: targetApiLevel,
        avd_name: avdName || null
      });

      if (response.data.success) {
        setTestId(response.data.test_id);
        setPolling(true);
        setLoadingMessage('');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start test');
    } finally {
      setLoading(false);
      setLoadingMessage('');
    }
  };

  const loadTest = async (testId: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.get(`${API_BASE}/api/android-test/${testId}`);
      setTestResult(response.data);
      setTestId(testId);
      loadScreenshots(testId);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load test results');
    } finally {
      setLoading(false);
    }
  };

  const deleteTest = async (testId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    
    if (!window.confirm('Möchten Sie diesen Test wirklich löschen?')) {
      return;
    }

    try {
      const response = await axios.delete(`${API_BASE}/api/android-test/${testId}`);
      if (response.data.success) {
        // Refresh the test list
        await loadRecentTests();
        // Clear current test if it was deleted
        if (testResult?.test_id === testId) {
          setTestResult(null);
          setTestId(null);
          setScreenshots([]);
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Fehler beim Löschen des Tests');
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return '#dc2626';
      case 'high': return '#f59e0b';
      case 'medium': return '#3b82f6';
      case 'low': return '#10b981';
      default: return '#6b7280';
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'critical': return <AlertTriangle className="w-5 h-5" style={{ color: '#dc2626' }} />;
      case 'high': return <AlertTriangle className="w-5 h-5" style={{ color: '#f59e0b' }} />;
      case 'medium': return <Activity className="w-5 h-5" style={{ color: '#3b82f6' }} />;
      case 'low': return <CheckCircle className="w-5 h-5" style={{ color: '#10b981' }} />;
      default: return null;
    }
  };

  const generateClaudePrompt = (type: string, issue: any) => {
    let prompt = '';
    
    if (type === 'accessibility') {
      switch (issue.type) {
        case 'missing_content_description':
          prompt = `Fix accessibility issue: Add content descriptions to ${issue.count || 'all'} UI elements that are missing them for screen reader support. Search for ImageView, ImageButton, and other visual elements without contentDescription attributes and add descriptive text.`;
          break;
        case 'small_touch_target':
          prompt = `Fix accessibility issue: Increase touch target sizes to at least 48x48dp for better usability. Search for clickable elements with small dimensions and update their minWidth/minHeight or add padding.`;
          break;
        default:
          prompt = `Fix accessibility issue: ${issue.description}`;
      }
    } else if (type === 'ux') {
      switch (issue.title) {
        case 'Add Content Descriptions':
          prompt = `Improve accessibility: Add meaningful content descriptions to all UI elements, especially images, buttons, and icons. This helps users with screen readers navigate your app.`;
          break;
        case 'Increase Touch Target Sizes':
          prompt = `Improve UX: Ensure all interactive elements have a minimum touch target size of 48x48dp. Add padding or increase dimensions for small buttons and clickable areas.`;
          break;
        case 'Implement User Onboarding':
          prompt = `Add user onboarding: Create a tutorial or onboarding flow for first-time users. This could include a welcome screen, feature highlights, or an interactive walkthrough of key functionality.`;
          break;
        default:
          prompt = `Improve ${issue.category}: ${issue.description}`;
      }
    } else if (type === 'performance') {
      switch (issue.type) {
        case 'high_startup_time':
          prompt = `Fix performance issue: Reduce app startup time from ${issue.value}ms. Optimize initialization code, lazy load heavy resources, defer non-critical work, and consider using App Startup library for efficient component initialization.`;
          break;
        case 'high_memory_usage':
          prompt = `Fix memory issue: Reduce memory usage (currently ${issue.value}MB). Look for memory leaks, optimize bitmap usage, implement proper caching strategies, and ensure proper cleanup in onDestroy methods.`;
          break;
        case 'janky_frames':
          prompt = `Fix UI performance: Reduce janky frames (${issue.value} detected). Profile the UI thread, optimize layouts, reduce overdraw, use RecyclerView for lists, and move heavy operations off the main thread.`;
          break;
        case 'high_cpu_usage':
          prompt = `Fix CPU usage: Optimize high CPU usage (${issue.value}%). Profile your app to find CPU-intensive operations, optimize algorithms, use background threads for heavy work, and implement efficient data structures.`;
          break;
        default:
          prompt = `Fix performance issue: ${issue.description}`;
      }
    }
    
    return prompt;
  };

  const copyPrompt = (prompt: string, id: string) => {
    navigator.clipboard.writeText(prompt);
    setCopiedPrompt(id);
    setTimeout(() => setCopiedPrompt(null), 2000);
  };

  const toggleIssueExpanded = (issueId: string) => {
    const newExpanded = new Set(expandedIssues);
    if (newExpanded.has(issueId)) {
      newExpanded.delete(issueId);
    } else {
      newExpanded.add(issueId);
    }
    setExpandedIssues(newExpanded);
  };

  const shouldShowClaudePrompt = (issue: any) => {
    // Don't show Claude prompt if issue is resolved (count is 0 or score is 100%)
    if (issue.count === 0) return false;
    if (issue.severity === 'resolved' || issue.severity === 'none') return false;
    return true;
  };

  const openPromptModal = (type: string, issue: any, prompt: string) => {
    setModalData({
      isOpen: true,
      type,
      issue,
      prompt
    });
  };

  const closeModal = () => {
    setModalData({ isOpen: false, type: '', issue: null, prompt: '' });
  };

  return (
    <div className="android-test-interface">
      <div className="header">
        <h1>
          <Smartphone className="inline-icon" />
          Android App Testing Agent
        </h1>
        <p>Automated QA & Performance Analysis for Android Apps</p>
      </div>

      {/* Test Configuration */}
      <div className="config-section">
        <h2>Test-Konfiguration</h2>
        <div className="form-grid">
          <div className="form-group">
            <label htmlFor="apk-path">
              <Upload className="inline-icon" />
              APK-Datei
            </label>
            <div className="file-input-wrapper">
              <input
                ref={fileInputRef}
                type="file"
                accept=".apk"
                onChange={handleFileSelect}
                style={{ display: 'none' }}
                disabled={loading || polling}
              />
              <input
                id="apk-path"
                type="text"
                value={apkPath}
                onChange={(e) => {
                  setApkPath(e.target.value);
                  setApkFile(null);
                }}
                placeholder="APK-Datei auswählen oder Pfad eingeben"
                disabled={loading || polling}
                className="file-path-input"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={loading || polling}
                className="file-select-button"
              >
                <FileSearch className="w-4 h-4" />
                Durchsuchen
              </button>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="avd-name">
              <Smartphone className="inline-icon" />
              AVD Name (Optional)
            </label>
            {availableAvds.length > 0 ? (
              <select
                id="avd-name"
                value={avdName}
                onChange={(e) => setAvdName(e.target.value)}
                disabled={loading || polling}
                className="avd-select"
              >
                <option value="">Standard AVD verwenden</option>
                {availableAvds.map((avd) => (
                  <option key={avd} value={avd}>
                    {avd}
                  </option>
                ))}
              </select>
            ) : (
              <input
                id="avd-name"
                type="text"
                value={avdName}
                onChange={(e) => setAvdName(e.target.value)}
                placeholder="Pixel_4_API_30"
                disabled={loading || polling}
              />
            )}
          </div>

          <div className="form-group">
            <label htmlFor="api-level">
              <Activity className="inline-icon" />
              Target API Level (Optional)
            </label>
            <input
              id="api-level"
              type="number"
              value={targetApiLevel || ''}
              onChange={(e) => setTargetApiLevel(e.target.value ? parseInt(e.target.value) : null)}
              placeholder="30"
              min="21"
              max="34"
              disabled={loading || polling}
            />
          </div>

          <div className="form-group actions-group">
            <label>
              <Play className="inline-icon" />
              Test-Aktionen
            </label>
            <div className="checkbox-group">
              <label>
                <input
                  type="checkbox"
                  checked={testActions.includes('tap_all_buttons')}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setTestActions([...testActions, 'tap_all_buttons']);
                    } else {
                      setTestActions(testActions.filter(a => a !== 'tap_all_buttons'));
                    }
                  }}
                  disabled={loading || polling}
                />
                Alle Buttons tappen
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={testActions.includes('scroll_all_views')}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setTestActions([...testActions, 'scroll_all_views']);
                    } else {
                      setTestActions(testActions.filter(a => a !== 'scroll_all_views'));
                    }
                  }}
                  disabled={loading || polling}
                />
                Alle Views scrollen
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={testActions.includes('input_text_fields')}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setTestActions([...testActions, 'input_text_fields']);
                    } else {
                      setTestActions(testActions.filter(a => a !== 'input_text_fields'));
                    }
                  }}
                  disabled={loading || polling}
                />
                Text-Felder ausfüllen
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={testActions.includes('check_permissions')}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setTestActions([...testActions, 'check_permissions']);
                    } else {
                      setTestActions(testActions.filter(a => a !== 'check_permissions'));
                    }
                  }}
                  disabled={loading || polling}
                />
                Berechtigungen prüfen
              </label>
            </div>
          </div>
        </div>

        <button
          className="start-test-button"
          onClick={startTest}
          disabled={loading || polling || !apkPath}
        >
          {loading ? (
            <>
              <div className="spinner" />
              {loadingMessage || 'Test wird gestartet...'}
            </>
          ) : polling ? (
            <>
              <div className="spinner" />
              Test läuft...
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              Test starten
            </>
          )}
        </button>

        {error && (
          <div className="error-message">
            <XCircle className="w-5 h-5" />
            {error}
          </div>
        )}
      </div>

      {/* Test Results */}
      {testResult && (
        <div className="results-section">
          <h2>Test-Ergebnisse</h2>
          
          {/* Summary */}
          <div className="summary-card">
            <div className="summary-header">
              <h3>{testResult.package_name}</h3>
              <span className={`status-badge ${testResult.app_launches ? 'success' : 'error'}`}>
                {testResult.app_launches ? (
                  <>
                    <CheckCircle className="w-4 h-4" />
                    App startet erfolgreich
                  </>
                ) : (
                  <>
                    <XCircle className="w-4 h-4" />
                    App-Start fehlgeschlagen
                  </>
                )}
              </span>
            </div>
            <div className="summary-stats">
              <div className="stat">
                <span className="stat-value">{((testResult.performance?.metrics?.startup_time_ms || 0) / 1000).toFixed(2)}s</span>
                <span className="stat-label">Startzeit</span>
              </div>
              <div className="stat">
                <span className="stat-value">{testResult.navigation?.crashes_detected || 0}</span>
                <span className="stat-label">Abstürze</span>
              </div>
              <div className="stat">
                <span className="stat-value">{testResult.navigation?.screens_accessed || 0}</span>
                <span className="stat-label">Getestete Screens</span>
              </div>
              <div className="stat">
                <span className="stat-value">{testResult.accessibility?.score || 0}%</span>
                <span className="stat-label">Barrierefreiheit</span>
              </div>
            </div>
          </div>

          {/* Errors */}
          {testResult.errors && testResult.errors.length > 0 && (
            <div className="errors-section">
              <h3>
                <AlertTriangle className="inline-icon" />
                Gefundene Fehler
              </h3>
              <div className="error-list">
                {testResult.errors.map((error, index) => (
                  <div key={index} className="error-item">
                    {error}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Performance Issues */}
          {testResult.performance?.issues?.length > 0 && (
            <div className="performance-section">
              <h3>
                <Zap className="inline-icon" />
                Performance-Probleme
              </h3>
              <div className="issues-grid">
                {testResult.performance?.issues?.map((issue, index) => {
                  const promptId = `performance-${index}`;
                  const prompt = generateClaudePrompt('performance', issue);
                  return (
                    <div key={index} className="issue-card">
                      <div className="issue-header">
                        <span className="issue-type">{issue.type}</span>
                        <span 
                          className="severity-badge"
                          style={{ backgroundColor: getSeverityColor(issue.severity) }}
                        >
                          {issue.severity}
                        </span>
                      </div>
                      <p>{issue.description}</p>
                      <div className="issue-metrics">
                        <span>Value: {issue.value}</span>
                        {issue.threshold && <span>Threshold: {issue.threshold}</span>}
                      </div>
                      <button 
                        className="view-details-button"
                        onClick={() => openPromptModal('performance', issue, prompt)}
                        title="View details and Claude Code prompt"
                      >
                        <Info className="w-4 h-4" />
                        View Details & Prompt
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Accessibility Issues */}
          {testResult.accessibility?.issues?.length > 0 && (
            <div className="accessibility-section">
              <h3>
                <Eye className="inline-icon" />
                Barrierefreiheit
              </h3>
              <div className="issues-grid">
                {testResult.accessibility?.issues?.map((issue, index) => {
                  const promptId = `accessibility-${index}`;
                  const issueId = `accessibility-issue-${index}`;
                  const prompt = generateClaudePrompt('accessibility', issue);
                  const isExpanded = expandedIssues.has(issueId);
                  const hasDetails = issue.elements && issue.elements.length > 0;
                  const showPrompt = shouldShowClaudePrompt(issue);
                  
                  return (
                    <div key={index} className="issue-card">
                      <div className="issue-header">
                        <span className="issue-type">{issue.type}</span>
                        <span 
                          className="severity-badge"
                          style={{ backgroundColor: getSeverityColor(issue.severity) }}
                        >
                          {issue.severity}
                        </span>
                      </div>
                      <p>{issue.description}</p>
                      {issue.count !== undefined && <span className="issue-count">Anzahl: {issue.count}</span>}
                      
                      {hasDetails && (
                        <button 
                          className="expand-details-button"
                          onClick={() => toggleIssueExpanded(issueId)}
                        >
                          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                          {isExpanded ? 'Details ausblenden' : 'Details anzeigen'}
                        </button>
                      )}
                      
                      {isExpanded && hasDetails && (
                        <div className="issue-details">
                          <h4>Betroffene Elemente:</h4>
                          <div className="elements-list">
                            {issue.elements!.map((element, elemIndex) => (
                              <div key={elemIndex} className="element-item">
                                {element.class && <span className="element-class">{element.class}</span>}
                                {element.id && <span className="element-id">ID: {element.id}</span>}
                                {element.text && <span className="element-text">Text: "{element.text}"</span>}
                                {element.bounds && <span className="element-bounds">Position: {element.bounds}</span>}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {showPrompt && (
                        <button 
                          className="view-details-button"
                          onClick={() => openPromptModal('accessibility', issue, prompt)}
                          title="View details and Claude Code prompt"
                        >
                          <Info className="w-4 h-4" />
                          View Details & Prompt
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* UX Recommendations */}
          {testResult.ux_recommendations?.length > 0 && (
            <div className="recommendations-section">
              <h3>
                <Activity className="inline-icon" />
                UX-Empfehlungen
              </h3>
              <div className="recommendations-list">
                {testResult.ux_recommendations?.map((rec, index) => {
                  const promptId = `ux-${index}`;
                  const prompt = generateClaudePrompt('ux', rec);
                  return (
                    <div key={index} className="recommendation-item">
                      <div className="recommendation-header">
                        {getPriorityIcon(rec.priority)}
                        <span className="recommendation-title">{rec.title}</span>
                        <span className="recommendation-category">{rec.category}</span>
                      </div>
                      <p>{rec.description}</p>
                      <button 
                        className="view-details-button"
                        onClick={() => openPromptModal('ux', rec, prompt)}
                        title="View details and Claude Code prompt"
                      >
                        <Info className="w-4 h-4" />
                        View Details & Prompt
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Screenshots */}
          {screenshots.length > 0 && (
            <div className="screenshots-section">
              <h3>
                <FileSearch className="inline-icon" />
                Screenshots
              </h3>
              <div className="screenshots-grid">
                {screenshots.map((screenshot, index) => (
                  <div 
                    key={index} 
                    className="screenshot-item"
                    onClick={() => setSelectedScreenshot(index)}
                  >
                    <img src={`${API_BASE}${screenshot.url}`} alt={screenshot.name} />
                    <div className="screenshot-info">
                      <span className="screenshot-name">{screenshot.name}</span>
                      {screenshot.action && (
                        <span className="screenshot-action">{screenshot.action}</span>
                      )}
                      {screenshot.description && (
                        <div className="screenshot-description">{screenshot.description}</div>
                      )}
                      {screenshot.ui_elements && (
                        <div className="screenshot-elements">
                          {screenshot.ui_elements.input_fields && screenshot.ui_elements.input_fields.length > 0 && (
                            <span>📝 {screenshot.ui_elements.input_fields.length} input fields 
                              ({screenshot.ui_elements.input_fields.filter(f => f.filled).length} filled)
                            </span>
                          )}
                          {screenshot.ui_elements.buttons && screenshot.ui_elements.buttons.length > 0 && (
                            <span>🔘 {screenshot.ui_elements.buttons.length} buttons</span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Recent Tests */}
      <div className="recent-tests-section">
        <h2>Letzte Tests</h2>
        <div className="tests-grid">
          {recentTests.map((test) => (
            <div 
              key={test.test_id} 
              className="test-card"
              onClick={() => loadTest(test.test_id)}
            >
              <div className="test-header">
                <span className="package-name">{test.package_name}</span>
                <div className="test-header-actions">
                  <span className={`test-status ${test.success ? 'success' : 'failed'}`}>
                    {test.success ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                  </span>
                  <button 
                    className="delete-test-button"
                    onClick={(e) => deleteTest(test.test_id, e)}
                    title="Test löschen"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <div className="test-info">
                <span>Abstürze: {test.crash_count}</span>
                {test.startup_time_seconds !== undefined && (
                  <span className="startup-time">
                    <Clock className="w-3 h-3" />
                    {test.startup_time_seconds}s
                  </span>
                )}
                <span>{new Date(test.timestamp).toLocaleString('de-DE')}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Detailed Screenshot Modal */}
      {selectedScreenshot !== null && screenshots[selectedScreenshot] && (
        <div className="screenshot-detail-modal" onClick={() => setSelectedScreenshot(null)}>
          <div className="screenshot-detail-content" onClick={(e) => e.stopPropagation()}>
            <div className="screenshot-detail-header">
              <h3>Screenshot Details</h3>
              <button className="close-button" onClick={() => setSelectedScreenshot(null)}>
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="screenshot-detail-body">
              <div className="screenshot-preview">
                <img src={`${API_BASE}${screenshots[selectedScreenshot]?.url}`} alt={screenshots[selectedScreenshot]?.name} />
                <div className="screenshot-navigation">
                  <button 
                    className="nav-button"
                    onClick={() => setSelectedScreenshot(Math.max(0, selectedScreenshot - 1))}
                    disabled={selectedScreenshot === 0}
                  >
                    <ChevronLeft className="w-5 h-5" />
                    Previous
                  </button>
                  <span className="screenshot-counter">
                    {selectedScreenshot + 1} / {screenshots.length}
                  </span>
                  <button 
                    className="nav-button"
                    onClick={() => setSelectedScreenshot(Math.min(screenshots.length - 1, selectedScreenshot + 1))}
                    disabled={selectedScreenshot === screenshots.length - 1}
                  >
                    Next
                    <ChevronRight className="w-5 h-5" />
                  </button>
                </div>
              </div>
              
              <div className="screenshot-details">
                <h4>{screenshots[selectedScreenshot]?.name}</h4>
                {screenshots[selectedScreenshot]?.action && (
                  <div className="detail-section">
                    <strong>Action Performed:</strong>
                    <p>{screenshots[selectedScreenshot]?.action}</p>
                  </div>
                )}
                
                {screenshots[selectedScreenshot]?.description && (
                  <div className="detail-section">
                    <strong>Screen Description:</strong>
                    <p className="description-full">{screenshots[selectedScreenshot]?.description}</p>
                  </div>
                )}
                
                {screenshots[selectedScreenshot]?.ui_elements && (
                  <div className="detail-section">
                    <strong>UI Elements Found:</strong>
                    <div className="ui-elements-summary">
                      {screenshots[selectedScreenshot]?.ui_elements?.input_fields && (screenshots[selectedScreenshot]?.ui_elements?.input_fields?.length || 0) > 0 && (
                        <div>
                          <span className="element-type">Input Fields:</span>
                          <ul>
                            {screenshots[selectedScreenshot]?.ui_elements?.input_fields?.map((field: any, idx: number) => (
                              <li key={idx}>
                                {field.hint || field.text || 'Unnamed field'} - 
                                {field.filled ? ' ✓ Filled' : ' ✗ Empty'}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {screenshots[selectedScreenshot]?.ui_elements?.buttons && (screenshots[selectedScreenshot]?.ui_elements?.buttons?.length || 0) > 0 && (
                        <div>
                          <span className="element-type">Buttons:</span>
                          <ul>
                            {screenshots[selectedScreenshot]?.ui_elements?.buttons?.slice(0, 10).map((button: any, idx: number) => (
                              <li key={idx}>{button.text || 'Unnamed button'}</li>
                            ))}
                            {(screenshots[selectedScreenshot]?.ui_elements?.buttons?.length || 0) > 10 && (
                              <li className="more-items">... and {(screenshots[selectedScreenshot]?.ui_elements?.buttons?.length || 0) - 10} more</li>
                            )}
                          </ul>
                        </div>
                      )}
                      {screenshots[selectedScreenshot]?.ui_elements?.total_elements && (
                        <div>
                          <span className="element-type">Total Interactive Elements:</span> {screenshots[selectedScreenshot]?.ui_elements?.total_elements}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Prompt Modal */}
      {modalData.isOpen && (
        <div className="prompt-modal-overlay" onClick={closeModal}>
          <div className="prompt-modal" onClick={(e) => e.stopPropagation()}>
            <div className="prompt-modal-header">
              <h3>Fix Details & Claude Code Prompt</h3>
              <button className="prompt-modal-close" onClick={closeModal}>
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="prompt-modal-body">
              {/* Issue Details */}
              <div className="prompt-modal-section">
                <h4>Issue Details</h4>
                {modalData.type === 'performance' && (
                  <>
                    <p><strong>Type:</strong> {modalData.issue.type.replace(/_/g, ' ')}</p>
                    <p><strong>Severity:</strong> {modalData.issue.severity}</p>
                    <p><strong>Current Value:</strong> {modalData.issue.value}</p>
                    {modalData.issue.threshold && (
                      <p><strong>Threshold:</strong> {modalData.issue.threshold}</p>
                    )}
                    <p><strong>Description:</strong> {modalData.issue.description}</p>
                  </>
                )}
                {modalData.type === 'accessibility' && (
                  <>
                    <p><strong>Type:</strong> {modalData.issue.type.replace(/_/g, ' ')}</p>
                    <p><strong>Severity:</strong> {modalData.issue.severity}</p>
                    {modalData.issue.count && (
                      <p><strong>Affected Elements:</strong> {modalData.issue.count}</p>
                    )}
                    <p><strong>Description:</strong> {modalData.issue.description}</p>
                  </>
                )}
                {modalData.type === 'ux' && (
                  <>
                    <p><strong>Category:</strong> {modalData.issue.category}</p>
                    <p><strong>Priority:</strong> {modalData.issue.priority}</p>
                    <p><strong>Title:</strong> {modalData.issue.title}</p>
                    <p><strong>Description:</strong> {modalData.issue.description}</p>
                  </>
                )}
              </div>
              
              {/* Element Details for Accessibility Issues */}
              {modalData.type === 'accessibility' && modalData.issue.elements && modalData.issue.elements.length > 0 && (
                <div className="prompt-modal-section">
                  <h4>Affected Elements ({modalData.issue.elements.length})</h4>
                  <div className="prompt-code-block">
                    {modalData.issue.elements.slice(0, 10).map((element: any, index: number) => (
                      <div key={index} style={{ marginBottom: '0.5rem' }}>
                        {element.class && <span>Class: {element.class} </span>}
                        {element.id && <span>| ID: {element.id} </span>}
                        {element.text && <span>| Text: "{element.text}" </span>}
                        {element.bounds && <span>| Bounds: {element.bounds}</span>}
                      </div>
                    ))}
                    {modalData.issue.elements.length > 10 && (
                      <div style={{ marginTop: '0.5rem', fontStyle: 'italic' }}>
                        ... and {modalData.issue.elements.length - 10} more elements
                      </div>
                    )}
                  </div>
                </div>
              )}
              
              {/* Claude Code Prompt */}
              <div className="prompt-modal-section">
                <h4>Claude Code Prompt</h4>
                <div className="prompt-code-block">
                  {modalData.prompt}
                </div>
              </div>
            </div>
            
            <div className="prompt-modal-footer">
              <button 
                className="copy-prompt-button"
                onClick={() => {
                  copyPrompt(modalData.prompt, 'modal');
                }}
              >
                <Copy className="w-4 h-4" />
                {copiedPrompt === 'modal' ? 'Copied!' : 'Copy Prompt'}
              </button>
              <button 
                className="file-select-button"
                onClick={closeModal}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AndroidTestInterface;
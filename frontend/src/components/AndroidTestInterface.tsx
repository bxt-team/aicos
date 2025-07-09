import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Upload, Play, FileSearch, AlertTriangle, CheckCircle, XCircle, Smartphone, Activity, Eye, Zap } from 'lucide-react';
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
}

const AndroidTestInterface: React.FC = () => {
  const [apkPath, setApkPath] = useState('');
  const [testActions, setTestActions] = useState<string[]>(['tap_all_buttons', 'scroll_all_views']);
  const [targetApiLevel, setTargetApiLevel] = useState<number | null>(null);
  const [avdName, setAvdName] = useState('');
  const [loading, setLoading] = useState(false);
  const [testId, setTestId] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [recentTests, setRecentTests] = useState<TestSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [polling, setPolling] = useState(false);
  const [screenshots, setScreenshots] = useState<Array<{name: string; url: string}>>([]);
  const [selectedScreenshot, setSelectedScreenshot] = useState<string | null>(null);

  const API_BASE = 'http://localhost:8000';

  // Load recent tests on mount
  useEffect(() => {
    loadRecentTests();
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

  const startTest = async () => {
    if (!apkPath) {
      setError('Please enter the APK file path');
      return;
    }

    setLoading(true);
    setError(null);
    setTestResult(null);
    setScreenshots([]);

    try {
      const response = await axios.post(`${API_BASE}/api/android-test`, {
        apk_path: apkPath,
        test_actions: testActions.length > 0 ? testActions : null,
        target_api_level: targetApiLevel,
        avd_name: avdName || null
      });

      if (response.data.success) {
        setTestId(response.data.test_id);
        setPolling(true);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start test');
    } finally {
      setLoading(false);
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

  return (
    <div className="android-test-interface">
      <div className="header">
        <h1>
          <Smartphone className="inline-icon" />
          Android App Testing Agent
        </h1>
        <p>Automatisierte QA & Performance-Analyse für Android Apps</p>
      </div>

      {/* Test Configuration */}
      <div className="config-section">
        <h2>Test-Konfiguration</h2>
        <div className="form-grid">
          <div className="form-group">
            <label htmlFor="apk-path">
              <Upload className="inline-icon" />
              APK-Dateipfad
            </label>
            <input
              id="apk-path"
              type="text"
              value={apkPath}
              onChange={(e) => setApkPath(e.target.value)}
              placeholder="/path/to/app.apk"
              disabled={loading || polling}
            />
          </div>

          <div className="form-group">
            <label htmlFor="avd-name">
              <Smartphone className="inline-icon" />
              AVD Name (Optional)
            </label>
            <input
              id="avd-name"
              type="text"
              value={avdName}
              onChange={(e) => setAvdName(e.target.value)}
              placeholder="Pixel_4_API_30"
              disabled={loading || polling}
            />
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
              Test wird gestartet...
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
                <span className="stat-value">{testResult.performance.metrics.startup_time_ms || 0}ms</span>
                <span className="stat-label">Startzeit</span>
              </div>
              <div className="stat">
                <span className="stat-value">{testResult.navigation.crashes_detected}</span>
                <span className="stat-label">Crashes</span>
              </div>
              <div className="stat">
                <span className="stat-value">{testResult.navigation.screens_accessed}</span>
                <span className="stat-label">Screens getestet</span>
              </div>
              <div className="stat">
                <span className="stat-value">{testResult.accessibility.score}%</span>
                <span className="stat-label">Accessibility Score</span>
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
          {testResult.performance.issues.length > 0 && (
            <div className="performance-section">
              <h3>
                <Zap className="inline-icon" />
                Performance-Probleme
              </h3>
              <div className="issues-grid">
                {testResult.performance.issues.map((issue, index) => (
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
                      <span>Wert: {issue.value}</span>
                      {issue.threshold && <span>Schwellwert: {issue.threshold}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Accessibility Issues */}
          {testResult.accessibility.issues.length > 0 && (
            <div className="accessibility-section">
              <h3>
                <Eye className="inline-icon" />
                Barrierefreiheit
              </h3>
              <div className="issues-grid">
                {testResult.accessibility.issues.map((issue, index) => (
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
                    {issue.count && <span className="issue-count">Anzahl: {issue.count}</span>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* UX Recommendations */}
          {testResult.ux_recommendations.length > 0 && (
            <div className="recommendations-section">
              <h3>
                <Activity className="inline-icon" />
                UX-Empfehlungen
              </h3>
              <div className="recommendations-list">
                {testResult.ux_recommendations.map((rec, index) => (
                  <div key={index} className="recommendation-item">
                    <div className="recommendation-header">
                      {getPriorityIcon(rec.priority)}
                      <span className="recommendation-title">{rec.title}</span>
                      <span className="recommendation-category">{rec.category}</span>
                    </div>
                    <p>{rec.description}</p>
                  </div>
                ))}
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
                    onClick={() => setSelectedScreenshot(screenshot.url)}
                  >
                    <img src={`${API_BASE}${screenshot.url}`} alt={screenshot.name} />
                    <span>{screenshot.name}</span>
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
                <span className={`test-status ${test.success ? 'success' : 'failed'}`}>
                  {test.success ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                </span>
              </div>
              <div className="test-info">
                <span>Crashes: {test.crash_count}</span>
                <span>{new Date(test.timestamp).toLocaleString('de-DE')}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Screenshot Modal */}
      {selectedScreenshot && (
        <div className="screenshot-modal" onClick={() => setSelectedScreenshot(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <img src={`${API_BASE}${selectedScreenshot}`} alt="Screenshot" />
            <button className="close-button" onClick={() => setSelectedScreenshot(null)}>
              <XCircle className="w-6 h-6" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AndroidTestInterface;
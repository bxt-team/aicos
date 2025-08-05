import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './MobileAnalyticsInterface.css';
import MobileAnalyticsDashboard from './MobileAnalyticsDashboard';
import { } from '../types/mobileAnalytics';

interface AppStoreAnalysis {
  app_id: string;
  app_name?: string;
  analysis_timestamp: string;
  listing_data?: any;
  listing_analysis: any;
  keyword_insights: any;
  review_sentiment?: {
    overall_sentiment: number;
    sentiment_label: string;
    positive_percentage: number;
    negative_percentage: number;
    neutral_percentage: number;
    common_themes: any[];
    pain_points: any[];
    positive_highlights: any[];
  };
  visual_assessment?: any;
  optimization_score?: {
    score: number;
    grade: string;
    issues: string[];
    strengths: string[];
  };
  recommendations: any[];
  competitive_insights?: any;
}

interface AnalysisRequest {
  url?: string;
  bundle_id?: string;
  include_reviews: boolean;
  include_visuals: boolean;
}

const MobileAnalyticsInterface: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'ios' | 'android' | 'meta' | 'analytics'>('ios');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // App Store Analysis State
  const [appStoreUrl, setAppStoreUrl] = useState('');
  const [bundleId, setBundleId] = useState('');
  const [includeReviews, setIncludeReviews] = useState(true);
  const [includeVisuals, setIncludeVisuals] = useState(true);
  const [appStoreAnalysis, setAppStoreAnalysis] = useState<AppStoreAnalysis | null>(null);
  
  // Play Store State
  const [playStoreUrl, setPlayStoreUrl] = useState('');
  const [packageId, setPackageId] = useState('');
  const [playStoreAnalysis, setPlayStoreAnalysis] = useState<any>(null);
  const [includePlayStoreReviews, setIncludePlayStoreReviews] = useState(true);
  const [includePlayStoreVisuals, setIncludePlayStoreVisuals] = useState(true);
  const [savedPlayStoreAnalyses, setSavedPlayStoreAnalyses] = useState<any[]>([]);
  const [selectedAnalysisId, setSelectedAnalysisId] = useState<string | null>(null);
  const [showDashboard, setShowDashboard] = useState(false);
  
  // Meta Ads State
  const [campaignId, setCampaignId] = useState('');
  const [accessToken, setAccessToken] = useState('');
  const [metaDateRange, setMetaDateRange] = useState({ start: '', end: '' });
  const [metaAnalysis, setMetaAnalysis] = useState<any>(null);
  
  // Google Analytics State
  const [propertyId, setPropertyId] = useState('');
  const [appId, setAppId] = useState('');
  const [gaDateRange, setGaDateRange] = useState({ start: '', end: '' });
  const [gaAnalysis, setGaAnalysis] = useState<any>(null);

  // Fetch saved Play Store analyses on mount and after new analysis
  useEffect(() => {
    if (activeTab === 'android') {
      fetchSavedPlayStoreAnalyses();
    }
  }, [activeTab]);

  const fetchSavedPlayStoreAnalyses = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/mobile-analytics/play-store/analyses');
      setSavedPlayStoreAnalyses(response.data.analyses || []);
    } catch (err) {
      console.error('Failed to fetch saved analyses:', err);
    }
  };

  const viewAnalysisDetails = async (analysisId: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get(`http://localhost:8000/api/mobile-analytics/play-store/analyses/${analysisId}`);
      setPlayStoreAnalysis(response.data);
      setSelectedAnalysisId(analysisId);
      setShowDashboard(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analysis details');
    } finally {
      setLoading(false);
    }
  };

  const deleteAnalysis = async (analysisId: string) => {
    if (!window.confirm('Are you sure you want to delete this analysis?')) {
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      await axios.delete(`http://localhost:8000/api/mobile-analytics/play-store/analyses/${analysisId}`);
      // Refresh the list after deletion
      await fetchSavedPlayStoreAnalyses();
      // If we were viewing the deleted analysis, go back to list
      if (selectedAnalysisId === analysisId) {
        setShowDashboard(false);
        setPlayStoreAnalysis(null);
        setSelectedAnalysisId(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete analysis');
    } finally {
      setLoading(false);
    }
  };

  const analyzeAppStore = async () => {
    if (!appStoreUrl && !bundleId) {
      setError('Please provide either an App Store URL or Bundle ID');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const requestData: AnalysisRequest = {
        url: appStoreUrl || undefined,
        bundle_id: bundleId || undefined,
        include_reviews: includeReviews,
        include_visuals: includeVisuals
      };

      const response = await axios.post(
        'http://localhost:8000/api/mobile-analytics/app-store/analyze',
        requestData
      );

      setAppStoreAnalysis(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze App Store listing');
    } finally {
      setLoading(false);
    }
  };

  const analyzePlayStore = async () => {
    if (!playStoreUrl && !packageId) {
      setError('Please provide either a Play Store URL or Package ID');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const requestData = {
        url: playStoreUrl || undefined,
        package_name: packageId || undefined,
        include_reviews: includePlayStoreReviews,
        include_visuals: includePlayStoreVisuals
      };

      const response = await axios.post(
        'http://localhost:8000/api/mobile-analytics/play-store/analyze',
        requestData
      );

      setPlayStoreAnalysis(response.data);
      // Refresh the list of saved analyses
      await fetchSavedPlayStoreAnalyses();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze Play Store listing');
    } finally {
      setLoading(false);
    }
  };

  const analyzeMetaAds = async () => {
    if (!campaignId) {
      setError('Please provide a Campaign ID');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const requestData: any = {
        campaign_id: campaignId
      };

      // Add access token if provided (for production mode)
      if (accessToken) {
        requestData.access_token = accessToken;
      }

      // Add date range if provided
      if (metaDateRange.start && metaDateRange.end) {
        requestData.date_range = metaDateRange;
      }

      const response = await axios.post(
        'http://localhost:8000/api/mobile-analytics/meta-ads/analyze',
        requestData
      );

      setMetaAnalysis(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze Meta Ads');
    } finally {
      setLoading(false);
    }
  };

  const analyzeGoogleAnalytics = async () => {
    if (!propertyId && !appId) {
      setError('Please provide either a Property ID or App ID');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const requestData: any = {
        property_id: propertyId || undefined,
        app_id: appId || undefined
      };

      // Add date range if provided
      if (gaDateRange.start && gaDateRange.end) {
        requestData.date_range = gaDateRange;
      }

      const response = await axios.post(
        'http://localhost:8000/api/mobile-analytics/google-analytics/analyze',
        requestData
      );

      setGaAnalysis(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze Google Analytics');
    } finally {
      setLoading(false);
    }
  };

  const renderAppStoreTab = () => (
    <div className="tab-content">
      <h3>iOS App Store Analysis</h3>
      
      <div className="input-section">
        <div className="input-group">
          <label>App Store URL</label>
          <input
            type="text"
            value={appStoreUrl}
            onChange={(e) => setAppStoreUrl(e.target.value)}
            placeholder="https://apps.apple.com/us/app/..."
            className="url-input"
          />
        </div>
        
        <div className="divider">OR</div>
        
        <div className="input-group">
          <label>Bundle ID</label>
          <input
            type="text"
            value={bundleId}
            onChange={(e) => setBundleId(e.target.value)}
            placeholder="com.example.app"
            className="bundle-input"
          />
        </div>

        <div className="options-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={includeReviews}
              onChange={(e) => setIncludeReviews(e.target.checked)}
            />
            Include Review Analysis
          </label>
          
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={includeVisuals}
              onChange={(e) => setIncludeVisuals(e.target.checked)}
            />
            Include Visual Assessment
          </label>
        </div>

        <button 
          onClick={analyzeAppStore} 
          disabled={loading}
          className="analyze-button"
        >
          {loading ? 'Analyzing...' : 'Analyze App Store Listing'}
        </button>
      </div>

      {appStoreAnalysis && (
        <div className="analysis-results">
          <h4>Analysis Results</h4>
          
          {/* Dashboard View */}
          <MobileAnalyticsDashboard 
            analysisData={appStoreAnalysis} 
            analysisType="app-store" 
          />
          
          {/* Optimization Score */}
          {appStoreAnalysis.optimization_score && (
            <div className="score-section">
              <div className="score-display">
                <div className="score-circle">
                  <span className="score-number">{appStoreAnalysis.optimization_score.score}</span>
                  <span className="score-grade">{appStoreAnalysis.optimization_score.grade}</span>
                </div>
                <div className="score-details">
                  <h5>Optimization Score</h5>
                  <div className="issues">
                    <strong>Issues:</strong>
                    <ul>
                      {appStoreAnalysis.optimization_score.issues.map((issue, idx) => (
                        <li key={idx}>{issue}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="strengths">
                    <strong>Strengths:</strong>
                    <ul>
                      {appStoreAnalysis.optimization_score.strengths.map((strength, idx) => (
                        <li key={idx}>{strength}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Review Sentiment */}
          {appStoreAnalysis.review_sentiment && (
            <div className="sentiment-section">
              <h5>Review Sentiment Analysis</h5>
              <div className="sentiment-overview">
                <div className="sentiment-score">
                  <span className={`sentiment-label ${appStoreAnalysis.review_sentiment.sentiment_label.toLowerCase().replace(' ', '-')}`}>
                    {appStoreAnalysis.review_sentiment.sentiment_label}
                  </span>
                  <span className="sentiment-value">{appStoreAnalysis.review_sentiment.overall_sentiment.toFixed(3)}</span>
                </div>
                
                <div className="sentiment-distribution">
                  <div className="sentiment-bar">
                    <div 
                      className="positive-bar" 
                      style={{ width: `${appStoreAnalysis.review_sentiment.positive_percentage}%` }}
                    />
                    <div 
                      className="neutral-bar" 
                      style={{ width: `${appStoreAnalysis.review_sentiment.neutral_percentage}%` }}
                    />
                    <div 
                      className="negative-bar" 
                      style={{ width: `${appStoreAnalysis.review_sentiment.negative_percentage}%` }}
                    />
                  </div>
                  <div className="sentiment-labels">
                    <span>Positive: {appStoreAnalysis.review_sentiment.positive_percentage}%</span>
                    <span>Neutral: {appStoreAnalysis.review_sentiment.neutral_percentage}%</span>
                    <span>Negative: {appStoreAnalysis.review_sentiment.negative_percentage}%</span>
                  </div>
                </div>
              </div>

              {/* Pain Points */}
              {appStoreAnalysis.review_sentiment.pain_points.length > 0 && (
                <div className="pain-points">
                  <h6>Top Pain Points</h6>
                  <ul>
                    {appStoreAnalysis.review_sentiment.pain_points.slice(0, 5).map((point, idx) => (
                      <li key={idx}>
                        <strong>{point.issue}:</strong> {point.frequency} mentions ({point.percentage_of_negative}% of negative reviews)
                        <span className={`severity severity-${point.severity.toLowerCase()}`}>{point.severity}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Positive Highlights */}
              {appStoreAnalysis.review_sentiment.positive_highlights.length > 0 && (
                <div className="positive-highlights">
                  <h6>What Users Love</h6>
                  <ul>
                    {appStoreAnalysis.review_sentiment.positive_highlights.slice(0, 5).map((highlight, idx) => (
                      <li key={idx}>
                        <strong>{highlight.aspect}:</strong> {highlight.mentions} mentions ({highlight.percentage_of_positive}% of positive reviews)
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Recommendations */}
          {appStoreAnalysis.recommendations.length > 0 && (
            <div className="recommendations-section">
              <h5>Optimization Recommendations</h5>
              <div className="recommendations-grid">
                {appStoreAnalysis.recommendations.map((rec, idx) => (
                  <div key={idx} className={`recommendation-card priority-${rec.priority}`}>
                    <div className="rec-header">
                      <span className="rec-category">{rec.category}</span>
                      <span className="rec-priority">{rec.priority} priority</span>
                    </div>
                    <p className="rec-text">{rec.recommendation}</p>
                    <div className="rec-footer">
                      <span className="rec-impact">Impact: {rec.expected_impact}</span>
                      <span className="rec-difficulty">Difficulty: {rec.implementation_difficulty}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Raw Analysis Data (Collapsible) */}
          <details className="raw-data-section">
            <summary>View Raw Analysis Data</summary>
            <pre>{JSON.stringify(appStoreAnalysis, null, 2)}</pre>
          </details>
        </div>
      )}
    </div>
  );

  const renderPlayStoreTab = () => (
    <div className="tab-content">
      <h3>Android Play Store Analysis</h3>
      
      {/* Saved Analyses List */}
      {!showDashboard && (
        <div className="saved-analyses-section">
          {savedPlayStoreAnalyses.length > 0 ? (
            <>
              <h4>Previous Analyses</h4>
              <div className="analyses-list">
                {savedPlayStoreAnalyses.map((analysis) => (
                  <div key={analysis.analysis_id} className="analysis-item">
                    <div className="analysis-info">
                      <h5>{analysis.app_name || 'Unknown App'}</h5>
                      <p className="package-name">{analysis.package_name}</p>
                      <p className="analysis-date">
                        {new Date(analysis.analysis_timestamp).toLocaleDateString()} 
                        {' at '}
                        {new Date(analysis.analysis_timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                    <div className="analysis-stats">
                      <span className="rating">⭐ {analysis.rating?.toFixed(1)}</span>
                      <span className="recommendations">
                        {analysis.recommendation_count} recommendations
                      </span>
                    </div>
                    <div className="analysis-actions">
                      <button 
                        onClick={() => viewAnalysisDetails(analysis.analysis_id)}
                        className="view-details-button"
                      >
                        View Dashboard
                      </button>
                      <button 
                        onClick={() => deleteAnalysis(analysis.analysis_id)}
                        className="delete-button"
                        disabled={loading}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="no-analyses-message">
              <p>No previous Play Store analyses found. Analyze your first app below!</p>
            </div>
          )}
        </div>
      )}
      
      {/* New Analysis Form */}
      {!showDashboard && (
      <div className="input-section">
        <div className="input-group">
          <label>Play Store URL</label>
          <input
            type="text"
            value={playStoreUrl}
            onChange={(e) => setPlayStoreUrl(e.target.value)}
            placeholder="https://play.google.com/store/apps/details?id=..."
            className="url-input"
          />
        </div>
        
        <div className="divider">OR</div>
        
        <div className="input-group">
          <label>Package ID</label>
          <input
            type="text"
            value={packageId}
            onChange={(e) => setPackageId(e.target.value)}
            placeholder="com.example.app"
            className="package-input"
          />
        </div>

        <div className="options-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={includePlayStoreReviews}
              onChange={(e) => setIncludePlayStoreReviews(e.target.checked)}
            />
            Include Review Analysis
          </label>
          
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={includePlayStoreVisuals}
              onChange={(e) => setIncludePlayStoreVisuals(e.target.checked)}
            />
            Include Visual Assessment
          </label>
        </div>

        <button 
          onClick={analyzePlayStore} 
          disabled={loading}
          className="analyze-button"
        >
          {loading ? 'Analyzing...' : 'Analyze Play Store Listing'}
        </button>
      </div>
      )}

      {/* Dashboard View */}
      {showDashboard && playStoreAnalysis && (
        <div className="dashboard-view">
          <button 
            onClick={() => {
              setShowDashboard(false);
              setPlayStoreAnalysis(null);
              setSelectedAnalysisId(null);
            }}
            className="back-button"
          >
            ← Back to List
          </button>
          
          <MobileAnalyticsDashboard 
            analysisData={playStoreAnalysis} 
            analysisType="play-store" 
          />
        </div>
      )}
      
      {/* Inline Analysis Results */}
      {!showDashboard && playStoreAnalysis && (
        <div className="analysis-results">
          <h4>Analysis Results</h4>
          
          {/* Dashboard View */}
          <MobileAnalyticsDashboard 
            analysisData={playStoreAnalysis} 
            analysisType="play-store" 
          />
          
          {/* Optimization Score */}
          {playStoreAnalysis.optimization_score && (
            <div className="score-section">
              <div className="score-display">
                <div className="score-circle">
                  <span className="score-number">{playStoreAnalysis.optimization_score.score}</span>
                  <span className="score-grade">{playStoreAnalysis.optimization_score.grade}</span>
                </div>
                <div className="score-details">
                  <h5>Optimization Score</h5>
                  <div className="issues">
                    <strong>Issues:</strong>
                    <ul>
                      {playStoreAnalysis.optimization_score.issues.map((issue: string, idx: number) => (
                        <li key={idx}>{issue}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="strengths">
                    <strong>Strengths:</strong>
                    <ul>
                      {playStoreAnalysis.optimization_score.strengths.map((strength: string, idx: number) => (
                        <li key={idx}>{strength}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Recommendations */}
          {playStoreAnalysis.recommendations && playStoreAnalysis.recommendations.length > 0 && (
            <div className="recommendations-section">
              <h5>Optimization Recommendations</h5>
              <div className="recommendations-grid">
                {playStoreAnalysis.recommendations.map((rec: any, idx: number) => (
                  <div key={idx} className={`recommendation-card priority-${rec.priority}`}>
                    <div className="rec-header">
                      <span className="rec-category">{rec.category}</span>
                      <span className="rec-priority">{rec.priority} priority</span>
                    </div>
                    <p className="rec-text">{rec.recommendation}</p>
                    <div className="rec-footer">
                      <span className="rec-impact">Impact: {rec.expected_impact}</span>
                      <span className="rec-difficulty">Difficulty: {rec.implementation_difficulty}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Raw Analysis Data (Collapsible) */}
          <details className="raw-data-section">
            <summary>View Raw Analysis Data</summary>
            <pre>{JSON.stringify(playStoreAnalysis, null, 2)}</pre>
          </details>
        </div>
      )}
    </div>
  );

  const renderMetaAdsTab = () => {
    // Function to extract campaign ID from Meta Ads Manager URL
    const extractCampaignIdFromUrl = (url: string): string | null => {
      try {
        // Match patterns like selected_campaign_ids=120227656917790066
        const campaignIdMatch = url.match(/selected_campaign_ids=(\d+)/);
        if (campaignIdMatch && campaignIdMatch[1]) {
          return campaignIdMatch[1];
        }
        return null;
      } catch (error) {
        return null;
      }
    };

    const handleCampaignInputChange = (value: string) => {
      // Check if it's a URL
      if (value.includes('adsmanager.facebook.com') || value.includes('business.facebook.com')) {
        const extractedId = extractCampaignIdFromUrl(value);
        if (extractedId) {
          setCampaignId(extractedId);
          setError(null);
        } else {
          setError('Could not extract Campaign ID from the URL. Please check the URL or enter the ID manually.');
        }
      } else {
        setCampaignId(value);
      }
    };

    return (
    <div className="tab-content">
      <h3>Meta Ads Performance Analysis</h3>
      
      <div className="input-section">
        <div className="input-group">
          <label>Campaign ID or Meta Ads Manager URL</label>
          <input
            type="text"
            value={campaignId}
            onChange={(e) => handleCampaignInputChange(e.target.value)}
            placeholder="Enter campaign ID or paste Meta Ads Manager URL"
            className="campaign-input"
          />
          <div className="help-text">
            <p><strong>How to get your Campaign ID:</strong></p>
            <ol>
              <li>Go to <a href="https://adsmanager.facebook.com" target="_blank" rel="noopener noreferrer">Meta Ads Manager</a></li>
              <li>Navigate to your campaign</li>
              <li>Copy the URL from your browser's address bar and paste it here</li>
              <li>Or find the Campaign ID in the campaign details (usually a long number like 120227656917790066)</li>
            </ol>
            <p className="example-text">
              <strong>Example URL:</strong><br />
              <code style={{ fontSize: '0.85em', wordBreak: 'break-all' }}>
                https://adsmanager.facebook.com/adsmanager/manage/campaigns?selected_campaign_ids=120227656917790066
              </code>
            </p>
          </div>
        </div>

        <div className="input-group">
          <label>Access Token (Required)</label>
          <input
            type="password"
            value={accessToken}
            onChange={(e) => setAccessToken(e.target.value)}
            placeholder="Enter your Meta access token"
            className="access-token-input"
          />
          <div className="help-text">
            <p>A valid Meta access token is required to analyze campaigns. See documentation for how to generate one.</p>
          </div>
        </div>

        <div className="date-range-group">
          <label>Date Range (Optional)</label>
          <div className="date-inputs">
            <input
              type="date"
              value={metaDateRange.start}
              onChange={(e) => setMetaDateRange({ ...metaDateRange, start: e.target.value })}
              placeholder="Start date"
              className="date-input"
            />
            <span className="date-separator">to</span>
            <input
              type="date"
              value={metaDateRange.end}
              onChange={(e) => setMetaDateRange({ ...metaDateRange, end: e.target.value })}
              placeholder="End date"
              className="date-input"
            />
          </div>
        </div>

        <button 
          onClick={analyzeMetaAds} 
          disabled={loading || !campaignId || !accessToken}
          className="analyze-button"
        >
          {loading ? 'Analyzing...' : 'Analyze Meta Ads Performance'}
        </button>
      </div>

      {metaAnalysis && (
        <div className="analysis-results">
          <h4>Analysis Results</h4>
          
          {/* Dashboard View */}
          <MobileAnalyticsDashboard 
            analysisData={metaAnalysis} 
            analysisType="meta-ads" 
          />
          
          {/* Performance Metrics */}
          {metaAnalysis.performance_metrics && (
            <div className="metrics-section">
              <h5>Performance Metrics</h5>
              <pre>{JSON.stringify(metaAnalysis.performance_metrics, null, 2)}</pre>
            </div>
          )}
          
          {/* Recommendations */}
          {metaAnalysis.recommendations && (
            <div className="recommendations-section">
              <h5>Recommendations</h5>
              <ul>
                {metaAnalysis.recommendations.map((rec: any, idx: number) => (
                  <li key={idx}>{rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
  };

  const renderGoogleAnalyticsTab = () => (
    <div className="tab-content">
      <h3>Google Analytics Mobile Analysis</h3>
      
      <div className="input-section">
        <div className="input-group">
          <label>GA4 Property ID</label>
          <input
            type="text"
            value={propertyId}
            onChange={(e) => setPropertyId(e.target.value)}
            placeholder="e.g., 123456789"
            className="property-input"
          />
        </div>
        
        <div className="divider">OR</div>
        
        <div className="input-group">
          <label>Mobile App ID</label>
          <input
            type="text"
            value={appId}
            onChange={(e) => setAppId(e.target.value)}
            placeholder="e.g., com.example.app"
            className="app-input"
          />
        </div>

        <div className="date-range-group">
          <label>Date Range (Optional)</label>
          <div className="date-inputs">
            <input
              type="date"
              value={gaDateRange.start}
              onChange={(e) => setGaDateRange({ ...gaDateRange, start: e.target.value })}
              placeholder="Start date"
              className="date-input"
            />
            <span className="date-separator">to</span>
            <input
              type="date"
              value={gaDateRange.end}
              onChange={(e) => setGaDateRange({ ...gaDateRange, end: e.target.value })}
              placeholder="End date"
              className="date-input"
            />
          </div>
        </div>

        <button 
          onClick={analyzeGoogleAnalytics} 
          disabled={loading || (!propertyId && !appId)}
          className="analyze-button"
        >
          {loading ? 'Analyzing...' : 'Analyze Mobile App Data'}
        </button>
      </div>

      {gaAnalysis && (
        <div className="analysis-results">
          <h4>Analysis Results</h4>
          
          {/* Dashboard View */}
          <MobileAnalyticsDashboard 
            analysisData={gaAnalysis} 
            analysisType="google-analytics" 
          />
          
          {/* User Behavior */}
          {gaAnalysis.user_behavior && (
            <div className="behavior-section">
              <h5>User Behavior Insights</h5>
              <pre>{JSON.stringify(gaAnalysis.user_behavior, null, 2)}</pre>
            </div>
          )}
          
          {/* Performance Metrics */}
          {gaAnalysis.performance_metrics && (
            <div className="metrics-section">
              <h5>App Performance Metrics</h5>
              <pre>{JSON.stringify(gaAnalysis.performance_metrics, null, 2)}</pre>
            </div>
          )}
          
          {/* Recommendations */}
          {gaAnalysis.recommendations && (
            <div className="recommendations-section">
              <h5>Recommendations</h5>
              <ul>
                {gaAnalysis.recommendations.map((rec: any, idx: number) => (
                  <li key={idx}>{rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );

  return (
    <div className="mobile-analytics-interface">
      <h2>Mobile App Performance Analytics</h2>
      
      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'ios' ? 'active' : ''}`}
          onClick={() => setActiveTab('ios')}
        >
          <span className="tab-icon">🍎</span>
          App Store
        </button>
        <button 
          className={`tab ${activeTab === 'android' ? 'active' : ''}`}
          onClick={() => setActiveTab('android')}
        >
          <span className="tab-icon">🤖</span>
          Play Store
        </button>
        <button 
          className={`tab ${activeTab === 'meta' ? 'active' : ''}`}
          onClick={() => setActiveTab('meta')}
        >
          <span className="tab-icon">📱</span>
          Meta Ads
        </button>
        <button 
          className={`tab ${activeTab === 'analytics' ? 'active' : ''}`}
          onClick={() => setActiveTab('analytics')}
        >
          <span className="tab-icon">📊</span>
          Google Analytics
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {activeTab === 'ios' && renderAppStoreTab()}
      {activeTab === 'android' && renderPlayStoreTab()}
      {activeTab === 'meta' && renderMetaAdsTab()}
      {activeTab === 'analytics' && renderGoogleAnalyticsTab()}
    </div>
  );
};

export default MobileAnalyticsInterface;
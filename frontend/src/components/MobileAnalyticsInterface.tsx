import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './MobileAnalyticsInterface.css';
import MobileAnalyticsDashboard from './MobileAnalyticsDashboard';

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
  
  // Meta Ads State
  const [adReportFile, setAdReportFile] = useState<File | null>(null);
  const [metaAnalysis, setMetaAnalysis] = useState<any>(null);
  
  // Google Analytics State
  const [gaDataFile, setGaDataFile] = useState<File | null>(null);
  const [gaAnalysis, setGaAnalysis] = useState<any>(null);

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
    setError('Play Store analysis coming soon!');
  };

  const analyzeMetaAds = async () => {
    setError('Meta Ads analysis coming soon!');
  };

  const analyzeGoogleAnalytics = async () => {
    setError('Google Analytics analysis coming soon!');
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

        <button 
          onClick={analyzePlayStore} 
          disabled={loading}
          className="analyze-button"
        >
          Analyze Play Store Listing
        </button>
      </div>

      <div className="coming-soon">
        <p>Play Store analysis functionality coming soon!</p>
      </div>
    </div>
  );

  const renderMetaAdsTab = () => (
    <div className="tab-content">
      <h3>Meta Ads Performance Analysis</h3>
      
      <div className="input-section">
        <div className="file-upload-group">
          <label>Upload Ad Report (CSV/Excel)</label>
          <input
            type="file"
            accept=".csv,.xlsx,.xls"
            onChange={(e) => setAdReportFile(e.target.files?.[0] || null)}
            className="file-input"
          />
          {adReportFile && (
            <p className="file-name">Selected: {adReportFile.name}</p>
          )}
        </div>

        <button 
          onClick={analyzeMetaAds} 
          disabled={loading || !adReportFile}
          className="analyze-button"
        >
          Analyze Meta Ads Performance
        </button>
      </div>

      <div className="coming-soon">
        <p>Meta Ads analysis functionality coming soon!</p>
      </div>
    </div>
  );

  const renderGoogleAnalyticsTab = () => (
    <div className="tab-content">
      <h3>Google Analytics Mobile Analysis</h3>
      
      <div className="input-section">
        <div className="file-upload-group">
          <label>Upload GA4 Export (CSV/JSON)</label>
          <input
            type="file"
            accept=".csv,.json"
            onChange={(e) => setGaDataFile(e.target.files?.[0] || null)}
            className="file-input"
          />
          {gaDataFile && (
            <p className="file-name">Selected: {gaDataFile.name}</p>
          )}
        </div>

        <button 
          onClick={analyzeGoogleAnalytics} 
          disabled={loading || !gaDataFile}
          className="analyze-button"
        >
          Analyze Mobile App Data
        </button>
      </div>

      <div className="coming-soon">
        <p>Google Analytics analysis functionality coming soon!</p>
      </div>
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
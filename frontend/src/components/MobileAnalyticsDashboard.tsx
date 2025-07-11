import React from 'react';
import './MobileAnalyticsDashboard.css';

interface DashboardProps {
  analysisData: any;
  analysisType: 'app-store' | 'play-store' | 'meta-ads' | 'google-analytics';
}

const MobileAnalyticsDashboard: React.FC<DashboardProps> = ({ analysisData, analysisType }) => {
  const renderAppStoreDashboard = () => {
    if (!analysisData) return null;

    const { optimization_score, review_sentiment, keyword_insights, recommendations } = analysisData;

    return (
      <div className="dashboard-grid">
        {/* Key Metrics Row */}
        <div className="metrics-row">
          <div className="metric-card">
            <h3>ASO Score</h3>
            <div className="metric-value">
              <span className="big-number">{optimization_score?.score || 0}</span>
              <span className="metric-label">{optimization_score?.grade || 'N/A'}</span>
            </div>
          </div>
          
          <div className="metric-card">
            <h3>User Sentiment</h3>
            <div className="metric-value">
              <span className={`sentiment-indicator ${review_sentiment?.sentiment_label?.toLowerCase().replace(' ', '-')}`}>
                {review_sentiment?.sentiment_label || 'Unknown'}
              </span>
            </div>
          </div>
          
          <div className="metric-card">
            <h3>Review Distribution</h3>
            <div className="mini-chart">
              <div className="review-bars">
                {[5, 4, 3, 2, 1].map(rating => (
                  <div key={rating} className="review-bar-row">
                    <span className="rating-label">{rating}★</span>
                    <div className="bar-container">
                      <div 
                        className="bar-fill"
                        style={{ width: `${Math.random() * 100}%` }} // Replace with actual data
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Charts Section */}
        <div className="charts-section">
          <div className="chart-card">
            <h3>Keyword Performance</h3>
            <div className="keyword-cloud">
              {keyword_insights?.suggested_keywords?.map((keyword: string, idx: number) => (
                <span 
                  key={idx} 
                  className="keyword-tag"
                  style={{ fontSize: `${Math.random() * 0.5 + 0.8}em` }}
                >
                  {keyword}
                </span>
              ))}
            </div>
          </div>
          
          <div className="chart-card">
            <h3>Sentiment Trend</h3>
            <div className="trend-chart">
              {/* Placeholder for actual chart */}
              <svg viewBox="0 0 300 100" className="simple-line-chart">
                <polyline
                  fill="none"
                  stroke="#007bff"
                  strokeWidth="2"
                  points="0,80 50,70 100,60 150,65 200,40 250,45 300,30"
                />
              </svg>
            </div>
          </div>
        </div>

        {/* Top Issues & Recommendations */}
        <div className="insights-section">
          <div className="insight-card">
            <h3>Top Issues</h3>
            <ul className="issues-list">
              {optimization_score?.issues?.slice(0, 3).map((issue: string, idx: number) => (
                <li key={idx} className="issue-item">
                  <span className="issue-icon">⚠️</span>
                  {issue}
                </li>
              ))}
            </ul>
          </div>
          
          <div className="insight-card">
            <h3>Quick Wins</h3>
            <ul className="recommendations-list">
              {recommendations?.filter((r: any) => r.implementation_difficulty === 'Easy')
                .slice(0, 3)
                .map((rec: any, idx: number) => (
                  <li key={idx} className="recommendation-item">
                    <span className="rec-icon">💡</span>
                    <div>
                      <strong>{rec.category}</strong>
                      <p>{rec.recommendation}</p>
                    </div>
                  </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    );
  };

  const renderPlayStoreDashboard = () => (
    <div className="coming-soon-dashboard">
      <h3>Play Store Analytics Dashboard</h3>
      <p>Coming soon! This dashboard will show:</p>
      <ul>
        <li>Play Store listing optimization metrics</li>
        <li>Android-specific performance indicators</li>
        <li>User acquisition funnel analysis</li>
        <li>Technical performance warnings (ANRs, crashes)</li>
      </ul>
    </div>
  );

  const renderMetaAdsDashboard = () => (
    <div className="coming-soon-dashboard">
      <h3>Meta Ads Performance Dashboard</h3>
      <p>Coming soon! This dashboard will show:</p>
      <ul>
        <li>Campaign performance metrics (CTR, CPI, ROAS)</li>
        <li>Creative performance analysis</li>
        <li>Audience insights and optimization</li>
        <li>Budget allocation recommendations</li>
      </ul>
    </div>
  );

  const renderGoogleAnalyticsDashboard = () => (
    <div className="coming-soon-dashboard">
      <h3>Google Analytics Mobile Dashboard</h3>
      <p>Coming soon! This dashboard will show:</p>
      <ul>
        <li>User flow and retention analysis</li>
        <li>Screen performance metrics</li>
        <li>Conversion funnel visualization</li>
        <li>User behavior insights</li>
      </ul>
    </div>
  );

  return (
    <div className="mobile-analytics-dashboard">
      {analysisType === 'app-store' && renderAppStoreDashboard()}
      {analysisType === 'play-store' && renderPlayStoreDashboard()}
      {analysisType === 'meta-ads' && renderMetaAdsDashboard()}
      {analysisType === 'google-analytics' && renderGoogleAnalyticsDashboard()}
    </div>
  );
};

export default MobileAnalyticsDashboard;
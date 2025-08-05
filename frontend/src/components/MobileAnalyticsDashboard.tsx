import React from 'react';
import './MobileAnalyticsDashboard.css';
import { PlayStoreAnalysis, AppStoreAnalysis } from '../types/mobileAnalytics';

interface DashboardProps {
  analysisData: PlayStoreAnalysis | AppStoreAnalysis | any;
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

  const renderPlayStoreDashboard = () => {
    if (!analysisData) return null;

    const { 
      rating, total_reviews, downloads, category,
      keyword_analysis, review_sentiment, visual_analysis, 
      recommendations, competitor_analysis 
    } = analysisData;

    return (
      <div className="dashboard-grid">
        {/* Key Metrics Row */}
        <div className="metrics-row">
          <div className="metric-card">
            <h3>App Rating</h3>
            <div className="metric-value">
              <span className="big-number">{rating || 0}</span>
              <span className="metric-label">★ ({total_reviews?.toLocaleString() || 0} reviews)</span>
            </div>
          </div>
          
          <div className="metric-card">
            <h3>Downloads</h3>
            <div className="metric-value">
              <span className="download-number">{downloads || 'N/A'}</span>
              <span className="metric-label">{category || 'Unknown'}</span>
            </div>
          </div>
          
          <div className="metric-card">
            <h3>Keyword Density</h3>
            <div className="density-bars">
              <div className="density-item">
                <span>Title</span>
                <div className="bar-container">
                  <div 
                    className="bar-fill"
                    style={{ width: `${(keyword_analysis?.keyword_density?.title || 0) * 100}%` }}
                  />
                </div>
              </div>
              <div className="density-item">
                <span>Short</span>
                <div className="bar-container">
                  <div 
                    className="bar-fill"
                    style={{ width: `${(keyword_analysis?.keyword_density?.short_description || 0) * 100}%` }}
                  />
                </div>
              </div>
              <div className="density-item">
                <span>Desc</span>
                <div className="bar-container">
                  <div 
                    className="bar-fill"
                    style={{ width: `${(keyword_analysis?.keyword_density?.description || 0) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Analysis Sections */}
        <div className="charts-section">
          <div className="chart-card">
            <h3>Review Sentiment Analysis</h3>
            {review_sentiment && (
              <div className="sentiment-details">
                <div className="sentiment-overview">
                  <span className={`sentiment-badge ${review_sentiment.sentiment_label?.toLowerCase().replace(' ', '-')}`}>
                    {review_sentiment.sentiment_label || 'Unknown'}
                  </span>
                  <span className="sentiment-score">
                    Score: {review_sentiment.sentiment_score?.toFixed(2) || 'N/A'}
                  </span>
                </div>
                
                {review_sentiment.pain_points && review_sentiment.pain_points.length > 0 && (
                  <div className="pain-points">
                    <h4>Top Pain Points</h4>
                    <ul>
                      {review_sentiment.pain_points.slice(0, 3).map((point: any, idx: number) => (
                        <li key={idx}>
                          <span className="severity-badge">{point.severity}</span>
                          {point.issue} ({point.frequency} mentions)
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {review_sentiment.positive_highlights && review_sentiment.positive_highlights.length > 0 && (
                  <div className="positive-highlights">
                    <h4>Positive Highlights</h4>
                    <ul>
                      {review_sentiment.positive_highlights.slice(0, 3).map((highlight: any, idx: number) => (
                        <li key={idx}>
                          ✓ {highlight.aspect} ({highlight.mentions} mentions)
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
          
          <div className="chart-card">
            <h3>Visual Quality Assessment</h3>
            {visual_analysis && (
              <div className="visual-assessment">
                <div className="visual-scores">
                  <div className="score-item">
                    <span>Icon</span>
                    <span className="score">{visual_analysis.icon_quality?.score || 0}/10</span>
                  </div>
                  <div className="score-item">
                    <span>Screenshots</span>
                    <span className="score">{visual_analysis.screenshots?.quality_score || 0}/10</span>
                  </div>
                  <div className="score-item">
                    <span>Video</span>
                    <span className="score">{visual_analysis.video?.present ? '✓' : '✗'}</span>
                  </div>
                </div>
                
                {visual_analysis.screenshots?.recommendations && (
                  <div className="visual-recommendations">
                    <h4>Visual Improvements</h4>
                    <ul>
                      {visual_analysis.screenshots.recommendations.slice(0, 3).map((rec: string, idx: number) => (
                        <li key={idx}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Keywords and Competitors */}
        <div className="insights-section">
          <div className="insight-card">
            <h3>Keyword Opportunities</h3>
            {keyword_analysis?.keyword_opportunities && (
              <div className="keyword-list">
                {keyword_analysis.keyword_opportunities.slice(0, 5).map((kw: any, idx: number) => (
                  <div key={idx} className="keyword-item">
                    <span className="keyword">{kw.keyword}</span>
                    <div className="keyword-meta">
                      <span className="volume">Vol: {kw.search_volume}</span>
                      <span className="competition">Comp: {kw.competition}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          
          <div className="insight-card">
            <h3>Top Recommendations</h3>
            <ul className="recommendations-list">
              {recommendations?.filter((r: any) => r.priority === 'high')
                .slice(0, 4)
                .map((rec: any, idx: number) => (
                  <li key={idx} className="recommendation-item">
                    <span className={`priority-badge ${rec.priority}`}>{rec.priority}</span>
                    <div>
                      <strong>{rec.category}</strong>
                      <p>{rec.recommendation}</p>
                      <span className="impact">Impact: {rec.expected_impact}</span>
                    </div>
                  </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Competitor Analysis */}
        {competitor_analysis && competitor_analysis.competitors && (
          <div className="competitor-section">
            <h3>Competitor Analysis</h3>
            <div className="competitor-grid">
              {competitor_analysis.competitors.slice(0, 3).map((comp: any, idx: number) => (
                <div key={idx} className="competitor-card">
                  <h4>{comp.name}</h4>
                  <div className="comp-stats">
                    <span>Rating: {comp.rating}★</span>
                    <span>Downloads: {comp.downloads}</span>
                  </div>
                  {comp.advantages && (
                    <div className="comp-advantages">
                      <strong>Their advantages:</strong>
                      <ul>
                        {comp.advantages.slice(0, 2).map((adv: string, i: number) => (
                          <li key={i}>{adv}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

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
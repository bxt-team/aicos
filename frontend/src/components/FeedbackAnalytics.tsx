import React, { useState, useEffect } from 'react';
import './FeedbackAnalytics.css';

interface FeedbackAnalyticsProps {
  onClose?: () => void;
}

interface StyleRanking {
  style: string;
  averageRating: number;
  count: number;
  ratingDistribution: Record<string, number>;
}

interface PromptRanking {
  prompt: string;
  averageRating: number;
  count: number;
  ratingDistribution: Record<string, number>;
}

interface AnalyticsData {
  styleRankings: StyleRanking[];
  bestPerformingStyle: string | null;
  promptRankings: PromptRanking[];
  bestPerformingPrompts: PromptRanking[];
  overallMetrics: {
    averageRating: number;
    totalFeedbackCount: number;
    ratingDistribution: Record<string, number>;
  };
  recentTrends: {
    periodDays: number;
    totalFeedback: number;
    averageRating: number;
    ratingTrend: Record<string, number>;
  };
}

const FeedbackAnalytics: React.FC<FeedbackAnalyticsProps> = ({ onClose }) => {
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'styles' | 'prompts' | 'trends'>('overview');

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/feedback-analytics');
      
      if (!response.ok) {
        throw new Error('Failed to fetch analytics data');
      }
      
      const data = await response.json();
      setAnalyticsData(data);
    } catch (err) {
      console.error('Error fetching analytics:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const renderRatingDistribution = (distribution: Record<string, number>) => {
    const total = Object.values(distribution).reduce((sum, count) => sum + count, 0);
    
    return (
      <div className="rating-distribution">
        {[5, 4, 3, 2, 1].map(rating => {
          const count = distribution[rating.toString()] || 0;
          const percentage = total > 0 ? (count / total) * 100 : 0;
          
          return (
            <div key={rating} className="rating-bar">
              <span className="rating-label">{rating}⭐</span>
              <div className="bar-container">
                <div 
                  className="bar-fill" 
                  style={{ width: `${percentage}%` }}
                />
              </div>
              <span className="rating-count">{count}</span>
            </div>
          );
        })}
      </div>
    );
  };

  const renderOverview = () => {
    if (!analyticsData) return null;

    const { overallMetrics, recentTrends } = analyticsData;

    return (
      <div className="overview-section">
        <div className="metrics-grid">
          <div className="metric-card">
            <h3>Overall Rating</h3>
            <div className="metric-value">{overallMetrics.averageRating.toFixed(1)}/5</div>
            <div className="metric-subtitle">Average across all images</div>
          </div>
          
          <div className="metric-card">
            <h3>Total Feedback</h3>
            <div className="metric-value">{overallMetrics.totalFeedbackCount}</div>
            <div className="metric-subtitle">Images rated</div>
          </div>
          
          <div className="metric-card">
            <h3>Recent Trend</h3>
            <div className="metric-value">{recentTrends.averageRating.toFixed(1)}/5</div>
            <div className="metric-subtitle">Last {recentTrends.periodDays} days</div>
          </div>
          
          <div className="metric-card">
            <h3>Best Style</h3>
            <div className="metric-value">{analyticsData.bestPerformingStyle || 'N/A'}</div>
            <div className="metric-subtitle">Highest rated style</div>
          </div>
        </div>
        
        <div className="charts-section">
          <div className="chart-container">
            <h3>Overall Rating Distribution</h3>
            {renderRatingDistribution(overallMetrics.ratingDistribution)}
          </div>
          
          <div className="chart-container">
            <h3>Recent Trend Distribution</h3>
            {renderRatingDistribution(recentTrends.ratingTrend)}
          </div>
        </div>
      </div>
    );
  };

  const renderStyles = () => {
    if (!analyticsData) return null;

    return (
      <div className="styles-section">
        <h3>Style Performance Rankings</h3>
        <div className="rankings-list">
          {analyticsData.styleRankings.map((style, index) => (
            <div key={style.style} className="ranking-item">
              <div className="ranking-header">
                <span className="ranking-position">#{index + 1}</span>
                <span className="ranking-name">{style.style}</span>
                <span className="ranking-rating">{style.averageRating.toFixed(1)}/5</span>
                <span className="ranking-count">({style.count} images)</span>
              </div>
              <div className="ranking-details">
                {renderRatingDistribution(style.ratingDistribution)}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderPrompts = () => {
    if (!analyticsData) return null;

    return (
      <div className="prompts-section">
        <h3>Top Performing Prompts</h3>
        <div className="rankings-list">
          {analyticsData.bestPerformingPrompts.map((prompt, index) => (
            <div key={index} className="ranking-item">
              <div className="ranking-header">
                <span className="ranking-position">#{index + 1}</span>
                <span className="ranking-rating">{prompt.averageRating.toFixed(1)}/5</span>
                <span className="ranking-count">({prompt.count} uses)</span>
              </div>
              <div className="prompt-text">{prompt.prompt}</div>
              <div className="ranking-details">
                {renderRatingDistribution(prompt.ratingDistribution)}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderTrends = () => {
    if (!analyticsData) return null;

    const { recentTrends } = analyticsData;

    return (
      <div className="trends-section">
        <h3>Recent Feedback Trends</h3>
        <div className="trends-content">
          <div className="trend-summary">
            <p><strong>Period:</strong> Last {recentTrends.periodDays} days</p>
            <p><strong>Total Feedback:</strong> {recentTrends.totalFeedback} ratings</p>
            <p><strong>Average Rating:</strong> {recentTrends.averageRating.toFixed(1)}/5</p>
          </div>
          
          <div className="trend-chart">
            <h4>Rating Distribution (Recent)</h4>
            {renderRatingDistribution(recentTrends.ratingTrend)}
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="analytics-container">
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Loading analytics data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analytics-container">
        <div className="error-state">
          <h3>Error Loading Analytics</h3>
          <p>{error}</p>
          <button onClick={fetchAnalytics} className="retry-button">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="analytics-container">
      <div className="analytics-header">
        <h2>Image Feedback Analytics</h2>
        {onClose && (
          <button onClick={onClose} className="close-button">
            ×
          </button>
        )}
      </div>
      
      <div className="analytics-tabs">
        <button 
          className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button 
          className={`tab-button ${activeTab === 'styles' ? 'active' : ''}`}
          onClick={() => setActiveTab('styles')}
        >
          Styles
        </button>
        <button 
          className={`tab-button ${activeTab === 'prompts' ? 'active' : ''}`}
          onClick={() => setActiveTab('prompts')}
        >
          Prompts
        </button>
        <button 
          className={`tab-button ${activeTab === 'trends' ? 'active' : ''}`}
          onClick={() => setActiveTab('trends')}
        >
          Trends
        </button>
      </div>
      
      <div className="analytics-content">
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'styles' && renderStyles()}
        {activeTab === 'prompts' && renderPrompts()}
        {activeTab === 'trends' && renderTrends()}
      </div>
    </div>
  );
};

export default FeedbackAnalytics;
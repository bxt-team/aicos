import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './InstagramPostingInterface.css';

interface InstagramPost {
  id: string;
  post_text: string;
  hashtags: string[];
  call_to_action: string;
  engagement_strategies: string[];
  optimal_posting_time: string;
  period_name: string;
  period_color: string;
  affirmation: string;
  style: string;
  created_at: string;
  source?: string;
}

interface VisualPost {
  id: string;
  text: string;
  period: string;
  tags: string[];
  period_color: string;
  image_style: string;
  post_format?: string;
  file_path: string;
  file_url: string;
  background_image: {
    id: string;
    photographer: string;
    pexels_url: string;
  };
  created_at: string;
  dimensions: {
    width: number;
    height: number;
  };
}

interface PostingStatus {
  can_post_now: boolean;
  can_post_in_seconds: number;
  last_post_time?: string;
  api_credentials_valid: boolean;
  account_info?: any;
  total_posts: number;
  rate_limit_interval: number;
}

interface PostingHistoryItem {
  id: string;
  container_id: string;
  image_url: string;
  caption: string;
  type: string;
  posted_at: string;
  instagram_url?: string;
  status: string;
}

interface ContentPreparation {
  optimized_caption: string;
  hashtags_count: number;
  recommended_posting_time: string;
  engagement_tips: string[];
  content_type: string;
  estimated_engagement: string;
  post_ready: boolean;
  adjustments_needed: string[];
  caption_length: number;
}

const InstagramPostingInterface: React.FC = () => {
  const [instagramPosts, setInstagramPosts] = useState<InstagramPost[]>([]);
  const [visualPosts, setVisualPosts] = useState<VisualPost[]>([]);
  const [postingStatus, setPostingStatus] = useState<PostingStatus | null>(null);
  const [postingHistory, setPostingHistory] = useState<PostingHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedInstagramPost, setSelectedInstagramPost] = useState<string>('');
  const [selectedVisualPost, setSelectedVisualPost] = useState<string>('');
  const [postType, setPostType] = useState<string>('feed_post');
  const [contentPreparation, setContentPreparation] = useState<ContentPreparation | null>(null);
  const [preparingContent, setPreparingContent] = useState(false);
  const [posting, setPosting] = useState(false);

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadInstagramPosts(),
        loadVisualPosts(),
        loadPostingStatus(),
        loadPostingHistory()
      ]);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadInstagramPosts = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/instagram-posts`);
      if (response.data.success) {
        setInstagramPosts(response.data.posts);
      }
    } catch (error) {
      console.error('Error loading Instagram posts:', error);
    }
  };

  const loadVisualPosts = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/visual-posts`);
      if (response.data.success) {
        setVisualPosts(response.data.posts);
      }
    } catch (error) {
      console.error('Error loading visual posts:', error);
    }
  };

  const loadPostingStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/instagram-posting-status`);
      if (response.data.success) {
        setPostingStatus(response.data);
      }
    } catch (error) {
      console.error('Error loading posting status:', error);
    }
  };

  const loadPostingHistory = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/instagram-posting-history?limit=20`);
      if (response.data.success) {
        setPostingHistory(response.data.posts);
      }
    } catch (error) {
      console.error('Error loading posting history:', error);
    }
  };

  const prepareContent = async () => {
    if (!selectedInstagramPost) {
      alert('Bitte wählen Sie einen Instagram Post aus');
      return;
    }

    setPreparingContent(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/prepare-instagram-content`, {
        instagram_post_id: selectedInstagramPost,
        visual_post_id: selectedVisualPost || undefined
      });

      if (response.data.success) {
        setContentPreparation(response.data.preparation);
      } else {
        alert(`Fehler bei der Content-Vorbereitung: ${response.data.error}`);
      }
    } catch (error: any) {
      console.error('Error preparing content:', error);
      const errorMessage = error.response?.data?.detail || 'Fehler bei der Content-Vorbereitung';
      alert(`Fehler: ${errorMessage}`);
    } finally {
      setPreparingContent(false);
    }
  };

  const postToInstagram = async () => {
    if (!selectedInstagramPost) {
      alert('Bitte wählen Sie einen Instagram Post aus');
      return;
    }

    if (!postingStatus?.can_post_now) {
      const waitTime = Math.ceil((postingStatus?.can_post_in_seconds || 0) / 60);
      alert(`Rate Limit aktiv. Bitte warten Sie noch ${waitTime} Minuten.`);
      return;
    }

    if (!contentPreparation?.post_ready) {
      alert('Content ist noch nicht bereit zum Posten. Bitte bereiten Sie den Content zuerst vor.');
      return;
    }

    setPosting(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/post-to-instagram`, {
        instagram_post_id: selectedInstagramPost,
        visual_post_id: selectedVisualPost || undefined,
        post_type: postType
      });

      if (response.data.success) {
        const result = response.data;
        const instagramUrl = result.instagram_url || '#';
        
        alert(`🎉 Erfolgreich auf Instagram gepostet!\n\nPost ID: ${result.post_id || result.story_id}\nInstagram URL: ${instagramUrl}`);
        
        // Refresh data
        await loadData();
        
        // Reset form
        setSelectedInstagramPost('');
        setSelectedVisualPost('');
        setContentPreparation(null);
        
        // Optional: Open Instagram post
        if (instagramUrl && instagramUrl !== '#') {
          window.open(instagramUrl, '_blank');
        }
      } else {
        alert(`Fehler beim Posten: ${response.data.error}`);
      }
    } catch (error: any) {
      console.error('Error posting to Instagram:', error);
      const errorMessage = error.response?.data?.detail || 'Fehler beim Instagram-Posting';
      alert(`Fehler: ${errorMessage}`);
    } finally {
      setPosting(false);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('de-DE');
  };

  const getSelectedInstagramPost = () => {
    return instagramPosts.find(post => post.id === selectedInstagramPost);
  };

  const getSelectedVisualPost = () => {
    return visualPosts.find(post => post.id === selectedVisualPost);
  };

  const refreshData = () => {
    loadData();
  };

  if (loading) {
    return (
      <div className="instagram-posting-interface">
        <div className="loading-container">
          <div className="loading-spinner">🔄</div>
          <p>Lade Instagram Posting Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="instagram-posting-interface">
      <div className="posting-header">
        <h2>📤 Instagram Posting Dashboard</h2>
        <p>Verwalten Sie Ihre Instagram Posts und posten Sie Inhalte direkt auf Instagram</p>
        <button onClick={refreshData} className="refresh-button" disabled={loading}>
          {loading ? '🔄 Laden...' : '🔄 Aktualisieren'}
        </button>
      </div>

      {/* API Status */}
      <div className="api-status-section">
        <h3>📡 API Status</h3>
        <div className="status-cards">
          <div className={`status-card ${postingStatus?.api_credentials_valid ? 'success' : 'error'}`}>
            <div className="status-icon">
              {postingStatus?.api_credentials_valid ? '✅' : '❌'}
            </div>
            <div className="status-content">
              <h4>Instagram API</h4>
              <p>{postingStatus?.api_credentials_valid ? 'Verbunden' : 'Nicht verbunden'}</p>
              {postingStatus?.account_info && (
                <small>@{postingStatus.account_info.username}</small>
              )}
            </div>
          </div>

          <div className={`status-card ${postingStatus?.can_post_now ? 'success' : 'warning'}`}>
            <div className="status-icon">
              {postingStatus?.can_post_now ? '🟢' : '🟡'}
            </div>
            <div className="status-content">
              <h4>Rate Limit</h4>
              <p>
                {postingStatus?.can_post_now 
                  ? 'Bereit zum Posten' 
                  : `Warten: ${Math.ceil((postingStatus?.can_post_in_seconds || 0) / 60)} Min`
                }
              </p>
              <small>Gesamt Posts: {postingStatus?.total_posts || 0}</small>
            </div>
          </div>
        </div>
      </div>

      {/* Posting Form */}
      <div className="posting-form-section">
        <h3>✨ Neuen Post erstellen</h3>
        
        <div className="form-grid">
          <div className="form-group">
            <label>Instagram Post wählen:</label>
            <select 
              value={selectedInstagramPost} 
              onChange={(e) => setSelectedInstagramPost(e.target.value)}
              disabled={posting}
            >
              <option value="">Wählen Sie einen Instagram Post</option>
              {instagramPosts.map(post => (
                <option key={post.id} value={post.id}>
                  {post.period_name} - {post.affirmation.substring(0, 50)}...
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Visueller Post (optional):</label>
            <select 
              value={selectedVisualPost} 
              onChange={(e) => setSelectedVisualPost(e.target.value)}
              disabled={posting}
            >
              <option value="">Kein visueller Post</option>
              {visualPosts.map(post => (
                <option key={post.id} value={post.id}>
                  {post.period} - {post.text.substring(0, 50)}... ({post.post_format})
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Post Typ:</label>
            <select 
              value={postType} 
              onChange={(e) => setPostType(e.target.value)}
              disabled={posting}
            >
              <option value="feed_post">Feed Post (4:5)</option>
              <option value="story">Story (9:16)</option>
            </select>
          </div>
        </div>

        <div className="form-actions">
          <button
            onClick={prepareContent}
            disabled={!selectedInstagramPost || preparingContent || posting}
            className="prepare-button"
          >
            {preparingContent ? '🔄 Vorbereiten...' : '🔍 Content vorbereiten'}
          </button>

          <button
            onClick={postToInstagram}
            disabled={!contentPreparation?.post_ready || posting || !postingStatus?.can_post_now}
            className="post-button"
          >
            {posting ? '🔄 Posten...' : '📤 Auf Instagram posten'}
          </button>
        </div>
      </div>

      {/* Content Preview */}
      {(selectedInstagramPost || selectedVisualPost) && (
        <div className="content-preview-section">
          <h3>👀 Content Vorschau</h3>
          
          <div className="preview-grid">
            {getSelectedInstagramPost() && (
              <div className="instagram-post-preview">
                <h4>📝 Instagram Post</h4>
                <div className="preview-card">
                  <div className="period-badge" style={{ backgroundColor: getSelectedInstagramPost()?.period_color }}>
                    {getSelectedInstagramPost()?.period_name}
                  </div>
                  <div className="post-content">
                    <p><strong>Affirmation:</strong> {getSelectedInstagramPost()?.affirmation}</p>
                    <p><strong>Hashtags:</strong> {getSelectedInstagramPost()?.hashtags.length} Tags</p>
                    <p><strong>CTA:</strong> {getSelectedInstagramPost()?.call_to_action}</p>
                  </div>
                </div>
              </div>
            )}

            {getSelectedVisualPost() && (
              <div className="visual-post-preview">
                <h4>🎨 Visueller Post</h4>
                <div className="preview-card">
                  <img 
                    src={`${API_BASE_URL}${getSelectedVisualPost()?.file_url}`} 
                    alt="Visual Post"
                    className="preview-image"
                  />
                  <div className="visual-info">
                    <p><strong>Format:</strong> {getSelectedVisualPost()?.post_format}</p>
                    <p><strong>Style:</strong> {getSelectedVisualPost()?.image_style}</p>
                    <p><strong>Größe:</strong> {getSelectedVisualPost()?.dimensions.width}x{getSelectedVisualPost()?.dimensions.height}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Content Preparation Results */}
      {contentPreparation && (
        <div className="preparation-results-section">
          <h3>📊 Content Analyse</h3>
          <div className="preparation-card">
            <div className="preparation-status">
              <span className={`status-indicator ${contentPreparation.post_ready ? 'ready' : 'not-ready'}`}>
                {contentPreparation.post_ready ? '✅ Bereit' : '⚠️ Nicht bereit'}
              </span>
            </div>
            
            <div className="preparation-details">
              <div className="detail-item">
                <strong>Caption Länge:</strong> {contentPreparation.caption_length} / 2200 Zeichen
              </div>
              <div className="detail-item">
                <strong>Hashtags:</strong> {contentPreparation.hashtags_count} / 30
              </div>
              <div className="detail-item">
                <strong>Empfohlene Zeit:</strong> {contentPreparation.recommended_posting_time}
              </div>
              <div className="detail-item">
                <strong>Erwartetes Engagement:</strong> {contentPreparation.estimated_engagement}
              </div>
            </div>

            {contentPreparation.adjustments_needed.length > 0 && (
              <div className="adjustments-needed">
                <h4>🔧 Erforderliche Anpassungen:</h4>
                <ul>
                  {contentPreparation.adjustments_needed.map((adjustment, index) => (
                    <li key={index}>{adjustment}</li>
                  ))}
                </ul>
              </div>
            )}

            {contentPreparation.engagement_tips.length > 0 && (
              <div className="engagement-tips">
                <h4>💡 Engagement Tipps:</h4>
                <ul>
                  {contentPreparation.engagement_tips.map((tip, index) => (
                    <li key={index}>{tip}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Posting History */}
      <div className="posting-history-section">
        <h3>📋 Posting Historie</h3>
        
        {postingHistory.length === 0 ? (
          <div className="no-history">
            <p>📝 Noch keine Posts auf Instagram veröffentlicht.</p>
          </div>
        ) : (
          <div className="history-list">
            {postingHistory.map((historyItem) => (
              <div key={historyItem.id} className="history-item">
                <div className="history-header">
                  <div className="history-type">
                    {historyItem.type === 'feed_post' ? '📱 Feed Post' : '📖 Story'}
                  </div>
                  <div className="history-date">
                    {formatTimestamp(historyItem.posted_at)}
                  </div>
                  <div className={`history-status ${historyItem.status}`}>
                    {historyItem.status === 'published' ? '✅ Veröffentlicht' : '❌ Fehler'}
                  </div>
                </div>
                
                <div className="history-content">
                  <p className="history-caption">
                    {historyItem.caption.substring(0, 100)}
                    {historyItem.caption.length > 100 ? '...' : ''}
                  </p>
                  
                  {historyItem.instagram_url && (
                    <a 
                      href={historyItem.instagram_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="instagram-link"
                    >
                      🔗 Auf Instagram ansehen
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default InstagramPostingInterface;
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './PostCompositionInterface.css';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

interface Template {
  name: string;
  description: string;
  options: string[];
}

interface ComposedPost {
  id: string;
  text: string;
  period: string;
  template_name: string;
  post_format: string;
  period_color: string;
  background_path: string;
  file_path: string;
  file_url: string;
  custom_options: { [key: string]: any };
  created_at: string;
  dimensions: {
    width: number;
    height: number;
  };
}

const PostCompositionInterface: React.FC = () => {
  const [posts, setPosts] = useState<ComposedPost[]>([]);
  const [templates, setTemplates] = useState<{ [key: string]: Template }>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Form state
  const [backgroundPath, setBackgroundPath] = useState('');
  const [text, setText] = useState('');
  const [selectedPeriod, setSelectedPeriod] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState('default');
  const [postFormat, setPostFormat] = useState('story');
  const [customOptions, setCustomOptions] = useState<{ [key: string]: any }>({});
  
  // Filter state
  const [filterPeriod, setFilterPeriod] = useState('');
  const [filterTemplate, setFilterTemplate] = useState('');
  
  // Integration state
  const [instagramPosts, setInstagramPosts] = useState<any[]>([]);
  const [visualPosts, setVisualPosts] = useState<any[]>([]);
  const [showInstagramImport, setShowInstagramImport] = useState(false);
  const [showVisualImport, setShowVisualImport] = useState(false);
  const [selectedInstagramPost, setSelectedInstagramPost] = useState<any>(null);
  const [selectedVisualPost, setSelectedVisualPost] = useState<any>(null);

  const periods = [
    'Image', 'Veränderung', 'Energie', 'Kreativität', 
    'Erfolg', 'Entspannung', 'Umsicht'
  ];

  const loadTemplates = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/composition-templates`);
      if (response.data.success) {
        setTemplates(response.data.templates);
      }
    } catch (err: any) {
      console.error('Error loading templates:', err);
    }
  }, []);

  const loadPosts = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (filterPeriod) params.append('period', filterPeriod);
      if (filterTemplate) params.append('template', filterTemplate);
      
      const response = await axios.get(`${API_BASE_URL}/api/composed-posts?${params}`);
      if (response.data.success) {
        setPosts(response.data.posts);
      }
    } catch (err: any) {
      console.error('Error loading posts:', err);
    }
  }, [filterPeriod, filterTemplate]);

  const loadInstagramPosts = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/instagram-posts`);
      if (response.data.success) {
        setInstagramPosts(response.data.posts);
      }
    } catch (err: any) {
      console.error('Error loading Instagram posts:', err);
    }
  }, []);

  const loadVisualPosts = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/visual-posts`);
      if (response.data.success) {
        setVisualPosts(response.data.posts);
      }
    } catch (err: any) {
      console.error('Error loading visual posts:', err);
    }
  }, []);

  useEffect(() => {
    loadTemplates();
    loadPosts();
  }, [loadTemplates, loadPosts]);

  useEffect(() => {
    loadPosts();
  }, [filterPeriod, filterTemplate, loadPosts]);

  const composePost = async () => {
    if (!backgroundPath || !text || !selectedPeriod) {
      setError('Bitte füllen Sie alle erforderlichen Felder aus');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/compose-post`, {
        background_path: backgroundPath,
        text: text,
        period: selectedPeriod,
        template_name: selectedTemplate,
        post_format: postFormat,
        custom_options: customOptions,
        force_new: false
      });

      if (response.data.success) {
        loadPosts();
        // Reset form
        setBackgroundPath('');
        setText('');
        setSelectedPeriod('');
        setCustomOptions({});
      } else {
        setError(response.data.error || 'Fehler beim Komponieren des Posts');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Fehler beim Komponieren des Posts');
    } finally {
      setLoading(false);
    }
  };

  const deletePost = async (postId: string) => {
    if (!window.confirm('Sind Sie sicher, dass Sie diesen Post löschen möchten?')) {
      return;
    }

    try {
      await axios.delete(`${API_BASE_URL}/api/composed-posts/${postId}`);
      loadPosts();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Fehler beim Löschen des Posts');
    }
  };

  const importFromInstagram = (instagramPost: any) => {
    setText(instagramPost.post_text || '');
    setSelectedPeriod(instagramPost.period_name || '');
    setShowInstagramImport(false);
    setSelectedInstagramPost(instagramPost);
  };

  const importFromVisual = (visualPost: any) => {
    // Visual Posts haben file_path (fertiger Post), nicht background_path
    // Wir verwenden den file_path als "Hintergrundbild" für die neue Komposition
    setBackgroundPath(visualPost.file_path || '');
    setText(visualPost.text || '');
    setSelectedPeriod(visualPost.period || '');
    setShowVisualImport(false);
    setSelectedVisualPost(visualPost);
  };

  const composeWithBothAgents = async () => {
    if (!selectedInstagramPost || !selectedVisualPost) {
      setError('Bitte wählen Sie sowohl einen Instagram-Post als auch einen visuellen Post aus');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/compose-integrated-post`, {
        instagram_post_id: selectedInstagramPost.id,
        visual_post_id: selectedVisualPost.id,
        template_name: selectedTemplate,
        post_format: postFormat,
        custom_options: customOptions
      });

      if (response.data.success) {
        loadPosts();
        // Reset selections
        setSelectedInstagramPost(null);
        setSelectedVisualPost(null);
        setText('');
        setBackgroundPath('');
        setSelectedPeriod('');
        setCustomOptions({});
      } else {
        setError(response.data.error || 'Fehler beim Kombinieren der Posts');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Fehler beim Kombinieren der Posts');
    } finally {
      setLoading(false);
    }
  };

  const renderTemplateOptions = () => {
    const template = templates[selectedTemplate];
    if (!template || !template.options.length) return null;

    return (
      <div className="template-options">
        <h4>Template-Optionen</h4>
        {template.options.map((option) => (
          <div key={option} className="option-input">
            <label>{option}:</label>
            <input
              type="text"
              value={customOptions[option] || ''}
              onChange={(e) => setCustomOptions(prev => ({ ...prev, [option]: e.target.value }))}
              placeholder={`${option} eingeben...`}
            />
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="post-composition-interface">
      <div className="header">
        <h2>🎨 Post Komposition</h2>
        <p>Komponiere professionelle visuelle Posts mit Templates und benutzerdefinierten Optionen</p>
      </div>

      {error && (
        <div className="error-banner">
          <strong>Fehler:</strong> {error}
          <button onClick={() => setError(null)}>✖</button>
        </div>
      )}

      <div className="content-grid">
        {/* Integration Section */}
        <div className="integration-section">
          <h3>🔗 Agent-Integration</h3>
          <p>Kombiniere Ergebnisse aus anderen Agenten für optimale Posts</p>
          
          <div className="integration-options">
            <div className="integration-option">
              <h4>Instagram TextWriter</h4>
              <button 
                onClick={() => {
                  setShowInstagramImport(true);
                  loadInstagramPosts();
                }}
                className="import-button"
              >
                📝 Text importieren
              </button>
              {selectedInstagramPost && (
                <div className="selected-import">
                  <span>✓ {selectedInstagramPost.post_text?.substring(0, 50)}...</span>
                  <button onClick={() => setSelectedInstagramPost(null)}>✖</button>
                </div>
              )}
            </div>
            
            <div className="integration-option">
              <h4>Visual Posts Creator</h4>
              <button 
                onClick={() => {
                  setShowVisualImport(true);
                  loadVisualPosts();
                }}
                className="import-button"
              >
                🎨 Bild importieren
              </button>
              {selectedVisualPost && (
                <div className="selected-import">
                  <span>✓ {selectedVisualPost.text?.substring(0, 50)}...</span>
                  <button onClick={() => setSelectedVisualPost(null)}>✖</button>
                </div>
              )}
            </div>
          </div>
          
          {(selectedInstagramPost && selectedVisualPost) && (
            <button 
              onClick={composeWithBothAgents}
              disabled={loading}
              className="compose-integrated-button"
            >
              {loading ? 'Kombiniere...' : '🎯 Kombiniert komponieren'}
            </button>
          )}
        </div>

        {/* Create Post Form */}
        <div className="create-section">
          <h3>Neuen Post komponieren</h3>
          
          <div className="form-group">
            <label>Hintergrundbild-Pfad *</label>
            <div className="form-input-with-actions">
              <input
                type="text"
                value={backgroundPath}
                onChange={(e) => setBackgroundPath(e.target.value)}
                placeholder="/pfad/zum/hintergrundbild.jpg"
                disabled={loading}
              />
              <button
                type="button"
                onClick={() => {
                  setShowVisualImport(true);
                  loadVisualPosts();
                }}
                className="inline-import-button"
                disabled={loading}
              >
                🎨 Visual importieren
              </button>
            </div>
            <small>Absoluter Pfad zum Hintergrundbild</small>
          </div>

          <div className="form-group">
            <label>Text *</label>
            <div className="form-input-with-actions">
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Text für den Post eingeben..."
                rows={4}
                disabled={loading}
              />
              <button
                type="button"
                onClick={() => {
                  setShowInstagramImport(true);
                  loadInstagramPosts();
                }}
                className="inline-import-button"
                disabled={loading}
              >
                📝 Instagram importieren
              </button>
            </div>
          </div>

          <div className="form-group">
            <label>Periode *</label>
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
            <label>Template</label>
            <select 
              value={selectedTemplate} 
              onChange={(e) => setSelectedTemplate(e.target.value)}
              disabled={loading}
            >
              {Object.entries(templates).map(([key, template]) => (
                <option key={key} value={key}>{template.name}</option>
              ))}
            </select>
            {templates[selectedTemplate] && (
              <small>{templates[selectedTemplate].description}</small>
            )}
          </div>

          <div className="form-group">
            <label>Post-Format</label>
            <select 
              value={postFormat} 
              onChange={(e) => setPostFormat(e.target.value)}
              disabled={loading}
            >
              <option value="story">Instagram Story (9:16)</option>
              <option value="post">Instagram Post (4:5)</option>
            </select>
          </div>

          {renderTemplateOptions()}

          <button 
            onClick={composePost}
            disabled={loading || !backgroundPath || !text || !selectedPeriod}
            className="compose-button"
          >
            {loading ? 'Komponiere Post...' : 'Post komponieren'}
          </button>
        </div>

        {/* Posts List */}
        <div className="posts-section">
          <div className="posts-header">
            <h3>Komponierte Posts</h3>
            
            <div className="filters">
              <select 
                value={filterPeriod} 
                onChange={(e) => setFilterPeriod(e.target.value)}
              >
                <option value="">Alle Perioden</option>
                {periods.map(period => (
                  <option key={period} value={period}>{period}</option>
                ))}
              </select>
              
              <select 
                value={filterTemplate} 
                onChange={(e) => setFilterTemplate(e.target.value)}
              >
                <option value="">Alle Templates</option>
                {Object.entries(templates).map(([key, template]) => (
                  <option key={key} value={key}>{template.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="posts-grid">
            {posts.length === 0 ? (
              <p className="no-posts">Keine Posts gefunden</p>
            ) : (
              posts.map((post) => (
                <div key={post.id} className="post-card">
                  <div className="post-image">
                    <img 
                      src={`${API_BASE_URL}${post.file_url}`} 
                      alt={`Post für ${post.period}`}
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = '/placeholder-image.png';
                      }}
                    />
                    <div className="post-overlay">
                      <span className="period-badge" style={{ backgroundColor: post.period_color }}>
                        {post.period}
                      </span>
                      <span className="template-badge">
                        {post.template_name}
                      </span>
                    </div>
                  </div>
                  
                  <div className="post-info">
                    <h4>{post.text.substring(0, 60)}...</h4>
                    <div className="post-meta">
                      <span>Format: {post.post_format}</span>
                      <span>{post.dimensions.width}x{post.dimensions.height}</span>
                      <span>{new Date(post.created_at).toLocaleDateString()}</span>
                    </div>
                    
                    {post.custom_options && Object.keys(post.custom_options).length > 0 && (
                      <div className="custom-options">
                        <strong>Optionen:</strong>
                        {Object.entries(post.custom_options).map(([key, value]) => (
                          <span key={key}>{key}: {JSON.stringify(value)}</span>
                        ))}
                      </div>
                    )}
                    
                    <div className="post-actions">
                      <button 
                        onClick={() => window.open(`${API_BASE_URL}${post.file_url}`, '_blank')}
                        className="view-button"
                      >
                        👁️ Ansehen
                      </button>
                      <button 
                        onClick={() => deletePost(post.id)}
                        className="delete-button"
                      >
                        🗑️ Löschen
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Templates Info */}
      <div className="templates-info">
        <h3>Verfügbare Templates</h3>
        <div className="templates-grid">
          {Object.entries(templates).map(([key, template]) => (
            <div key={key} className="template-info-card">
              <h4>{template.name}</h4>
              <p>{template.description}</p>
              {template.options.length > 0 && (
                <div className="template-options-list">
                  <strong>Optionen:</strong>
                  <ul>
                    {template.options.map((option) => (
                      <li key={option}>{option}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Instagram Import Modal */}
      {showInstagramImport && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Instagram Posts importieren</h3>
              <button onClick={() => setShowInstagramImport(false)}>✖</button>
            </div>
            <div className="modal-content">
              <div className="import-grid">
                {instagramPosts.map((post) => (
                  <div key={post.id} className="import-card">
                    <div className="import-preview">
                      <div className="period-badge" style={{ backgroundColor: post.period_color }}>
                        {post.period_name}
                      </div>
                      <p>{post.post_text?.substring(0, 100)}...</p>
                      <div className="hashtags-preview">
                        {post.hashtags?.slice(0, 5).map((tag: string, i: number) => (
                          <span key={i} className="hashtag">#{tag}</span>
                        ))}
                      </div>
                    </div>
                    <button 
                      onClick={() => importFromInstagram(post)}
                      className="import-select-button"
                    >
                      Auswählen
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Visual Posts Import Modal */}
      {showVisualImport && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Visual Posts importieren</h3>
              <button onClick={() => setShowVisualImport(false)}>✖</button>
            </div>
            <div className="modal-content">
              <div className="import-grid">
                {visualPosts.map((post) => (
                  <div key={post.id} className="import-card">
                    <div className="import-preview">
                      {post.file_url && (
                        <img 
                          src={`${API_BASE_URL}${post.file_url}`} 
                          alt={post.text} 
                          className="visual-preview"
                        />
                      )}
                      <div className="period-badge" style={{ backgroundColor: post.period_color }}>
                        {post.period}
                      </div>
                      <p>{post.text?.substring(0, 100)}...</p>
                    </div>
                    <button 
                      onClick={() => importFromVisual(post)}
                      className="import-select-button"
                    >
                      Auswählen
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PostCompositionInterface;
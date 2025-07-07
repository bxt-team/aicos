import React, { useState, useEffect } from 'react';
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

  const periods = [
    'Image', 'Veränderung', 'Energie', 'Kreativität', 
    'Erfolg', 'Entspannung', 'Umsicht'
  ];

  useEffect(() => {
    loadTemplates();
    loadPosts();
  }, []);

  useEffect(() => {
    loadPosts();
  }, [filterPeriod, filterTemplate]);

  const loadTemplates = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/composition-templates`);
      if (response.data.success) {
        setTemplates(response.data.templates);
      }
    } catch (err: any) {
      console.error('Error loading templates:', err);
    }
  };

  const loadPosts = async () => {
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
  };

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
        {/* Create Post Form */}
        <div className="create-section">
          <h3>Neuen Post komponieren</h3>
          
          <div className="form-group">
            <label>Hintergrundbild-Pfad *</label>
            <input
              type="text"
              value={backgroundPath}
              onChange={(e) => setBackgroundPath(e.target.value)}
              placeholder="/pfad/zum/hintergrundbild.jpg"
              disabled={loading}
            />
            <small>Absoluter Pfad zum Hintergrundbild</small>
          </div>

          <div className="form-group">
            <label>Text *</label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Text für den Post eingeben..."
              rows={4}
              disabled={loading}
            />
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
                    
                    {Object.keys(post.custom_options).length > 0 && (
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
    </div>
  );
};

export default PostCompositionInterface;
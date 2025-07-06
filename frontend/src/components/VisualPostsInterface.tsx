import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './VisualPostsInterface.css';

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

interface Affirmation {
  id: string;
  text: string;
  period_name: string;
  period_color: string;
  created_at: string;
}

interface ImageSearchResult {
  id: string;
  url: string;
  alt_description: string;
  photographer: string;
  pexels_url: string;
}

const VisualPostsInterface: React.FC = () => {
  const [posts, setPosts] = useState<VisualPost[]>([]);
  const [affirmations, setAffirmations] = useState<Affirmation[]>([]);
  const [searchResults, setSearchResults] = useState<ImageSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  
  // Form states
  const [selectedAffirmation, setSelectedAffirmation] = useState<string>('');
  const [customText, setCustomText] = useState<string>('');
  const [selectedPeriod, setSelectedPeriod] = useState<string>('');
  const [customTags, setCustomTags] = useState<string>('');
  const [imageStyle, setImageStyle] = useState<string>('minimal');
  const [postFormat, setPostFormat] = useState<string>('post');
  const [filterPeriod, setFilterPeriod] = useState<string>('');
  
  // Search states
  const [searchTags, setSearchTags] = useState<string>('');
  const [searchPeriod, setSearchPeriod] = useState<string>('');

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  const periods = [
    'Image', 'Veränderung', 'Energie', 'Kreativität', 
    'Erfolg', 'Entspannung', 'Umsicht'
  ];

  const imageStyles = [
    { value: 'minimal', label: 'Minimal (leichtes Overlay)' },
    { value: 'dramatic', label: 'Dramatisch (starkes Overlay)' },
    { value: 'gradient', label: 'Gradient (Verlauf)' }
  ];

  const postFormats = [
    { value: 'post', label: 'Instagram Post (4:5 - 1080x1350)' },
    { value: 'story', label: 'Instagram Story (9:16 - 1080x1920)' }
  ];

  useEffect(() => {
    loadPosts();
    loadAffirmations();
  }, []);

  const loadPosts = async (periodFilter?: string) => {
    try {
      const url = periodFilter 
        ? `${API_BASE_URL}/visual-posts?period=${periodFilter}`
        : `${API_BASE_URL}/visual-posts`;
      
      const response = await axios.get(url);
      if (response.data.success) {
        setPosts(response.data.posts);
      }
    } catch (error) {
      console.error('Error loading visual posts:', error);
    }
  };

  const loadAffirmations = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/affirmations`);
      if (response.data.success) {
        setAffirmations(response.data.affirmations);
      }
    } catch (error) {
      console.error('Error loading affirmations:', error);
    }
  };

  const handleSearchImages = async () => {
    if (!searchTags.trim() || !searchPeriod) return;

    setSearchLoading(true);
    try {
      const tags = searchTags.split(',').map(tag => tag.trim()).filter(tag => tag);
      
      const response = await axios.post(`${API_BASE_URL}/search-images`, {
        tags,
        period: searchPeriod,
        count: 6
      });

      if (response.data.success) {
        setSearchResults(response.data.images);
      } else {
        alert(`Fehler bei der Bildsuche: ${response.data.message}`);
      }
    } catch (error: any) {
      console.error('Error searching images:', error);
      const errorMessage = error.response?.data?.detail || 'Fehler bei der Bildsuche';
      alert(`Fehler: ${errorMessage}`);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleCreatePost = async (useAffirmation: boolean = false) => {
    setLoading(true);
    try {
      let response;
      
      if (useAffirmation && selectedAffirmation) {
        // Create from existing affirmation
        const tags = customTags ? customTags.split(',').map(tag => tag.trim()).filter(tag => tag) : [];
        
        response = await axios.post(`${API_BASE_URL}/create-affirmation-post`, {
          affirmation_id: selectedAffirmation,
          image_style: imageStyle,
          post_format: postFormat,
          tags: tags.length > 0 ? tags : undefined,
          force_new: true
        });
      } else {
        // Create custom post
        if (!customText.trim() || !selectedPeriod) {
          alert('Text und Periode sind erforderlich');
          return;
        }
        
        const tags = customTags ? customTags.split(',').map(tag => tag.trim()).filter(tag => tag) : [];
        
        response = await axios.post(`${API_BASE_URL}/create-visual-post`, {
          text: customText,
          period: selectedPeriod,
          tags: tags.length > 0 ? tags : undefined,
          image_style: imageStyle,
          post_format: postFormat,
          force_new: true
        });
      }

      if (response.data.success) {
        await loadPosts(filterPeriod || undefined);
        
        // Reset form
        setSelectedAffirmation('');
        setCustomText('');
        setSelectedPeriod('');
        setCustomTags('');
        setImageStyle('minimal');
        setPostFormat('post');
        
        alert(response.data.message);
      } else {
        alert(`Fehler: ${response.data.message}`);
      }
    } catch (error: any) {
      console.error('Error creating visual post:', error);
      const errorMessage = error.response?.data?.detail || 'Fehler beim Erstellen des visuellen Posts';
      alert(`Fehler: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePost = async (postId: string) => {
    if (!window.confirm('Möchten Sie diesen visuellen Post wirklich löschen?')) {
      return;
    }

    try {
      const response = await axios.delete(`${API_BASE_URL}/visual-posts/${postId}`);
      
      if (response.data.success) {
        await loadPosts(filterPeriod || undefined);
        alert('Post erfolgreich gelöscht');
      } else {
        alert(`Fehler: ${response.data.message}`);
      }
    } catch (error: any) {
      console.error('Error deleting post:', error);
      const errorMessage = error.response?.data?.detail || 'Fehler beim Löschen des Posts';
      alert(`Fehler: ${errorMessage}`);
    }
  };

  const handleFilterChange = (period: string) => {
    setFilterPeriod(period);
    loadPosts(period || undefined);
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <div className="visual-posts-interface">
      <div className="visual-posts-header">
        <h2>7 Cycles Visuelle Posts Generator</h2>
        <p>Erstelle visuell ansprechende Instagram Posts (4:5) und Stories (9:16) für deine Affirmationen</p>
      </div>

      {/* Image Search Section */}
      <div className="image-search-section">
        <h3>Bildsuche testen</h3>
        <div className="search-form">
          <div className="form-row">
            <div className="form-group">
              <label>Suchbegriffe (komma-getrennt):</label>
              <input
                type="text"
                value={searchTags}
                onChange={(e) => setSearchTags(e.target.value)}
                placeholder="z.B. natur, see, ruhe, meditation"
                disabled={searchLoading}
              />
            </div>
            <div className="form-group">
              <label>Periode:</label>
              <select 
                value={searchPeriod} 
                onChange={(e) => setSearchPeriod(e.target.value)}
                disabled={searchLoading}
              >
                <option value="">Wähle eine Periode</option>
                {periods.map(period => (
                  <option key={period} value={period}>{period}</option>
                ))}
              </select>
            </div>
            <button
              onClick={handleSearchImages}
              disabled={searchLoading || !searchTags.trim() || !searchPeriod}
              className="search-button"
            >
              {searchLoading ? 'Suche...' : 'Bilder suchen'}
            </button>
          </div>
        </div>

        {searchResults.length > 0 && (
          <div className="search-results">
            <h4>Gefundene Bilder:</h4>
            <div className="images-grid">
              {searchResults.map((image) => (
                <div key={image.id} className="image-result">
                  <img src={image.url} alt={image.alt_description} />
                  <div className="image-info">
                    <p>Fotograf: {image.photographer}</p>
                    <a href={image.pexels_url} target="_blank" rel="noopener noreferrer">
                      Auf Pexels ansehen
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Post Creation Section */}
      <div className="post-creation-section">
        <h3>Visuellen Post erstellen</h3>
        
        <div className="creation-tabs">
          <div className="tab-content">
            <div className="creation-options">
              
              {/* From Affirmation */}
              <div className="creation-option">
                <h4>Aus bestehender Affirmation</h4>
                <div className="form-group">
                  <label>Affirmation auswählen:</label>
                  <select 
                    value={selectedAffirmation} 
                    onChange={(e) => setSelectedAffirmation(e.target.value)}
                    disabled={loading}
                  >
                    <option value="">Wähle eine Affirmation</option>
                    {affirmations.map(affirmation => (
                      <option key={affirmation.id} value={affirmation.id}>
                        {affirmation.text} ({affirmation.period_name})
                      </option>
                    ))}
                  </select>
                </div>
                <button
                  onClick={() => handleCreatePost(true)}
                  disabled={loading || !selectedAffirmation}
                  className="create-button"
                >
                  {loading ? 'Erstelle...' : 'Post aus Affirmation erstellen'}
                </button>
              </div>

              {/* Custom Post */}
              <div className="creation-option">
                <h4>Benutzerdefinierten Post erstellen</h4>
                <div className="form-group">
                  <label>Affirmationstext:</label>
                  <textarea
                    value={customText}
                    onChange={(e) => setCustomText(e.target.value)}
                    placeholder="Gib deinen Affirmationstext ein..."
                    disabled={loading}
                    rows={3}
                  />
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label>Periode:</label>
                    <select 
                      value={selectedPeriod} 
                      onChange={(e) => setSelectedPeriod(e.target.value)}
                      disabled={loading}
                    >
                      <option value="">Wähle eine Periode</option>
                      {periods.map(period => (
                        <option key={period} value={period}>{period}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <button
                  onClick={() => handleCreatePost(false)}
                  disabled={loading || !customText.trim() || !selectedPeriod}
                  className="create-button"
                >
                  {loading ? 'Erstelle...' : 'Benutzerdefinierten Post erstellen'}
                </button>
              </div>
            </div>

            {/* Common Options */}
            <div className="common-options">
              <div className="form-row">
                <div className="form-group">
                  <label>Format:</label>
                  <select 
                    value={postFormat} 
                    onChange={(e) => setPostFormat(e.target.value)}
                    disabled={loading}
                  >
                    {postFormats.map(format => (
                      <option key={format.value} value={format.value}>
                        {format.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Bildstil:</label>
                  <select 
                    value={imageStyle} 
                    onChange={(e) => setImageStyle(e.target.value)}
                    disabled={loading}
                  >
                    {imageStyles.map(style => (
                      <option key={style.value} value={style.value}>
                        {style.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Zusätzliche Tags (optional):</label>
                  <input
                    type="text"
                    value={customTags}
                    onChange={(e) => setCustomTags(e.target.value)}
                    placeholder="z.B. natur, himmel, strand"
                    disabled={loading}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Posts Display Section */}
      <div className="posts-display-section">
        <div className="display-header">
          <h3>Deine visuellen Posts</h3>
          <div className="filter-section">
            <label>Nach Periode filtern:</label>
            <select 
              value={filterPeriod} 
              onChange={(e) => handleFilterChange(e.target.value)}
            >
              <option value="">Alle Perioden</option>
              {periods.map(period => (
                <option key={period} value={period}>{period}</option>
              ))}
            </select>
          </div>
        </div>

        {posts.length === 0 ? (
          <div className="no-posts">
            <p>Noch keine visuellen Posts erstellt.</p>
            <p>Erstelle deinen ersten visuellen Post oben!</p>
          </div>
        ) : (
          <div className="posts-grid">
            {posts.map((post) => (
              <div key={post.id} className="visual-post-card">
                <div className="post-image">
                  <img 
                    src={`${API_BASE_URL}${post.file_url}`} 
                    alt={post.text}
                    loading="lazy"
                  />
                </div>
                <div className="post-details">
                  <div className="post-text">{post.text}</div>
                  <div className="post-meta">
                    <span 
                      className="period-tag"
                      style={{ backgroundColor: post.period_color }}
                    >
                      {post.period}
                    </span>
                    <span className="image-style">{post.image_style}</span>
                  </div>
                  <div className="post-info">
                    <div className="tags">
                      Tags: {post.tags.join(', ')}
                    </div>
                    <div className="photographer">
                      Foto: <a href={post.background_image.pexels_url} target="_blank" rel="noopener noreferrer">
                        {post.background_image.photographer}
                      </a>
                    </div>
                    <div className="timestamp">
                      Erstellt: {formatTimestamp(post.created_at)}
                    </div>
                    <div className="dimensions">
                      {post.dimensions.width}x{post.dimensions.height}px
                      {post.post_format === 'post' ? ' (Instagram Post)' : ' (Instagram Story)'}
                    </div>
                  </div>
                  <div className="post-actions">
                    <button
                      onClick={() => handleDeletePost(post.id)}
                      className="delete-button"
                    >
                      Löschen
                    </button>
                    <a
                      href={`${API_BASE_URL}${post.file_url}`}
                      download={`affirmation-${post.period.toLowerCase()}-${post.id.slice(0, 8)}.jpg`}
                      className="download-button"
                    >
                      Herunterladen
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default VisualPostsInterface;
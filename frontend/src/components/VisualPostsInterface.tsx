import React, { useState, useEffect, useCallback } from 'react';
import ProjectRequired from './ProjectRequired';
import { apiService } from '../services/api';
import './VisualPostsInterface.css';
import ImageFeedback from './ImageFeedback';
import FeedbackAnalytics from './FeedbackAnalytics';

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

interface InstagramPost {
  id: string;
  post_text: string;
  hashtags: string[];
  call_to_action: string;
  period_name: string;
  period_color: string;
  affirmation: string;
  style: string;
  created_at: string;
  source: string;
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
  const [instagramPosts, setInstagramPosts] = useState<InstagramPost[]>([]);
  const [searchResults, setSearchResults] = useState<ImageSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  
  // Form states
  const [selectedAffirmation, setSelectedAffirmation] = useState<string>('');
  const [selectedInstagramPost, setSelectedInstagramPost] = useState<string>('');
  const [customText, setCustomText] = useState<string>('');
  const [selectedPeriod, setSelectedPeriod] = useState<string>('');
  const [customTags, setCustomTags] = useState<string>('');
  const [imageStyle, setImageStyle] = useState<string>('minimal');
  const [postFormat, setPostFormat] = useState<string>('post');
  const [filterPeriod, setFilterPeriod] = useState<string>('');
  const [showInstagramPostModal, setShowInstagramPostModal] = useState<boolean>(false);
  
  // Search states
  const [searchTags, setSearchTags] = useState<string>('');
  const [searchPeriod, setSearchPeriod] = useState<string>('');
  const [aiContext, setAiContext] = useState<string>('');
  
  // Feedback states
  const [showAnalytics, setShowAnalytics] = useState<boolean>(false);
  
  // Prevent duplicate popup
  const [hasShownDataLoadedPopup, setHasShownDataLoadedPopup] = useState<boolean>(false);
  
  // Force refresh state
  const [refreshKey, setRefreshKey] = useState<number>(0);


  const periods = [
    'Image', 'Veränderung', 'Energie', 'Kreativität', 
    'Erfolg', 'Entspannung', 'Umsicht'
  ];

  const imageStyles = [
    { value: 'minimal', label: 'Minimal (leichtes Overlay)' },
    { value: 'dramatic', label: 'Dramatisch (starkes Overlay)' },
    { value: 'gradient', label: 'Gradient (Verlauf)' },
    { value: 'dalle', label: 'DALL-E AI Generiert' }
  ];

  const postFormats = [
    { value: 'post', label: 'Instagram Post (4:5 - 1080x1350)' },
    { value: 'story', label: 'Instagram Story (9:16 - 1080x1920)' }
  ];

  const loadPosts = useCallback(async (periodFilter?: string) => {
    try {
      console.log('Loading posts with filter:', periodFilter);
      const response = await apiService.visualPosts.list(periodFilter);
      console.log('Posts response:', response.data);
      
      if (response.data.success) {
        setPosts(response.data.posts || []);
        console.log('Set posts:', response.data.posts?.length || 0, 'posts');
      }
    } catch (error) {
      console.error('Error loading visual posts:', error);
    }
  }, []);

  const loadAffirmations = useCallback(async () => {
    try {
      const response = await apiService.affirmations.list();
      if (response.data.success) {
        setAffirmations(response.data.affirmations || []);
      }
    } catch (error) {
      console.error('Error loading affirmations:', error);
    }
  }, []);

  const loadInstagramPosts = useCallback(async () => {
    try {
      const response = await apiService.instagram.listPosts();
      if (response.data.success) {
        setInstagramPosts(response.data.posts || []);
      }
    } catch (error) {
      console.error('Error loading Instagram posts:', error);
    }
  }, []);

  const handleUrlParameters = useCallback(() => {
    const urlParams = new URLSearchParams(window.location.search);
    
    // Check if we have Instagram post data in URL parameters
    const text = urlParams.get('text');
    const period = urlParams.get('period');
    const tags = urlParams.get('tags');
    const imageStyle = urlParams.get('image_style');
    const postFormat = urlParams.get('post_format');
    const source = urlParams.get('source');
    
    if (text && period && source === 'instagram_post') {
      // Pre-populate form with Instagram post data
      setCustomText(text);
      setSelectedPeriod(period);
      setCustomTags(tags || '');
      setImageStyle(imageStyle || 'minimal');
      setPostFormat(postFormat || 'post');
      
      // For DALL-E, pre-populate AI context with Instagram data
      if (imageStyle === 'dalle') {
        const instagramPostText = urlParams.get('instagram_post_text');
        const instagramHashtags = urlParams.get('instagram_hashtags');
        const instagramCta = urlParams.get('instagram_cta');
        
        let contextText = '';
        if (instagramPostText) contextText += `Post-Text: ${instagramPostText}\n`;
        if (instagramHashtags) contextText += `Hashtags: ${instagramHashtags}\n`;
        if (instagramCta) contextText += `Call-to-Action: ${instagramCta}`;
        
        setAiContext(contextText.trim());
      }
      
      // Show notification that data was loaded - only once
      if (!hasShownDataLoadedPopup) {
        setTimeout(() => {
          if (imageStyle === 'dalle') {
            alert('✅ Instagram Post-Daten wurden erfolgreich geladen! DALL-E AI-Bild-Generation ist aktiviert mit vorausgefülltem Kontext. Du kannst nun auf "Generieren" klicken.');
          } else {
            alert('✅ Instagram Post-Daten wurden erfolgreich geladen! Du kannst nun auf "Generieren" klicken.');
          }
          setHasShownDataLoadedPopup(true);
        }, 100);
      }
    }
  }, [hasShownDataLoadedPopup]);

  useEffect(() => {
    loadPosts();
    loadAffirmations();
    loadInstagramPosts();
    handleUrlParameters();
  }, [loadPosts, loadAffirmations, loadInstagramPosts, handleUrlParameters]);
  
  // Add effect to reload posts when refresh key changes
  useEffect(() => {
    if (refreshKey > 0) {
      console.log('Refresh key changed, reloading posts...');
      loadPosts(filterPeriod || undefined);
    }
  }, [refreshKey, filterPeriod, loadPosts]);


  const handleSearchImages = async () => {
    if (!searchTags.trim() || !searchPeriod) return;

    setSearchLoading(true);
    try {
      const tags = searchTags.split(',').map(tag => tag.trim()).filter(tag => tag);
      
      const response = await apiService.visualPosts.searchImages(tags, searchPeriod, 6);

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
      
      // Check if this is DALL-E AI image generation from Instagram post
      const urlParams = new URLSearchParams(window.location.search);
      const isInstagramSource = urlParams.get('source') === 'instagram_post';
      const isDALLEStyle = imageStyle === 'dalle';
      
      if (isDALLEStyle) {
        // Create AI image using DALL-E
        const tags = customTags ? customTags.split(',').map(tag => tag.trim()).filter(tag => tag) : [];
        
        if (isInstagramSource) {
          // Create AI image from Instagram post data
          console.log('Creating Instagram AI image with data:', {
            text: customText,
            period: selectedPeriod,
            tags: tags.length > 0 ? tags : undefined,
            image_style: imageStyle,
            post_format: postFormat,
            affirmation_id: urlParams.get('affirmation_id'),
            source: urlParams.get('source'),
            instagram_post_text: urlParams.get('instagram_post_text'),
            instagram_hashtags: urlParams.get('instagram_hashtags'),
            instagram_cta: urlParams.get('instagram_cta'),
            instagram_style: urlParams.get('instagram_style')
          });
          
          response = await apiService.visualPosts.create({
            text: customText,
            period: selectedPeriod,
            tags: tags.length > 0 ? tags : undefined,
            image_style: imageStyle,
            post_format: postFormat,
            affirmation_id: urlParams.get('affirmation_id'),
            source: urlParams.get('source'),
            instagram_post_text: urlParams.get('instagram_post_text'),
            instagram_hashtags: urlParams.get('instagram_hashtags'),
            instagram_cta: urlParams.get('instagram_cta'),
            instagram_style: urlParams.get('instagram_style')
          });
          
          console.log('Instagram AI image response:', response.data);
        } else {
          // Create AI image with manual context
          response = await apiService.visualPosts.create({
            text: customText,
            period: selectedPeriod,
            tags: tags.length > 0 ? tags : undefined,
            image_style: imageStyle,
            post_format: postFormat,
            ai_context: aiContext,
            force_new: true
          });
        }
      } else if (useAffirmation && selectedAffirmation) {
        // Create from existing affirmation
        const selectedAff = affirmations.find(a => a.id === selectedAffirmation);
        if (!selectedAff) {
          throw new Error('Selected affirmation not found');
        }
        
        const tags = customTags ? customTags.split(',').map(tag => tag.trim()).filter(tag => tag) : [];
        
        response = await apiService.visualPosts.create({
          text: selectedAff.text,
          period: selectedAff.period_name,
          tags: tags.length > 0 ? tags : undefined,
          image_style: imageStyle,
          post_format: postFormat,
          force_new: true
        });
      } else if (selectedInstagramPost) {
        // Create from selected Instagram post
        const selectedPost = instagramPosts.find(p => p.id === selectedInstagramPost);
        if (selectedPost) {
          const tags = customTags ? customTags.split(',').map(tag => tag.trim()).filter(tag => tag) : [];
          
          response = await apiService.visualPosts.create({
            text: selectedPost.affirmation,
            period: selectedPost.period_name,
            tags: tags.length > 0 ? tags : undefined,
            image_style: imageStyle,
            post_format: postFormat,
            source: 'existing_instagram_post',
            instagram_post_text: selectedPost.post_text,
            instagram_hashtags: selectedPost.hashtags.join(', '),
            instagram_cta: selectedPost.call_to_action,
            instagram_style: selectedPost.style,
            force_new: true
          });
        }
      } else {
        // Create custom post
        if (!customText.trim() || !selectedPeriod) {
          alert('Text und Periode sind erforderlich');
          return;
        }
        
        const tags = customTags ? customTags.split(',').map(tag => tag.trim()).filter(tag => tag) : [];
        
        response = await apiService.visualPosts.create({
          text: customText,
          period: selectedPeriod,
          tags: tags.length > 0 ? tags : undefined,
          image_style: imageStyle,
          post_format: postFormat,
          force_new: true
        });
      }

      if (response && response.data.success) {
        console.log('Post created successfully, reloading posts...');
        
        // Small delay to ensure file is saved
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Force refresh by updating key
        setRefreshKey(prev => prev + 1);
        
        await loadPosts(filterPeriod || undefined);
        console.log('Posts reloaded after creation');
        
        // Reset form
        setSelectedAffirmation('');
        setSelectedInstagramPost('');
        setCustomText('');
        setSelectedPeriod('');
        setCustomTags('');
        setImageStyle('minimal');
        setPostFormat('post');
        
        // Clear URL parameters after successful creation
        if (window.location.search) {
          window.history.replaceState({}, document.title, window.location.pathname);
        }
        
        // Show success message with details
        const successMessage = response.data.message || 'Visueller Post erfolgreich erstellt';
        if (response.data.visual_post) {
          alert(`✅ ${successMessage}\n\nNeuer visueller Post wurde erstellt und ist nun in der Liste sichtbar.`);
        } else {
          alert(`✅ ${successMessage}`);
        }
      } else if (response) {
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
      const response = await apiService.visualPosts.delete(postId);
      
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

  const handleSelectInstagramPost = (post: InstagramPost) => {
    setSelectedInstagramPost(post.id);
    setCustomText(post.affirmation);
    setSelectedPeriod(post.period_name);
    setCustomTags(''); // Don't auto-populate hashtags into additional tags field
    setImageStyle('dalle'); // Default to DALL-E for Instagram posts
    setAiContext(`Post-Text: ${post.post_text}\nHashtags: ${post.hashtags.join(', ')}\nCall-to-Action: ${post.call_to_action}`);
    setShowInstagramPostModal(false);
  };

  const renderInstagramPostModal = () => {
    if (!showInstagramPostModal) return null;
    
    return (
      <div className="modal-overlay">
        <div className="modal-content instagram-posts-modal">
          <div className="modal-header">
            <h3>Instagram Post auswählen</h3>
            <button 
              onClick={() => setShowInstagramPostModal(false)}
              className="close-button"
            >
              ×
            </button>
          </div>
          <div className="modal-body">
            <div className="instagram-posts-grid">
              {instagramPosts.map((post) => (
                <div 
                  key={post.id} 
                  className="instagram-post-card"
                  onClick={() => handleSelectInstagramPost(post)}
                >
                  <div className="post-header">
                    <span 
                      className="period-badge"
                      style={{ backgroundColor: post.period_color }}
                    >
                      {post.period_name}
                    </span>
                    <span className="post-date">
                      {new Date(post.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="post-content">
                    <div className="post-text">
                      {post.post_text.length > 100 
                        ? `${post.post_text.substring(0, 100)}...` 
                        : post.post_text
                      }
                    </div>
                    <div className="post-affirmation">
                      <strong>Affirmation:</strong> {post.affirmation}
                    </div>
                    <div className="post-hashtags">
                      {post.hashtags.slice(0, 3).map((tag, index) => (
                        <span key={index} className="hashtag">{tag}</span>
                      ))}
                      {post.hashtags.length > 3 && (
                        <span className="hashtag-more">+{post.hashtags.length - 3} more</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <ProjectRequired>
    <div className="visual-posts-interface">
      <div className="visual-posts-header">
        <div className="header-content">
          <div className="header-text">
            <h2>7 Cycles Visuelle Posts Generator</h2>
            <p>Erstelle visuell ansprechende Instagram Posts (4:5) und Stories (9:16) für deine Affirmationen</p>
          </div>
          <div className="header-actions">
            <button 
              onClick={() => setShowAnalytics(true)}
              className="analytics-button"
            >
              📊 Feedback Analytics
            </button>
          </div>
        </div>
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
              
              {/* From Instagram Post */}
              <div className="creation-option">
                <h4>🎯 Aus bestehendem Instagram Post</h4>
                <div className="form-group">
                  <label>Instagram Post auswählen:</label>
                  <div className="instagram-post-selector">
                    <button
                      type="button"
                      onClick={() => setShowInstagramPostModal(true)}
                      className="select-instagram-post-button"
                      disabled={loading}
                    >
                      {selectedInstagramPost 
                        ? `Ausgewählt: ${instagramPosts.find(p => p.id === selectedInstagramPost)?.post_text?.substring(0, 50)}...`
                        : 'Instagram Post auswählen'}
                    </button>
                    {selectedInstagramPost && (
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedInstagramPost('');
                          setCustomText('');
                          setSelectedPeriod('');
                          setCustomTags('');
                          setAiContext('');
                        }}
                        className="clear-selection-button"
                      >
                        ×
                      </button>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => handleCreatePost(false)}
                  disabled={loading || !selectedInstagramPost}
                  className="create-button primary"
                >
                  {loading ? 'Erstelle...' : '🎨 AI-Bild aus Instagram Post erstellen'}
                </button>
              </div>

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

              {/* AI Context Field for DALL-E */}
              {imageStyle === 'dalle' && (
                <div className="ai-context-section">
                  <div className="form-group">
                    <label>🤖 AI Kontext für bessere Bildgenerierung (optional):</label>
                    <textarea
                      value={aiContext}
                      onChange={(e) => setAiContext(e.target.value)}
                      placeholder="Beschreiben Sie zusätzlichen Kontext für die AI-Bildgenerierung, z.B. 'Eine Person in Meditation am Strand bei Sonnenuntergang mit spiritueller Atmosphäre' oder fügen Sie Social Media Post-Inhalte hinzu..."
                      disabled={loading}
                      rows={4}
                      className="ai-context-textarea"
                    />
                    <small className="context-help">
                      💡 Tipp: Je detaillierter der Kontext, desto präziser wird das generierte Bild. 
                      Sie können hier Social Media Post-Texte, Hashtags oder spezifische Bildwünsche einfügen.
                    </small>
                  </div>
                </div>
              )}
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
          <div className="posts-grid" key={refreshKey}>
            {posts.map((post, index) => (
              <div key={`${post.id}-${index}-${refreshKey}`} className="visual-post-card">
                <div className="post-image">
                  <img 
                    src={post.file_url.startsWith('http') ? post.file_url : `${window.location.origin}${post.file_url}`} 
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
                    <span className={`image-style ${post.image_style === 'dalle' ? 'ai-generated' : ''}`}>
                      {post.image_style === 'dalle' ? '🤖 DALL-E AI' : post.image_style}
                    </span>
                  </div>
                  <div className="post-info">
                    {post.tags && post.tags.length > 0 && (
                      <div className="tags">
                        Tags: {post.tags.join(', ')}
                      </div>
                    )}
                    <div className="photographer">
                      {post.image_style === 'dalle' ? (
                        <span>🤖 KI-generiert mit DALL-E AI</span>
                      ) : post.background_image ? (
                        <>
                          Foto: <a href={post.background_image.pexels_url} target="_blank" rel="noopener noreferrer">
                            {post.background_image.photographer}
                          </a>
                        </>
                      ) : null}
                    </div>
                    <div className="timestamp">
                      Erstellt: {formatTimestamp(post.created_at)}
                    </div>
                    {post.dimensions && (
                      <div className="dimensions">
                        {post.dimensions.width}x{post.dimensions.height}px
                        {post.post_format === 'post' ? ' (Instagram Post)' : ' (Instagram Story)'}
                      </div>
                    )}
                    {post.image_style === 'dalle' && (post as any).ai_prompt && (
                      <div className="ai-prompt-info">
                        <strong>🤖 AI Prompt:</strong>
                        <p className="ai-prompt-text">{(post as any).ai_prompt}</p>
                      </div>
                    )}
                  </div>
                  <div className="post-actions">
                    <button
                      onClick={() => handleDeletePost(post.id)}
                      className="delete-button"
                    >
                      Löschen
                    </button>
                    <a
                      href={post.file_url.startsWith('http') ? post.file_url : `${window.location.origin}${post.file_url}`}
                      download={`affirmation-${post.period.toLowerCase()}-${post.id.slice(0, 8)}.jpg`}
                      className="download-button"
                    >
                      Herunterladen
                    </a>
                  </div>
                  
                  {/* Image Feedback Component */}
                  <ImageFeedback
                    imagePath={post.file_path}
                    generationParams={{
                      text: post.text,
                      period: post.period,
                      tags: post.tags || [],
                      style: post.image_style,
                      post_format: post.post_format,
                      ai_generated: post.image_style === 'dalle',
                      ...(post.image_style === 'dalle' && { 
                        ai_prompt: (post as any).ai_prompt,
                        dalle_prompt: (post as any).dalle_prompt 
                      })
                    }}
                    onFeedbackSubmit={(feedback) => {
                      console.log('Feedback submitted for', post.id, feedback);
                      // Optional: Show success message or update UI
                    }}
                    onRegenerateRequest={async (request) => {
                      console.log('Regeneration requested for', post.id, request);
                      // Refresh the posts to show the new regenerated image
                      await loadPosts(filterPeriod || undefined);
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Feedback Analytics Modal */}
      {showAnalytics && (
        <div className="modal-overlay">
          <div className="modal-content">
            <FeedbackAnalytics onClose={() => setShowAnalytics(false)} />
          </div>
        </div>
      )}
      
      {/* Instagram Post Selection Modal */}
      {renderInstagramPostModal()}
    </div>
    </ProjectRequired>
  );
};

export default VisualPostsInterface;
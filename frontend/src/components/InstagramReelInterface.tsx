import React, { useState, useEffect, useCallback } from 'react';
import './InstagramReelInterface.css';
import VoiceOverInterface from './VoiceOverInterface';

interface InstagramReelInterfaceProps {
  apiBaseUrl: string;
}

interface ReelData {
  id: string;
  instagram_text: string;
  period: string;
  additional_input: string;
  period_color: string;
  script: {
    title: string;
    duration: string;
    scenes: Array<{
      scene_number: number;
      duration: string;
      spoken_text: string;
      visual_description: string;
      camera_movement?: string;
      effects?: string;
    }>;
    call_to_action: string;
    hashtags: string[];
    music_mood: string;
  };
  runway_prompt?: string;
  runway_settings?: {
    aspect_ratio: string;
    duration: string;
    quality: string;
    style: string;
    mood: string;
  };
  sora_prompt?: string;
  sora_settings?: {
    aspect_ratio: string;
    duration: number;
    loop: boolean;
    loop_style: string;
    quality: string;
    fps: number;
    style: string;
    mood: string;
    color_theme: string;
  };
  image_paths: string[];
  image_descriptions: string[];
  file_path: string;
  file_url: string;
  thumbnail_url?: string;
  created_at: string;
  duration: string;
  hashtags: string[];
  provider?: string;
  is_loop?: boolean;
  loop_style?: string;
}

interface PeriodTheme {
  color: string;
  mood: string;
  style: string;
}

interface VideoProvider {
  name: string;
  description: string;
  max_duration: number;
  supports_loops: boolean;
  formats: string[];
  quality: string;
}

interface LoopStyle {
  name: string;
  description: string;
  best_for: string;
}

interface InstagramPost {
  id: string;
  text: string;
  period: string;
  hashtags: string[];
  created_at: string;
  affirmation?: string;
  post_text?: string;
  period_name?: string;
  period_color?: string;
}

interface ComposedPost {
  id: string;
  text: string;
  period: string;
  file_url: string;
  created_at: string;
}

const InstagramReelInterface: React.FC<InstagramReelInterfaceProps> = ({ apiBaseUrl }) => {
  // Helper function to get recommended loop style based on period
  const getRecommendedLoopStyle = (period: string): string => {
    const recommendations: Record<string, string> = {
      'Image': 'morph - Für visuelle Transformationen',
      'Veränderung': 'seamless - Für fließende Übergänge',
      'Energie': 'bounce - Für dynamische Bewegungen',
      'Kreativität': 'kaleidoscope - Für kreative Effekte',
      'Erfolg': 'zoom - Für kraftvolle Statements',
      'Entspannung': 'flow - Für beruhigende Bewegungen',
      'Umsicht': 'fade - Für sanfte Reflexionen'
    };
    return recommendations[period] || 'seamless - Universell einsetzbar';
  };
  const [reels, setReels] = useState<ReelData[]>([]);
  const [instagramPosts, setInstagramPosts] = useState<InstagramPost[]>([]);
  // const [composedPosts, setComposedPosts] = useState<ComposedPost[]>([]);
  const [, setPeriodThemes] = useState<Record<string, PeriodTheme>>({});
  const [videoProviders, setVideoProviders] = useState<Record<string, VideoProvider>>({});
  const [loopStyles, setLoopStyles] = useState<Record<string, LoopStyle>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState<string>('');
  const [selectedPost, setSelectedPost] = useState<string>('');
  const [selectedImages, setSelectedImages] = useState<string[]>([]);
  const [availableImages, setAvailableImages] = useState<{value: string, label: string, period: string, thumbnail?: string}[]>([]);
  const [additionalInput, setAdditionalInput] = useState('');
  const [customText, setCustomText] = useState('');
  const [selectedProvider, setSelectedProvider] = useState<string>('sora');
  const [selectedLoopStyle, setSelectedLoopStyle] = useState<string>('seamless');
  const [selectedReel, setSelectedReel] = useState<ReelData | null>(null);
  const [showScript, setShowScript] = useState(false);
  const [activeTab, setActiveTab] = useState('generate');
  const [showPostModal, setShowPostModal] = useState(false);
  const [showImageModal, setShowImageModal] = useState(false);
  const [visualPosts, setVisualPosts] = useState<any[]>([]);
  const [showVoiceOverModal, setShowVoiceOverModal] = useState(false);
  const [selectedReelForVoiceOver, setSelectedReelForVoiceOver] = useState<ReelData | null>(null);
  const [showPreviewText, setShowPreviewText] = useState(false);

  const periods = [
    'Image', 'Veränderung', 'Energie', 'Kreativität', 
    'Erfolg', 'Entspannung', 'Umsicht'
  ];

  const loadReels = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/instagram-reels`);
      const data = await response.json();
      if (data.success) {
        setReels(data.reels);
      }
    } catch (err) {
      console.error('Error loading reels:', err);
    }
  }, [apiBaseUrl]);

  const loadInstagramPosts = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/instagram-posts`);
      const data = await response.json();
      if (data.success) {
        setInstagramPosts(data.posts);
      }
    } catch (err) {
      console.error('Error loading Instagram posts:', err);
    }
  }, [apiBaseUrl]);

  const loadComposedPosts = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/composed-posts`);
      const data = await response.json();
      if (data.success) {
        // setComposedPosts(data.posts);
      }
    } catch (err) {
      console.error('Error loading composed posts:', err);
    }
  }, [apiBaseUrl]);

  const loadVisualPosts = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/visual-posts`);
      const data = await response.json();
      if (data.success) {
        setVisualPosts(data.posts);
      }
    } catch (err) {
      console.error('Error loading visual posts:', err);
    }
  }, [apiBaseUrl]);

  const loadPeriodThemes = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/reel-themes`);
      const data = await response.json();
      if (data.success) {
        setPeriodThemes(data.themes);
      }
    } catch (err) {
      console.error('Error loading period themes:', err);
    }
  }, [apiBaseUrl]);

  const loadVideoProviders = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/video-providers`);
      const data = await response.json();
      if (data.success) {
        setVideoProviders(data.providers);
      }
    } catch (err) {
      console.error('Error loading video providers:', err);
    }
  }, [apiBaseUrl]);

  const loadLoopStyles = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/loop-styles`);
      const data = await response.json();
      if (data.success) {
        setLoopStyles(data.loop_styles);
      }
    } catch (err) {
      console.error('Error loading loop styles:', err);
    }
  }, [apiBaseUrl]);

  useEffect(() => {
    loadReels();
    loadInstagramPosts();
    loadComposedPosts();
    loadVisualPosts();
    loadPeriodThemes();
    loadVideoProviders();
    loadLoopStyles();
  }, [loadReels, loadInstagramPosts, loadComposedPosts, loadVisualPosts, loadPeriodThemes, loadVideoProviders, loadLoopStyles]);

  const generateReel = async () => {
    if (!selectedPeriod || (!selectedPost && !customText)) {
      setError('Bitte wählen Sie eine Periode und einen Text oder Post aus.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const selectedPostData = instagramPosts.find(p => p.id === selectedPost);
      const textToUse = customText || selectedPostData?.text || '';
      
      const response = await fetch(`${apiBaseUrl}/api/generate-instagram-reel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          instagram_text: textToUse,
          period: selectedPeriod,
          additional_input: additionalInput,
          image_paths: selectedImages,
          image_descriptions: selectedImages.map(img => `Image: ${img}`),
          provider: selectedProvider,
          loop_style: selectedLoopStyle,
          force_new: false
        }),
      });

      const data = await response.json();
      
      if (data.success) {
        setReels(prev => [data.reel, ...prev]);
        setSelectedPost('');
        setCustomText('');
        setAdditionalInput('');
        setSelectedImages([]);
        setError(null);
      } else {
        setError(data.message || 'Fehler beim Generieren des Reels');
      }
    } catch (err) {
      setError('Fehler beim Generieren des Reels');
      console.error('Error generating reel:', err);
    } finally {
      setLoading(false);
    }
  };

  const deleteReel = async (reelId: string) => {
    if (!window.confirm('Möchten Sie diesen Reel wirklich löschen?')) return;

    try {
      const response = await fetch(`${apiBaseUrl}/api/instagram-reels/${reelId}`, {
        method: 'DELETE',
      });

      const data = await response.json();
      
      if (data.success) {
        setReels(prev => prev.filter(reel => reel.id !== reelId));
        if (selectedReel?.id === reelId) {
          setSelectedReel(null);
        }
      } else {
        setError(data.message || 'Fehler beim Löschen des Reels');
      }
    } catch (err) {
      setError('Fehler beim Löschen des Reels');
      console.error('Error deleting reel:', err);
    }
  };

  const viewReelDetails = (reel: ReelData) => {
    setSelectedReel(reel);
    setShowScript(false);
    setActiveTab('details');
  };

  const handleAddVoiceOver = (reel: ReelData) => {
    setSelectedReelForVoiceOver(reel);
    setShowVoiceOverModal(true);
  };

  const handleVoiceOverComplete = (result: any) => {
    setShowVoiceOverModal(false);
    setSelectedReelForVoiceOver(null);
    // Refresh reels or show success message
    loadReels();
  };

  const getImageOptions = useCallback(() => {
    return visualPosts
      .filter(post => !selectedPeriod || post.period === selectedPeriod)
      .map(post => ({
        value: post.file_url,
        label: `${post.period} - ${post.text ? post.text.substring(0, 50) : 'Kein Text'}...`,
        period: post.period,
        thumbnail: post.file_url
      }));
  }, [visualPosts, selectedPeriod]);

  useEffect(() => {
    setAvailableImages(getImageOptions());
  }, [getImageOptions]);

  const handlePostSelection = (postId: string) => {
    const post = instagramPosts.find(p => p.id === postId);
    if (post) {
      setSelectedPost(postId);
      setSelectedPeriod(post.period || post.period_name || '');
      setShowPostModal(false);
      
      // Auto-suggest content based on period
      if (!additionalInput && post.period) {
        const periodSuggestions: Record<string, string> = {
          'Image': 'Zeige die visuelle Transformation und persönliche Entwicklung',
          'Veränderung': 'Betone den Wandel und neue Perspektiven',
          'Energie': 'Fokus auf Dynamik, Aktivität und Lebensfreude',
          'Kreativität': 'Kreative Ausdruckskraft und künstlerische Elemente',
          'Erfolg': 'Erfolgsmomente und Zielerreichung hervorheben',
          'Entspannung': 'Ruhe, Balance und innere Harmonie vermitteln',
          'Umsicht': 'Weisheit, Reflexion und bewusste Entscheidungen'
        };
        setAdditionalInput(periodSuggestions[post.period] || '');
      }
    }
  };

  const handleImageSelection = (imageUrl: string) => {
    if (selectedImages.includes(imageUrl)) {
      setSelectedImages(selectedImages.filter(i => i !== imageUrl));
    } else {
      setSelectedImages([...selectedImages, imageUrl]);
    }
  };

  const filteredReels = selectedPeriod 
    ? reels.filter(reel => reel.period === selectedPeriod)
    : reels;

  return (
    <div className="instagram-reel-interface">
      <div className="header">
        <div className="header-content">
          <h1>Instagram Reel Generator</h1>
          <p>Erstelle professionelle Instagram Reels mit KI-Scripts, Runway-Videos und ChatGPT Sora 5-Sekunden-Loops</p>
        </div>
        <div className="reel-count">
          {reels.length} Reels erstellt
        </div>
      </div>

      {error && (
        <div className="error-message">
          <p>{error}</p>
        </div>
      )}

      <div className="tabs">
        <div className="tab-list">
          <button 
            className={`tab ${activeTab === 'generate' ? 'active' : ''}`}
            onClick={() => setActiveTab('generate')}
          >
            Reel Generieren
          </button>
          <button 
            className={`tab ${activeTab === 'library' ? 'active' : ''}`}
            onClick={() => setActiveTab('library')}
          >
            Reel Bibliothek
          </button>
          <button 
            className={`tab ${activeTab === 'details' ? 'active' : ''}`}
            onClick={() => setActiveTab('details')}
          >
            Reel Details
          </button>
        </div>

        {activeTab === 'generate' && (
          <div className="tab-content">
            <div className="card">
              <div className="card-header">
                <h2>Neuen Instagram Reel erstellen</h2>
                <p>Wählen Sie einen bestehenden Post oder geben Sie eigenen Text ein</p>
              </div>
              <div className="card-content">
                {selectedProvider && videoProviders[selectedProvider] && (
                  <div className="provider-info">
                    <h4>🎯 {videoProviders[selectedProvider].name}</h4>
                    <p>{videoProviders[selectedProvider].description}</p>
                    <div className="provider-specs">
                      <span>Max. Dauer: {videoProviders[selectedProvider].max_duration}s</span>
                      <span>Loops: {videoProviders[selectedProvider].supports_loops ? '✅' : '❌'}</span>
                      <span>Qualität: {videoProviders[selectedProvider].quality}</span>
                    </div>
                  </div>
                )}
                
                <div className="form-grid">
                  <div className="form-group">
                    <label htmlFor="period">7 Cycles Periode</label>
                    <div className="period-selector">
                      {periods.map(period => (
                        <button
                          key={period}
                          type="button"
                          className={`period-btn ${selectedPeriod === period ? 'active' : ''}`}
                          onClick={() => setSelectedPeriod(period)}
                        >
                          {period}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="form-group">
                    <label htmlFor="provider">Video Generator</label>
                    <select 
                      id="provider"
                      value={selectedProvider} 
                      onChange={(e) => setSelectedProvider(e.target.value)}
                      className="select"
                    >
                      {Object.entries(videoProviders).map(([key, provider]) => (
                        <option key={key} value={key}>
                          {provider.name} - {provider.description}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="form-grid">
                  <div className="form-group">
                    <label>Instagram Post auswählen (optional)</label>
                    <button 
                      type="button"
                      onClick={() => setShowPostModal(true)}
                      className="btn-outline full-width"
                    >
                      {selectedPost ? (
                        <>📄 {(() => {
                          const post = instagramPosts.find(p => p.id === selectedPost);
                          const displayText = post?.affirmation || post?.text || post?.post_text || 'Kein Text';
                          return displayText.substring(0, 50) + (displayText.length > 50 ? '...' : '');
                        })()}</>
                      ) : (
                        '📄 Instagram Post auswählen'
                      )}
                    </button>
                    {selectedPost && (
                      <button 
                        type="button"
                        onClick={() => {setSelectedPost(''); setSelectedPeriod('');}}
                        className="btn-ghost full-width"
                        style={{marginTop: '8px'}}
                      >
                        🗑️ Auswahl entfernen
                      </button>
                    )}
                  </div>

                  {selectedProvider === 'sora' && (
                    <div className="form-group">
                      <label htmlFor="loopStyle">Loop-Stil (Sora)</label>
                      <select 
                        id="loopStyle"
                        value={selectedLoopStyle} 
                        onChange={(e) => setSelectedLoopStyle(e.target.value)}
                        className="select"
                      >
                        {Object.entries(loopStyles).map(([key, style]) => (
                          <option key={key} value={key}>
                            {style.name} - {style.description}
                          </option>
                        ))}
                      </select>
                      <small className="loop-style-help">
                        Perfekt für: {loopStyles[selectedLoopStyle]?.best_for}
                      </small>
                      {selectedPeriod && (
                        <small className="period-recommendation">
                          💡 Empfehlung für {selectedPeriod}: {getRecommendedLoopStyle(selectedPeriod)}
                        </small>
                      )}
                    </div>
                  )}
                </div>

                <div className="form-group">
                  <label htmlFor="customText">
                    Oder eigenen Text eingeben
                    {customText && (
                      <span className="char-count">
                        {customText.length} Zeichen • ~{Math.ceil(customText.length / 150)} Sek.
                      </span>
                    )}
                  </label>
                  <textarea
                    id="customText"
                    placeholder="Geben Sie hier Ihren eigenen Text ein..."
                    value={customText}
                    onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setCustomText(e.target.value)}
                    className="textarea large"
                  />
                  {customText.length > 300 && (
                    <small className="text-warning">
                      ⚠️ Längere Texte können zu schnelleren Sprechgeschwindigkeiten führen
                    </small>
                  )}
                </div>

                <div className="form-group">
                  <label htmlFor="additionalInput">Zusätzlicher Input (optional)</label>
                  <textarea
                    id="additionalInput"
                    placeholder="Zusätzliche Anweisungen, Stimmung, spezielle Anforderungen..."
                    value={additionalInput}
                    onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setAdditionalInput(e.target.value)}
                    className="textarea"
                  />
                </div>

                <div className="form-group">
                  <label>Bilder auswählen (optional)</label>
                  <button 
                    type="button"
                    onClick={() => setShowImageModal(true)}
                    className="btn-outline full-width"
                  >
                    {selectedImages.length > 0 ? (
                      <>🖼️ {selectedImages.length} Bild(er) ausgewählt</>
                    ) : (
                      '🖼️ Bilder auswählen'
                    )}
                  </button>
                  {selectedImages.length > 0 && (
                    <button 
                      type="button"
                      onClick={() => setSelectedImages([])}
                      className="btn-ghost full-width"
                      style={{marginTop: '8px'}}
                    >
                      🗑️ Alle entfernen
                    </button>
                  )}
                </div>

                {(selectedPost || customText) && (
                  <div className="preview-section">
                    <button 
                      type="button"
                      onClick={() => setShowPreviewText(!showPreviewText)}
                      className="btn-ghost full-width"
                    >
                      {showPreviewText ? '👁️ Vorschau verbergen' : '👁️ Textvorschau anzeigen'}
                    </button>
                    {showPreviewText && (
                      <div className="text-preview">
                        <h4>Reel Text Vorschau:</h4>
                        <p>{customText || instagramPosts.find(p => p.id === selectedPost)?.text || ''}</p>
                        {additionalInput && (
                          <div className="additional-preview">
                            <strong>Zusätzliche Anweisungen:</strong>
                            <p>{additionalInput}</p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
                
                <button 
                  onClick={generateReel} 
                  disabled={loading || !selectedPeriod || (!selectedPost && !customText)}
                  className="btn-primary full-width"
                >
                  {loading ? (
                    <>
                      <span className="spinner">⏳</span>
                      Reel wird erstellt...
                    </>
                  ) : (
                    <>
                      🎬 Instagram Reel generieren
                      {selectedPeriod && (
                        <span className="period-indicator">{selectedPeriod}</span>
                      )}
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'library' && (
          <div className="tab-content">
            <div className="library-header">
              <h2>Reel Bibliothek</h2>
              <select 
                value={selectedPeriod} 
                onChange={(e) => setSelectedPeriod(e.target.value)}
                className="select"
              >
                <option value="">Alle Perioden</option>
                {periods.map(period => (
                  <option key={period} value={period}>
                    {period}
                  </option>
                ))}
              </select>
            </div>

            <div className="reels-grid">
              {filteredReels.map(reel => (
                <div key={reel.id} className="reel-card">
                  <div className="reel-header">
                    <span 
                      className="period-badge"
                      style={{ backgroundColor: reel.period_color }}
                    >
                      {reel.period}
                    </span>
                    <div className="reel-meta">
                      <span className="provider-badge">
                        {reel.provider === 'sora' ? '🎥 Sora' : '🎬 Runway'}
                      </span>
                      <span className="duration">{reel.duration}s</span>
                      {reel.is_loop && <span className="loop-indicator">🔄</span>}
                    </div>
                  </div>
                  <h3>{reel.script.title}</h3>
                  <p className="reel-text">{reel.instagram_text}</p>
                  
                  <div className="hashtags">
                    {reel.hashtags.slice(0, 3).map(tag => (
                      <span key={tag} className="hashtag">
                        {tag}
                      </span>
                    ))}
                  </div>
                  
                  <div className="reel-actions">
                    <button 
                      onClick={() => viewReelDetails(reel)}
                      className="btn-outline"
                    >
                      👁️ Details
                    </button>
                    <button 
                      onClick={() => handleAddVoiceOver(reel)}
                      className="btn-outline"
                    >
                      🎤 Voice Over
                    </button>
                    <button 
                      onClick={() => deleteReel(reel.id)}
                      className="btn-ghost"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {filteredReels.length === 0 && (
              <div className="empty-state">
                <p>Keine Reels gefunden.</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'details' && (
          <div className="tab-content">
            {selectedReel ? (
              <div className="reel-details">
                <div className="card">
                  <div className="card-header">
                    <div className="details-header">
                      <h2>{selectedReel.script.title}</h2>
                      <span 
                        className="period-badge"
                        style={{ backgroundColor: selectedReel.period_color }}
                      >
                        {selectedReel.period}
                      </span>
                    </div>
                    <p>Erstellt am {new Date(selectedReel.created_at).toLocaleDateString('de-DE')}</p>
                  </div>
                  <div className="card-content">
                    <div className="details-grid">
                      <div className="details-section">
                        <h4>Instagram Text</h4>
                        <p>{selectedReel.instagram_text}</p>
                        
                        <h4>Zusätzlicher Input</h4>
                        <p>{selectedReel.additional_input || 'Keine zusätzlichen Eingaben'}</p>
                        
                        <h4>Hashtags</h4>
                        <div className="hashtags">
                          {selectedReel.hashtags.map(tag => (
                            <span key={tag} className="hashtag">
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                      
                      <div className="details-section">
                        <h4>Video Einstellungen</h4>
                        <div className="settings-list">
                          <div><strong>Provider:</strong> {selectedReel.provider === 'sora' ? 'ChatGPT Sora' : 'Runway AI'}</div>
                          <div><strong>Dauer:</strong> {selectedReel.duration}s</div>
                          {selectedReel.is_loop && <div><strong>Loop:</strong> Ja</div>}
                          {selectedReel.loop_style && <div><strong>Loop-Stil:</strong> {selectedReel.loop_style}</div>}
                          {selectedReel.runway_settings && (
                            <>
                              <div><strong>Seitenverhältnis:</strong> {selectedReel.runway_settings.aspect_ratio}</div>
                              <div><strong>Stil:</strong> {selectedReel.runway_settings.style}</div>
                              <div><strong>Stimmung:</strong> {selectedReel.runway_settings.mood}</div>
                            </>
                          )}
                          {selectedReel.sora_settings && (
                            <>
                              <div><strong>Seitenverhältnis:</strong> {selectedReel.sora_settings.aspect_ratio}</div>
                              <div><strong>FPS:</strong> {selectedReel.sora_settings.fps}</div>
                              <div><strong>Qualität:</strong> {selectedReel.sora_settings.quality}</div>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div className="details-actions">
                      <button 
                        onClick={() => setShowScript(!showScript)}
                        className="btn-outline"
                      >
                        📄 {showScript ? 'Script verbergen' : 'Script anzeigen'}
                      </button>
                      <button 
                        onClick={() => handleAddVoiceOver(selectedReel)}
                        className="btn-outline"
                      >
                        🎤 Voice Over hinzufügen
                      </button>
                      {selectedReel.file_url && (
                        <a 
                          href={selectedReel.file_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="btn-primary"
                        >
                          ▶️ Video ansehen
                        </a>
                      )}
                    </div>
                  </div>
                </div>

                {showScript && (
                  <div className="card">
                    <div className="card-header">
                      <h2>Video Script</h2>
                    </div>
                    <div className="card-content">
                      <div className="script-details">
                        <div className="script-section">
                          <strong>Musik-Stimmung:</strong> {selectedReel.script.music_mood}
                        </div>
                        
                        <div className="script-section">
                          <strong>Szenen:</strong>
                          <div className="scenes">
                            {selectedReel.script.scenes.map((scene, index) => (
                              <div key={index} className="scene">
                                <div className="scene-header">
                                  <span className="scene-badge">Szene {scene.scene_number}</span>
                                  <span className="scene-duration">{scene.duration}</span>
                                </div>
                                <p><strong>Text:</strong> {scene.spoken_text}</p>
                                <p><strong>Visuals:</strong> {scene.visual_description}</p>
                                {scene.camera_movement && (
                                  <p><strong>Kamera:</strong> {scene.camera_movement}</p>
                                )}
                                {scene.effects && (
                                  <p><strong>Effekte:</strong> {scene.effects}</p>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                        
                        <div className="script-section">
                          <strong>Call-to-Action:</strong> {selectedReel.script.call_to_action}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="empty-state">
                <p>
                  Wählen Sie einen Reel aus der Bibliothek aus, um Details anzuzeigen.
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Instagram Post Selection Modal */}
      {showPostModal && (
        <div className="modal-overlay" onClick={() => setShowPostModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Instagram Post auswählen</h3>
              <button 
                className="modal-close-btn"
                onClick={() => setShowPostModal(false)}
              >
                ✕
              </button>
            </div>
            <div className="modal-body">
              <div className="post-selection-grid">
                {instagramPosts.map(post => (
                  <div 
                    key={post.id} 
                    className={`post-option ${selectedPost === post.id ? 'selected' : ''}`}
                    onClick={() => handlePostSelection(post.id)}
                  >
                    <div className="post-preview">
                      <div className="post-header">
                        <span className="period-badge" style={{backgroundColor: post.period_color || '#3b82f6'}}>
                          {post.period || post.period_name}
                        </span>
                        <span className="post-date">
                          {new Date(post.created_at).toLocaleDateString('de-DE')}
                        </span>
                      </div>
                      {post.affirmation && (
                        <div className="affirmation-preview prominent">
                          <span className="affirmation-label">✨ Affirmation:</span>
                          <p className="affirmation-text">"{post.affirmation}"</p>
                        </div>
                      )}
                      <p className="post-text">{post.text || post.post_text}</p>
                      {post.hashtags && post.hashtags.length > 0 && (
                        <div className="post-hashtags">
                          {post.hashtags.slice(0, 3).map(tag => (
                            <span key={tag} className="hashtag">{tag}</span>
                          ))}
                        </div>
                      )}
                    </div>
                    {selectedPost === post.id && (
                      <div className="selected-indicator">✓</div>
                    )}
                  </div>
                ))}
              </div>
              {instagramPosts.length === 0 && (
                <div className="empty-state-small">
                  <p>Keine Instagram Posts verfügbar.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Image Selection Modal */}
      {showImageModal && (
        <div className="modal-overlay" onClick={() => setShowImageModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Bilder auswählen</h3>
              <button 
                className="modal-close-btn"
                onClick={() => setShowImageModal(false)}
              >
                ✕
              </button>
            </div>
            <div className="modal-body">
              <div className="modal-actions">
                <button 
                  className="btn-outline"
                  onClick={() => setShowImageModal(false)}
                >
                  Fertig ({selectedImages.length} ausgewählt)
                </button>
              </div>
              {selectedPeriod && availableImages.filter(img => img.period === selectedPeriod).length > 0 && (
                <div className="quick-actions">
                  <button 
                    className="btn-ghost"
                    onClick={() => {
                      const periodImages = availableImages
                        .filter(img => img.period === selectedPeriod)
                        .map(img => img.value);
                      setSelectedImages(Array.from(new Set([...selectedImages, ...periodImages])));
                    }}
                  >
                    Alle aus {selectedPeriod} auswählen
                  </button>
                  <button 
                    className="btn-ghost"
                    onClick={() => setSelectedImages([])}
                  >
                    Auswahl löschen
                  </button>
                </div>
              )}
              <div className="image-selection-grid">
                {availableImages.map(option => (
                  <div 
                    key={option.value} 
                    className={`image-option ${selectedImages.includes(option.value) ? 'selected' : ''} ${selectedPeriod && option.period !== selectedPeriod ? 'dimmed' : ''}`}
                    onClick={() => handleImageSelection(option.value)}
                  >
                    <div className="image-preview">
                      <img 
                        src={option.thumbnail} 
                        alt={option.label}
                        onError={(e) => {
                          const target = e.target as HTMLImageElement;
                          target.style.display = 'none';
                          target.parentElement!.innerHTML = '<div class="image-placeholder">📷</div>';
                        }}
                      />
                    </div>
                    <div className="image-info">
                      <span className="period-tag">{option.period}</span>
                      <p className="image-label">{option.label}</p>
                    </div>
                    {selectedImages.includes(option.value) && (
                      <div className="selected-indicator">✓</div>
                    )}
                  </div>
                ))}
              </div>
              {availableImages.length === 0 && (
                <div className="empty-state-small">
                  <p>Keine Bilder verfügbar{selectedPeriod ? ` für ${selectedPeriod}` : ''}.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Voice Over Modal */}
      {showVoiceOverModal && selectedReelForVoiceOver && (
        <div className="modal-overlay" onClick={() => setShowVoiceOverModal(false)}>
          <div className="modal-content large-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Voice Over für Reel hinzufügen</h3>
              <button 
                className="modal-close-btn"
                onClick={() => setShowVoiceOverModal(false)}
              >
                ✕
              </button>
            </div>
            <div className="modal-body">
              <div className="reel-info-summary">
                <h4>{selectedReelForVoiceOver.script.title}</h4>
                <p>Periode: <span className="period-badge" style={{backgroundColor: selectedReelForVoiceOver.period_color}}>
                  {selectedReelForVoiceOver.period}
                </span></p>
                <p>Dauer: {selectedReelForVoiceOver.duration}s</p>
              </div>
              
              <VoiceOverInterface
                apiBaseUrl={apiBaseUrl}
                videoPath={selectedReelForVoiceOver.file_path}
                onVoiceOverComplete={handleVoiceOverComplete}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default InstagramReelInterface;
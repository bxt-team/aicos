import React, { useState, useEffect } from 'react';
import './InstagramReelInterface.css';

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
}

interface ComposedPost {
  id: string;
  text: string;
  period: string;
  file_url: string;
  created_at: string;
}

const InstagramReelInterface: React.FC<InstagramReelInterfaceProps> = ({ apiBaseUrl }) => {
  const [reels, setReels] = useState<ReelData[]>([]);
  const [instagramPosts, setInstagramPosts] = useState<InstagramPost[]>([]);
  const [composedPosts, setComposedPosts] = useState<ComposedPost[]>([]);
  const [, setPeriodThemes] = useState<Record<string, PeriodTheme>>({});
  const [videoProviders, setVideoProviders] = useState<Record<string, VideoProvider>>({});
  const [loopStyles, setLoopStyles] = useState<Record<string, LoopStyle>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState<string>('');
  const [selectedPost, setSelectedPost] = useState<string>('');
  const [selectedImages, setSelectedImages] = useState<string[]>([]);
  const [additionalInput, setAdditionalInput] = useState('');
  const [customText, setCustomText] = useState('');
  const [selectedProvider, setSelectedProvider] = useState<string>('sora');
  const [selectedLoopStyle, setSelectedLoopStyle] = useState<string>('seamless');
  const [selectedReel, setSelectedReel] = useState<ReelData | null>(null);
  const [showScript, setShowScript] = useState(false);
  const [activeTab, setActiveTab] = useState('generate');

  const periods = [
    'Image', 'Veränderung', 'Energie', 'Kreativität', 
    'Erfolg', 'Entspannung', 'Umsicht'
  ];

  const loadReels = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/instagram-reels`);
      const data = await response.json();
      if (data.success) {
        setReels(data.reels);
      }
    } catch (err) {
      console.error('Error loading reels:', err);
    }
  };

  const loadInstagramPosts = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/instagram-posts`);
      const data = await response.json();
      if (data.success) {
        setInstagramPosts(data.posts);
      }
    } catch (err) {
      console.error('Error loading Instagram posts:', err);
    }
  };

  const loadComposedPosts = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/composed-posts`);
      const data = await response.json();
      if (data.success) {
        setComposedPosts(data.posts);
      }
    } catch (err) {
      console.error('Error loading composed posts:', err);
    }
  };

  const loadPeriodThemes = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/reel-themes`);
      const data = await response.json();
      if (data.success) {
        setPeriodThemes(data.themes);
      }
    } catch (err) {
      console.error('Error loading period themes:', err);
    }
  };

  const loadVideoProviders = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/video-providers`);
      const data = await response.json();
      if (data.success) {
        setVideoProviders(data.providers);
      }
    } catch (err) {
      console.error('Error loading video providers:', err);
    }
  };

  const loadLoopStyles = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/loop-styles`);
      const data = await response.json();
      if (data.success) {
        setLoopStyles(data.loop_styles);
      }
    } catch (err) {
      console.error('Error loading loop styles:', err);
    }
  };

  useEffect(() => {
    loadReels();
    loadInstagramPosts();
    loadComposedPosts();
    loadPeriodThemes();
    loadVideoProviders();
    loadLoopStyles();
  }, [apiBaseUrl]);

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
      
      const response = await fetch(`${apiBaseUrl}/api/generate-reel`, {
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

  const getImageOptions = () => {
    return composedPosts
      .filter(post => !selectedPeriod || post.period === selectedPeriod)
      .map(post => ({
        value: post.file_url,
        label: `${post.period} - ${post.text.substring(0, 50)}...`,
        period: post.period
      }));
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
                    <select 
                      id="period"
                      value={selectedPeriod} 
                      onChange={(e) => setSelectedPeriod(e.target.value)}
                      className="select"
                    >
                      <option value="">Periode auswählen</option>
                      {periods.map(period => (
                        <option key={period} value={period}>
                          {period}
                        </option>
                      ))}
                    </select>
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
                    <label htmlFor="post">Instagram Post auswählen (optional)</label>
                    <select 
                      id="post"
                      value={selectedPost} 
                      onChange={(e) => setSelectedPost(e.target.value)}
                      className="select"
                    >
                      <option value="">Post auswählen</option>
                      {instagramPosts
                        .filter(post => !selectedPeriod || post.period === selectedPeriod)
                        .map(post => (
                          <option key={post.id} value={post.id}>
                            {post.text.substring(0, 50)}...
                          </option>
                        ))}
                    </select>
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
                    </div>
                  )}
                </div>

                <div className="form-group">
                  <label htmlFor="customText">Oder eigenen Text eingeben</label>
                  <textarea
                    id="customText"
                    placeholder="Geben Sie hier Ihren eigenen Text ein..."
                    value={customText}
                    onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setCustomText(e.target.value)}
                    className="textarea large"
                  />
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
                  <select 
                    value="" 
                    onChange={(e: React.ChangeEvent<HTMLSelectElement>) => {
                      const value = e.target.value;
                      if (value && !selectedImages.includes(value)) {
                        setSelectedImages([...selectedImages, value]);
                      }
                    }}
                    className="select"
                  >
                    <option value="">Bild hinzufügen</option>
                    {getImageOptions().map(option => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                  
                  {selectedImages.length > 0 && (
                    <div className="selected-images">
                      {selectedImages.map(img => (
                        <div key={img} className="selected-image">
                          <span>{img}</span>
                          <button
                            type="button"
                            onClick={() => setSelectedImages(selectedImages.filter(i => i !== img))}
                            className="remove-btn"
                          >
                            🗑️
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

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
                    'Instagram Reel generieren'
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
    </div>
  );
};

export default InstagramReelInterface;
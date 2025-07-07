import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './VideoGenerationInterface.css';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

interface VideoType {
  name: string;
  description: string;
  options: string[];
  min_images: number;
  recommended_images: string;
}

interface Video {
  id: string;
  video_type: string;
  image_paths: string[];
  duration: number;
  fps: number;
  options: { [key: string]: any };
  file_path: string;
  file_url: string;
  filename: string;
  file_size: number;
  created_at: string;
  dimensions: {
    width: number;
    height: number;
  };
}

const VideoGenerationInterface: React.FC = () => {
  const [videos, setVideos] = useState<Video[]>([]);
  const [videoTypes, setVideoTypes] = useState<{ [key: string]: VideoType }>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ffmpegAvailable, setFfmpegAvailable] = useState(false);
  
  // Form state
  const [imagePaths, setImagePaths] = useState<string[]>(['']);
  const [selectedVideoType, setSelectedVideoType] = useState('slideshow');
  const [duration, setDuration] = useState(15);
  const [fps, setFps] = useState(30);
  const [customOptions, setCustomOptions] = useState<{ [key: string]: any }>({});
  
  // Filter state
  const [filterVideoType, setFilterVideoType] = useState('');

  useEffect(() => {
    loadVideoTypes();
    loadVideos();
  }, []);

  useEffect(() => {
    loadVideos();
  }, [filterVideoType]);

  const loadVideoTypes = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/video-types`);
      if (response.data.success) {
        setVideoTypes(response.data.video_types);
        setFfmpegAvailable(response.data.ffmpeg_available);
      }
    } catch (err: any) {
      console.error('Error loading video types:', err);
      setError('Fehler beim Laden der Video-Typen');
    }
  };

  const loadVideos = async () => {
    try {
      const params = new URLSearchParams();
      if (filterVideoType) params.append('video_type', filterVideoType);
      
      const response = await axios.get(`${API_BASE_URL}/api/videos?${params}`);
      if (response.data.success) {
        setVideos(response.data.videos);
      }
    } catch (err: any) {
      console.error('Error loading videos:', err);
    }
  };

  const generateVideo = async () => {
    const validImagePaths = imagePaths.filter(path => path.trim() !== '');
    
    if (validImagePaths.length === 0) {
      setError('Bitte geben Sie mindestens einen Bildpfad ein');
      return;
    }

    const selectedType = videoTypes[selectedVideoType];
    if (selectedType && validImagePaths.length < selectedType.min_images) {
      setError(`Dieser Video-Typ benötigt mindestens ${selectedType.min_images} Bild(er)`);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/generate-video`, {
        image_paths: validImagePaths,
        video_type: selectedVideoType,
        duration: duration,
        fps: fps,
        options: customOptions,
        force_new: false
      });

      if (response.data.success) {
        loadVideos();
        // Reset form
        setImagePaths(['']);
        setCustomOptions({});
      } else {
        setError(response.data.error || 'Fehler beim Generieren des Videos');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Fehler beim Generieren des Videos');
    } finally {
      setLoading(false);
    }
  };

  const deleteVideo = async (videoId: string) => {
    if (!window.confirm('Sind Sie sicher, dass Sie dieses Video löschen möchten?')) {
      return;
    }

    try {
      await axios.delete(`${API_BASE_URL}/api/videos/${videoId}`);
      loadVideos();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Fehler beim Löschen des Videos');
    }
  };

  const cleanupTempFiles = async () => {
    try {
      const response = await axios.post(`${API_BASE_URL}/api/cleanup-temp-files`);
      if (response.data.success) {
        alert(response.data.message);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Fehler beim Aufräumen der temporären Dateien');
    }
  };

  const addImagePath = () => {
    setImagePaths([...imagePaths, '']);
  };

  const removeImagePath = (index: number) => {
    const newPaths = imagePaths.filter((_, i) => i !== index);
    setImagePaths(newPaths.length > 0 ? newPaths : ['']);
  };

  const updateImagePath = (index: number, value: string) => {
    const newPaths = [...imagePaths];
    newPaths[index] = value;
    setImagePaths(newPaths);
  };

  const formatFileSize = (bytes: number): string => {
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(2)} MB`;
  };

  const renderVideoTypeOptions = () => {
    const videoType = videoTypes[selectedVideoType];
    if (!videoType || !videoType.options.length) return null;

    return (
      <div className="video-options">
        <h4>Video-Optionen</h4>
        {videoType.options.map((option) => {
          let inputElement;
          
          switch (option) {
            case 'direction':
              inputElement = (
                <select
                  value={customOptions[option] || 'right'}
                  onChange={(e) => setCustomOptions(prev => ({ ...prev, [option]: e.target.value }))}
                >
                  <option value="right">Rechts</option>
                  <option value="left">Links</option>
                  <option value="up">Oben</option>
                  <option value="down">Unten</option>
                </select>
              );
              break;
            case 'speed':
              inputElement = (
                <input
                  type="number"
                  min="1"
                  max="10"
                  step="0.5"
                  value={customOptions[option] || 2}
                  onChange={(e) => setCustomOptions(prev => ({ ...prev, [option]: parseFloat(e.target.value) }))}
                />
              );
              break;
            case 'zoom_start':
            case 'zoom_end':
              inputElement = (
                <input
                  type="number"
                  min="0.5"
                  max="3"
                  step="0.1"
                  value={customOptions[option] || (option === 'zoom_start' ? 1.0 : 1.2)}
                  onChange={(e) => setCustomOptions(prev => ({ ...prev, [option]: parseFloat(e.target.value) }))}
                />
              );
              break;
            case 'transition_duration':
              inputElement = (
                <input
                  type="number"
                  min="0.5"
                  max="5"
                  step="0.1"
                  value={customOptions[option] || 1.0}
                  onChange={(e) => setCustomOptions(prev => ({ ...prev, [option]: parseFloat(e.target.value) }))}
                />
              );
              break;
            default:
              inputElement = (
                <input
                  type="text"
                  value={customOptions[option] || ''}
                  onChange={(e) => setCustomOptions(prev => ({ ...prev, [option]: e.target.value }))}
                  placeholder={`${option} eingeben...`}
                />
              );
          }

          return (
            <div key={option} className="option-input">
              <label>{option}:</label>
              {inputElement}
            </div>
          );
        })}
      </div>
    );
  };

  if (!ffmpegAvailable) {
    return (
      <div className="video-generation-interface">
        <div className="header">
          <h2>🎬 Video Generation</h2>
          <div className="ffmpeg-warning">
            <h3>⚠️ FFmpeg nicht verfügbar</h3>
            <p>
              FFmpeg ist nicht installiert oder nicht verfügbar. 
              Video-Generation ist ohne FFmpeg nicht möglich.
            </p>
            <p>
              Bitte installieren Sie FFmpeg auf dem Server, um diese Funktion zu nutzen.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="video-generation-interface">
      <div className="header">
        <h2>🎬 Video Generation</h2>
        <p>Erstelle ansprechende Instagram Reels aus Bildern mit verschiedenen Effekten</p>
      </div>

      {error && (
        <div className="error-banner">
          <strong>Fehler:</strong> {error}
          <button onClick={() => setError(null)}>✖</button>
        </div>
      )}

      <div className="content-grid">
        {/* Create Video Form */}
        <div className="create-section">
          <h3>Neues Video erstellen</h3>
          
          <div className="form-group">
            <label>Bildpfade *</label>
            {imagePaths.map((path, index) => (
              <div key={index} className="image-path-input">
                <input
                  type="text"
                  value={path}
                  onChange={(e) => updateImagePath(index, e.target.value)}
                  placeholder="/pfad/zum/bild.jpg"
                  disabled={loading}
                />
                {imagePaths.length > 1 && (
                  <button 
                    type="button" 
                    onClick={() => removeImagePath(index)}
                    className="remove-path-button"
                  >
                    ✖
                  </button>
                )}
              </div>
            ))}
            <button 
              type="button" 
              onClick={addImagePath}
              className="add-path-button"
              disabled={loading}
            >
              + Bild hinzufügen
            </button>
          </div>

          <div className="form-group">
            <label>Video-Typ</label>
            <select 
              value={selectedVideoType} 
              onChange={(e) => setSelectedVideoType(e.target.value)}
              disabled={loading}
            >
              {Object.entries(videoTypes).map(([key, videoType]) => (
                <option key={key} value={key}>{videoType.name}</option>
              ))}
            </select>
            {videoTypes[selectedVideoType] && (
              <div className="video-type-info">
                <p>{videoTypes[selectedVideoType].description}</p>
                <p>
                  <strong>Empfohlene Anzahl Bilder:</strong> {videoTypes[selectedVideoType].recommended_images}
                </p>
              </div>
            )}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Dauer (Sekunden)</label>
              <input
                type="number"
                min="5"
                max="60"
                value={duration}
                onChange={(e) => setDuration(parseInt(e.target.value))}
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label>FPS</label>
              <select 
                value={fps} 
                onChange={(e) => setFps(parseInt(e.target.value))}
                disabled={loading}
              >
                <option value={24}>24 FPS</option>
                <option value={30}>30 FPS</option>
                <option value={60}>60 FPS</option>
              </select>
            </div>
          </div>

          {renderVideoTypeOptions()}

          <button 
            onClick={generateVideo}
            disabled={loading || imagePaths.filter(p => p.trim()).length === 0}
            className="generate-button"
          >
            {loading ? 'Generiere Video...' : 'Video generieren'}
          </button>
        </div>

        {/* Videos List */}
        <div className="videos-section">
          <div className="videos-header">
            <h3>Generierte Videos</h3>
            
            <div className="header-actions">
              <select 
                value={filterVideoType} 
                onChange={(e) => setFilterVideoType(e.target.value)}
              >
                <option value="">Alle Video-Typen</option>
                {Object.entries(videoTypes).map(([key, videoType]) => (
                  <option key={key} value={key}>{videoType.name}</option>
                ))}
              </select>
              
              <button 
                onClick={cleanupTempFiles}
                className="cleanup-button"
              >
                🧹 Temp-Dateien löschen
              </button>
            </div>
          </div>

          <div className="videos-grid">
            {videos.length === 0 ? (
              <p className="no-videos">Keine Videos gefunden</p>
            ) : (
              videos.map((video) => (
                <div key={video.id} className="video-card">
                  <div className="video-preview">
                    <video 
                      src={`${API_BASE_URL}${video.file_url}`}
                      controls
                      preload="metadata"
                      className="video-element"
                    >
                      Ihr Browser unterstützt das Video-Element nicht.
                    </video>
                    <div className="video-overlay">
                      <span className="video-type-badge">
                        {videoTypes[video.video_type]?.name || video.video_type}
                      </span>
                    </div>
                  </div>
                  
                  <div className="video-info">
                    <h4>{video.filename}</h4>
                    
                    <div className="video-meta">
                      <span>Typ: {video.video_type}</span>
                      <span>Dauer: {video.duration}s</span>
                      <span>FPS: {video.fps}</span>
                      <span>Größe: {formatFileSize(video.file_size)}</span>
                      <span>{video.dimensions.width}x{video.dimensions.height}</span>
                      <span>{new Date(video.created_at).toLocaleDateString()}</span>
                    </div>
                    
                    <div className="image-paths">
                      <strong>Verwendete Bilder:</strong>
                      <ul>
                        {video.image_paths.map((path, index) => (
                          <li key={index} title={path}>
                            {path.split('/').pop()}
                          </li>
                        ))}
                      </ul>
                    </div>
                    
                    {Object.keys(video.options).length > 0 && (
                      <div className="video-options-display">
                        <strong>Optionen:</strong>
                        {Object.entries(video.options).map(([key, value]) => (
                          <span key={key}>{key}: {JSON.stringify(value)}</span>
                        ))}
                      </div>
                    )}
                    
                    <div className="video-actions">
                      <button 
                        onClick={() => window.open(`${API_BASE_URL}${video.file_url}`, '_blank')}
                        className="download-button"
                      >
                        📥 Download
                      </button>
                      <button 
                        onClick={() => deleteVideo(video.id)}
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

      {/* Video Types Info */}
      <div className="video-types-info">
        <h3>Verfügbare Video-Typen</h3>
        <div className="video-types-grid">
          {Object.entries(videoTypes).map(([key, videoType]) => (
            <div key={key} className="video-type-card">
              <h4>{videoType.name}</h4>
              <p>{videoType.description}</p>
              <div className="video-type-details">
                <p><strong>Mindestanzahl Bilder:</strong> {videoType.min_images}</p>
                <p><strong>Empfohlen:</strong> {videoType.recommended_images}</p>
                {videoType.options.length > 0 && (
                  <div>
                    <strong>Verfügbare Optionen:</strong>
                    <ul>
                      {videoType.options.map((option) => (
                        <li key={option}>{option}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default VideoGenerationInterface;
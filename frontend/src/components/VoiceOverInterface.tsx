import React, { useState, useEffect, useCallback } from 'react';
import ProjectRequired from './ProjectRequired';
import './VoiceOverInterface.css';

interface VoiceOverInterfaceProps {
  apiBaseUrl: string;
  videoPath?: string;
  onVoiceOverComplete?: (result: any) => void;
}

interface Voice {
  voice_id: string;
  name: string;
  gender: string;
  style: string;
}

interface CaptionStyle {
  font: string;
  font_size: number;
  color: string;
  outline_color: string;
  outline_width: number;
  position: string;
  margin: number;
}

interface VoiceOver {
  id: string;
  text: string;
  voice: string;
  voice_name: string;
  language: string;
  file_url: string;
  duration: number;
  created_at: string;
}

const VoiceOverInterface: React.FC<VoiceOverInterfaceProps> = ({ 
  apiBaseUrl, 
  videoPath,
  onVoiceOverComplete 
}) => {
  const [activeTab, setActiveTab] = useState<'generate' | 'process' | 'history'>('generate');
  const [scriptText, setScriptText] = useState('');
  const [selectedVoice, setSelectedVoice] = useState('bella');
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const [selectedCaptionStyle, setSelectedCaptionStyle] = useState('minimal');
  const [burnInCaptions, setBurnInCaptions] = useState(true);
  const [availableVoices, setAvailableVoices] = useState<Record<string, Voice>>({});
  const [captionStyles, setCaptionStyles] = useState<Record<string, CaptionStyle>>({});
  const [voiceOvers, setVoiceOvers] = useState<VoiceOver[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [generatedVoiceOver, setGeneratedVoiceOver] = useState<any>(null);
  const [processedVideo, setProcessedVideo] = useState<any>(null);
  const [isElevenLabsConfigured, setIsElevenLabsConfigured] = useState(false);

  // Video content for script generation
  const [videoContent, setVideoContent] = useState('');
  const [targetDuration, setTargetDuration] = useState(30);
  const [scriptStyle, setScriptStyle] = useState('conversational');
  const [period, setPeriod] = useState('');
  const [generatedScript, setGeneratedScript] = useState<any>(null);

  // Load available voices and caption styles
  useEffect(() => {
    fetchAvailableVoices();
    fetchCaptionStyles();
    fetchVoiceOvers();
  }, []);

  const fetchAvailableVoices = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/available-voices`);
      const data = await response.json();
      if (data.voices) {
        setAvailableVoices(data.voices);
        setIsElevenLabsConfigured(data.elevenlabs_configured);
      }
    } catch (error) {
      console.error('Error fetching voices:', error);
    }
  };

  const fetchCaptionStyles = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/caption-styles`);
      const data = await response.json();
      if (data.styles) {
        setCaptionStyles(data.styles);
      }
    } catch (error) {
      console.error('Error fetching caption styles:', error);
    }
  };

  const fetchVoiceOvers = async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/voice-overs`);
      const data = await response.json();
      if (data.voice_overs) {
        setVoiceOvers(data.voice_overs);
      }
    } catch (error) {
      console.error('Error fetching voice overs:', error);
    }
  };

  const generateVoiceScript = async () => {
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch(`${apiBaseUrl}/api/generate-voice-script`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          video_content: videoContent,
          target_duration: targetDuration,
          style: scriptStyle,
          period: period || null
        }),
      });

      const data = await response.json();
      if (data.success) {
        setGeneratedScript(data.script);
        setScriptText(data.script.script);
        setSuccess('Voice-over script generated successfully!');
      } else {
        setError(data.message || 'Failed to generate script');
      }
    } catch (error) {
      setError('Error generating voice script: ' + error);
    } finally {
      setIsLoading(false);
    }
  };

  const generateVoiceOver = async () => {
    if (!scriptText.trim()) {
      setError('Please enter text for voice over');
      return;
    }

    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch(`${apiBaseUrl}/api/generate-voice-over`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: scriptText,
          voice: selectedVoice,
          language: selectedLanguage,
        }),
      });

      const data = await response.json();
      if (data.success) {
        setGeneratedVoiceOver(data.voice_over);
        setSuccess('Voice-over generated successfully!');
        fetchVoiceOvers(); // Refresh the list
      } else {
        setError(data.message || 'Failed to generate voice over');
      }
    } catch (error) {
      setError('Error generating voice over: ' + error);
    } finally {
      setIsLoading(false);
    }
  };

  const processVideoWithVoiceAndCaptions = async () => {
    if (!videoPath || !scriptText.trim()) {
      setError('Please provide a video path and script text');
      return;
    }

    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch(`${apiBaseUrl}/api/process-video-with-voice-and-captions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          video_path: videoPath,
          script_text: scriptText,
          voice: selectedVoice,
          language: selectedLanguage,
          caption_style: selectedCaptionStyle,
          burn_in_captions: burnInCaptions,
        }),
      });

      const data = await response.json();
      if (data.success) {
        setProcessedVideo(data.final_video);
        setSuccess('Video processed with voice-over and captions!');
        if (onVoiceOverComplete) {
          onVoiceOverComplete(data);
        }
      } else {
        setError(data.message || 'Failed to process video');
      }
    } catch (error) {
      setError('Error processing video: ' + error);
    } finally {
      setIsLoading(false);
    }
  };

  const playAudio = (url: string) => {
    const audio = new Audio(url);
    audio.play();
  };

  const renderScriptSegments = () => {
    if (!generatedScript || !generatedScript.segments) return null;

    return (
      <div className="script-segments">
        <h4>Script Segments:</h4>
        {generatedScript.segments.map((segment: any, index: number) => (
          <div key={index} className="script-segment">
            <div className="segment-time">
              {segment.start_time}s - {segment.end_time}s
            </div>
            <div className="segment-text">{segment.text}</div>
            <div className="segment-emphasis">Emphasis: {segment.emphasis}</div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <ProjectRequired>
    <div className="voice-over-interface">
      <h2>Voice Over & Captions</h2>

      {!isElevenLabsConfigured && (
        <div className="warning-message">
          ⚠️ ElevenLabs API key not configured. Voice generation will not work.
        </div>
      )}

      <div className="tabs">
        <button
          className={`tab ${activeTab === 'generate' ? 'active' : ''}`}
          onClick={() => setActiveTab('generate')}
        >
          Generate Voice Over
        </button>
        <button
          className={`tab ${activeTab === 'process' ? 'active' : ''}`}
          onClick={() => setActiveTab('process')}
        >
          Process Video
        </button>
        <button
          className={`tab ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          History
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}

      {activeTab === 'generate' && (
        <div className="generate-section">
          <div className="script-generation">
            <h3>Generate Voice Script</h3>
            <div className="form-group">
              <label>Video Content Description:</label>
              <textarea
                value={videoContent}
                onChange={(e) => setVideoContent(e.target.value)}
                placeholder="Describe what's happening in the video..."
                rows={3}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Target Duration (seconds):</label>
                <input
                  type="number"
                  value={targetDuration}
                  onChange={(e) => setTargetDuration(Number(e.target.value))}
                  min={5}
                  max={60}
                />
              </div>

              <div className="form-group">
                <label>Style:</label>
                <select
                  value={scriptStyle}
                  onChange={(e) => setScriptStyle(e.target.value)}
                >
                  <option value="conversational">Conversational</option>
                  <option value="professional">Professional</option>
                  <option value="energetic">Energetic</option>
                  <option value="calm">Calm</option>
                  <option value="storytelling">Storytelling</option>
                </select>
              </div>

              <div className="form-group">
                <label>Period (optional):</label>
                <select
                  value={period}
                  onChange={(e) => setPeriod(e.target.value)}
                >
                  <option value="">None</option>
                  <option value="Image">Image</option>
                  <option value="Veränderung">Veränderung</option>
                  <option value="Energie">Energie</option>
                  <option value="Kreativität">Kreativität</option>
                  <option value="Erfolg">Erfolg</option>
                  <option value="Entspannung">Entspannung</option>
                  <option value="Umsicht">Umsicht</option>
                </select>
              </div>
            </div>

            <button
              onClick={generateVoiceScript}
              disabled={isLoading || !videoContent}
              className="primary-button"
            >
              Generate Script
            </button>

            {generatedScript && renderScriptSegments()}
          </div>

          <div className="voice-generation">
            <h3>Generate Voice Over</h3>
            <div className="form-group">
              <label>Script Text:</label>
              <textarea
                value={scriptText}
                onChange={(e) => setScriptText(e.target.value)}
                placeholder="Enter the text for voice over..."
                rows={6}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Voice:</label>
                <select
                  value={selectedVoice}
                  onChange={(e) => setSelectedVoice(e.target.value)}
                >
                  {Object.entries(availableVoices).map(([key, voice]) => (
                    <option key={key} value={key}>
                      {voice.name} ({voice.gender}, {voice.style})
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Language:</label>
                <select
                  value={selectedLanguage}
                  onChange={(e) => setSelectedLanguage(e.target.value)}
                >
                  <option value="en">English</option>
                  <option value="de">German</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                  <option value="it">Italian</option>
                  <option value="pt">Portuguese</option>
                  <option value="nl">Dutch</option>
                  <option value="pl">Polish</option>
                </select>
              </div>
            </div>

            <button
              onClick={generateVoiceOver}
              disabled={isLoading || !scriptText || !isElevenLabsConfigured}
              className="primary-button"
            >
              Generate Voice Over
            </button>

            {generatedVoiceOver && (
              <div className="generated-voice-over">
                <h4>Generated Voice Over:</h4>
                <div className="voice-info">
                  <p>Voice: {generatedVoiceOver.voice_name}</p>
                  <p>Duration: {generatedVoiceOver.duration?.toFixed(2)}s</p>
                  <button
                    onClick={() => playAudio(generatedVoiceOver.file_url)}
                    className="play-button"
                  >
                    ▶️ Play Audio
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'process' && (
        <div className="process-section">
          <h3>Process Video with Voice & Captions</h3>
          
          {videoPath && (
            <div className="video-info">
              <p>Video Path: {videoPath}</p>
            </div>
          )}

          <div className="form-group">
            <label>Script Text:</label>
            <textarea
              value={scriptText}
              onChange={(e) => setScriptText(e.target.value)}
              placeholder="Enter the script for voice over..."
              rows={6}
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Voice:</label>
              <select
                value={selectedVoice}
                onChange={(e) => setSelectedVoice(e.target.value)}
              >
                {Object.entries(availableVoices).map(([key, voice]) => (
                  <option key={key} value={key}>
                    {voice.name} ({voice.gender}, {voice.style})
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Caption Style:</label>
              <select
                value={selectedCaptionStyle}
                onChange={(e) => setSelectedCaptionStyle(e.target.value)}
              >
                {Object.entries(captionStyles).map(([key, style]) => (
                  <option key={key} value={key}>
                    {key.charAt(0).toUpperCase() + key.slice(1)} 
                    ({style.font}, {style.font_size}px)
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  checked={burnInCaptions}
                  onChange={(e) => setBurnInCaptions(e.target.checked)}
                />
                Burn in captions
              </label>
            </div>
          </div>

          <button
            onClick={processVideoWithVoiceAndCaptions}
            disabled={isLoading || !videoPath || !scriptText || !isElevenLabsConfigured}
            className="primary-button"
          >
            Process Video
          </button>

          {processedVideo && (
            <div className="processed-video">
              <h4>Processed Video:</h4>
              <video controls src={processedVideo.url} style={{ maxWidth: '100%' }} />
              <p>Download: <a href={processedVideo.url} download>Download Video</a></p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'history' && (
        <div className="history-section">
          <h3>Voice Over History</h3>
          <div className="voice-over-list">
            {voiceOvers.length === 0 ? (
              <p>No voice overs generated yet.</p>
            ) : (
              voiceOvers.map((vo) => (
                <div key={vo.id} className="voice-over-item">
                  <div className="vo-info">
                    <h4>{vo.voice_name}</h4>
                    <p className="vo-text">{vo.text.substring(0, 100)}...</p>
                    <p className="vo-meta">
                      Language: {vo.language} | Duration: {vo.duration?.toFixed(2)}s
                    </p>
                    <p className="vo-date">
                      Created: {new Date(vo.created_at).toLocaleString()}
                    </p>
                  </div>
                  <button
                    onClick={() => playAudio(vo.file_url)}
                    className="play-button"
                  >
                    ▶️ Play
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {isLoading && (
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
          <p>Processing...</p>
        </div>
      )}
    </div>
    </ProjectRequired>
  );
};

export default VoiceOverInterface;
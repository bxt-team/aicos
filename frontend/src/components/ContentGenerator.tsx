import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './ContentGenerator.css';

interface ContentRequest {
  knowledge_files?: string[];
  style_preferences?: Record<string, string>;
}

const ContentGenerator: React.FC = () => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleGenerateContent = async () => {
    setIsGenerating(true);
    setError(null);

    try {
      const requestData: ContentRequest = {
        knowledge_files: ['affirmations.txt', 'wellness_tips.txt'],
        style_preferences: {
          image_style: 'inspirational',
          tone: 'motivational',
          format: 'instagram_post'
        }
      };

      const response = await axios.post('http://localhost:8000/content/generate', requestData);
      const { content_id } = response.data;

      navigate(`/content/${content_id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate content');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="content-generator">
      <div className="generator-container">
        <h2>Generate Instagram Content</h2>
        <p className="generator-description">
          Create engaging Instagram posts with AI-powered content generation using your knowledge files.
          Our system will research topics, write compelling captions, and generate beautiful images.
        </p>

        <div className="generator-features">
          <div className="feature">
            <h3>📚 Knowledge-Based</h3>
            <p>Uses your affirmations and wellness tips to create authentic content</p>
          </div>
          <div className="feature">
            <h3>✍️ AI Writing</h3>
            <p>Generates engaging captions with hooks, value, and call-to-actions</p>
          </div>
          <div className="feature">
            <h3>🎨 Visual Creation</h3>
            <p>Creates stunning images tailored to your content and brand</p>
          </div>
          <div className="feature">
            <h3>👀 Preview & Approve</h3>
            <p>Review and approve content before publishing</p>
          </div>
        </div>

        <div className="generator-actions">
          <button 
            className="generate-button"
            onClick={handleGenerateContent}
            disabled={isGenerating}
          >
            {isGenerating ? (
              <>
                <span className="spinner"></span>
                Generating Content...
              </>
            ) : (
              'Generate Instagram Content'
            )}
          </button>
        </div>

        {error && (
          <div className="error-message">
            <p>Error: {error}</p>
          </div>
        )}

        <div className="generator-info">
          <h3>How it works:</h3>
          <ol>
            <li>Our AI analyzes your knowledge files for trending topics</li>
            <li>Creates compelling Instagram captions optimized for engagement</li>
            <li>Generates beautiful, brand-aligned images</li>
            <li>Presents everything for your review and approval</li>
          </ol>
        </div>
      </div>
    </div>
  );
};

export default ContentGenerator;
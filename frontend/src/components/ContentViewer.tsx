import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import './ContentViewer.css';

interface ContentData {
  content_id: string;
  status: string;
  created_at: string;
  research_results: string;
  written_content: string;
  visual_concepts: string;
  images: Array<{
    success: boolean;
    image_url: string;
    image_path: string;
    prompt: string;
    style: string;
  }>;
  error?: string;
  image_error?: string;
  completed_at?: string;
}

const ContentViewer: React.FC = () => {
  const { contentId } = useParams<{ contentId: string }>();
  const [content, setContent] = useState<ContentData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [approvalStatus, setApprovalStatus] = useState<string>('pending');
  const [feedback, setFeedback] = useState<string>('');

  useEffect(() => {
    if (!contentId) return;

    const pollContent = async () => {
      try {
        const response = await axios.get(`http://localhost:8000/content/${contentId}`);
        const data = response.data;
        console.log('Content status:', data.status, 'Last updated:', data.last_updated); // Debug log
        setContent(data);
        
        if (data.status === 'completed' || data.status === 'failed') {
          setLoading(false);
        }
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to fetch content');
        setLoading(false);
      }
    };

    pollContent();

    const interval = setInterval(pollContent, 1000); // Poll every second for more responsive updates
    return () => clearInterval(interval);
  }, [contentId]);

  const handleApproval = async (approved: boolean) => {
    if (!contentId) return;

    try {
      await axios.post('http://localhost:8000/approve-content', {
        content_id: contentId,
        approved,
        feedback: feedback || null
      });
      
      setApprovalStatus(approved ? 'approved' : 'rejected');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit approval');
    }
  };

  if (loading) {
    return (
      <div className="content-viewer">
        <div className="loading-container">
          <div className="spinner-large"></div>
          <h2>Generating Your Content...</h2>
          <p>This may take a few minutes while our AI creates your Instagram content.</p>
          {content && (
            <div className="status-info">
              <p>Status: {content.status}</p>
              <div className="progress-steps">
                <div className={`step ${content.status === 'generating_text' || content.status === 'generating_images' || content.status === 'completed' ? 'active' : ''}`}>
                  📝 Generating Text
                </div>
                <div className={`step ${content.status === 'generating_images' || content.status === 'completed' ? 'active' : ''}`}>
                  🎨 Creating Images
                </div>
                <div className={`step ${content.status === 'completed' ? 'active' : ''}`}>
                  ✅ Complete
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  if (error || !content) {
    return (
      <div className="content-viewer">
        <div className="error-container">
          <h2>Error</h2>
          <p>{error || 'Content not found'}</p>
        </div>
      </div>
    );
  }

  if (content.status === 'failed') {
    return (
      <div className="content-viewer">
        <div className="error-container">
          <h2>Content Generation Failed</h2>
          <p>{content.error || 'Unknown error occurred'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="content-viewer">
      <div className="content-container">
        <div className="content-header">
          <h2>Generated Instagram Content</h2>
          <div className="content-meta">
            <span className="status">Status: {content.status}</span>
            <span className="created">Created: {new Date(content.created_at).toLocaleString()}</span>
          </div>
        </div>

        <div className="content-sections">
          <div className="section">
            <h3>📊 Research Results</h3>
            <div className="content-box">
              <pre>{content.research_results}</pre>
            </div>
          </div>

          <div className="section">
            <h3>✍️ Written Content</h3>
            <div className="content-box">
              <pre>{content.written_content}</pre>
            </div>
          </div>

          <div className="section">
            <h3>🎨 Visual Concepts</h3>
            <div className="content-box">
              <pre>{content.visual_concepts}</pre>
            </div>
          </div>

          {content.images && content.images.length > 0 && (
            <div className="section">
              <h3>🖼️ Generated Images</h3>
              <div className="images-grid">
                {content.images.map((image, index) => (
                  <div key={index} className="image-card">
                    <img src={image.image_url} alt={`Generated content ${index + 1}`} />
                    <div className="image-info">
                      <p><strong>Prompt:</strong> {image.prompt}</p>
                      <p><strong>Style:</strong> {image.style}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {content.image_error && (
            <div className="section">
              <h3>⚠️ Image Generation Error</h3>
              <div className="error-box">
                <p>{content.image_error}</p>
              </div>
            </div>
          )}
        </div>

        <div className="approval-section">
          <h3>Approval</h3>
          <div className="approval-form">
            <textarea
              placeholder="Optional feedback or comments..."
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              rows={4}
            />
            <div className="approval-buttons">
              <button 
                className="approve-button"
                onClick={() => handleApproval(true)}
                disabled={approvalStatus !== 'pending'}
              >
                ✅ Approve
              </button>
              <button 
                className="reject-button"
                onClick={() => handleApproval(false)}
                disabled={approvalStatus !== 'pending'}
              >
                ❌ Reject
              </button>
            </div>
            {approvalStatus !== 'pending' && (
              <div className="approval-status">
                Status: {approvalStatus}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContentViewer;
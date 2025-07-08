import React, { useState } from 'react';
import './ImageFeedback.css';

interface ImageFeedbackProps {
  imagePath: string;
  generationParams?: Record<string, any>;
  onFeedbackSubmit?: (feedback: FeedbackData) => void;
  onRegenerateRequest?: (feedback: RegenerationRequest) => void;
}

interface RegenerationRequest {
  originalImagePath: string;
  feedback: string;
  rating: number;
  originalPrompt?: string;
  generationParams?: Record<string, any>;
  keepOriginalStyle?: boolean;
}

interface FeedbackData {
  rating: number;
  comments: string;
  tags: string[];
}

const ImageFeedback: React.FC<ImageFeedbackProps> = ({ 
  imagePath, 
  generationParams = {},
  onFeedbackSubmit,
  onRegenerateRequest 
}) => {
  const [rating, setRating] = useState<number>(0);
  const [comments, setComments] = useState<string>('');
  const [tags, setTags] = useState<string[]>([]);
  const [customTag, setCustomTag] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [showFeedbackForm, setShowFeedbackForm] = useState<boolean>(false);
  const [isRegenerating, setIsRegenerating] = useState<boolean>(false);
  const [keepOriginalStyle, setKeepOriginalStyle] = useState<boolean>(true);
  
  const predefinedTags = [
    'inspiring', 'calming', 'energetic', 'spiritual', 'creative',
    'professional', 'warm', 'modern', 'artistic', 'peaceful',
    'motivational', 'healing', 'transformative', 'elegant'
  ];

  const handleStarClick = (starRating: number) => {
    setRating(starRating);
    if (!showFeedbackForm) {
      setShowFeedbackForm(true);
    }
  };

  const handleTagToggle = (tag: string) => {
    setTags(prev => 
      prev.includes(tag) 
        ? prev.filter(t => t !== tag)
        : [...prev, tag]
    );
  };

  const handleAddCustomTag = () => {
    if (customTag.trim() && !tags.includes(customTag.trim())) {
      setTags(prev => [...prev, customTag.trim()]);
      setCustomTag('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (rating === 0) {
      alert('Please provide a rating before submitting');
      return;
    }

    setIsSubmitting(true);
    
    try {
      const feedbackData: FeedbackData = {
        rating,
        comments,
        tags
      };

      // Submit feedback to backend
      const response = await fetch('/api/submit-feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          imagePath,
          ...feedbackData,
          generationParams
        })
      });

      if (response.ok) {
        // Call parent callback if provided
        if (onFeedbackSubmit) {
          onFeedbackSubmit(feedbackData);
        }
        
        // Reset form
        setRating(0);
        setComments('');
        setTags([]);
        setShowFeedbackForm(false);
        
        alert('Feedback submitted successfully!');
      } else {
        throw new Error('Failed to submit feedback');
      }
    } catch (error) {
      console.error('Error submitting feedback:', error);
      alert('Error submitting feedback. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRegenerateWithFeedback = async () => {
    if (rating === 0) {
      alert('Please provide a rating before regenerating');
      return;
    }

    if (!comments.trim()) {
      alert('Please provide feedback comments explaining what you want changed');
      return;
    }

    setIsRegenerating(true);
    
    try {
      const regenerationRequest: RegenerationRequest = {
        originalImagePath: imagePath,
        feedback: comments,
        rating,
        originalPrompt: generationParams?.ai_prompt || generationParams?.dalle_prompt,
        generationParams,
        keepOriginalStyle
      };

      // Call the regeneration API
      const response = await fetch('/api/regenerate-with-feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(regenerationRequest)
      });

      if (response.ok) {
        const result = await response.json();
        
        // Call parent callback if provided
        if (onRegenerateRequest) {
          onRegenerateRequest(regenerationRequest);
        }
        
        // Reset form
        setRating(0);
        setComments('');
        setTags([]);
        setShowFeedbackForm(false);
        
        alert(`Image regenerated successfully! \n\nOriginal prompt: ${result.original_prompt}\n\nOptimized prompt: ${result.optimized_prompt}`);
      } else {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to regenerate image');
      }
    } catch (error) {
      console.error('Error regenerating image:', error);
      alert(`Error regenerating image: ${error instanceof Error ? error.message : 'Please try again.'}`);
    } finally {
      setIsRegenerating(false);
    }
  };

  const StarRating = () => (
    <div className="star-rating">
      <span className="rating-label">Rate this image:</span>
      {[1, 2, 3, 4, 5].map(star => (
        <button
          key={star}
          type="button"
          className={`star ${star <= rating ? 'filled' : ''}`}
          onClick={() => handleStarClick(star)}
          aria-label={`Rate ${star} stars`}
        >
          ⭐
        </button>
      ))}
      {rating > 0 && (
        <span className="rating-text">({rating}/5)</span>
      )}
    </div>
  );

  return (
    <div className="image-feedback-container">
      <StarRating />
      
      {showFeedbackForm && (
        <form onSubmit={handleSubmit} className="feedback-form">
          <div className="form-group">
            <label htmlFor="comments">Additional Comments (optional):</label>
            <textarea
              id="comments"
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              placeholder="What did you like or dislike about this image? How could it be improved?"
              rows={3}
            />
          </div>
          
          <div className="form-group">
            <label>Tags (select all that apply):</label>
            <div className="tags-container">
              {predefinedTags.map(tag => (
                <button
                  key={tag}
                  type="button"
                  className={`tag-button ${tags.includes(tag) ? 'selected' : ''}`}
                  onClick={() => handleTagToggle(tag)}
                >
                  {tag}
                </button>
              ))}
            </div>
            
            <div className="custom-tag-input">
              <input
                type="text"
                value={customTag}
                onChange={(e) => setCustomTag(e.target.value)}
                placeholder="Add custom tag"
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddCustomTag())}
              />
              <button type="button" onClick={handleAddCustomTag}>Add</button>
            </div>
            
            {tags.length > 0 && (
              <div className="selected-tags">
                <span>Selected tags: </span>
                {tags.map(tag => (
                  <span key={tag} className="selected-tag">
                    {tag}
                    <button 
                      type="button" 
                      onClick={() => handleTagToggle(tag)}
                      aria-label={`Remove ${tag} tag`}
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>
          
          {/* Regeneration options for AI-generated images */}
          {generationParams?.ai_generated && (
            <div className="form-group regeneration-options">
              <label>
                <input
                  type="checkbox"
                  checked={keepOriginalStyle}
                  onChange={(e) => setKeepOriginalStyle(e.target.checked)}
                />
                Keep original style
              </label>
              <p className="help-text">
                When enabled, the regenerated image will maintain the same visual style as the original.
              </p>
            </div>
          )}
          
          <div className="form-actions">
            <button 
              type="submit" 
              disabled={isSubmitting || rating === 0}
              className="submit-button"
            >
              {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
            </button>
            
            {/* Regenerate button for AI-generated images */}
            {generationParams?.ai_generated && onRegenerateRequest && (
              <button 
                type="button" 
                disabled={isRegenerating || rating === 0 || !comments.trim()}
                className="regenerate-button"
                onClick={handleRegenerateWithFeedback}
              >
                {isRegenerating ? 'Regenerating...' : 'Regenerate with Feedback'}
              </button>
            )}
            
            <button 
              type="button" 
              onClick={() => setShowFeedbackForm(false)}
              className="cancel-button"
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  );
};

export default ImageFeedback;
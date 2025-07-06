import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './QAInterface.css';

interface QAInterfaceProps {}

interface Question {
  id: string;
  question: string;
  answer: string;
  timestamp: string;
}

const QAInterface: React.FC<QAInterfaceProps> = () => {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<Question[]>([]);
  const [overview, setOverview] = useState<string>('');
  const [showOverview, setShowOverview] = useState(false);

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  useEffect(() => {
    loadOverview();
  }, []);

  const loadOverview = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/knowledge-overview`);
      if (response.data.success) {
        setOverview(response.data.overview);
      }
    } catch (error) {
      console.error('Error loading knowledge overview:', error);
    }
  };

  const handleSubmitQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/ask-question`, {
        question: question.trim()
      });

      if (response.data.success) {
        const newQuestion: Question = {
          id: Date.now().toString(),
          question: question.trim(),
          answer: response.data.answer,
          timestamp: new Date().toISOString()
        };

        setHistory(prev => [newQuestion, ...prev]);
        setQuestion('');
      }
    } catch (error: any) {
      console.error('Error asking question:', error);
      const errorMessage = error.response?.data?.detail || 'Ein Fehler ist beim Verarbeiten Ihrer Frage aufgetreten.';
      
      const errorQuestion: Question = {
        id: Date.now().toString(),
        question: question.trim(),
        answer: `Fehler: ${errorMessage}`,
        timestamp: new Date().toISOString()
      };

      setHistory(prev => [errorQuestion, ...prev]);
    } finally {
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const suggestedQuestions = [
    "Was sind die 7 Lebenszyklen?",
    "Wie kann ich meine Energie während verschiedener Zyklen optimieren?",
    "Was ist die Beziehung zwischen Tages- und Jahreszyklen?",
    "Wie erkenne ich, in welchem Zyklus ich mich gerade befinde?",
    "Was sind die Schlüsselprinzipien des zyklusbasierten Lebens?",
    "Wie kann Kreativität durch Zyklusbewusstsein gesteigert werden?",
    "Welche Rolle spielt Ruhe in den 7 Zyklen?"
  ];

  return (
    <div className="qa-interface">
      <div className="qa-header">
        <h2>Ask About the 7 Cycles of Life</h2>
        <p>Get insights and answers based on the comprehensive knowledge base</p>
        
        <button
          className="overview-toggle"
          onClick={() => setShowOverview(!showOverview)}
        >
          {showOverview ? 'Hide' : 'Show'} Knowledge Overview
        </button>
        
        {showOverview && (
          <div className="overview-section">
            <h3>Knowledge Base Overview</h3>
            <div className="overview-content">
              {overview || 'Loading overview...'}
            </div>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmitQuestion} className="question-form">
        <div className="input-group">
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question about the 7 Cycles of Life..."
            className="question-input"
            rows={3}
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="submit-button"
          >
            {loading ? 'Thinking...' : 'Ask Question'}
          </button>
        </div>
      </form>

      <div className="suggested-questions">
        <h4>Suggested Questions:</h4>
        <div className="suggestion-grid">
          {suggestedQuestions.map((suggested, index) => (
            <button
              key={index}
              onClick={() => setQuestion(suggested)}
              className="suggestion-button"
              disabled={loading}
            >
              {suggested}
            </button>
          ))}
        </div>
      </div>

      <div className="qa-history">
        <h3>Recent Questions & Answers</h3>
        {history.length === 0 ? (
          <p className="no-history">No questions asked yet. Try asking something!</p>
        ) : (
          <div className="history-list">
            {history.map((qa) => (
              <div key={qa.id} className="qa-item">
                <div className="question-section">
                  <strong>Q:</strong> {qa.question}
                  <span className="timestamp">{formatTimestamp(qa.timestamp)}</span>
                </div>
                <div className="answer-section">
                  <strong>A:</strong>
                  <div className="answer-content">{qa.answer}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default QAInterface;
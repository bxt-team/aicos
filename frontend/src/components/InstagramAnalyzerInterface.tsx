import React, { useState, useEffect } from 'react';
import './InstagramAnalyzerInterface.css';

interface ContentAnalysis {
  primary_content_types?: string[];
  posting_frequency?: string;
  content_themes?: string[];
  recurring_formats?: string[];
  visual_style?: string;
}

interface EngagementStrategies {
  primary_cta_types?: string[];
  interaction_methods?: string[];
  community_building?: string;
  engagement_rate_estimate?: string;
}

interface PostingPatterns {
  frequency?: string;
  consistency?: string;
  optimal_times?: string[];
  posting_rhythm?: string;
}

interface HashtagStrategy {
  average_hashtag_count?: number;
  hashtag_mix?: string;
  branded_hashtags?: string[];
  niche_hashtags?: string[];
  recommended_hashtag_count?: number;
  hashtag_categories?: {
    niche_specific?: string[];
    broader_reach?: string[];
    branded?: string[];
    trending?: string[];
  };
  hashtag_rotation_plan?: string;
}

interface VisualBranding {
  color_scheme?: string[];
  design_consistency?: string;
  typography_style?: string;
  filter_style?: string;
  color_palette?: string[];
  design_consistency_rules?: string[];
  typography_guidelines?: string;
  image_style_guide?: string;
}

interface Tonality {
  writing_style?: string;
  personality?: string;
  caption_length?: string;
  emoji_usage?: string;
  brand_personality?: string;
  caption_structure?: string;
  emoji_and_formatting?: string;
}

interface SuccessFactors {
  key_differentiators?: string[];
  engagement_drivers?: string[];
  community_building_strengths?: string[];
  content_quality_factors?: string[];
}

interface ContentExamples {
  high_engagement_post_types?: string[];
  signature_content_formats?: string[];
  trending_content_themes?: string[];
}

interface OverallAssessment {
  success_level?: string;
  growth_indicators?: string[];
  competitive_advantages?: string[];
  areas_of_excellence?: string[];
}

interface Analysis {
  analysis_id: string;
  account_username: string;
  analyzed_at: string;
  analysis_focus: string;
  content_analysis?: ContentAnalysis;
  engagement_strategies?: EngagementStrategies;
  posting_patterns?: PostingPatterns;
  hashtag_strategy?: HashtagStrategy;
  visual_branding?: VisualBranding;
  tonality?: Tonality;
  success_factors?: SuccessFactors;
  content_examples?: ContentExamples;
  overall_assessment?: OverallAssessment;
}

interface ContentStrategy {
  primary_content_types?: string[];
  content_themes?: string[];
  recurring_formats?: string[];
  visual_style_guide?: string;
  content_ratio?: string;
}

interface PostingStrategy {
  recommended_frequency?: string;
  optimal_posting_times?: string[];
  content_calendar_structure?: string;
  consistency_rules?: string[];
}

interface EngagementStrategyType {
  primary_cta_strategies?: string[];
  community_building_tactics?: string[];
  interaction_methods?: string[];
  engagement_goals?: string[];
}

interface ImplementationPhase {
  focus?: string;
  key_actions?: string[];
  success_metrics?: string[];
}

interface ImplementationPlan {
  week_1_4?: ImplementationPhase;
  month_2_3?: ImplementationPhase;
  month_4_6?: ImplementationPhase;
}

interface SuccessIndicators {
  engagement_targets?: string[];
  growth_milestones?: string[];
  content_performance_kpis?: string[];
}

interface AdaptationNotes {
  key_adaptations_from_original?: string[];
  niche_specific_adjustments?: string[];
  account_stage_considerations?: string[];
}

interface Strategy {
  strategy_id: string;
  based_on_analysis: string;
  target_niche: string;
  account_stage: string;
  created_at: string;
  analyzed_account: string;
  content_strategy?: ContentStrategy;
  posting_strategy?: PostingStrategy;
  engagement_strategy?: EngagementStrategyType;
  hashtag_strategy?: HashtagStrategy;
  visual_branding?: VisualBranding;
  tonality_guide?: Tonality;
  implementation_plan?: ImplementationPlan;
  success_indicators?: SuccessIndicators;
  adaptation_notes?: AdaptationNotes;
  error?: string;
  raw_strategy?: string;
}

interface CommonSuccessFactors {
  universal_strategies?: string[];
  consistent_content_types?: string[];
  shared_engagement_tactics?: string[];
  common_posting_patterns?: string[];
}

interface KeyDifferences {
  niche_specific_approaches?: string[];
  unique_strategies?: string[];
  varying_content_focuses?: string[];
}

interface BestPractices {
  content_creation?: string[];
  engagement_optimization?: string[];
  visual_branding?: string[];
  hashtag_usage?: string[];
}

interface TrendInsights {
  current_trends?: string[];
  emerging_content_formats?: string[];
  effective_hashtag_strategies?: string[];
}

interface StrategicRecommendations {
  for_new_accounts?: string[];
  for_growing_accounts?: string[];
  for_established_accounts?: string[];
}

interface ComparativeAnalysis {
  comparative_analysis_id: string;
  analyzed_accounts: string[];
  common_success_factors?: CommonSuccessFactors;
  key_differences?: KeyDifferences;
  identified_best_practices?: BestPractices;
  trend_insights?: TrendInsights;
  strategic_recommendations?: StrategicRecommendations;
}

const InstagramAnalyzerInterface: React.FC = () => {
  const [activeTab, setActiveTab] = useState('analyze');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Single account analysis
  const [accountInput, setAccountInput] = useState('');
  const [analysisFocus, setAnalysisFocus] = useState('comprehensive');
  const [currentAnalysis, setCurrentAnalysis] = useState<Analysis | null>(null);
  
  // Multiple accounts analysis
  const [multipleAccounts, setMultipleAccounts] = useState<string[]>(['']);
  const [comparativeAnalysis, setComparativeAnalysis] = useState<ComparativeAnalysis | null>(null);
  
  // Strategy generation
  const [selectedAnalysisId, setSelectedAnalysisId] = useState('');
  const [targetNiche, setTargetNiche] = useState('7cycles');
  const [accountStage, setAccountStage] = useState('starting');
  const [currentStrategy, setCurrentStrategy] = useState<Strategy | null>(null);
  
  // Stored data
  const [storedAnalyses, setStoredAnalyses] = useState<Analysis[]>([]);
  const [storedStrategies, setStoredStrategies] = useState<Strategy[]>([]);

  useEffect(() => {
    loadStoredData();
  }, []);

  const loadStoredData = async () => {
    try {
      const response = await fetch('/api/instagram-analyses');
      if (response.ok) {
        const data = await response.json();
        setStoredAnalyses(data.analyses || []);
        
        // Parse strategies that have raw_strategy but no detailed strategy
        const processedStrategies = (data.strategies || []).map((strategy: Strategy) => {
          if (strategy.raw_strategy && strategy.error && !strategy.content_strategy) {
            try {
              const rawStrategy = strategy.raw_strategy;
              const jsonMatch = rawStrategy.match(/```json\s*\n(.*?)\n```/s);
              if (jsonMatch) {
                const parsedStrategy = JSON.parse(jsonMatch[1]);
                return { ...strategy, ...parsedStrategy };
              }
            } catch (e) {
              console.error('Failed to parse raw strategy:', e);
            }
          }
          return strategy;
        });
        
        setStoredStrategies(processedStrategies);
      }
    } catch (err) {
      console.error('Error loading stored data:', err);
    }
  };

  const analyzeAccount = async () => {
    if (!accountInput.trim()) {
      setError('Bitte geben Sie einen Instagram-Account ein');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/analyze-instagram-account', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          account_url_or_username: accountInput,
          analysis_focus: analysisFocus
        })
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Received analysis data:', data);
        
        // If analysis has raw_analysis, try to parse it
        let analysis = data.analysis;
        if (analysis.raw_analysis && !analysis.content_analysis) {
          try {
            const rawAnalysis = analysis.raw_analysis;
            const jsonMatch = rawAnalysis.match(/```json\s*\n(.*?)\n```/s);
            if (jsonMatch) {
              const parsedData = JSON.parse(jsonMatch[1]);
              analysis = { ...analysis, ...parsedData };
            }
          } catch (e) {
            console.error('Failed to parse raw analysis:', e);
          }
        }
        
        setCurrentAnalysis(analysis);
        await loadStoredData(); // Refresh stored data
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Fehler bei der Account-Analyse');
      }
    } catch (err) {
      setError('Netzwerkfehler bei der Account-Analyse');
    } finally {
      setLoading(false);
    }
  };

  const analyzeMultipleAccounts = async () => {
    const validAccounts = multipleAccounts.filter(acc => acc.trim());
    if (validAccounts.length < 2) {
      setError('Bitte geben Sie mindestens 2 Instagram-Accounts ein');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/analyze-multiple-accounts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          account_list: validAccounts,
          analysis_focus: analysisFocus
        })
      });

      if (response.ok) {
        const data = await response.json();
        setComparativeAnalysis(data.comparative_analysis);
        await loadStoredData(); // Refresh stored data
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Fehler bei der Multi-Account-Analyse');
      }
    } catch (err) {
      setError('Netzwerkfehler bei der Multi-Account-Analyse');
    } finally {
      setLoading(false);
    }
  };

  const generateStrategy = async () => {
    if (!selectedAnalysisId) {
      setError('Bitte wählen Sie eine Analyse aus');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/generate-strategy-from-analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          analysis_id: selectedAnalysisId,
          target_niche: targetNiche,
          account_stage: accountStage
        })
      });

      if (response.ok) {
        const data = await response.json();
        let strategy = data.strategy;
        
        // If strategy has raw_strategy but no detailed strategy, try to parse it
        if (strategy.raw_strategy && strategy.error && !strategy.content_strategy) {
          try {
            const rawStrategy = strategy.raw_strategy;
            const jsonMatch = rawStrategy.match(/```json\s*\n(.*?)\n```/s);
            if (jsonMatch) {
              const parsedStrategy = JSON.parse(jsonMatch[1]);
              strategy = { ...strategy, ...parsedStrategy };
            }
          } catch (e) {
            console.error('Failed to parse raw strategy:', e);
          }
        }
        
        setCurrentStrategy(strategy);
        await loadStoredData(); // Refresh stored data
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Fehler bei der Strategie-Generierung');
      }
    } catch (err) {
      setError('Netzwerkfehler bei der Strategie-Generierung');
    } finally {
      setLoading(false);
    }
  };

  const addAccountInput = () => {
    setMultipleAccounts([...multipleAccounts, '']);
  };

  const updateAccountInput = (index: number, value: string) => {
    const updated = [...multipleAccounts];
    updated[index] = value;
    setMultipleAccounts(updated);
  };

  const removeAccountInput = (index: number) => {
    setMultipleAccounts(multipleAccounts.filter((_, i) => i !== index));
  };

  const renderAnalysisResults = (analysis: Analysis) => {
    if (!analysis) return null;

    console.log('Rendering analysis:', analysis);
    
    return (
      <div className="analysis-results">
        <h3>Analyse von {analysis.account_username}</h3>
        
        {analysis.content_analysis && (
          <div className="analysis-section">
            <h4>Content-Analyse</h4>
            <div className="analysis-grid">
              <div className="analysis-item">
                <strong>Haupt-Content-Typen:</strong>
                <ul>
                  {analysis.content_analysis.primary_content_types?.map((type: string, i: number) => (
                    <li key={i}>{type}</li>
                  ))}
                </ul>
              </div>
              <div className="analysis-item">
                <strong>Posting-Frequenz:</strong> {analysis.content_analysis.posting_frequency}
              </div>
              <div className="analysis-item">
                <strong>Visueller Stil:</strong> {analysis.content_analysis.visual_style}
              </div>
            </div>
          </div>
        )}

        {analysis.engagement_strategies && (
          <div className="analysis-section">
            <h4>Engagement-Strategien</h4>
            <div className="analysis-grid">
              <div className="analysis-item">
                <strong>Primäre CTAs:</strong>
                <ul>
                  {analysis.engagement_strategies.primary_cta_types?.map((cta: string, i: number) => (
                    <li key={i}>{cta}</li>
                  ))}
                </ul>
              </div>
              <div className="analysis-item">
                <strong>Engagement-Rate:</strong> {analysis.engagement_strategies.engagement_rate_estimate}
              </div>
            </div>
          </div>
        )}

        {analysis.success_factors && (
          <div className="analysis-section">
            <h4>Erfolgsfaktoren</h4>
            <div className="analysis-grid">
              <div className="analysis-item">
                <strong>Haupt-Differenzierungsmerkmale:</strong>
                <ul>
                  {analysis.success_factors.key_differentiators?.map((factor: string, i: number) => (
                    <li key={i}>{factor}</li>
                  ))}
                </ul>
              </div>
              <div className="analysis-item">
                <strong>Engagement-Treiber:</strong>
                <ul>
                  {analysis.success_factors.engagement_drivers?.map((driver: string, i: number) => (
                    <li key={i}>{driver}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}
        
        {/* Debug: Show all available data */}
        <div className="analysis-section">
          <h4>Debug: Verfügbare Daten</h4>
          <pre style={{backgroundColor: '#f5f5f5', padding: '10px', overflow: 'auto', fontSize: '12px'}}>
            {JSON.stringify(analysis, null, 2)}
          </pre>
        </div>
      </div>
    );
  };

  const renderStrategyResults = (strategy: Strategy) => {
    if (!strategy) return null;

    return (
      <div className="strategy-results">
        <h3>Strategie für {strategy.target_niche} ({strategy.account_stage})</h3>
        <p><strong>Basiert auf Analyse von:</strong> {strategy.analyzed_account}</p>
        
        {strategy.content_strategy && (
          <div className="strategy-section">
            <h4>Content-Strategie</h4>
            <div className="strategy-grid">
              <div className="strategy-item">
                <strong>Empfohlene Content-Typen:</strong>
                <ul>
                  {strategy.content_strategy.primary_content_types?.map((type: string, i: number) => (
                    <li key={i}>{type}</li>
                  ))}
                </ul>
              </div>
              <div className="strategy-item">
                <strong>Content-Themen:</strong>
                <ul>
                  {strategy.content_strategy.content_themes?.map((theme: string, i: number) => (
                    <li key={i}>{theme}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {strategy.posting_strategy && (
          <div className="strategy-section">
            <h4>Posting-Strategie</h4>
            <div className="strategy-grid">
              <div className="strategy-item">
                <strong>Empfohlene Frequenz:</strong> {strategy.posting_strategy.recommended_frequency}
              </div>
              <div className="strategy-item">
                <strong>Optimale Posting-Zeiten:</strong>
                <ul>
                  {strategy.posting_strategy.optimal_posting_times?.map((time: string, i: number) => (
                    <li key={i}>{time}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {strategy.hashtag_strategy && (
          <div className="strategy-section">
            <h4>Hashtag-Strategie</h4>
            <div className="strategy-grid">
              <div className="strategy-item">
                <strong>Empfohlene Anzahl:</strong> {strategy.hashtag_strategy.recommended_hashtag_count}
              </div>
              {strategy.hashtag_strategy.hashtag_categories && (
                <div className="strategy-item">
                  <strong>Hashtag-Kategorien:</strong>
                  {Object.entries(strategy.hashtag_strategy.hashtag_categories).map(([category, hashtags]) => (
                    <div key={category}>
                      <em>{category}:</em> {Array.isArray(hashtags) ? hashtags.join(', ') : ''}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {strategy.implementation_plan && (
          <div className="strategy-section">
            <h4>Umsetzungsplan</h4>
            {Object.entries(strategy.implementation_plan).map(([phase, plan]) => (
              <div key={phase} className="implementation-phase">
                <h5>{phase.replace('_', ' ').toUpperCase()}</h5>
                <p><strong>Fokus:</strong> {plan.focus}</p>
                <div><strong>Hauptaktionen:</strong></div>
                <ul>
                  {plan.key_actions?.map((action: string, i: number) => (
                    <li key={i}>{action}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const renderComparativeAnalysis = (analysis: ComparativeAnalysis) => {
    if (!analysis) return null;

    return (
      <div className="comparative-analysis-results">
        <h3>Vergleichsanalyse von {analysis.analyzed_accounts.length} Accounts</h3>
        <p><strong>Analysierte Accounts:</strong> {analysis.analyzed_accounts.join(', ')}</p>
        
        {analysis.common_success_factors && (
          <div className="analysis-section">
            <h4>Gemeinsame Erfolgsfaktoren</h4>
            <div className="analysis-grid">
              <div className="analysis-item">
                <strong>Universelle Strategien:</strong>
                <ul>
                  {analysis.common_success_factors.universal_strategies?.map((strategy: string, i: number) => (
                    <li key={i}>{strategy}</li>
                  ))}
                </ul>
              </div>
              <div className="analysis-item">
                <strong>Konsistente Content-Typen:</strong>
                <ul>
                  {analysis.common_success_factors.consistent_content_types?.map((type: string, i: number) => (
                    <li key={i}>{type}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {analysis.identified_best_practices && (
          <div className="analysis-section">
            <h4>Identifizierte Best Practices</h4>
            <div className="analysis-grid">
              {Object.entries(analysis.identified_best_practices).map(([category, practices]) => (
                <div key={category} className="analysis-item">
                  <strong>{category.replace('_', ' ').toUpperCase()}:</strong>
                  <ul>
                    {Array.isArray(practices) && practices.map((practice: string, i: number) => (
                      <li key={i}>{practice}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        )}

        {analysis.strategic_recommendations && (
          <div className="analysis-section">
            <h4>Strategische Empfehlungen</h4>
            <div className="analysis-grid">
              {Object.entries(analysis.strategic_recommendations).map(([stage, recommendations]) => (
                <div key={stage} className="analysis-item">
                  <strong>{stage.replace('_', ' ').toUpperCase()}:</strong>
                  <ul>
                    {Array.isArray(recommendations) && recommendations.map((rec: string, i: number) => (
                      <li key={i}>{rec}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="instagram-analyzer-interface">
      <div className="header">
        <h2>Instagram Success Analyzer & Strategie-Generator</h2>
        <p>Analysiere erfolgreiche Instagram-Accounts und generiere umsetzbare Posting-Strategien</p>
      </div>

      <div className="tabs">
        <button 
          className={`tab-button ${activeTab === 'analyze' ? 'active' : ''}`}
          onClick={() => setActiveTab('analyze')}
        >
          Account Analysieren
        </button>
        <button 
          className={`tab-button ${activeTab === 'multiple' ? 'active' : ''}`}
          onClick={() => setActiveTab('multiple')}
        >
          Mehrere Accounts
        </button>
        <button 
          className={`tab-button ${activeTab === 'strategy' ? 'active' : ''}`}
          onClick={() => setActiveTab('strategy')}
        >
          Strategie Generieren
        </button>
        <button 
          className={`tab-button ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          Gespeicherte Analysen
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {activeTab === 'analyze' && (
        <div className="tab-content">
          <div className="input-section">
            <h3>Instagram Account Analysieren</h3>
            <div className="form-group">
              <label>Instagram Account (URL oder @username):</label>
              <input
                type="text"
                value={accountInput}
                onChange={(e) => setAccountInput(e.target.value)}
                placeholder="@7cyclesapp oder https://www.instagram.com/7cyclesapp/"
                disabled={loading}
              />
            </div>
            <div className="form-group">
              <label>Analyse-Fokus:</label>
              <select 
                value={analysisFocus} 
                onChange={(e) => setAnalysisFocus(e.target.value)}
                disabled={loading}
              >
                <option value="comprehensive">Umfassend</option>
                <option value="content">Content-Fokus</option>
                <option value="engagement">Engagement-Fokus</option>
                <option value="branding">Branding-Fokus</option>
              </select>
            </div>
            <button 
              onClick={analyzeAccount} 
              disabled={loading || !accountInput.trim()}
              className="analyze-button"
            >
              {loading ? 'Analysiere...' : 'Account Analysieren'}
            </button>
          </div>

          {currentAnalysis && renderAnalysisResults(currentAnalysis)}
        </div>
      )}

      {activeTab === 'multiple' && (
        <div className="tab-content">
          <div className="input-section">
            <h3>Mehrere Accounts Vergleichen</h3>
            <div className="form-group">
              <label>Instagram Accounts:</label>
              {multipleAccounts.map((account, index) => (
                <div key={index} className="account-input-row">
                  <input
                    type="text"
                    value={account}
                    onChange={(e) => updateAccountInput(index, e.target.value)}
                    placeholder={`Account ${index + 1} (@username oder URL)`}
                    disabled={loading}
                  />
                  {multipleAccounts.length > 1 && (
                    <button 
                      onClick={() => removeAccountInput(index)}
                      className="remove-button"
                      disabled={loading}
                    >
                      ✕
                    </button>
                  )}
                </div>
              ))}
              <button onClick={addAccountInput} className="add-button" disabled={loading}>
                + Account hinzufügen
              </button>
            </div>
            <div className="form-group">
              <label>Analyse-Fokus:</label>
              <select 
                value={analysisFocus} 
                onChange={(e) => setAnalysisFocus(e.target.value)}
                disabled={loading}
              >
                <option value="comprehensive">Umfassend</option>
                <option value="content">Content-Fokus</option>
                <option value="engagement">Engagement-Fokus</option>
                <option value="branding">Branding-Fokus</option>
              </select>
            </div>
            <button 
              onClick={analyzeMultipleAccounts} 
              disabled={loading || multipleAccounts.filter(acc => acc.trim()).length < 2}
              className="analyze-button"
            >
              {loading ? 'Analysiere...' : 'Accounts Vergleichen'}
            </button>
          </div>

          {comparativeAnalysis && renderComparativeAnalysis(comparativeAnalysis)}
        </div>
      )}

      {activeTab === 'strategy' && (
        <div className="tab-content">
          <div className="input-section">
            <h3>Strategie aus Analyse Generieren</h3>
            <div className="form-group">
              <label>Basis-Analyse wählen:</label>
              <select 
                value={selectedAnalysisId} 
                onChange={(e) => setSelectedAnalysisId(e.target.value)}
                disabled={loading}
              >
                <option value="">-- Analyse wählen --</option>
                {storedAnalyses.map(analysis => (
                  <option key={analysis.analysis_id} value={analysis.analysis_id}>
                    {analysis.account_username} ({new Date(analysis.analyzed_at).toLocaleDateString()})
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Ziel-Nische:</label>
              <select 
                value={targetNiche} 
                onChange={(e) => setTargetNiche(e.target.value)}
                disabled={loading}
              >
                <option value="7cycles">7 Cycles</option>
                <option value="wellness">Wellness</option>
                <option value="spirituality">Spiritualität</option>
                <option value="coaching">Coaching</option>
                <option value="lifestyle">Lifestyle</option>
                <option value="personal_development">Persönlichkeitsentwicklung</option>
              </select>
            </div>
            <div className="form-group">
              <label>Account-Stadium:</label>
              <select 
                value={accountStage} 
                onChange={(e) => setAccountStage(e.target.value)}
                disabled={loading}
              >
                <option value="starting">Beginnend (0-1k Follower)</option>
                <option value="growing">Wachsend (1k-10k Follower)</option>
                <option value="established">Etabliert (10k+ Follower)</option>
              </select>
            </div>
            <button 
              onClick={generateStrategy} 
              disabled={loading || !selectedAnalysisId}
              className="analyze-button"
            >
              {loading ? 'Generiere...' : 'Strategie Generieren'}
            </button>
          </div>

          {currentStrategy && renderStrategyResults(currentStrategy)}
        </div>
      )}

      {activeTab === 'history' && (
        <div className="tab-content">
          <h3>Gespeicherte Analysen & Strategien</h3>
          
          <div className="history-section">
            <h4>Analysen ({storedAnalyses.length})</h4>
            {storedAnalyses.length === 0 ? (
              <p>Keine gespeicherten Analysen gefunden.</p>
            ) : (
              <div className="history-list">
                {storedAnalyses.map(analysis => (
                  <div key={analysis.analysis_id} className="history-item" onClick={() => {
                    setCurrentAnalysis(analysis);
                    setActiveTab('analyze');
                  }}>
                    <div className="history-header">
                      <strong>{analysis.account_username}</strong>
                      <span className="date">{new Date(analysis.analyzed_at).toLocaleDateString()}</span>
                    </div>
                    <div className="history-details">
                      Fokus: {analysis.analysis_focus} | 
                      {analysis.overall_assessment?.success_level && ` Erfolg: ${analysis.overall_assessment.success_level}`}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="history-section">
            <h4>Strategien ({storedStrategies.length})</h4>
            {storedStrategies.length === 0 ? (
              <p>Keine gespeicherten Strategien gefunden.</p>
            ) : (
              <div className="history-list">
                {storedStrategies.map(strategy => (
                  <div key={strategy.strategy_id} className="history-item" onClick={() => {
                    setCurrentStrategy(strategy);
                    setActiveTab('strategy');
                  }}>
                    <div className="history-header">
                      <strong>{strategy.target_niche} ({strategy.account_stage})</strong>
                      <span className="date">{new Date(strategy.created_at).toLocaleDateString()}</span>
                    </div>
                    <div className="history-details">
                      Basiert auf: {strategy.analyzed_account}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default InstagramAnalyzerInterface;
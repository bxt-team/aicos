import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './AffirmationsInterface.css';

interface Affirmation {
  id: string;
  text: string;
  theme: string;
  focus: string;
  created_at: string;
  period_type: string;
  period_info: any;
}

interface PeriodType {
  description: string;
  phases?: string[];
  stages?: string[];
}

interface PeriodsData {
  success: boolean;
  period_types: { [key: string]: PeriodType };
}

const AffirmationsInterface: React.FC = () => {
  const [affirmations, setAffirmations] = useState<Affirmation[]>([]);
  const [loading, setLoading] = useState(false);
  const [periods, setPeriods] = useState<PeriodsData | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState<string>('');
  const [selectedPhase, setSelectedPhase] = useState<string>('');
  const [customPeriodInfo, setCustomPeriodInfo] = useState<string>('');
  const [affirmationCount, setAffirmationCount] = useState<number>(5);
  const [filterPeriod, setFilterPeriod] = useState<string>('');

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  useEffect(() => {
    loadPeriods();
    loadAffirmations();
  }, []);

  const loadPeriods = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/periods`);
      setPeriods(response.data);
    } catch (error) {
      console.error('Error loading periods:', error);
    }
  };

  const loadAffirmations = async (periodFilter?: string) => {
    try {
      const url = periodFilter 
        ? `${API_BASE_URL}/affirmations?period_type=${periodFilter}`
        : `${API_BASE_URL}/affirmations`;
      
      const response = await axios.get(url);
      if (response.data.success) {
        setAffirmations(response.data.affirmations);
      }
    } catch (error) {
      console.error('Error loading affirmations:', error);
    }
  };

  const handleGenerateAffirmations = async () => {
    if (!selectedPeriod) return;

    setLoading(true);
    try {
      let periodInfo: any = {};
      
      if (selectedPhase) {
        periodInfo.phase = selectedPhase;
      }
      
      if (customPeriodInfo) {
        try {
          const customInfo = JSON.parse(customPeriodInfo);
          periodInfo = { ...periodInfo, ...customInfo };
        } catch {
          periodInfo.custom = customPeriodInfo;
        }
      }

      const response = await axios.post(`${API_BASE_URL}/generate-affirmations`, {
        period_type: selectedPeriod,
        period_info: periodInfo,
        count: affirmationCount
      });

      if (response.data.success) {
        setAffirmations(prev => [...response.data.affirmations, ...prev]);
        
        // Reset form
        setSelectedPeriod('');
        setSelectedPhase('');
        setCustomPeriodInfo('');
        setAffirmationCount(5);
        
        // Show success message
        alert(response.data.message);
      }
    } catch (error: any) {
      console.error('Error generating affirmations:', error);
      const errorMessage = error.response?.data?.detail || 'Ein Fehler ist beim Generieren der Affirmationen aufgetreten.';
      alert(`Fehler: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (period: string) => {
    setFilterPeriod(period);
    loadAffirmations(period || undefined);
  };

  const getPhaseOptions = () => {
    if (!periods || !selectedPeriod) return [];
    
    const periodData = periods.period_types[selectedPeriod];
    return periodData?.phases || periodData?.stages || [];
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getThemeColor = (theme: string) => {
    const themes: { [key: string]: string } = {
      'energie': '#ff6b6b',
      'kreativitaet': '#4ecdc4',
      'erfolg': '#45b7d1',
      'beziehungen': '#f9ca24',
      'wachstum': '#6c5ce7',
      'allgemein': '#a0a0a0'
    };
    return themes[theme] || themes.allgemein;
  };

  return (
    <div className="affirmations-interface">
      <div className="affirmations-header">
        <h2>7 Lebenszyklen Affirmationen-Generator</h2>
        <p>Erstelle personalisierte Affirmationen basierend auf deinem aktuellen Lebenszyklus und deiner Periode</p>
      </div>

      <div className="generator-section">
        <h3>Neue Affirmationen generieren</h3>
        <div className="generator-form">
          <div className="form-row">
            <div className="form-group">
              <label>Perioden-Typ:</label>
              <select 
                value={selectedPeriod} 
                onChange={(e) => setSelectedPeriod(e.target.value)}
                disabled={loading}
              >
                <option value="">Wähle einen Perioden-Typ</option>
                {periods && Object.entries(periods.period_types).map(([key, value]) => {
                  const germanNames: {[key: string]: string} = {
                    'tag': 'Tag',
                    'woche': 'Woche',
                    'monat': 'Monat',
                    'jahr': 'Jahr',
                    'leben': 'Leben'
                  };
                  return (
                    <option key={key} value={key}>
                      {germanNames[key] || key} - {value.description}
                    </option>
                  );
                })}
              </select>
            </div>

            <div className="form-group">
              <label>Phase/Stadium:</label>
              <select 
                value={selectedPhase} 
                onChange={(e) => setSelectedPhase(e.target.value)}
                disabled={loading || !selectedPeriod}
              >
                <option value="">Wähle eine Phase (optional)</option>
                {getPhaseOptions().map(phase => {
                  const germanPhases: {[key: string]: string} = {
                    'morgen': 'Morgen',
                    'nachmittag': 'Nachmittag',
                    'abend': 'Abend',
                    'nacht': 'Nacht',
                    'planung': 'Planung',
                    'aktion': 'Aktion',
                    'vollendung': 'Vollendung',
                    'reflexion': 'Reflexion',
                    'neumond': 'Neumond',
                    'zunehmend': 'Zunehmend',
                    'vollmond': 'Vollmond',
                    'abnehmend': 'Abnehmend',
                    'fruehling': 'Frühling',
                    'sommer': 'Sommer',
                    'herbst': 'Herbst',
                    'winter': 'Winter',
                    'kindheit': 'Kindheit',
                    'jugend': 'Jugend',
                    'erwachsenenalter': 'Erwachsenenalter',
                    'reife': 'Reife',
                    'weisheit': 'Weisheit'
                  };
                  return (
                    <option key={phase} value={phase}>
                      {germanPhases[phase] || phase}
                    </option>
                  );
                })}
              </select>
            </div>

            <div className="form-group">
              <label>Anzahl der Affirmationen:</label>
              <input
                type="number"
                min="1"
                max="20"
                value={affirmationCount}
                onChange={(e) => setAffirmationCount(parseInt(e.target.value) || 5)}
                disabled={loading}
              />
            </div>
          </div>

          <div className="form-group">
            <label>Zusätzlicher Kontext (Optional):</label>
            <textarea
              value={customPeriodInfo}
              onChange={(e) => setCustomPeriodInfo(e.target.value)}
              placeholder="Füge spezifischen Kontext oder JSON-Daten für deine aktuelle Situation hinzu..."
              disabled={loading}
              rows={3}
            />
          </div>

          <button
            onClick={handleGenerateAffirmations}
            disabled={loading || !selectedPeriod}
            className="generate-button"
          >
            {loading ? 'Generiere...' : 'Affirmationen generieren'}
          </button>
        </div>
      </div>

      <div className="affirmations-display">
        <div className="display-header">
          <h3>Deine Affirmationen</h3>
          <div className="filter-section">
            <label>Nach Periode filtern:</label>
            <select 
              value={filterPeriod} 
              onChange={(e) => handleFilterChange(e.target.value)}
            >
              <option value="">Alle Perioden</option>
              {periods && Object.keys(periods.period_types).map(key => {
                const germanNames: {[key: string]: string} = {
                  'tag': 'Tag',
                  'woche': 'Woche',
                  'monat': 'Monat',
                  'jahr': 'Jahr',
                  'leben': 'Leben'
                };
                return (
                  <option key={key} value={key}>
                    {germanNames[key] || key}
                  </option>
                );
              })}
            </select>
          </div>
        </div>

        {affirmations.length === 0 ? (
          <div className="no-affirmations">
            <p>Noch keine Affirmationen generiert.</p>
            <p>Wähle oben einen Perioden-Typ und generiere dein erstes Set von Affirmationen!</p>
          </div>
        ) : (
          <div className="affirmations-grid">
            {affirmations.map((affirmation) => (
              <div key={affirmation.id} className="affirmation-card">
                <div className="affirmation-content">
                  <div className="affirmation-text">"{affirmation.text}"</div>
                  <div className="affirmation-meta">
                    <span 
                      className="theme-tag"
                      style={{ backgroundColor: getThemeColor(affirmation.theme) }}
                    >
                      {affirmation.theme}
                    </span>
                    <span className="focus-text">{affirmation.focus}</span>
                  </div>
                  <div className="period-info">
                    <strong>Periode:</strong> {(() => {
                      const germanNames: {[key: string]: string} = {
                        'tag': 'Tag',
                        'woche': 'Woche',
                        'monat': 'Monat',
                        'jahr': 'Jahr',
                        'leben': 'Leben'
                      };
                      return germanNames[affirmation.period_type] || affirmation.period_type;
                    })()}
                    {affirmation.period_info?.phase && (
                      <span> - {(() => {
                        const germanPhases: {[key: string]: string} = {
                          'morgen': 'Morgen',
                          'nachmittag': 'Nachmittag',
                          'abend': 'Abend',
                          'nacht': 'Nacht',
                          'planung': 'Planung',
                          'aktion': 'Aktion',
                          'vollendung': 'Vollendung',
                          'reflexion': 'Reflexion',
                          'neumond': 'Neumond',
                          'zunehmend': 'Zunehmend',
                          'vollmond': 'Vollmond',
                          'abnehmend': 'Abnehmend',
                          'fruehling': 'Frühling',
                          'sommer': 'Sommer',
                          'herbst': 'Herbst',
                          'winter': 'Winter',
                          'kindheit': 'Kindheit',
                          'jugend': 'Jugend',
                          'erwachsenenalter': 'Erwachsenenalter',
                          'reife': 'Reife',
                          'weisheit': 'Weisheit'
                        };
                        return germanPhases[affirmation.period_info.phase] || affirmation.period_info.phase;
                      })()}</span>
                    )}
                  </div>
                  <div className="timestamp">
                    Erstellt: {formatTimestamp(affirmation.created_at)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AffirmationsInterface;
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './AffirmationsInterface.css';

interface Affirmation {
  id: string;
  text: string;
  theme: string;
  focus: string;
  created_at: string;
  period_type: string;
  period_name?: string;
  period_info: any;
}

interface PeriodType {
  description: string;
  phases?: string[];
  stages?: string[];
  keywords?: string[];
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

  const loadPeriods = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/periods`);
      setPeriods(response.data);
    } catch (error) {
      console.error('Error loading periods:', error);
    }
  }, [API_BASE_URL]);

  const loadAffirmations = useCallback(async (periodFilter?: string) => {
    try {
      const url = periodFilter 
        ? `${API_BASE_URL}/affirmations?period_name=${periodFilter}`
        : `${API_BASE_URL}/affirmations`;
      
      const response = await axios.get(url);
      if (response.data.success) {
        setAffirmations(response.data.affirmations);
      }
    } catch (error) {
      console.error('Error loading affirmations:', error);
    }
  }, [API_BASE_URL]);

  useEffect(() => {
    loadPeriods();
    loadAffirmations();
  }, [loadPeriods, loadAffirmations]);

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
        period_name: selectedPeriod,
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
    return periodData?.keywords || [];
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getThemeColor = (affirmation: any) => {
    // First try to get color from period_color field
    if (affirmation.period_color) {
      return affirmation.period_color;
    }
    
    // Fallback to 7 Cycles theme mapping
    const cyclesColors: { [key: string]: string } = {
      'Image': '#DAA520',
      'Veränderung': '#2196F3', 
      'Energie': '#F44336',
      'Kreativität': '#FFD700',
      'Erfolg': '#CC0066',
      'Entspannung': '#4CAF50',
      'Umsicht': '#9C27B0'
    };
    
    return cyclesColors[affirmation.theme] || '#a0a0a0';
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
                  return (
                    <option key={key} value={key}>
                      {key} - {value.description}
                    </option>
                  );
                })}
              </select>
            </div>

            <div className="form-group">
              <label>Fokus-Stichwort:</label>
              <select 
                value={selectedPhase} 
                onChange={(e) => setSelectedPhase(e.target.value)}
                disabled={loading || !selectedPeriod}
              >
                <option value="">Wähle ein Fokus-Stichwort (optional)</option>
                {getPhaseOptions().map((keyword: string) => (
                  <option key={keyword} value={keyword}>
                    {keyword}
                  </option>
                ))}
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
              {periods && Object.keys(periods.period_types).map(key => (
                <option key={key} value={key}>
                  {key}
                </option>
              ))}
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
                  <div className="affirmation-text">{affirmation.text}</div>
                  <div className="affirmation-meta">
                    <span 
                      className="theme-tag"
                      style={{ backgroundColor: getThemeColor(affirmation) }}
                    >
                      {affirmation.theme}
                    </span>
                    <span className="focus-text">{affirmation.focus}</span>
                  </div>
                  <div className="period-info">
                    <strong>7 Cycles Periode:</strong> {affirmation.period_name || affirmation.period_type || affirmation.theme}
                    {affirmation.period_info?.phase && (
                      <span> - {affirmation.period_info.phase}</span>
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
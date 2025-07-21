import React, { useState, useEffect, useCallback } from 'react';
import { apiService } from '../services/api';
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
  color?: string;
  phases?: string[];
  stages?: string[];
  keywords?: string[];
}

interface PeriodsData {
  status: string;
  periods: { [key: string]: PeriodType };
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


  const loadPeriods = useCallback(async () => {
    try {
      const response = await apiService.affirmations.getPeriods();
      setPeriods(response.data);
    } catch (error) {
      console.error('Error loading periods:', error);
    }
  }, []);

  const loadAffirmations = useCallback(async (periodFilter?: string) => {
    try {
      const response = await apiService.affirmations.list(periodFilter);
      if (response.data.status === 'success') {
        const affirmationsData = Array.isArray(response.data.affirmations) 
          ? response.data.affirmations 
          : [];
        setAffirmations(affirmationsData);
      }
    } catch (error) {
      console.error('Error loading affirmations:', error);
    }
  }, []);

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

      const response = await apiService.affirmations.generate({
        period_name: selectedPeriod,
        period_info: periodInfo,
        count: affirmationCount
      });

      if (response.data.status === 'success') {
        const newAffirmations = Array.isArray(response.data.affirmations) 
          ? response.data.affirmations 
          : [];
        setAffirmations(prev => [...newAffirmations, ...prev]);
        
        // Reset form
        setSelectedPeriod('');
        setSelectedPhase('');
        setCustomPeriodInfo('');
        setAffirmationCount(5);
        
        // Show success message
        alert(response.data.message || 'Affirmationen erfolgreich generiert!');
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
    if (!selectedPeriod) return [];
    
    // Define keywords for each period type
    const periodKeywords: { [key: string]: string[] } = {
      'Image': ['Selbstbild', 'Identität', 'Ausstrahlung', 'Präsenz', 'Authentizität'],
      'Veränderung': ['Transformation', 'Wandel', 'Neuanfang', 'Loslassen', 'Evolution'],
      'Energie': ['Vitalität', 'Kraft', 'Aktivität', 'Dynamik', 'Lebensfreude'],
      'Kreativität': ['Schöpferkraft', 'Innovation', 'Inspiration', 'Ausdruck', 'Vision'],
      'Erfolg': ['Zielerreichung', 'Anerkennung', 'Leistung', 'Fülle', 'Manifestation'],
      'Entspannung': ['Ruhe', 'Frieden', 'Balance', 'Regeneration', 'Harmonie'],
      'Umsicht': ['Weisheit', 'Reflexion', 'Klarheit', 'Erkenntnis', 'Bewusstsein']
    };
    
    return periodKeywords[selectedPeriod] || [];
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getThemeColor = (affirmation: any) => {
    // First try to get color from period_color field
    if (affirmation.period_color) {
      return affirmation.period_color;
    }
    
    // Try to get color from periods data
    if (periods && affirmation.theme && periods.periods[affirmation.theme]?.color) {
      return periods.periods[affirmation.theme].color;
    }
    
    // Fallback to 7 Cycles theme mapping
    const cyclesColors: { [key: string]: string } = {
      'Image': '#FF6B6B',
      'Veränderung': '#4ECDC4', 
      'Energie': '#FFE66D',
      'Kreativität': '#A8E6CF',
      'Erfolg': '#C7CEEA',
      'Entspannung': '#FFDAB9',
      'Umsicht': '#B4A0E5'
    };
    
    return cyclesColors[affirmation.theme] || '#a0a0a0';
  };

  return (
    <div className="affirmations-interface">
      <div className="affirmations-header">
        <h2>AI Company - Affirmations Generator</h2>
        <p>Create personalized affirmations based on your current life cycle and period</p>
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
                {periods && Object.entries(periods.periods).map(([key, value]) => {
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
                {getPhaseOptions().map((keyword) => (
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
              {periods && Object.keys(periods.periods).map(key => (
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
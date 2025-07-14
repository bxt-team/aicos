export interface KeywordOpportunity {
  keyword: string;
  search_volume: string;
  competition: string;
  relevance: number;
}

export interface PainPoint {
  issue: string;
  frequency: number;
  severity: string;
  percentage_of_negative: number;
}

export interface PositiveHighlight {
  aspect: string;
  mentions: number;
  percentage_of_positive: number;
}

export interface FeatureRequest {
  feature: string;
  mentions: number;
  priority: string;
}

export interface VisualQuality {
  score: number;
  recommendations: string[];
}

export interface ScreenshotAnalysis {
  count: number;
  quality_score: number;
  recommendations: string[];
}

export interface VideoAnalysis {
  present: boolean;
  quality_score?: number;
  recommendations: string[];
}

export interface Recommendation {
  category: string;
  recommendation: string;
  priority: string;
  expected_impact: string;
  implementation_difficulty: string;
}

export interface KeywordAnalysis {
  primary_keywords: string[];
  keyword_density: {
    title: number;
    short_description: number;
    description: number;
  };
  keyword_opportunities?: KeywordOpportunity[];
}

export interface ReviewSentiment {
  sentiment_label: string;
  sentiment_score: number;
  pain_points?: PainPoint[];
  positive_highlights?: PositiveHighlight[];
  feature_requests?: FeatureRequest[];
}

export interface VisualAnalysis {
  icon_quality?: VisualQuality;
  screenshots?: ScreenshotAnalysis;
  video?: VideoAnalysis;
}

export interface Competitor {
  name: string;
  rating: number;
  downloads: string;
  advantages?: string[];
  disadvantages?: string[];
}

export interface CompetitorAnalysis {
  competitors: Competitor[];
  market_position?: string;
  competitive_advantages?: string[];
  competitive_disadvantages?: string[];
}

export interface PlayStoreAnalysis {
  app_id: string;
  app_name: string;
  package_name: string;
  developer: string;
  category: string;
  rating: number;
  total_reviews: number;
  downloads: string;
  last_updated: string;
  keyword_analysis: KeywordAnalysis;
  review_sentiment: ReviewSentiment;
  visual_analysis: VisualAnalysis;
  recommendations: Recommendation[];
  competitor_analysis: CompetitorAnalysis;
  analysis_timestamp: string;
}

export interface AppStoreOptimization {
  score: number;
  grade: string;
  issues: string[];
}

export interface AppStoreAnalysis {
  app_name: string;
  optimization_score: AppStoreOptimization;
  review_sentiment: ReviewSentiment;
  keyword_insights: {
    suggested_keywords: string[];
  };
  recommendations: Recommendation[];
}
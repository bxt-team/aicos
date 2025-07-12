export interface AgentConfig {
  id: string;
  name: string;
  route: string;
  icon: string;
  description: string;
  category: string;
  enabled: boolean;
  apiHealthCheck?: string;
  features: string[];
  version?: string;
}

export const agentConfigs: AgentConfig[] = [
  {
    id: 'dashboard',
    name: 'Agent Dashboard',
    route: '/',
    icon: '🏠',
    description: 'Übersicht und Management aller verfügbaren AI-Agenten',
    category: 'System Management',
    enabled: true,
    features: ['Agent Übersicht', 'Health Monitoring', 'Systemstatus'],
    version: '1.0'
  },
  {
    id: 'qa',
    name: 'Q&A Experte',
    route: '/qa',
    icon: '❓',
    description: 'Beantwortet Fragen über die 7 Lebenszyklen basierend auf der Wissensdatenbank',
    category: 'Wissen & Forschung',
    enabled: true,
    apiHealthCheck: '/qa-health',
    features: ['Fragebeantwortung', 'Wissensdatenbank', 'Kontextuelle Antworten'],
    version: '1.0'
  },
  {
    id: 'affirmations',
    name: 'Affirmationen Generator',
    route: '/affirmations',
    icon: '💫',
    description: 'Erstellt kraftvolle, personalisierte Affirmationen für jede 7 Cycles Periode',
    category: 'Persönlichkeitsentwicklung',
    enabled: true,
    apiHealthCheck: '/periods',
    features: ['7 Cycles Integration', 'Personalisierung', 'Periodenspezifisch'],
    version: '1.0'
  },
  {
    id: 'instagram-posts',
    name: 'Instagram Post & Hashtag TextWriter',
    route: '/instagram-posts',
    icon: '📱',
    description: 'Generiert Instagram Posts mit Affirmationen, relevanten Hashtags und Call-to-Actions',
    category: 'Social Media Marketing',
    enabled: true,
    apiHealthCheck: '/instagram-posts',
    features: ['Hashtag Research', 'Call-to-Actions', 'Engagement Strategien', 'Content Marketing'],
    version: '1.0'
  },
  {
    id: 'instagram-poster',
    name: 'Instagram Poster Agent',
    route: '/instagram-posting',
    icon: '📤',
    description: 'Postet Inhalte direkt auf Instagram mit optimaler Timing und Engagement-Strategien',
    category: 'Social Media Marketing',
    enabled: true,
    apiHealthCheck: '/instagram-posting-status',
    features: ['Direct Instagram Posting', 'Content Optimization', 'Rate Limiting', 'Posting History'],
    version: '1.0'
  },
  {
    id: 'instagram-analyzer',
    name: 'Instagram Success Analyzer',
    route: '/instagram-analyzer',
    icon: '🔍',
    description: 'Analysiert erfolgreiche Instagram-Accounts und generiert umsetzbare Posting-Strategien',
    category: 'Social Media Marketing',
    enabled: true,
    apiHealthCheck: '/instagram-analyses',
    features: ['Account Analysis', 'Success Factor Identification', 'Strategy Generation', 'Competitive Analysis'],
    version: '1.0'
  },
  {
    id: 'visual-posts',
    name: 'Visuelle Posts Creator',
    route: '/visual-posts',
    icon: '🎨',
    description: 'Erstellt ästhetische visuelle Affirmations-Posts mit Hintergrundbildern',
    category: 'Visual Content',
    enabled: true,
    apiHealthCheck: '/visual-posts',
    features: ['Bildsuche', 'Farb-Overlays', 'Design Automation', 'Instagram Stories'],
    version: '1.0'
  },
  {
    id: 'content-generator',
    name: 'Vollständiger Content Generator',
    route: '/content-generator',
    icon: '⚡',
    description: 'Vollständige Content-Erstellung mit CrewAI Flow System',
    category: 'Content Creation',
    enabled: true,
    apiHealthCheck: '/content',
    features: ['CrewAI Integration', 'Multi-Agent Workflows', 'Research & Writing', 'Bild-Generierung'],
    version: '1.0'
  },
  {
    id: 'workflow-manager',
    name: 'Workflow Manager',
    route: '/workflows',
    icon: '🔄',
    description: 'Orchestriert komplette Content-Workflows von Affirmationen bis zu geplanten Posts und Reels',
    category: 'System Management',
    enabled: true,
    apiHealthCheck: '/api/workflow-templates',
    features: ['Multi-Agent Orchestration', 'Workflow Templates', 'Monitoring', 'Video Generation', 'Post Composition'],
    version: '1.0'
  },
  {
    id: 'post-composition',
    name: 'Post Komposition',
    route: '/post-composition',
    icon: '🎨',
    description: 'Komponiere professionelle visuelle Posts mit Templates und benutzerdefinierten Optionen',
    category: 'Visual Content',
    enabled: true,
    apiHealthCheck: '/api/composition-templates',
    features: ['Template System', 'Custom Options', 'Multi-Format Support', 'Professional Design'],
    version: '1.0'
  },
  {
    id: 'video-generation',
    name: 'Video Generation',
    route: '/video-generation',
    icon: '🎬',
    description: 'Erstelle ansprechende Instagram Reels aus Bildern mit verschiedenen Effekten und Animationen',
    category: 'Visual Content',
    enabled: true,
    apiHealthCheck: '/api/video-types',
    features: ['Multiple Video Types', 'FFmpeg Integration', 'Instagram Reels', 'Professional Effects'],
    version: '1.0'
  },
  {
    id: 'instagram-reel',
    name: 'Instagram Reel Generator',
    route: '/instagram-reel',
    icon: '🎥',
    description: 'Erstelle professionelle Instagram Reels mit KI-Scripts, Runway-Videos und ChatGPT Sora 5-Sekunden-Loops',
    category: 'Visual Content',
    enabled: true,
    apiHealthCheck: '/api/reel-themes',
    features: ['Video Script Generation', 'Runway AI Integration', 'ChatGPT Sora Loops', '7 Cycles Optimized', '5s Loop Videos'],
    version: '2.0'
  },
  {
    id: 'android-test',
    name: 'Android App Testing Agent',
    route: '/android-test',
    icon: '📱',
    description: 'Automatisierte QA- und Performance-Tests für Android Apps mit detaillierter Fehleranalyse und UX-Empfehlungen',
    category: 'Quality Assurance',
    enabled: true,
    apiHealthCheck: '/health',
    features: ['Automatisierte UI-Tests', 'Performance-Analyse', 'Crash-Erkennung', 'Accessibility-Prüfung', 'UX-Optimierung'],
    version: '1.0'
  },
  {
    id: 'voice-over-captions',
    name: 'Voice Over & Captions',
    route: '/voice-over',
    icon: '🎙️',
    description: 'Erstelle professionelle Voice-Overs und Untertitel für Videos mit KI-Sprachsynthese und automatischer Transkription',
    category: 'Video Content',
    enabled: true,
    apiHealthCheck: '/api/available-voices',
    features: ['Voice-Over Generation', 'ElevenLabs Integration', 'Auto-Untertitelung', 'Multi-Language Support', 'Video Processing'],
    version: '1.0'
  },
  {
    id: 'mobile-analytics',
    name: 'Mobile App Analytics',
    route: '/mobile-analytics',
    icon: '📊',
    description: 'Analysiere und optimiere App Store und Play Store Listings, Meta Ads Performance und Google Analytics für mobile Apps',
    category: 'Mobile Marketing',
    enabled: true,
    apiHealthCheck: '/api/mobile-analytics/app-store/health',
    features: ['App Store ASO Analysis', 'Play Store Optimization', 'Meta Ads Performance', 'Google Analytics Mobile', 'Review Sentiment Analysis', 'Keyword Optimization'],
    version: '1.0'
  },
  {
    id: 'threads',
    name: 'Threads Manager',
    route: '/threads',
    icon: '🧵',
    description: 'Manage Meta Threads content with AI-powered analysis, strategy, and scheduling',
    category: 'Social Media Marketing',
    enabled: true,
    apiHealthCheck: '/api/threads/health',
    features: ['Profile Analysis', 'Content Strategy', 'Post Generation', 'Approval Workflow', 'Smart Scheduling'],
    version: '1.0'
  },
  {
    id: 'x-twitter',
    name: 'X (Twitter) Manager',
    route: '/x-twitter',
    icon: '𝕏',
    description: 'Comprehensive X/Twitter management with viral content creation and engagement optimization',
    category: 'Social Media Marketing',
    enabled: true,
    apiHealthCheck: '/api/x/health',
    features: ['Tweet Analysis', 'Thread Creation', 'Poll Management', 'Viral Strategies', 'Algorithm Optimization'],
    version: '1.0'
  }
];

export const getEnabledAgents = (): AgentConfig[] => {
  return agentConfigs.filter(agent => agent.enabled);
};

export const getAgentsByCategory = (): { [category: string]: AgentConfig[] } => {
  const enabledAgents = getEnabledAgents();
  return enabledAgents.reduce((acc, agent) => {
    if (!acc[agent.category]) {
      acc[agent.category] = [];
    }
    acc[agent.category].push(agent);
    return acc;
  }, {} as { [category: string]: AgentConfig[] });
};

export const getAgentById = (id: string): AgentConfig | undefined => {
  return agentConfigs.find(agent => agent.id === id);
};

export const getAgentByRoute = (route: string): AgentConfig | undefined => {
  return agentConfigs.find(agent => agent.route === route);
};
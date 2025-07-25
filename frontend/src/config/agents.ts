export interface AgentConfig {
  id: string;
  name: string;
  route: string;
  icon: string;
  description: string;
  category: string;
  enabled: boolean;
  features: string[];
  version?: string;
}

export const agentConfigs: AgentConfig[] = [
  {
    id: 'dashboard',
    name: 'Agent Dashboard',
    route: '/',
    icon: '🏠',
    description: 'Overview and management of all available AI agents',
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
    description: 'Answers questions about the 7 life cycles based on the knowledge database',
    category: 'Knowledge & Research',
    enabled: true,
    features: ['Fragebeantwortung', 'Wissensdatenbank', 'Kontextuelle Antworten'],
    version: '1.0'
  },
  {
    id: 'affirmations',
    name: 'Affirmationen Generator',
    route: '/affirmations',
    icon: '💫',
    description: 'Creates powerful, personalized affirmations for each 7 Cycles period',
    category: 'Personal Development',
    enabled: true,
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
    features: ['Account Analysis', 'Success Factor Identification', 'Strategy Generation', 'Competitive Analysis'],
    version: '1.0'
  },
  {
    id: 'visual-posts',
    name: 'Visuelle Posts Creator',
    route: '/visual-posts',
    icon: '🎨',
    description: 'Creates aesthetic visual affirmation posts with background images',
    category: 'Visual Content',
    enabled: true,
    features: ['Bildsuche', 'Farb-Overlays', 'Design Automation', 'Instagram Stories'],
    version: '1.0'
  },
  {
    id: 'content-generator',
    name: 'Vollständiger Content Generator',
    route: '/content-generator',
    icon: '⚡',
    description: 'Complete content creation with CrewAI Flow System',
    category: 'Content Creation',
    enabled: true,
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
    features: ['Video Script Generation', 'Runway AI Integration', 'ChatGPT Sora Loops', '7 Cycles Optimized', '5s Loop Videos'],
    version: '2.0'
  },
  {
    id: 'app-test',
    name: 'Mobile App Testing Agent',
    route: '/app-test',
    icon: '📱',
    description: 'Automated QA and performance tests for iOS and Android apps with detailed error analysis and UX recommendations',
    category: 'Quality Assurance',
    enabled: true,
    features: ['iOS & Android Testing', 'Automated UI Tests', 'Performance Analysis', 'Crash Detection', 'Accessibility Testing', 'Cross-Platform Comparison'],
    version: '2.0'
  },
  {
    id: 'voice-over-captions',
    name: 'Voice Over & Captions',
    route: '/voice-over',
    icon: '🎙️',
    description: 'Create professional voice-overs and subtitles for videos with AI speech synthesis and automatic transcription',
    category: 'Video Content',
    enabled: true,
    features: ['Voice-Over Generation', 'ElevenLabs Integration', 'Auto-Untertitelung', 'Multi-Language Support', 'Video Processing'],
    version: '1.0'
  },
  {
    id: 'mobile-analytics',
    name: 'Mobile App Analytics',
    route: '/mobile-analytics',
    icon: '📊',
    description: 'Analyze and optimize App Store and Play Store listings, Meta Ads performance and Google Analytics for mobile apps',
    category: 'Mobile Marketing',
    enabled: true,
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
    features: ['Tweet Analysis', 'Thread Creation', 'Poll Management', 'Viral Strategies', 'Algorithm Optimization'],
    version: '1.0'
  },
  {
    id: 'organization-debug',
    name: 'Organization Debug',
    route: '/organization-debug',
    icon: '🐛',
    description: 'Debug tools for organization membership and permissions',
    category: 'Development Tools',
    enabled: true,
    features: ['Test Members Query', 'Debug Membership', 'API Testing'],
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
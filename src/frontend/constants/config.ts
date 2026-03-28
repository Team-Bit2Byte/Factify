/**
 * Application configuration and constants
 */

export const APP_CONFIG = {
  name: 'Factify',
  tagline: 'Forensic Editorial',
} as const;

export const MOCK_ANALYSIS_DATA = {
  title: 'Global Energy Shortage: The Hidden Narrative Revealed',
  articleId: '4920-X1',
  analysisDate: 'Oct 24, 2023',
  probability: 82,
  confidence: 'high' as const,
  metrics: {
    syntaxDeviation: 94,
    semanticConsistency: 12,
    authorityAlignment: 8,
  },
  textAnalysis: {
    sentiment: 'Hyper-Negative',
    clickbaitScore: 9.4,
    aiAuthored: {
      isLikely: true,
      probability: 76,
    },
  },
  imageForensics: {
    manipulation: 'detected' as const,
    elaResult: 'High Noise',
    origin: 'Stock Asset',
  },
  domainTrust: {
    blacklistStatus: 'flagged' as const,
    domainAge: '14 Days',
    ipLocation: 'Obfuscated',
  },
  findings: [
    {
      type: 'error' as const,
      message: 'Emotionally exaggerated language designed to trigger fear.',
    },
    {
      type: 'error' as const,
      message: 'Low credibility source domain with history of retracted claims.',
    },
    {
      type: 'error' as const,
      message: 'Inconsistent metadata timestamps in the accompanying media.',
    },
  ],
} as const;

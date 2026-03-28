/**
 * API service for communicating with the backend
 */

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:3001';

export interface DetectionResult {
  verdict: 'likely_original' | 'unverified' | 'likely_fake_false';
  verdict_label: string;
  raw_score: number;
  fake_probability: number;
  original_probability: number;
  confidence: 'low' | 'medium' | 'high';
  confidence_score: number;
  summary: string;
  findings: string[];
}

export interface AlgorithmAssessment {
  overall_score: number;
  verdict: 'likely_original' | 'unverified' | 'likely_fake_false';
  module_scores: Record<string, number>;
  explanations: string[];
  suspicious_phrases: string[];
  top_negative_terms: Array<{
    term: string;
    frequency: number;
    suspicion_level: number;
  }>;
  greedy_signals: Array<{
    pattern_name: string;
    severity: number;
  }>;
  claim_flags: string[];
  source_label: string;
}

export interface TweetModelAssessment {
  enabled: boolean;
  model_name: string;
  verdict: 'likely_original' | 'unverified' | 'likely_fake_false';
  verdict_label: string;
  raw_probability: number;
  fake_probability: number;
  original_probability: number;
  confidence: 'low' | 'medium' | 'high';
  confidence_score: number;
  threshold_used: number;
  feature_count: number;
  derived_feature_count: number;
  coverage_ratio: number;
  summary: string;
  notes: string[];
}

export interface AnalysisResult {
  combined_text: string;
  headline: string;
  body: string;
  dates: string[];
  people: string[];
  organizations: string[];
  locations: string[];
  source: string;
  suspicious_elements: string[];
  image_path: string;
  image_type: string;
  engine_used: string;
  ocr_region_count: number;
  caption: string;
  processing_time_sec: number;
  raw_ocr_text: string;
  input_type?: 'text' | 'image' | 'url';
  url?: string;
  detection: DetectionResult;
  algorithms: AlgorithmAssessment;
  tweet_model?: TweetModelAssessment;
}

export interface AnalyzeImageResponse {
  success: boolean;
  filename: string;
  result: AnalysisResult;
  error?: string;
}

export interface AnalyzeUrlResponse {
  success: boolean;
  url: string;
  result: AnalysisResult;
  error?: string;
}

export interface AnalyzeTextResponse {
  success: boolean;
  result: AnalysisResult;
  error?: string;
}

/**
 * Upload and analyze an image file
 */
export async function analyzeImage(file: File, signal?: AbortSignal): Promise<AnalyzeImageResponse> {
  const formData = new FormData();
  formData.append('image', file);

  const response = await fetch(`${API_BASE_URL}/api/analyze-image`, {
    method: 'POST',
    body: formData,
    signal,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(error.error || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

export async function analyzeUrl(url: string, signal?: AbortSignal): Promise<AnalyzeUrlResponse> {
  const response = await fetch(`${API_BASE_URL}/api/analyze-url`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ url }),
    signal,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(error.error || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

export async function analyzeText(text: string, signal?: AbortSignal): Promise<AnalyzeTextResponse> {
  const response = await fetch(`${API_BASE_URL}/api/analyze-text`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text }),
    signal,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Unknown error' }));
    throw new Error(error.error || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * Check if the API server is running
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`);
    return response.ok;
  } catch (error) {
    return false;
  }
}

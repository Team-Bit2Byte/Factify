/**
 * API service for communicating with the backend
 */

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:3001';

export interface ImageAnalysisResult {
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
}

export interface AnalyzeImageResponse {
  success: boolean;
  filename: string;
  result: ImageAnalysisResult;
  error?: string;
}

/**
 * Upload and analyze an image file
 */
export async function analyzeImage(file: File): Promise<AnalyzeImageResponse> {
  const formData = new FormData();
  formData.append('image', file);

  const response = await fetch(`${API_BASE_URL}/api/analyze-image`, {
    method: 'POST',
    body: formData,
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

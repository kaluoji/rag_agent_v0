/**
 * Fetch-based HTTP client for RAG Regulatory Analysis API
 * Replaces axios with native Fetch API + retry logic + full type safety
 */

import type {
  OrchestrationResult,
  Query,
  ReportRequest,
  ReportJobResponse,
  APIError,
  PaginatedResponse,
} from './types';
import { addNotification } from './stores';

// ============================================================================
// TYPES
// ============================================================================

interface FetchOptions extends RequestInit {
  timeout?: number;
  retry?: number;
}

interface APIResponse<T> {
  data?: T;
  error?: APIError;
  status: number;
}

// ============================================================================
// CONFIGURATION
// ============================================================================

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const REQUEST_TIMEOUT = 30000; // 30 seconds
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Construct full URL from endpoint
 */
function getURL(endpoint: string): string {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
  return url;
}

/**
 * Sleep for specified milliseconds
 */
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Check if error is retryable
 */
function isRetryable(status: number): boolean {
  // Retry on 408 (timeout), 429 (too many requests), 5xx errors
  return status === 408 || status === 429 || (status >= 500 && status < 600);
}

/**
 * Parse JSON response safely
 */
async function parseJSON<T>(response: Response): Promise<T> {
  const text = await response.text();
  if (!text) {
    return {} as T;
  }
  try {
    return JSON.parse(text) as T;
  } catch (error) {
    console.error('Failed to parse JSON:', error, 'Text:', text);
    return {} as T;
  }
}

/**
 * Handle API error response
 */
function handleError(status: number, data: unknown): APIError {
  if (typeof data === 'object' && data !== null && 'message' in data) {
    return {
      statusCode: status,
      message: (data as Record<string, unknown>).message as string,
      error: (data as Record<string, unknown>).error as string | undefined,
      details: (data as Record<string, unknown>).details as Record<string, unknown> | undefined,
    };
  }

  const errorMessages: Record<number, string> = {
    400: 'Bad request',
    401: 'Unauthorized',
    403: 'Forbidden',
    404: 'Not found',
    408: 'Request timeout',
    429: 'Too many requests',
    500: 'Internal server error',
    502: 'Bad gateway',
    503: 'Service unavailable',
  };

  return {
    statusCode: status,
    message: errorMessages[status] || `HTTP ${status} error`,
    timestamp: new Date(),
  };
}

// ============================================================================
// CORE FETCH FUNCTION
// ============================================================================

/**
 * Core fetch function with retry logic, timeout, and error handling
 */
async function fetchAPI<T>(
  endpoint: string,
  options: FetchOptions = {}
): Promise<APIResponse<T>> {
  const {
    timeout = REQUEST_TIMEOUT,
    retry = MAX_RETRIES,
    ...fetchOptions
  } = options;

  const url = getURL(endpoint);
  const headers = new Headers(fetchOptions.headers || {});

  // Set default headers
  if (!headers.has('Content-Type') && fetchOptions.body && typeof fetchOptions.body === 'string') {
    headers.set('Content-Type', 'application/json');
  }

  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= retry; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      const response = await fetch(url, {
        ...fetchOptions,
        headers,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      const data = await parseJSON<T>(response);

      if (!response.ok) {
        const error = handleError(response.status, data);

        // If error is retryable and we have retries left, retry
        if (isRetryable(response.status) && attempt < retry) {
          const delay = RETRY_DELAY * Math.pow(2, attempt); // Exponential backoff
          console.warn(
            `API request failed with status ${response.status}, retrying in ${delay}ms...`
          );
          await sleep(delay);
          continue;
        }

        return {
          error,
          status: response.status,
        };
      }

      return {
        data,
        status: response.status,
      };
    } catch (error) {
      lastError = error as Error;

      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        // Network error - retryable
        if (attempt < retry) {
          const delay = RETRY_DELAY * Math.pow(2, attempt);
          console.warn(
            `Network error, retrying in ${delay}ms...`
          );
          await sleep(delay);
          continue;
        }
      }

      // Not retryable or out of retries
      const apiError: APIError = {
        statusCode: 0,
        message: error instanceof Error ? error.message : 'Unknown error',
        error: 'NETWORK_ERROR',
        timestamp: new Date(),
      };

      return {
        error: apiError,
        status: 0,
      };
    }
  }

  // All retries exhausted
  const apiError: APIError = {
    statusCode: 0,
    message: lastError?.message || 'Request failed after max retries',
    error: 'MAX_RETRIES_EXCEEDED',
    timestamp: new Date(),
  };

  return {
    error: apiError,
    status: 0,
  };
}

// ============================================================================
// HTTP METHOD WRAPPERS
// ============================================================================

/**
 * GET request
 */
export async function get<T>(endpoint: string, options?: FetchOptions): Promise<APIResponse<T>> {
  return fetchAPI<T>(endpoint, {
    ...options,
    method: 'GET',
  });
}

/**
 * POST request
 */
export async function post<T>(
  endpoint: string,
  body?: Record<string, unknown>,
  options?: FetchOptions
): Promise<APIResponse<T>> {
  return fetchAPI<T>(endpoint, {
    ...options,
    method: 'POST',
    body: body ? JSON.stringify(body) : undefined,
  });
}

/**
 * PUT request
 */
export async function put<T>(
  endpoint: string,
  body?: Record<string, unknown>,
  options?: FetchOptions
): Promise<APIResponse<T>> {
  return fetchAPI<T>(endpoint, {
    ...options,
    method: 'PUT',
    body: body ? JSON.stringify(body) : undefined,
  });
}

/**
 * DELETE request
 */
export async function deleteRequest<T>(
  endpoint: string,
  options?: FetchOptions
): Promise<APIResponse<T>> {
  return fetchAPI<T>(endpoint, {
    ...options,
    method: 'DELETE',
  });
}

/**
 * PATCH request
 */
export async function patch<T>(
  endpoint: string,
  body?: Record<string, unknown>,
  options?: FetchOptions
): Promise<APIResponse<T>> {
  return fetchAPI<T>(endpoint, {
    ...options,
    method: 'PATCH',
    body: body ? JSON.stringify(body) : undefined,
  });
}

// ============================================================================
// API ENDPOINTS
// ============================================================================

/**
 * Process a regulatory query and get analysis
 */
export async function processQuery(
  text: string,
  sector?: string
): Promise<APIResponse<OrchestrationResult>> {
  const result = await post<OrchestrationResult>('/api/query', {
    query: text,
    sector: sector || 'general',
  });

  if (result.error) {
    addNotification({
      type: 'error',
      message: result.error.message,
      duration: 5000,
    });
  }

  return result;
}

/**
 * Get query history
 */
export async function getQueryHistory(
  page: number = 1,
  pageSize: number = 20
): Promise<APIResponse<PaginatedResponse<Query>>> {
  return get<PaginatedResponse<Query>>(
    `/api/queries?page=${page}&pageSize=${pageSize}`
  );
}

/**
 * Get single query by ID
 */
export async function getQuery(queryId: string): Promise<APIResponse<Query>> {
  return get<Query>(`/api/queries/${queryId}`);
}

/**
 * Delete a query
 */
export async function deleteQueryAPI(queryId: string): Promise<APIResponse<{ success: boolean }>> {
  return deleteRequest<{ success: boolean }>(`/api/queries/${queryId}`);
}

/**
 * Generate a regulatory report from query analysis
 */
export async function generateReport(
  queryId: string,
  reportOptions: ReportRequest
): Promise<APIResponse<ReportJobResponse>> {
  const result = await post<ReportJobResponse>('/api/reports/generate', {
    queryId,
    ...reportOptions,
  });

  if (result.error) {
    addNotification({
      type: 'error',
      message: `Report generation failed: ${result.error.message}`,
      duration: 5000,
    });
  } else {
    addNotification({
      type: 'info',
      message: 'Report generation started',
      duration: 3000,
    });
  }

  return result;
}

/**
 * Get report generation job status
 */
export async function getReportStatus(
  jobId: string
): Promise<APIResponse<ReportJobResponse>> {
  return get<ReportJobResponse>(`/api/reports/status/${jobId}`);
}

/**
 * Download report file
 */
export async function downloadReport(
  reportId: string
): Promise<{
  blob?: Blob;
  error?: APIError;
  status: number;
}> {
  try {
    const url = getURL(`/api/reports/${reportId}/download`);
    const response = await fetch(url, {
      method: 'GET',
    });

    if (!response.ok) {
      const data = await parseJSON<APIError>(response);
      return {
        error: handleError(response.status, data),
        status: response.status,
      };
    }

    const blob = await response.blob();
    return {
      blob,
      status: response.status,
    };
  } catch (error) {
    return {
      error: {
        statusCode: 0,
        message: error instanceof Error ? error.message : 'Download failed',
        error: 'DOWNLOAD_ERROR',
      },
      status: 0,
    };
  }
}

/**
 * Upload file for analysis
 */
export async function uploadFile(
  file: File,
  sector?: string
): Promise<APIResponse<{ fileId: string; fileName: string }>> {
  const formData = new FormData();
  formData.append('file', file);
  if (sector) {
    formData.append('sector', sector);
  }

  try {
    const url = getURL('/api/upload');
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    const data = await parseJSON<{ fileId: string; fileName: string }>(response);

    if (!response.ok) {
      return {
        error: handleError(response.status, data),
        status: response.status,
      };
    }

    return {
      data,
      status: response.status,
    };
  } catch (error) {
    return {
      error: {
        statusCode: 0,
        message: error instanceof Error ? error.message : 'Upload failed',
        error: 'UPLOAD_ERROR',
      },
      status: 0,
    };
  }
}

/**
 * Search queries by text
 */
export async function searchQueries(
  searchText: string,
  filters?: {
    sector?: string;
    type?: string;
    startDate?: Date;
    endDate?: Date;
  }
): Promise<APIResponse<PaginatedResponse<Query>>> {
  const params = new URLSearchParams({
    q: searchText,
    ...(filters?.sector && { sector: filters.sector }),
    ...(filters?.type && { type: filters.type }),
    ...(filters?.startDate && { startDate: filters.startDate.toISOString() }),
    ...(filters?.endDate && { endDate: filters.endDate.toISOString() }),
  });

  return get<PaginatedResponse<Query>>(
    `/api/queries/search?${params.toString()}`
  );
}

/**
 * Get health check
 */
export async function healthCheck(): Promise<APIResponse<{ status: string; version?: string }>> {
  return get<{ status: string; version?: string }>('/health');
}

/**
 * Get API configuration
 */
export async function getConfig(): Promise<APIResponse<{
  version: string;
  supportedSectors: string[];
  supportedAnalysisTypes: string[];
}>> {
  return get<{
    version: string;
    supportedSectors: string[];
    supportedAnalysisTypes: string[];
  }>('/api/config');
}

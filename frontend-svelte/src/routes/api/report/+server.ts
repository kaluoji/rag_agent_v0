import type { RequestHandler } from './$types';
import type { ReportRequest, ReportJobResponse } from '$lib/types';

/**
 * POST /api/report - Generate report from query
 * GET /api/report - Get report status
 * Proxy endpoints for report generation endpoints
 */

const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000';
const REPORT_TIMEOUT = 120000; // 2 minutes

interface ReportGenerationRequest {
  queryId: string;
  analysisType: 'comprehensive' | 'quick' | 'gap-analysis' | 'executive-summary';
  sector: 'banking' | 'insurance' | 'telecoms' | 'general';
  format?: 'docx' | 'pdf' | 'html';
  includeExecutiveSummary?: boolean;
  includeGapAnalysis?: boolean;
  includeRecommendations?: boolean;
}

/**
 * Handle POST request for report generation
 */
export const POST: RequestHandler = async ({ request, url }) => {
  try {
    // Check if this is a generation request or status check
    const action = url.searchParams.get('action');

    if (action === 'status') {
      return handleStatusCheck(request);
    }

    // Default to generation request
    return handleReportGeneration(request);
  } catch (error) {
    console.error('Error in report API route:', error);
    return new Response(
      JSON.stringify({
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error occurred',
        statusCode: 500,
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

/**
 * Handle GET request for report status
 */
export const GET: RequestHandler = async ({ url }) => {
  try {
    const jobId = url.searchParams.get('jobId');

    if (!jobId) {
      return new Response(
        JSON.stringify({
          error: 'Validation error',
          message: 'jobId query parameter is required',
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Forward to backend
    const backendUrl = new URL(`/api/reports/status/${jobId}`, API_BASE_URL);
    const response = await fetch(backendUrl.toString(), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return new Response(
        JSON.stringify({
          error: 'Backend error',
          statusCode: response.status,
          message: errorData.message || `Backend returned status ${response.status}`,
        }),
        {
          status: response.status,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    const data = (await response.json()) as ReportJobResponse;
    return new Response(JSON.stringify(data), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    console.error('Error checking report status:', error);
    return new Response(
      JSON.stringify({
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error occurred',
        statusCode: 500,
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

/**
 * Handle report generation request
 */
async function handleReportGeneration(request: Request): Promise<Response> {
  // Parse request body
  let body: ReportGenerationRequest;
  try {
    body = (await request.json()) as ReportGenerationRequest;
  } catch (error) {
    return new Response(
      JSON.stringify({
        error: 'Invalid JSON',
        message: 'Request body must be valid JSON',
        details: error instanceof Error ? error.message : 'Unknown error',
      }),
      {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }

  // Validate required fields
  if (!body.queryId || !body.analysisType || !body.sector) {
    return new Response(
      JSON.stringify({
        error: 'Validation error',
        message: 'queryId, analysisType, and sector are required',
      }),
      {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REPORT_TIMEOUT);

  try {
    const backendUrl = new URL('/api/reports/generate', API_BASE_URL);

    const backendResponse = await fetch(backendUrl.toString(), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!backendResponse.ok) {
      const errorData = await backendResponse.json().catch(() => ({}));
      return new Response(
        JSON.stringify({
          error: 'Backend error',
          statusCode: backendResponse.status,
          message:
            errorData.message || `Backend returned status ${backendResponse.status}`,
          details: errorData.details || errorData.error,
        }),
        {
          status: backendResponse.status,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    const data = (await backendResponse.json()) as ReportJobResponse;
    return new Response(JSON.stringify(data), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        return new Response(
          JSON.stringify({
            error: 'Request timeout',
            message: 'Report generation request took too long. Please try again.',
            statusCode: 408,
          }),
          {
            status: 408,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      }

      return new Response(
        JSON.stringify({
          error: 'Backend connection error',
          message: 'Failed to connect to report generation service',
          details: error.message,
          statusCode: 503,
        }),
        {
          status: 503,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    throw error;
  }
}

/**
 * Handle status check request
 */
async function handleStatusCheck(request: Request): Promise<Response> {
  let body: { jobId: string };
  try {
    body = (await request.json()) as { jobId: string };
  } catch (error) {
    return new Response(
      JSON.stringify({
        error: 'Invalid JSON',
        message: 'Request body must be valid JSON',
      }),
      {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }

  if (!body.jobId) {
    return new Response(
      JSON.stringify({
        error: 'Validation error',
        message: 'jobId is required',
      }),
      {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }

  try {
    const backendUrl = new URL(`/api/reports/status/${body.jobId}`, API_BASE_URL);
    const response = await fetch(backendUrl.toString(), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return new Response(
        JSON.stringify({
          error: 'Backend error',
          statusCode: response.status,
          message: errorData.message || `Backend returned status ${response.status}`,
        }),
        {
          status: response.status,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    const data = (await response.json()) as ReportJobResponse;
    return new Response(JSON.stringify(data), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    return new Response(
      JSON.stringify({
        error: 'Backend connection error',
        message: error instanceof Error ? error.message : 'Failed to check status',
        statusCode: 503,
      }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
}

/**
 * Handle OPTIONS request for CORS preflight
 */
export const OPTIONS: RequestHandler = async () => {
  return new Response(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
};

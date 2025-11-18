import type { RequestHandler } from './$types';
import type { OrchestrationResult } from '$lib/types';

/**
 * POST /api/query
 * Proxy endpoint for processing regulatory queries
 * Forwards request to backend /query endpoint
 * Returns analysis results from orchestrator agent
 */

const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000';
const REQUEST_TIMEOUT = 60000; // 60 seconds for complex analysis

interface QueryRequest {
  query: string;
  sector?: string;
  type?: 'compliance' | 'gap-analysis' | 'report';
}

/**
 * Handle POST request for query processing
 */
export const POST: RequestHandler = async ({ request }) => {
  try {
    // Validate request method
    if (request.method !== 'POST') {
      return new Response(
        JSON.stringify({
          error: 'Method not allowed',
          message: 'Only POST requests are supported',
        }),
        {
          status: 405,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Parse request body
    let body: QueryRequest;
    try {
      body = (await request.json()) as QueryRequest;
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
    if (!body.query || typeof body.query !== 'string') {
      return new Response(
        JSON.stringify({
          error: 'Validation error',
          message: 'Query text is required and must be a string',
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Validate query length
    if (body.query.trim().length === 0 || body.query.length > 5000) {
      return new Response(
        JSON.stringify({
          error: 'Validation error',
          message: 'Query must be between 1 and 5000 characters',
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Set default sector if not provided
    const sector = body.sector || 'general';

    // Construct backend request
    const backendUrl = new URL('/query', API_BASE_URL);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

    try {
      const backendResponse = await fetch(backendUrl.toString(), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: body.query,
          sector,
          type: body.type || 'compliance',
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      // Handle backend errors
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

      // Parse and return backend response
      const data = (await backendResponse.json()) as OrchestrationResult;

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
              message: 'The query processing took too long. Please try again.',
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
            message: 'Failed to connect to analysis service',
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
  } catch (error) {
    console.error('Error in query API route:', error);
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
 * Handle OPTIONS request for CORS preflight
 */
export const OPTIONS: RequestHandler = async () => {
  return new Response(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
};

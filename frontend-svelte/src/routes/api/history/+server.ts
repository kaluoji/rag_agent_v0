import type { RequestHandler } from './$types';
import type { Query, PaginatedResponse } from '$lib/types';

/**
 * GET /api/history - Get query history with pagination and filters
 * DELETE /api/history/:id - Delete a query
 * Proxy endpoints for query history management
 */

const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000';
const HISTORY_TIMEOUT = 30000; // 30 seconds

/**
 * Handle GET request for query history
 */
export const GET: RequestHandler = async ({ url }) => {
  try {
    // Extract query parameters
    const page = url.searchParams.get('page') || '1';
    const pageSize = url.searchParams.get('pageSize') || '20';
    const sector = url.searchParams.get('sector');
    const type = url.searchParams.get('type');
    const search = url.searchParams.get('search');
    const startDate = url.searchParams.get('startDate');
    const endDate = url.searchParams.get('endDate');

    // Validate pagination parameters
    const pageNum = parseInt(page, 10);
    const pageSizeNum = parseInt(pageSize, 10);

    if (isNaN(pageNum) || pageNum < 1) {
      return new Response(
        JSON.stringify({
          error: 'Validation error',
          message: 'Page must be a positive integer',
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    if (isNaN(pageSizeNum) || pageSizeNum < 1 || pageSizeNum > 100) {
      return new Response(
        JSON.stringify({
          error: 'Validation error',
          message: 'PageSize must be between 1 and 100',
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Build backend URL with query parameters
    const backendUrl = new URL('/api/queries', API_BASE_URL);
    backendUrl.searchParams.set('page', page);
    backendUrl.searchParams.set('pageSize', pageSize);

    if (sector) {
      backendUrl.searchParams.set('sector', sector);
    }
    if (type) {
      backendUrl.searchParams.set('type', type);
    }
    if (search) {
      backendUrl.searchParams.set('search', search);
    }
    if (startDate) {
      backendUrl.searchParams.set('startDate', startDate);
    }
    if (endDate) {
      backendUrl.searchParams.set('endDate', endDate);
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), HISTORY_TIMEOUT);

    try {
      const response = await fetch(backendUrl.toString(), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        return new Response(
          JSON.stringify({
            error: 'Backend error',
            statusCode: response.status,
            message: errorData.message || `Backend returned status ${response.status}`,
            details: errorData.details || errorData.error,
          }),
          {
            status: response.status,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      }

      const data = (await response.json()) as PaginatedResponse<Query>;
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
              message: 'History request took too long. Please try again.',
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
            message: 'Failed to connect to history service',
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
    console.error('Error in history GET API route:', error);
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
 * Handle DELETE request for query deletion
 */
export const DELETE: RequestHandler = async ({ url }) => {
  try {
    const queryId = url.searchParams.get('id');

    if (!queryId) {
      return new Response(
        JSON.stringify({
          error: 'Validation error',
          message: 'Query ID is required',
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    const backendUrl = new URL(`/api/queries/${queryId}`, API_BASE_URL);

    const response = await fetch(backendUrl.toString(), {
      method: 'DELETE',
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
          details: errorData.details || errorData.error,
        }),
        {
          status: response.status,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    const data = await response.json();
    return new Response(JSON.stringify(data), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    console.error('Error in history DELETE API route:', error);
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
      'Access-Control-Allow-Methods': 'GET, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
};

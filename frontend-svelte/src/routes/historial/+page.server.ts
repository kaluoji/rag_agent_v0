import type { PageServerLoad } from './$types';
import type { Query, PaginatedResponse } from '$lib/types';

/**
 * Server-side load function for history page
 * Loads all queries from backend with pagination support
 */

const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Fetch all queries from backend with pagination
 * @param page - Page number (1-indexed)
 * @param pageSize - Items per page
 * @returns Paginated query results
 */
async function fetchAllQueries(
  page: number = 1,
  pageSize: number = 50
): Promise<PaginatedResponse<Query>> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/queries?page=${page}&pageSize=${pageSize}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      console.warn(`Failed to fetch queries: ${response.status}`);
      return {
        data: [],
        meta: {
          total: 0,
          page: 1,
          pageSize,
          totalPages: 0,
        },
      };
    }

    return (await response.json()) as PaginatedResponse<Query>;
  } catch (error) {
    console.error('Error fetching queries:', error);
    return {
      data: [],
      meta: {
        total: 0,
        page: 1,
        pageSize,
        totalPages: 0,
      },
    };
  }
}

/**
 * Page load function - runs on server
 * Pre-loads paginated query history
 */
export const load: PageServerLoad = async ({ url }) => {
  try {
    const page = parseInt(url.searchParams.get('page') || '1', 10);
    const pageSize = parseInt(url.searchParams.get('pageSize') || '50', 10);

    const queryData = await fetchAllQueries(page, pageSize);

    return {
      queries: queryData.data,
      pagination: queryData.meta,
      timestamp: new Date().toISOString(),
    };
  } catch (error) {
    console.error('Error in history page load:', error);
    return {
      queries: [],
      pagination: {
        total: 0,
        page: 1,
        pageSize: 50,
        totalPages: 0,
      },
      error: 'Failed to load query history',
      timestamp: new Date().toISOString(),
    };
  }
};

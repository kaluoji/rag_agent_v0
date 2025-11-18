import type { PageServerLoad } from './$types';
import type { Query } from '$lib/types';

/**
 * Server-side load function for query detail page
 * Pre-loads specific query by ID from backend
 */

const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Fetch single query from backend
 * @param queryId - Query ID to fetch
 * @returns Query object if found, null otherwise
 */
async function fetchQuery(queryId: string): Promise<Query | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/queries/${queryId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      console.warn(`Failed to fetch query ${queryId}: ${response.status}`);
      return null;
    }

    return (await response.json()) as Query;
  } catch (error) {
    console.error(`Error fetching query ${queryId}:`, error);
    return null;
  }
}

/**
 * Page load function - runs on server
 * Pre-loads query data for detail page
 */
export const load: PageServerLoad = async ({ params }) => {
  try {
    const { id } = params;

    if (!id) {
      return {
        query: null,
        error: 'Query ID is required',
        timestamp: new Date().toISOString(),
      };
    }

    const query = await fetchQuery(id);

    return {
      query,
      timestamp: new Date().toISOString(),
      ...(query ? {} : { error: 'Query not found' }),
    };
  } catch (error) {
    console.error('Error in query detail page load:', error);
    return {
      query: null,
      error: 'Failed to load query details',
      timestamp: new Date().toISOString(),
    };
  }
};

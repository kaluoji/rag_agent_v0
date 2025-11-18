import type { PageServerLoad } from './$types';
import type { Query, PaginatedResponse } from '$lib/types';

/**
 * Server-side load function for main page
 * Pre-loads recent queries for display in sidebar or quick access
 * Executed on server before page renders
 */

const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Fetch recent queries from backend
 * @returns List of recent queries (last 10)
 */
async function fetchRecentQueries(): Promise<Query[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/queries?page=1&pageSize=10`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      console.warn(`Failed to fetch recent queries: ${response.status}`);
      return [];
    }

    const data = (await response.json()) as PaginatedResponse<Query>;
    return data.data || [];
  } catch (error) {
    console.error('Error fetching recent queries:', error);
    return [];
  }
}

/**
 * Page load function - runs on server
 * Pre-loads data needed for the page
 */
export const load: PageServerLoad = async ({ fetch: svelteKitFetch }) => {
  try {
    // Load recent queries in parallel
    const recentQueries = await fetchRecentQueries();

    return {
      recentQueries,
      timestamp: new Date().toISOString(),
    };
  } catch (error) {
    console.error('Error in page load:', error);
    return {
      recentQueries: [],
      error: 'Failed to load initial data',
      timestamp: new Date().toISOString(),
    };
  }
};

import type { PageServerLoad } from './$types';

/**
 * Server-side load function for news page
 * Pre-loads news and updates from backend
 */

const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Fetch news items from backend
 * @returns Array of news items
 */
async function fetchNews(): Promise<any[]> {
  try {
    // If backend has a news endpoint, call it here
    // For now, return empty array - frontend will use mock data
    const response = await fetch(`${API_BASE_URL}/api/news`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      console.warn(`Failed to fetch news: ${response.status}`);
      return [];
    }

    return (await response.json()) as any[];
  } catch (error) {
    console.error('Error fetching news:', error);
    // Return empty array - frontend will use mock data
    return [];
  }
}

/**
 * Page load function - runs on server
 * Pre-loads news data
 */
export const load: PageServerLoad = async () => {
  try {
    const news = await fetchNews();

    return {
      news,
      timestamp: new Date().toISOString(),
    };
  } catch (error) {
    console.error('Error in news page load:', error);
    return {
      news: [],
      timestamp: new Date().toISOString(),
    };
  }
};

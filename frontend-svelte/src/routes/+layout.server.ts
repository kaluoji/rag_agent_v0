/**
 * Server-side layout loader for RAG Regulatory Analysis System
 * Initializes authentication, configuration, and global data
 */

import type { LayoutServerLoad } from './$types';

/**
 * Server-side load function for app layout
 * Runs once on server startup and provides data to all routes
 */
export const load: LayoutServerLoad = async ({ fetch, url }) => {
  // Get API configuration
  let config = null;
  let error = null;

  try {
    const response = await fetch('/api/config', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (response.ok) {
      config = await response.json();
    } else {
      error = `Failed to load config: ${response.status}`;
      console.error(error);
    }
  } catch (err) {
    error = `Error loading config: ${err instanceof Error ? err.message : 'Unknown error'}`;
    console.error(error);
    // Continue with default config even if this fails
  }

  // Default configuration if API is unavailable
  const defaultConfig = {
    version: '1.0.0',
    supportedSectors: ['banking', 'insurance', 'telecoms', 'general'],
    supportedAnalysisTypes: ['compliance', 'gap-analysis', 'report'],
  };

  return {
    // API configuration
    config: config || defaultConfig,

    // Environment
    apiUrl: process.env.VITE_API_URL || 'http://localhost:8000',
    wsHost: process.env.VITE_WS_HOST || 'localhost',
    wsPort: parseInt(process.env.VITE_WS_PORT || '8000', 10),

    // Application metadata
    app: {
      name: 'RAG Regulatory Analysis',
      version: process.env.npm_package_version || '1.0.0',
      description: 'AI-powered regulatory compliance analysis and reporting system',
    },

    // URL information
    pathname: url.pathname,

    // Error info if any
    ...(error && { error }),
  };
};

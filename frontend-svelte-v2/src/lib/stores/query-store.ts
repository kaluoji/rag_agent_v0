// src/lib/stores/query-store.ts
import { writable, get } from 'svelte/store';
import type { Query } from '$lib/types';

interface QueryStoreState {
  query: string;
  response: any;
  isLoading: boolean;
  error: string | null;
  recentQueries: Query[];
}

const STORAGE_KEY = 'recentQueries';
const MAX_QUERIES = 50;

// Initial state
const initialState: QueryStoreState = {
  query: '',
  response: null,
  isLoading: false,
  error: null,
  recentQueries: []
};

// Create the writable store
const { subscribe, set, update } = writable<QueryStoreState>(initialState);

// Helper function to save to localStorage
function saveToLocalStorage(queries: Query[]) {
  try {
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(queries));
    }
  } catch (e) {
    console.error('Failed to save queries to localStorage', e);
  }
}

// Helper function to load from localStorage
function loadFromLocalStorage(): Query[] {
  try {
    if (typeof localStorage !== 'undefined') {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const queries = JSON.parse(stored);
        // Validate structure
        const validQueries = queries.filter(
          (q: any) => q && q.id && q.text && q.timestamp
        );
        return validQueries;
      }
    }
  } catch (e) {
    console.error('Failed to load queries from localStorage', e);
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem(STORAGE_KEY);
    }
  }
  return [];
}

// Store methods
export const queryStore = {
  subscribe,

  setQuery: (query: string) => {
    update((state) => ({ ...state, query }));
  },

  setResponse: (response: any) => {
    update((state) => {
      const newState = { ...state, response };

      // Add to history when we get a response
      if (state.query && state.query.trim() !== '') {
        const queryObj: Query = {
          id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
          text: state.query,
          timestamp: new Date().toISOString(),
          response: typeof response === 'string' ? response : JSON.stringify(response),
          type: state.query.toLowerCase().includes('gap') ? 'gap_analysis' : 'consultation',
          hasDocuments: false
        };

        queryStore.addToHistory(queryObj);
      }

      return newState;
    });
  },

  startLoading: () => {
    update((state) => ({ ...state, isLoading: true, error: null }));
  },

  stopLoading: () => {
    update((state) => ({ ...state, isLoading: false }));
  },

  setError: (error: string) => {
    update((state) => ({ ...state, error, isLoading: false }));
  },

  reset: () => {
    update((state) => ({
      ...state,
      query: '',
      response: null,
      isLoading: false,
      error: null
    }));
  },

  addToHistory: (queryObj: Partial<Query>) => {
    update((state) => {
      const newQuery: Query = {
        id: queryObj.id || Date.now().toString() + Math.random().toString(36).substr(2, 9),
        text: queryObj.text || state.query,
        timestamp: queryObj.timestamp || new Date().toISOString(),
        response: queryObj.response || state.response,
        type: queryObj.type || (queryObj.text && queryObj.text.toLowerCase().includes('gap') ? 'gap_analysis' : 'consultation'),
        hasDocuments: queryObj.hasDocuments || false,
        metadata: queryObj.metadata
      };

      // Add to beginning and keep only MAX_QUERIES
      const updated = [
        newQuery,
        ...state.recentQueries.filter(q => q.id !== newQuery.id)
      ].slice(0, MAX_QUERIES);

      // Save to localStorage
      saveToLocalStorage(updated);

      return { ...state, recentQueries: updated };
    });
  },

  loadStoredQueries: () => {
    const queries = loadFromLocalStorage();
    update((state) => ({ ...state, recentQueries: queries }));
  },

  getQueryById: (id: string): Query | null => {
    const state = get({ subscribe });
    return state.recentQueries.find(q => q.id === id) || null;
  },

  removeQueryFromHistory: (id: string) => {
    update((state) => {
      const updated = state.recentQueries.filter(q => q.id !== id);
      saveToLocalStorage(updated);
      return { ...state, recentQueries: updated };
    });
  },

  clearAllHistory: () => {
    update((state) => {
      if (typeof localStorage !== 'undefined') {
        localStorage.removeItem(STORAGE_KEY);
      }
      return { ...state, recentQueries: [] };
    });
  },

  searchInHistory: (searchTerm: string): Query[] => {
    const state = get({ subscribe });
    if (!searchTerm.trim()) return state.recentQueries;

    const term = searchTerm.toLowerCase();
    return state.recentQueries.filter(
      q =>
        q.text.toLowerCase().includes(term) ||
        (q.response && q.response.toLowerCase().includes(term))
    );
  }
};

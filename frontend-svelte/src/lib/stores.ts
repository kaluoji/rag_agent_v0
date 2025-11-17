/**
 * Svelte stores for application state management
 * Replaces Zustand with native Svelte stores + custom hooks
 */

import { writable, derived, type Writable, type Readable } from 'svelte/store';
import type {
  Message,
  Query,
  ChatStoreState,
  QueryStoreState,
  ReportStoreState,
  UIStoreState,
  Notification,
} from './types';

// ============================================================================
// UTILITIES
// ============================================================================

/**
 * Creates a writable store that persists to localStorage
 * @param key - localStorage key
 * @param initialValue - initial value if not in localStorage
 */
function createLocalStorage<T>(key: string, initialValue: T): Writable<T> {
  const store = writable<T>(initialValue);

  // Load from localStorage on initialization
  if (typeof window !== 'undefined') {
    try {
      const stored = localStorage.getItem(key);
      if (stored) {
        store.set(JSON.parse(stored));
      }
    } catch (error) {
      console.error(`Failed to load ${key} from localStorage:`, error);
    }

    // Subscribe to changes and persist
    store.subscribe((value) => {
      try {
        localStorage.setItem(key, JSON.stringify(value));
      } catch (error) {
        console.error(`Failed to save ${key} to localStorage:`, error);
      }
    });
  }

  return store;
}

// ============================================================================
// MESSAGE STORE
// ============================================================================

const initialChatState: ChatStoreState = {
  messages: [],
  loading: false,
  error: null,
  autoScroll: true,
  currentQueryId: null,
};

export const messageStore = writable<ChatStoreState>(initialChatState);

/**
 * Add a message to the chat
 */
export function addMessage(message: Message): void {
  messageStore.update((state) => ({
    ...state,
    messages: [...state.messages, message],
  }));
}

/**
 * Clear all messages
 */
export function clearMessages(): void {
  messageStore.update((state) => ({
    ...state,
    messages: [],
  }));
}

/**
 * Set loading state
 */
export function setMessageLoading(loading: boolean): void {
  messageStore.update((state) => ({
    ...state,
    loading,
  }));
}

/**
 * Set error state
 */
export function setMessageError(error: string | null): void {
  messageStore.update((state) => ({
    ...state,
    error,
  }));
}

/**
 * Derived store for latest message
 */
export const latestMessage: Readable<Message | null | undefined> = derived(messageStore, ($messageStore) => {
  if ($messageStore.messages.length === 0) return null;
  return $messageStore.messages[$messageStore.messages.length - 1];
});

/**
 * Derived store for message count
 */
export const messageCount: Readable<number> = derived(messageStore, ($messageStore) =>
  $messageStore.messages.length
);

// ============================================================================
// QUERY STORE
// ============================================================================

const initialQueryState: QueryStoreState = {
  queries: [],
  currentQuery: null,
  loading: false,
  error: null,
  selectedSector: null,
  selectedType: null,
};

export const queryStore = createLocalStorage<QueryStoreState>('rag-queries', initialQueryState);

/**
 * Add a new query
 */
export function addQuery(query: Query): void {
  queryStore.update((state) => ({
    ...state,
    queries: [query, ...state.queries],
    currentQuery: query,
  }));
}

/**
 * Update current query
 */
export function updateCurrentQuery(query: Query): void {
  queryStore.update((state) => ({
    ...state,
    currentQuery: query,
    queries: state.queries.map((q) => (q.id === query.id ? query : q)),
  }));
}

/**
 * Set current query by ID
 */
export function setCurrentQuery(queryId: string | null): void {
  queryStore.update((state) => ({
    ...state,
    currentQuery: queryId ? state.queries.find((q) => q.id === queryId) || null : null,
  }));
}

/**
 * Delete a query
 */
export function deleteQuery(queryId: string): void {
  queryStore.update((state) => ({
    ...state,
    queries: state.queries.filter((q) => q.id !== queryId),
    currentQuery: state.currentQuery?.id === queryId ? null : state.currentQuery,
  }));
}

/**
 * Clear all queries
 */
export function clearQueries(): void {
  queryStore.update((state) => ({
    ...state,
    queries: [],
    currentQuery: null,
  }));
}

/**
 * Set loading state
 */
export function setQueryLoading(loading: boolean): void {
  queryStore.update((state) => ({
    ...state,
    loading,
  }));
}

/**
 * Set error state
 */
export function setQueryError(error: string | null): void {
  queryStore.update((state) => ({
    ...state,
    error,
  }));
}

/**
 * Set sector filter
 */
export function setSelectedSector(sector: string | null): void {
  queryStore.update((state) => ({
    ...state,
    selectedSector: sector,
  }));
}

/**
 * Set type filter
 */
export function setSelectedType(type: Query['type'] | null): void {
  queryStore.update((state) => ({
    ...state,
    selectedType: type,
  }));
}

/**
 * Derived store for filtered queries
 */
export const filteredQueries: Readable<Query[]> = derived(queryStore, ($queryStore) => {
  let filtered = [...$queryStore.queries];

  if ($queryStore.selectedSector) {
    filtered = filtered.filter((q) => q.sector === $queryStore.selectedSector);
  }

  if ($queryStore.selectedType) {
    filtered = filtered.filter((q) => q.type === $queryStore.selectedType);
  }

  return filtered;
});

/**
 * Derived store for query count
 */
export const queryCount: Readable<number> = derived(queryStore, ($queryStore) =>
  $queryStore.queries.length
);

/**
 * Derived store for recent queries (last 10)
 */
export const recentQueries: Readable<Query[]> = derived(queryStore, ($queryStore) =>
  $queryStore.queries.slice(0, 10)
);

// ============================================================================
// REPORT STORE
// ============================================================================

const initialReportState: ReportStoreState = {
  reports: [],
  currentReport: null,
  generating: false,
  error: null,
  jobId: null,
  progress: 0,
};

export const reportStore = writable<ReportStoreState>(initialReportState);

/**
 * Add a report
 */
export function addReport(report: Query & { artifact?: any }): void {
  reportStore.update((state) => ({
    ...state,
    reports: [report, ...state.reports],
    currentReport: report,
  }));
}

/**
 * Update current report
 */
export function updateCurrentReport(report: Query & { artifact?: any }): void {
  reportStore.update((state) => ({
    ...state,
    currentReport: report,
    reports: state.reports.map((r) => (r.id === report.id ? report : r)),
  }));
}

/**
 * Set current report by ID
 */
export function setCurrentReport(reportId: string | null): void {
  reportStore.update((state) => ({
    ...state,
    currentReport: reportId ? state.reports.find((r) => r.id === reportId) || null : null,
  }));
}

/**
 * Delete a report
 */
export function deleteReport(reportId: string): void {
  reportStore.update((state) => ({
    ...state,
    reports: state.reports.filter((r) => r.id !== reportId),
    currentReport: state.currentReport?.id === reportId ? null : state.currentReport,
  }));
}

/**
 * Start report generation
 */
export function startReportGeneration(jobId: string): void {
  reportStore.update((state) => ({
    ...state,
    generating: true,
    jobId,
    progress: 0,
    error: null,
  }));
}

/**
 * Update report progress
 */
export function updateReportProgress(progress: number): void {
  reportStore.update((state) => ({
    ...state,
    progress: Math.min(100, progress),
  }));
}

/**
 * Complete report generation
 */
export function completeReportGeneration(): void {
  reportStore.update((state) => ({
    ...state,
    generating: false,
    progress: 100,
  }));
}

/**
 * Set report error
 */
export function setReportError(error: string | null): void {
  reportStore.update((state) => ({
    ...state,
    generating: false,
    error,
  }));
}

/**
 * Derived store for report count
 */
export const reportCount: Readable<number> = derived(reportStore, ($reportStore) =>
  $reportStore.reports.length
);

// ============================================================================
// UI STORE
// ============================================================================

const initialUIState: UIStoreState = {
  theme: 'light',
  sidebarOpen: true,
  notifications: [],
  modal: {
    isOpen: false,
  },
};

export const uiStore = createLocalStorage<UIStoreState>('rag-ui', initialUIState);

/**
 * Toggle theme between light and dark
 */
export function toggleTheme(): void {
  uiStore.update((state) => ({
    ...state,
    theme: state.theme === 'light' ? 'dark' : 'light',
  }));
}

/**
 * Set theme explicitly
 */
export function setTheme(theme: 'light' | 'dark'): void {
  uiStore.update((state) => ({
    ...state,
    theme,
  }));
}

/**
 * Toggle sidebar
 */
export function toggleSidebar(): void {
  uiStore.update((state) => ({
    ...state,
    sidebarOpen: !state.sidebarOpen,
  }));
}

/**
 * Set sidebar open state
 */
export function setSidebarOpen(open: boolean): void {
  uiStore.update((state) => ({
    ...state,
    sidebarOpen: open,
  }));
}

/**
 * Add notification
 */
export function addNotification(notification: Omit<Notification, 'id'>): string {
  const id = Math.random().toString(36).substr(2, 9);
  const fullNotification: Notification = { ...notification, id };

  uiStore.update((state) => ({
    ...state,
    notifications: [...state.notifications, fullNotification],
  }));

  // Auto-dismiss if duration specified
  if (notification.duration) {
    setTimeout(() => dismissNotification(id), notification.duration);
  }

  return id;
}

/**
 * Dismiss notification
 */
export function dismissNotification(id: string): void {
  uiStore.update((state) => ({
    ...state,
    notifications: state.notifications.filter((n) => n.id !== id),
  }));
}

/**
 * Clear all notifications
 */
export function clearNotifications(): void {
  uiStore.update((state) => ({
    ...state,
    notifications: [],
  }));
}

/**
 * Open modal
 */
export function openModal(title: string, content: string, type: 'confirm' | 'alert' | 'info' = 'info'): void {
  uiStore.update((state) => ({
    ...state,
    modal: {
      isOpen: true,
      title,
      content,
      type,
    },
  }));
}

/**
 * Close modal
 */
export function closeModal(): void {
  uiStore.update((state) => ({
    ...state,
    modal: {
      isOpen: false,
    },
  }));
}

/**
 * Derived store for notification count
 */
export const notificationCount: Readable<number> = derived(uiStore, ($uiStore) =>
  $uiStore.notifications.length
);

// ============================================================================
// COMBINED STORES
// ============================================================================

/**
 * Derived store combining all loading states
 */
export const isLoading: Readable<boolean> = derived(
  [messageStore, queryStore, reportStore],
  ([$messageStore, $queryStore, $reportStore]) =>
    $messageStore.loading || $queryStore.loading || $reportStore.generating
);

/**
 * Derived store combining all error states
 */
export const currentError: Readable<string | null> = derived(
  [messageStore, queryStore, reportStore],
  ([$messageStore, $queryStore, $reportStore]) =>
    $messageStore.error || $queryStore.error || $reportStore.error
);

/**
 * Unit tests for Svelte stores
 * Tests store initialization, actions, and derived stores
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  // Message store
  messageStore,
  addMessage,
  clearMessages,
  setMessageLoading,
  setMessageError,
  latestMessage,
  messageCount,
  // Query store
  queryStore,
  addQuery,
  updateCurrentQuery,
  setCurrentQuery,
  deleteQuery,
  clearQueries,
  setQueryLoading,
  setQueryError,
  setSelectedSector,
  setSelectedType,
  filteredQueries,
  queryCount,
  recentQueries,
  // Report store
  reportStore,
  addReport,
  updateCurrentReport,
  setCurrentReport,
  deleteReport,
  startReportGeneration,
  updateReportProgress,
  completeReportGeneration,
  setReportError,
  reportCount,
  // UI store
  uiStore,
  toggleTheme,
  setTheme,
  toggleSidebar,
  setSidebarOpen,
  addNotification,
  dismissNotification,
  clearNotifications,
  openModal,
  closeModal,
  notificationCount,
  // Derived stores
  isLoading,
  currentError,
} from '../stores';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('Message Store', () => {
  beforeEach(() => {
    clearMessages();
  });

  it('should initialize with empty messages', async () => {
    let state: any;
    const unsubscribe = messageStore.subscribe((s) => {
      state = s;
    });

    expect(state.messages).toEqual([]);
    expect(state.loading).toBe(false);
    expect(state.error).toBe(null);

    unsubscribe();
  });

  it('should add messages', async () => {
    const message = {
      id: '1',
      role: 'user' as const,
      content: 'Test message',
      timestamp: new Date(),
    };

    addMessage(message);

    let state: any;
    messageStore.subscribe((s) => {
      state = s;
    })();

    expect(state.messages).toHaveLength(1);
    expect(state.messages[0].content).toBe('Test message');
  });

  it('should set loading state', async () => {
    setMessageLoading(true);

    let state: any;
    messageStore.subscribe((s) => {
      state = s;
    })();

    expect(state.loading).toBe(true);

    setMessageLoading(false);
    messageStore.subscribe((s) => {
      state = s;
    })();

    expect(state.loading).toBe(false);
  });

  it('should set error state', async () => {
    const errorMsg = 'Test error';
    setMessageError(errorMsg);

    let state: any;
    messageStore.subscribe((s) => {
      state = s;
    })();

    expect(state.error).toBe(errorMsg);

    setMessageError(null);
    messageStore.subscribe((s) => {
      state = s;
    })();

    expect(state.error).toBe(null);
  });

  it('should clear all messages', async () => {
    const msg1 = {
      id: '1',
      role: 'user' as const,
      content: 'Message 1',
      timestamp: new Date(),
    };
    const msg2 = {
      id: '2',
      role: 'assistant' as const,
      content: 'Message 2',
      timestamp: new Date(),
    };

    addMessage(msg1);
    addMessage(msg2);

    let state: any;
    messageStore.subscribe((s) => {
      state = s;
    })();

    expect(state.messages).toHaveLength(2);

    clearMessages();

    messageStore.subscribe((s) => {
      state = s;
    })();

    expect(state.messages).toHaveLength(0);
  });
});

describe('Query Store', () => {
  beforeEach(() => {
    clearQueries();
    localStorageMock.clear();
  });

  it('should initialize with empty queries', async () => {
    let state: any;
    queryStore.subscribe((s) => {
      state = s;
    })();

    expect(state.queries).toEqual([]);
    expect(state.currentQuery).toBe(null);
  });

  it('should add queries', async () => {
    const query = {
      id: '1',
      text: 'Test query',
      timestamp: new Date(),
      status: 'completed' as const,
      type: 'compliance' as const,
    };

    addQuery(query);

    let state: any;
    queryStore.subscribe((s) => {
      state = s;
    })();

    expect(state.queries).toHaveLength(1);
    expect(state.currentQuery?.text).toBe('Test query');
  });

  it('should persist queries to localStorage', async () => {
    const query = {
      id: '1',
      text: 'Test query',
      timestamp: new Date(),
      status: 'completed' as const,
    };

    addQuery(query);

    const stored = localStorage.getItem('rag-queries');
    expect(stored).toBeTruthy();
    const parsed = JSON.parse(stored!);
    expect(parsed.queries).toHaveLength(1);
  });

  it('should update current query', async () => {
    const query = {
      id: '1',
      text: 'Original',
      timestamp: new Date(),
      status: 'completed' as const,
    };

    addQuery(query);

    const updated = {
      ...query,
      text: 'Updated',
    };

    updateCurrentQuery(updated);

    let state: any;
    queryStore.subscribe((s) => {
      state = s;
    })();

    expect(state.currentQuery?.text).toBe('Updated');
    expect(state.queries[0].text).toBe('Updated');
  });

  it('should delete query', async () => {
    const query1 = {
      id: '1',
      text: 'Query 1',
      timestamp: new Date(),
      status: 'completed' as const,
    };
    const query2 = {
      id: '2',
      text: 'Query 2',
      timestamp: new Date(),
      status: 'completed' as const,
    };

    addQuery(query1);
    addQuery(query2);

    let state: any;
    queryStore.subscribe((s) => {
      state = s;
    })();

    expect(state.queries).toHaveLength(2);

    deleteQuery('1');

    queryStore.subscribe((s) => {
      state = s;
    })();

    expect(state.queries).toHaveLength(1);
    expect(state.queries[0].id).toBe('2');
  });

  it('should filter queries by sector', async () => {
    const query1 = {
      id: '1',
      text: 'Banking query',
      timestamp: new Date(),
      status: 'completed' as const,
      sector: 'banking',
    };
    const query2 = {
      id: '2',
      text: 'Insurance query',
      timestamp: new Date(),
      status: 'completed' as const,
      sector: 'insurance',
    };

    addQuery(query1);
    addQuery(query2);
    setSelectedSector('banking');

    let filtered: any;
    filteredQueries.subscribe((f) => {
      filtered = f;
    })();

    expect(filtered).toHaveLength(1);
    expect(filtered[0].sector).toBe('banking');
  });

  it('should filter queries by type', async () => {
    const query1 = {
      id: '1',
      text: 'Compliance check',
      timestamp: new Date(),
      status: 'completed' as const,
      type: 'compliance' as const,
    };
    const query2 = {
      id: '2',
      text: 'GAP analysis',
      timestamp: new Date(),
      status: 'completed' as const,
      type: 'gap-analysis' as const,
    };

    addQuery(query1);
    addQuery(query2);
    setSelectedType('gap-analysis');

    let filtered: any;
    filteredQueries.subscribe((f) => {
      filtered = f;
    })();

    expect(filtered).toHaveLength(1);
    expect(filtered[0].type).toBe('gap-analysis');
  });

  it('should provide query count', async () => {
    addQuery({
      id: '1',
      text: 'Query 1',
      timestamp: new Date(),
      status: 'completed' as const,
    });
    addQuery({
      id: '2',
      text: 'Query 2',
      timestamp: new Date(),
      status: 'completed' as const,
    });

    let count: number;
    queryCount.subscribe((c) => {
      count = c;
    })();

    expect(count).toBe(2);
  });

  it('should provide recent queries (last 10)', async () => {
    for (let i = 0; i < 15; i++) {
      addQuery({
        id: String(i),
        text: `Query ${i}`,
        timestamp: new Date(),
        status: 'completed' as const,
      });
    }

    let recent: any;
    recentQueries.subscribe((r) => {
      recent = r;
    })();

    expect(recent).toHaveLength(10);
  });
});

describe('Report Store', () => {
  beforeEach(() => {
    reportStore.set({
      reports: [],
      currentReport: null,
      generating: false,
      error: null,
      jobId: null,
      progress: 0,
    });
  });

  it('should initialize empty report store', async () => {
    let state: any;
    reportStore.subscribe((s) => {
      state = s;
    })();

    expect(state.reports).toEqual([]);
    expect(state.generating).toBe(false);
  });

  it('should start report generation', async () => {
    startReportGeneration('job-123');

    let state: any;
    reportStore.subscribe((s) => {
      state = s;
    })();

    expect(state.generating).toBe(true);
    expect(state.jobId).toBe('job-123');
    expect(state.progress).toBe(0);
  });

  it('should update report progress', async () => {
    startReportGeneration('job-123');
    updateReportProgress(50);

    let state: any;
    reportStore.subscribe((s) => {
      state = s;
    })();

    expect(state.progress).toBe(50);
  });

  it('should complete report generation', async () => {
    startReportGeneration('job-123');
    completeReportGeneration();

    let state: any;
    reportStore.subscribe((s) => {
      state = s;
    })();

    expect(state.generating).toBe(false);
    expect(state.progress).toBe(100);
  });

  it('should set report error', async () => {
    startReportGeneration('job-123');
    setReportError('Generation failed');

    let state: any;
    reportStore.subscribe((s) => {
      state = s;
    })();

    expect(state.error).toBe('Generation failed');
    expect(state.generating).toBe(false);
  });
});

describe('UI Store', () => {
  beforeEach(() => {
    localStorageMock.clear();
    uiStore.set({
      theme: 'light',
      sidebarOpen: true,
      notifications: [],
      modal: {
        isOpen: false,
      },
    });
  });

  it('should initialize with light theme', async () => {
    let state: any;
    uiStore.subscribe((s) => {
      state = s;
    })();

    expect(state.theme).toBe('light');
  });

  it('should toggle theme', async () => {
    toggleTheme();

    let state: any;
    uiStore.subscribe((s) => {
      state = s;
    })();

    expect(state.theme).toBe('dark');

    toggleTheme();

    uiStore.subscribe((s) => {
      state = s;
    })();

    expect(state.theme).toBe('light');
  });

  it('should set theme explicitly', async () => {
    setTheme('dark');

    let state: any;
    uiStore.subscribe((s) => {
      state = s;
    })();

    expect(state.theme).toBe('dark');
  });

  it('should toggle sidebar', async () => {
    toggleSidebar();

    let state: any;
    uiStore.subscribe((s) => {
      state = s;
    })();

    expect(state.sidebarOpen).toBe(false);
  });

  it('should add notification', async () => {
    const id = addNotification({
      type: 'info',
      message: 'Test notification',
      duration: 5000,
    });

    let state: any;
    uiStore.subscribe((s) => {
      state = s;
    })();

    expect(state.notifications).toHaveLength(1);
    expect(state.notifications[0].message).toBe('Test notification');
  });

  it('should dismiss notification', async () => {
    const id = addNotification({
      type: 'info',
      message: 'Test notification',
    });

    dismissNotification(id);

    let state: any;
    uiStore.subscribe((s) => {
      state = s;
    })();

    expect(state.notifications).toHaveLength(0);
  });

  it('should clear all notifications', async () => {
    addNotification({
      type: 'info',
      message: 'Notification 1',
    });
    addNotification({
      type: 'info',
      message: 'Notification 2',
    });

    let state: any;
    uiStore.subscribe((s) => {
      state = s;
    })();

    expect(state.notifications).toHaveLength(2);

    clearNotifications();

    uiStore.subscribe((s) => {
      state = s;
    })();

    expect(state.notifications).toHaveLength(0);
  });

  it('should open modal', async () => {
    openModal('Test Title', 'Test content', 'info');

    let state: any;
    uiStore.subscribe((s) => {
      state = s;
    })();

    expect(state.modal.isOpen).toBe(true);
    expect(state.modal.title).toBe('Test Title');
  });

  it('should close modal', async () => {
    openModal('Test', 'Content');
    closeModal();

    let state: any;
    uiStore.subscribe((s) => {
      state = s;
    })();

    expect(state.modal.isOpen).toBe(false);
  });
});

describe('Derived Stores', () => {
  beforeEach(() => {
    clearMessages();
    clearQueries();
    setMessageLoading(false);
    setQueryLoading(false);
  });

  it('should combine loading states', async () => {
    let loading: boolean;
    isLoading.subscribe((l) => {
      loading = l;
    })();

    expect(loading).toBe(false);

    setMessageLoading(true);

    isLoading.subscribe((l) => {
      loading = l;
    })();

    expect(loading).toBe(true);
  });

  it('should combine error states', async () => {
    let error: string | null;
    currentError.subscribe((e) => {
      error = e;
    })();

    expect(error).toBe(null);

    setMessageError('Message error');

    currentError.subscribe((e) => {
      error = e;
    })();

    expect(error).toBe('Message error');
  });
});

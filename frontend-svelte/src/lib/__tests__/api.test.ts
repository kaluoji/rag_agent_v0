/**
 * Unit tests for API client
 * Tests fetch logic, error handling, retry mechanisms, and timeouts
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  get,
  post,
  put,
  deleteRequest,
  patch,
  processQuery,
  getQueryHistory,
  getQuery,
  deleteQueryAPI,
  generateReport,
  getReportStatus,
  downloadReport,
  uploadFile,
  searchQueries,
  healthCheck,
  getConfig,
} from '../api';

// Mock fetch globally
global.fetch = vi.fn();

// Mock environment variables
vi.stubGlobal('import', {
  meta: {
    env: {
      VITE_API_URL: 'http://localhost:8000',
    },
  },
});

const mockFetch = global.fetch as any;

describe('API Client - Utility Functions', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should handle successful GET request', async () => {
    const mockData = { id: '1', name: 'Test' };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify(mockData),
    });

    const result = await get('/api/test');

    expect(result.status).toBe(200);
    expect(result.data).toEqual(mockData);
    expect(result.error).toBeUndefined();
  });

  it('should handle successful POST request', async () => {
    const mockData = { id: '1', created: true };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 201,
      text: async () => JSON.stringify(mockData),
    });

    const result = await post('/api/test', { name: 'Test' });

    expect(result.status).toBe(201);
    expect(result.data).toEqual(mockData);
  });

  it('should handle successful PUT request', async () => {
    const mockData = { id: '1', updated: true };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify(mockData),
    });

    const result = await put('/api/test/1', { name: 'Updated' });

    expect(result.status).toBe(200);
    expect(result.data).toEqual(mockData);
  });

  it('should handle successful DELETE request', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 204,
      text: async () => '',
    });

    const result = await deleteRequest('/api/test/1');

    expect(result.status).toBe(204);
  });

  it('should handle successful PATCH request', async () => {
    const mockData = { id: '1', patched: true };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify(mockData),
    });

    const result = await patch('/api/test/1', { name: 'Patched' });

    expect(result.status).toBe(200);
    expect(result.data).toEqual(mockData);
  });
});

describe('API Client - Error Handling', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should handle 400 Bad Request', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      text: async () => JSON.stringify({ message: 'Bad request' }),
    });

    const result = await get('/api/test');

    expect(result.status).toBe(400);
    expect(result.error).toBeDefined();
    expect(result.error?.statusCode).toBe(400);
    expect(result.error?.message).toBe('Bad request');
  });

  it('should handle 401 Unauthorized', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      text: async () => JSON.stringify({ message: 'Unauthorized' }),
    });

    const result = await get('/api/protected');

    expect(result.error?.statusCode).toBe(401);
  });

  it('should handle 403 Forbidden', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 403,
      text: async () => JSON.stringify({ message: 'Forbidden' }),
    });

    const result = await get('/api/forbidden');

    expect(result.error?.statusCode).toBe(403);
  });

  it('should handle 404 Not Found', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      text: async () => JSON.stringify({ message: 'Not found' }),
    });

    const result = await get('/api/missing');

    expect(result.error?.statusCode).toBe(404);
  });

  it('should handle 500 Internal Server Error', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      text: async () => JSON.stringify({ message: 'Internal server error' }),
    });

    const result = await get('/api/error');

    expect(result.error?.statusCode).toBe(500);
  });

  it('should handle network error', async () => {
    mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'));

    const result = await get('/api/test', { retry: 0 });

    expect(result.error).toBeDefined();
    expect(result.error?.error).toBe('NETWORK_ERROR');
  });

  it('should handle empty response body', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => '',
    });

    const result = await get('/api/test');

    expect(result.status).toBe(200);
    expect(result.data).toEqual({});
  });

  it('should handle malformed JSON response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => '{invalid json}',
    });

    const result = await get('/api/test');

    expect(result.status).toBe(200);
    expect(result.data).toEqual({});
  });
});

describe('API Client - Retry Logic', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should retry on 429 (Too Many Requests)', async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: false,
        status: 429,
        text: async () => JSON.stringify({ message: 'Too many requests' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ data: 'success' }),
      });

    const promise = get('/api/test', { retry: 1 });
    vi.runAllTimersAsync();
    const result = await promise;

    expect(mockFetch).toHaveBeenCalledTimes(2);
    expect(result.data).toEqual({ data: 'success' });
  });

  it('should retry on 5xx errors', async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: false,
        status: 503,
        text: async () => JSON.stringify({ message: 'Service unavailable' }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ data: 'recovered' }),
      });

    const promise = get('/api/test', { retry: 1 });
    vi.runAllTimersAsync();
    const result = await promise;

    expect(mockFetch).toHaveBeenCalledTimes(2);
    expect(result.data).toEqual({ data: 'recovered' });
  });

  it('should not retry on 4xx errors', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      text: async () => JSON.stringify({ message: 'Bad request' }),
    });

    const result = await get('/api/test', { retry: 3 });

    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(result.error?.statusCode).toBe(400);
  });

  it('should respect max retries limit', async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: false,
        status: 503,
        text: async () => JSON.stringify({ message: 'Error 1' }),
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 503,
        text: async () => JSON.stringify({ message: 'Error 2' }),
      });

    const promise = get('/api/test', { retry: 1 });
    vi.runAllTimersAsync();
    const result = await promise;

    expect(mockFetch).toHaveBeenCalledTimes(2);
    expect(result.error?.statusCode).toBe(503);
  });
});

describe('API Client - Timeout', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should timeout on slow requests', async () => {
    const abortSpy = vi.fn();

    mockFetch.mockImplementation((_url: string, options: RequestInit) => {
      return new Promise((resolve) => {
        // Simulate slow response
        setTimeout(() => {
          resolve({
            ok: true,
            status: 200,
            text: async () => JSON.stringify({ data: 'late' }),
          });
        }, 50000); // 50 seconds

        // Abort should be called
        if (options.signal) {
          (options.signal as AbortSignal).addEventListener('abort', abortSpy);
        }
      });
    });

    const promise = get('/api/test', { timeout: 1000, retry: 0 });
    vi.advanceTimersByTime(1100);

    const result = await promise;

    // Timeout should cause an error or abort
    expect(result.error).toBeDefined();
  });
});

describe('API Endpoints', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should process query', async () => {
    const mockResult = {
      status: 'success',
      data: { analysis: 'result' },
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify(mockResult),
    });

    const result = await processQuery('Test query', 'banking');

    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/query',
      expect.objectContaining({
        method: 'POST',
      })
    );
  });

  it('should get query history', async () => {
    const mockQueries = {
      items: [],
      total: 0,
      page: 1,
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify(mockQueries),
    });

    const result = await getQueryHistory(1, 20);

    expect(result.status).toBe(200);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/queries?page=1&pageSize=20'),
      expect.any(Object)
    );
  });

  it('should get single query', async () => {
    const mockQuery = {
      id: '123',
      text: 'Test query',
      status: 'completed',
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify(mockQuery),
    });

    const result = await getQuery('123');

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/queries/123'),
      expect.any(Object)
    );
  });

  it('should delete query', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({ success: true }),
    });

    const result = await deleteQueryAPI('123');

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/queries/123'),
      expect.objectContaining({
        method: 'DELETE',
      })
    );
  });

  it('should generate report', async () => {
    const mockResponse = {
      jobId: 'job-123',
      status: 'processing',
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify(mockResponse),
    });

    const result = await generateReport('123', {
      title: 'Test Report',
      format: 'docx',
    });

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/reports/generate'),
      expect.objectContaining({
        method: 'POST',
      })
    );
  });

  it('should get report status', async () => {
    const mockStatus = {
      jobId: 'job-123',
      status: 'completed',
      progress: 100,
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify(mockStatus),
    });

    const result = await getReportStatus('job-123');

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/reports/status/job-123'),
      expect.any(Object)
    );
  });

  it('should search queries', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({ items: [], total: 0 }),
    });

    const result = await searchQueries('GDPR', {
      sector: 'banking',
      type: 'compliance',
    });

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/queries/search?'),
      expect.any(Object)
    );
  });

  it('should perform health check', async () => {
    const mockHealth = {
      status: 'healthy',
      version: '1.0.0',
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify(mockHealth),
    });

    const result = await healthCheck();

    expect(result.data).toEqual(mockHealth);
  });

  it('should get API configuration', async () => {
    const mockConfig = {
      version: '1.0.0',
      supportedSectors: ['banking', 'insurance'],
      supportedAnalysisTypes: ['compliance', 'gap-analysis'],
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () => JSON.stringify(mockConfig),
    });

    const result = await getConfig();

    expect(result.data?.supportedSectors).toContain('banking');
  });
});

describe('API Client - File Operations', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should download report file', async () => {
    const mockBlob = new Blob(['file content'], {
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    });

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      blob: async () => mockBlob,
    });

    const result = await downloadReport('report-123');

    expect(result.blob).toEqual(mockBlob);
    expect(result.error).toBeUndefined();
  });

  it('should upload file', async () => {
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });

    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      text: async () =>
        JSON.stringify({
          fileId: 'file-123',
          fileName: 'test.pdf',
        }),
    });

    const result = await uploadFile(file, 'banking');

    expect(result.data?.fileId).toBe('file-123');
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/upload'),
      expect.objectContaining({
        method: 'POST',
      })
    );
  });

  it('should handle download error', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      text: async () => JSON.stringify({ message: 'Not found' }),
    });

    const result = await downloadReport('missing-report');

    expect(result.error).toBeDefined();
    expect(result.error?.statusCode).toBe(404);
  });

  it('should handle upload error', async () => {
    const file = new File(['test'], 'test.pdf');

    mockFetch.mockRejectedValueOnce(new Error('Upload failed'));

    const result = await uploadFile(file);

    expect(result.error).toBeDefined();
    expect(result.error?.error).toBe('UPLOAD_ERROR');
  });
});

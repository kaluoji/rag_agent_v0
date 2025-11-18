# Svelte+TypeScript Frontend - Developer Quick Reference

## Project Structure

```
frontend-svelte/
├── src/
│   ├── lib/                          # Core libraries
│   │   ├── types.ts                  # All TypeScript interfaces
│   │   ├── stores.ts                 # Svelte stores with actions
│   │   ├── api.ts                    # HTTP client
│   │   ├── websocket.ts              # WebSocket client
│   │   └── utils.ts                  # Utility functions
│   ├── components/                   # Reusable components (to be created)
│   ├── routes/                       # Page routes
│   │   ├── +layout.svelte            # Root layout
│   │   ├── +layout.server.ts         # Server loader
│   │   └── +page.svelte              # Home page (to be created)
│   ├── app.css                       # Global styles
│   ├── app.html                      # Root HTML
│   └── main.js                       # Entry point
├── svelte.config.js                  # SvelteKit config
├── vite.config.ts                    # Vite config
├── tsconfig.json                     # TypeScript config
├── tailwind.config.js                # Tailwind config
├── postcss.config.js                 # PostCSS config
└── package.json                      # Dependencies
```

---

## Quick Start

### Import Patterns

```typescript
// Types
import type { Message, Query, OrchestrationResult } from '$lib/types';

// Stores
import { messageStore, addMessage, messageCount } from '$lib/stores';
import { queryStore, addQuery, filteredQueries } from '$lib/stores';
import { reportStore, startReportGeneration } from '$lib/stores';
import { uiStore, toggleTheme, addNotification } from '$lib/stores';

// API
import { processQuery, getQueryHistory, generateReport } from '$lib/api';

// WebSocket
import { getWSClient, initWebSocket } from '$lib/websocket';

// Utilities
import {
  formatTimestamp,
  calculateReadingTime,
  downloadFile,
  delay
} from '$lib/utils';
```

---

## Common Tasks

### 1. Display Messages from Store

```svelte
<script lang="ts">
  import { messageStore } from '$lib/stores';
  import { formatTimestamp } from '$lib/utils';
  import type { Message } from '$lib/types';

  let messages: Message[] = [];

  messageStore.subscribe(state => {
    messages = state.messages;
  });
</script>

{#each messages as message (message.id)}
  <div class="message {message.role}">
    <div class="content">{message.content}</div>
    <span class="timestamp">
      {formatTimestamp(message.timestamp, 'time')}
    </span>
  </div>
{/each}
```

### 2. Process User Query

```svelte
<script lang="ts">
  import { addMessage, setMessageLoading, setMessageError } from '$lib/stores';
  import { processQuery } from '$lib/api';
  import type { Message } from '$lib/types';

  async function handleQuery(text: string) {
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    };

    addMessage(userMessage);
    setMessageLoading(true);

    try {
      const result = await processQuery(text, 'banking');

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: result.data?.analysis || 'No analysis available',
        timestamp: new Date(),
        sources: result.data?.sources,
      };

      addMessage(assistantMessage);
    } catch (error) {
      setMessageError(error instanceof Error ? error.message : 'Unknown error');
    } finally {
      setMessageLoading(false);
    }
  }
</script>

<input
  type="text"
  on:change={e => handleQuery(e.currentTarget.value)}
  placeholder="Ask a regulatory question..."
/>
```

### 3. Generate Report with Real-time Progress

```svelte
<script lang="ts">
  import { startReportGeneration, updateReportProgress, completeReportGeneration } from '$lib/stores';
  import { generateReport } from '$lib/api';
  import { getWSClient } from '$lib/websocket';
  import type { ReportRequest } from '$lib/types';

  async function handleGenerateReport(queryId: string) {
    const options: ReportRequest = {
      query: 'What are GDPR requirements?',
      analysisType: 'comprehensive',
      sector: 'banking',
    };

    const response = await generateReport(queryId, options);

    if (response.data?.jobId) {
      const jobId = response.data.jobId;
      startReportGeneration(jobId);

      // Subscribe to progress updates
      const ws = getWSClient();

      ws.onReportProgress(jobId, (update) => {
        updateReportProgress(update.progress ?? 0);
        console.log(`Report: ${update.stage} - ${update.progress}%`);
      });

      ws.onReportComplete(jobId, (path) => {
        completeReportGeneration();
        console.log('Report ready:', path);
      });

      ws.onReportError(jobId, (error) => {
        console.error('Report error:', error);
      });
    }
  }
</script>
```

### 4. Filter Query History

```svelte
<script lang="ts">
  import { setSelectedSector, setSelectedType, filteredQueries } from '$lib/stores';

  function filterBySector(sector: string) {
    setSelectedSector(sector);
  }

  function filterByType(type: 'compliance' | 'gap-analysis' | 'report') {
    setSelectedType(type);
  }
</script>

<select on:change={e => filterBySector(e.currentTarget.value)}>
  <option value="">All sectors</option>
  <option value="banking">Banking</option>
  <option value="insurance">Insurance</option>
</select>

{#each $filteredQueries as query (query.id)}
  <div class="query-item">
    <h3>{query.text}</h3>
    <p>{query.sector} - {query.type}</p>
  </div>
{/each}
```

### 5. Show Notifications

```svelte
<script lang="ts">
  import { addNotification } from '$lib/stores';

  function handleSuccess() {
    addNotification({
      type: 'success',
      message: 'Report generated successfully!',
      duration: 3000,
    });
  }

  function handleError() {
    addNotification({
      type: 'error',
      message: 'Failed to process query. Please try again.',
      duration: 5000,
    });
  }

  function handleWithAction() {
    addNotification({
      type: 'info',
      message: 'Would you like to download this report?',
      duration: 0, // No auto-dismiss
      action: {
        label: 'Download',
        callback: () => {
          console.log('Downloading...');
        },
      },
    });
  }
</script>

<button on:click={handleSuccess}>Success</button>
<button on:click={handleError}>Error</button>
<button on:click={handleWithAction}>With Action</button>
```

### 6. Dark Mode Support

```svelte
<script lang="ts">
  import { uiStore, toggleTheme } from '$lib/stores';

  let theme: 'light' | 'dark' = 'light';

  uiStore.subscribe(state => {
    theme = state.theme;
  });
</script>

<button on:click={toggleTheme}>
  {theme === 'light' ? 'Dark Mode' : 'Light Mode'}
</button>

<style>
  /* Colors automatically adapt based on CSS variables */
  button {
    color: var(--color-text-primary);
    background-color: var(--color-bg-elevated);
  }
</style>
```

### 7. Download File

```svelte
<script lang="ts">
  import { downloadFile } from '$lib/utils';

  async function handleDownloadReport(reportId: string) {
    const response = await fetch(`/api/reports/${reportId}/download`);
    const blob = await response.blob();
    downloadFile(blob, 'report.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document');
  }
</script>
```

---

## Store API Reference

### messageStore

```typescript
// Read
let state = messageStore;  // Writable<ChatStoreState>

// Write
addMessage(message: Message)
clearMessages()
setMessageLoading(loading: boolean)
setMessageError(error: string | null)

// Derived
$latestMessage: Message | null
$messageCount: number
```

### queryStore

```typescript
// Read
let state = queryStore;  // Writable<QueryStoreState>

// Write
addQuery(query: Query)
updateCurrentQuery(query: Query)
setCurrentQuery(queryId: string | null)
deleteQuery(queryId: string)
clearQueries()
setQueryLoading(loading: boolean)
setQueryError(error: string | null)
setSelectedSector(sector: string | null)
setSelectedType(type: Query['type'] | null)

// Derived
$filteredQueries: Query[]
$recentQueries: Query[]
$queryCount: number
```

### reportStore

```typescript
// Read
let state = reportStore;  // Writable<ReportStoreState>

// Write
addReport(report: Query & { artifact? })
updateCurrentReport(report: Query & { artifact? })
setCurrentReport(reportId: string | null)
deleteReport(reportId: string)
startReportGeneration(jobId: string)
updateReportProgress(progress: number)
completeReportGeneration()
setReportError(error: string | null)

// Derived
$reportCount: number
```

### uiStore

```typescript
// Read
let state = uiStore;  // Writable<UIStoreState>

// Write
toggleTheme()
setTheme(theme: 'light' | 'dark')
toggleSidebar()
setSidebarOpen(open: boolean)
addNotification(notification: Omit<Notification, 'id'>): string
dismissNotification(id: string)
clearNotifications()
openModal(title: string, content: string, type?: 'confirm' | 'alert' | 'info')
closeModal()

// Derived
$notificationCount: number
```

---

## API Methods

### Query Operations

```typescript
// Process query
const result = await processQuery(text: string, sector?: string);
// Returns: APIResponse<OrchestrationResult>

// Get query history
const result = await getQueryHistory(page?: number, pageSize?: number);
// Returns: APIResponse<PaginatedResponse<Query>>

// Get single query
const result = await getQuery(queryId: string);
// Returns: APIResponse<Query>

// Delete query
const result = await deleteQueryAPI(queryId: string);
// Returns: APIResponse<{ success: boolean }>

// Search queries
const result = await searchQueries(text: string, filters?: {
  sector?: string;
  type?: string;
  startDate?: Date;
  endDate?: Date;
});
// Returns: APIResponse<PaginatedResponse<Query>>
```

### Report Operations

```typescript
// Generate report
const result = await generateReport(queryId: string, options: ReportRequest);
// Returns: APIResponse<ReportJobResponse>

// Get report status
const result = await getReportStatus(jobId: string);
// Returns: APIResponse<ReportJobResponse>

// Download report
const result = await downloadReport(reportId: string);
// Returns: { blob?: Blob; error?: APIError; status: number }
```

### File Operations

```typescript
// Upload file
const result = await uploadFile(file: File, sector?: string);
// Returns: APIResponse<{ fileId: string; fileName: string }>

// Health check
const result = await healthCheck();
// Returns: APIResponse<{ status: string; version?: string }>

// Get config
const result = await getConfig();
// Returns: APIResponse<{
//   version: string;
//   supportedSectors: string[];
//   supportedAnalysisTypes: string[];
// }>
```

---

## WebSocket API Reference

### Connection

```typescript
const ws = getWSClient();
await initWebSocket();
ws.disconnect();
```

### Methods

```typescript
ws.send(type: string, data?: unknown)
ws.on<T>(type: string, handler: (data: T) => void): () => void
ws.once<T>(type: string, handler: (data: T) => void)
ws.isConnected(): boolean
ws.getReadyState(): 'CONNECTING' | 'OPEN' | 'CLOSING' | 'CLOSED'
```

### Event Subscriptions for Reports

```typescript
// Subscribe to progress
const unsubscribe = ws.onReportProgress(jobId, (update: ReportProgressUpdate) => {
  console.log(`Progress: ${update.progress}%`);
  console.log(`Stage: ${update.stage}`);
});

// Subscribe to completion
ws.onReportComplete(jobId, (path: string) => {
  console.log('Report ready at:', path);
});

// Subscribe to error
ws.onReportError(jobId, (error: string) => {
  console.error('Report failed:', error);
});

// Unsubscribe
unsubscribe();
```

---

## Utility Functions

### Text Formatting

```typescript
formatTimestamp(date: Date, format?: 'short' | 'long' | 'time'): string
formatFileSize(bytes: number): string
truncateText(text: string, maxLength: number, suffix?: string): string
extractMarkdown(content: string): string
calculateReadingTime(text: string): number
highlightSyntax(code: string, language?: string): string
escapeHTML(text: string): string
```

### Document Handling

```typescript
parseDocxContent(docxBuffer: ArrayBuffer): Promise<string>
arrayBufferToBase64(buffer: ArrayBuffer): string
base64ToArrayBuffer(base64: string): ArrayBuffer
blobToArrayBuffer(blob: Blob): Promise<ArrayBuffer>
blobToDataUrl(blob: Blob): Promise<string>
downloadFile(data: Blob | string, filename: string, mimeType?: string): void
```

### Array Operations

```typescript
removeDuplicates<T>(array: T[], key?: keyof T): T[]
groupBy<T>(array: T[], key: keyof T): Record<string, T[]>
flatten<T>(array: (T | T[])[]): T[]
```

### Validation

```typescript
isValidEmail(email: string): boolean
isValidURL(url: string): boolean
isImageFile(file: File): boolean
isPdfFile(file: File): boolean
isDocxFile(file: File): boolean
```

### Async Utilities

```typescript
delay(ms: number): Promise<void>
retryAsync<T>(
  fn: () => Promise<T>,
  options?: {
    maxAttempts?: number;
    initialDelay?: number;
    maxDelay?: number;
    backoffMultiplier?: number;
  }
): Promise<T>
withTimeout<T>(
  promise: Promise<T>,
  timeoutMs: number,
  timeoutError?: Error
): Promise<T>
```

### Object Operations

```typescript
deepClone<T>(obj: T): T
deepMerge<T extends Record<string, any>>(target: T, ...sources: any[]): T
```

---

## Styling Guide

### CSS Variables (Light Mode)

```css
/* Primary Colors */
--color-primary: #00548f
--color-primary-light: #0073b7
--color-primary-dark: #003d66

/* Secondary Colors */
--color-secondary: #4d0a2e
--color-secondary-light: #6b1141

/* Backgrounds */
--color-bg: #f5f7fa
--color-bg-alt: #fafbfc
--color-bg-elevated: #ffffff

/* Text Colors */
--color-text-primary: #1a1a1a
--color-text-secondary: #666666
--color-text-tertiary: #999999
--color-text-inverse: #ffffff

/* Semantic */
--color-success: #10b981
--color-warning: #f59e0b
--color-error: #ef4444
--color-info: #3b82f6

/* Shadows */
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05)
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1)
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1)
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1)
```

### Button Classes

```html
<button class="btn-primary">Primary Action</button>
<button class="btn-secondary">Secondary Action</button>
<button class="btn-danger">Danger Action</button>
```

### Utility Classes

```html
<!-- Text overflow -->
<div class="truncate">Text with ellipsis...</div>
<div class="line-clamp-2">Multi-line text...</div>

<!-- Shadows -->
<div class="shadow-elevated">Elevated card</div>

<!-- Animations -->
<div class="animate-spin">Loading...</div>
<div class="animate-pulse">Pulsing</div>
<div class="animate-fadeIn">Fading in</div>
<div class="animate-slideInUp">Sliding up</div>
```

### Markdown Styling

```html
<div class="prose">
  <h1>Title</h1>
  <p>Paragraph</p>
  <code>inline code</code>
  <pre><code>code block</code></pre>
  <blockquote>Quote</blockquote>
</div>
```

---

## Error Handling Pattern

```typescript
import type { APIError } from '$lib/types';

// Check for errors in API responses
const response = await processQuery(text);

if (response.error) {
  const error: APIError = response.error;

  console.error(`Error [${error.statusCode}]: ${error.message}`);

  if (error.statusCode === 401) {
    // Handle authentication error
  } else if (error.statusCode === 429) {
    // Handle rate limiting
  } else if (error.statusCode >= 500) {
    // Handle server error
  }
} else {
  // Use response.data
  const analysis = response.data?.analysis;
}
```

---

## TypeScript Tips

### Type-safe Store Subscriptions

```svelte
<script lang="ts">
  import { messageStore } from '$lib/stores';
  import type { ChatStoreState } from '$lib/types';

  let state: ChatStoreState;

  const unsubscribe = messageStore.subscribe(s => {
    state = s;
    // state.messages is typed as Message[]
    // state.loading is typed as boolean
  });

  onDestroy(unsubscribe);
</script>
```

### Type-safe API Responses

```typescript
import type { OrchestrationResult, APIError } from '$lib/types';
import type { APIResponse } from '$lib/api';

const response: APIResponse<OrchestrationResult> = await processQuery(text);

if (response.error) {
  // error is typed as APIError
  console.error(response.error.message);
} else {
  // data is typed as OrchestrationResult
  console.log(response.data?.analysis);
}
```

---

## Performance Tips

1. **Use Derived Stores** for computed values
   ```typescript
   export const messageCount = derived(messageStore, $ => $.messages.length);
   ```

2. **Unsubscribe from stores** in onDestroy
   ```typescript
   const unsub = messageStore.subscribe(...);
   onDestroy(() => unsub());
   ```

3. **Use svelte:window** for global events
   ```svelte
   <svelte:window on:resize={handleResize} />
   ```

4. **Lazy load components**
   ```typescript
   import { lazy } from 'svelte';
   const ReportViewer = lazy(() => import('./ReportViewer.svelte'));
   ```

5. **Use IndexedDB** for large datasets
   ```typescript
   // Consider for large query history
   ```

---

## Debugging

### Console Logging

```typescript
import { log } from '$lib/utils';

log('log', 'User query submitted', { text, sector });
log('warn', 'Slow API response', { duration: 3000 });
log('error', 'Failed to generate report', error);
```

### Component State Inspection

```svelte
<script>
  import { messageStore, queryStore, reportStore, uiStore } from '$lib/stores';
</script>

<!-- Display store state in dev mode -->
{#if import.meta.env.DEV}
  <pre>{JSON.stringify({
    messages: $messageStore,
    queries: $queryStore,
    reports: $reportStore,
    ui: $uiStore
  }, null, 2)}</pre>
{/if}
```

### Network Inspector

All API requests are logged to console with:
- Request method and endpoint
- Request payload (if any)
- Response status and data
- Retry attempts and timing

---

**Last Updated**: November 17, 2025

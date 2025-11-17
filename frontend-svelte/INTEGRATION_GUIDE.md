# Svelte Frontend Integration Guide

## Quick Start

### Prerequisites

- Node.js 18+ installed
- Backend API running on `http://localhost:8000`
- SvelteKit configured with default adapter

### Installation

```bash
cd frontend-svelte

# Install dependencies
npm install

# Create .env.local file
echo 'VITE_API_URL=http://localhost:8000' > .env.local

# Start development server
npm run dev
```

Frontend will be available at `http://localhost:5173`

---

## Architecture Overview

```
Frontend (Svelte)
    ↓
SvelteKit Routes (/api/*)
    ↓ (proxy forward)
Backend FastAPI
    ↓ (response)
SvelteKit Routes
    ↓ (translate errors)
Frontend (components)
```

### Data Flow Examples

**Query Processing:**
```
1. User types query in ChatInterface
2. Frontend calls POST /api/query
3. SvelteKit validates and forwards to backend /query
4. Backend returns OrchestrationResult
5. Frontend displays analysis in chat
```

**Report Generation:**
```
1. User clicks "Generate Report"
2. Frontend POST /api/report with options
3. SvelteKit forwards to backend /api/reports/generate
4. Backend returns jobId (async processing)
5. Frontend polls GET /api/report?jobId=xxx
6. When complete, user downloads report
```

---

## File Organization

### Pages (Content)
```
src/routes/
├── +page.svelte                  # Home - chat interface
├── historial/+page.svelte        # History - list all queries
├── consulta/[id]/+page.svelte    # Detail - single query analysis
└── novedades/+page.svelte        # News - regulatory updates
```

### API Routes (Backend Proxy)
```
src/routes/api/
├── query/+server.ts              # Process new queries
├── report/+server.ts             # Generate reports
├── file/+server.ts               # Upload/download files
└── history/+server.ts            # Query history management
```

### Server Load Functions
```
src/routes/
├── +page.server.ts               # Load recent queries
├── historial/+page.server.ts     # Load all queries
├── consulta/[id]/+page.server.ts # Load specific query
└── novedades/+page.server.ts     # Load news items
```

---

## Key Features

### 1. Server-Side Rendering (SSR)

All pages support SSR with `+page.server.ts` functions:

```typescript
export const load: PageServerLoad = async ({ params }) => {
  const data = await fetchFromBackend();
  return data; // Available as page data
};
```

**Benefits:**
- Faster initial page load
- SEO friendly
- Pre-loaded data
- Better performance on slow networks

### 2. Type Safety

Full TypeScript support with types from `$lib/types.ts`:

```typescript
// All data is properly typed
const query: Query = {};
const result: OrchestrationResult = {};
const error: APIError = {};
```

### 3. Error Handling

Consistent error handling across all routes:

```typescript
// Request validation
if (!body.query) return error(400, "Query required");

// Network errors
try {
  const response = await fetch(url);
} catch (error) {
  // Handle timeout, network error
}

// Backend errors
if (!response.ok) {
  return error(response.status, errorData.message);
}
```

### 4. Accessibility (WCAG 2.1 AA)

Every page includes:
- Semantic HTML
- ARIA labels
- Keyboard navigation
- Screen reader support
- Focus management
- Color contrast compliance

Example:
```svelte
<div role="search" aria-label="Search queries">
  <input
    type="text"
    aria-label="Search term"
    on:input={handleSearch}
  />
</div>
```

### 5. Responsive Design

Mobile-first approach with breakpoints:
- **480px** - Phones
- **768px** - Tablets
- **1024px** - Large tablets
- **1200px+** - Desktop

```svelte
<style>
  @media (max-width: 768px) {
    /* Tablet and mobile styles */
  }

  @media (max-width: 480px) {
    /* Mobile-only styles */
  }
</style>
```

### 6. Dark Mode

Automatic dark mode support via CSS variables:

```css
:root {
  --color-primary: #0054 8f;
  --color-bg: #ffffff;
  --color-text-primary: #0f172a;
}

[data-theme='dark'] {
  --color-primary: #93c5fd;
  --color-bg: #0f172a;
  --color-text-primary: #f1f5f9;
}
```

Theme toggle in `+layout.svelte` updates `data-theme` attribute on `<html>`.

---

## API Integration

### Query Processing

**Frontend Action:**
```svelte
<script>
  import { processQuery } from '$lib/api';

  async function sendQuery(text: string) {
    const result = await processQuery(text, 'banking');
    if (result.error) {
      // Handle error
    } else {
      // Display result.data
    }
  }
</script>
```

**Route Handler:**
```typescript
// POST /api/query
export const POST: RequestHandler = async ({ request }) => {
  const body = await request.json();

  // Validate
  if (!body.query) return error(400, 'Query required');

  // Forward to backend
  const response = await fetch(`${API_BASE_URL}/query`, {
    method: 'POST',
    body: JSON.stringify(body)
  });

  // Handle errors and return
  return new Response(await response.json());
};
```

### Report Generation

**Frontend Action:**
```svelte
<script>
  import { generateReport } from '$lib/api';

  async function startReport() {
    const result = await generateReport(queryId, {
      analysisType: 'comprehensive',
      sector: 'banking'
    });

    if (result.data?.jobId) {
      // Start polling for status
      pollReportStatus(result.data.jobId);
    }
  }
</script>
```

**Route Handler:**
```typescript
// POST /api/report
export const POST: RequestHandler = async ({ request }) => {
  const body = await request.json();

  // Forward to backend /api/reports/generate
  const response = await fetch(
    `${API_BASE_URL}/api/reports/generate`,
    { method: 'POST', body: JSON.stringify(body) }
  );

  return new Response(await response.json());
};
```

### History Management

**Frontend Action:**
```svelte
<script>
  import { getQueryHistory, deleteQueryAPI } from '$lib/api';

  async function loadHistory() {
    const result = await getQueryHistory(1, 20);
    // Display result.data.data and result.data.meta
  }

  async function removeQuery(id: string) {
    const result = await deleteQueryAPI(id);
  }
</script>
```

**Route Handler:**
```typescript
// GET /api/history?page=1&pageSize=20
export const GET: RequestHandler = async ({ url }) => {
  const page = url.searchParams.get('page') || '1';
  const pageSize = url.searchParams.get('pageSize') || '20';

  // Forward with all parameters
  const response = await fetch(
    `${API_BASE_URL}/api/queries?page=${page}&pageSize=${pageSize}`
  );

  return new Response(await response.json());
};
```

---

## Environment Setup

### Development

```bash
# .env.local (git-ignored)
VITE_API_URL=http://localhost:8000
```

### Production

```bash
# Build
npm run build

# Environment variables set at runtime
export VITE_API_URL=https://api.example.com
node build
```

### Docker

```dockerfile
FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Build
COPY . .
RUN npm run build

# Runtime environment
ENV VITE_API_URL=http://backend:8000

EXPOSE 3000

CMD ["node", "build"]
```

---

## Component Integration

### Using Pages with Components

**Example: ChatInterface in main page**

```svelte
<!-- src/routes/+page.svelte -->
<script>
  import ChatInterface from '$lib/components/ChatInterface.svelte';
  import type { PageData } from './$types';

  export let data: PageData;

  // data includes recentQueries from +page.server.ts
</script>

<ChatInterface recentQueries={data.recentQueries} />
```

### Passing Data from Server

**Server load function:**
```typescript
// src/routes/historial/+page.server.ts
export const load: PageServerLoad = async () => {
  const queries = await fetchQueries();
  return { queries };
};
```

**Page component:**
```svelte
<!-- src/routes/historial/+page.svelte -->
<script lang="ts">
  import type { PageData } from './$types';

  export let data: PageData;

  $: queries = data.queries;
</script>

{#each queries as query}
  <!-- render -->
{/each}
```

---

## Store Integration

### Using Stores in Routes

All pages can access stores:

```svelte
<script>
  import {
    messageStore,
    queryStore,
    uiStore,
    addNotification
  } from '$lib/stores';

  // Subscribe to stores
  let messages: Message[] = [];
  const unsubscribe = messageStore.subscribe(state => {
    messages = state.messages;
  });

  // Dispatch actions
  addNotification({
    type: 'success',
    message: 'Query processed!',
    duration: 3000
  });
</script>
```

### LocalStorage Persistence

Query store persists to localStorage:

```typescript
export const queryStore = createLocalStorage<QueryStoreState>(
  'rag-queries',
  initialState
);
```

- Automatically loads on page load
- Automatically saves on changes
- Key: `rag-queries`
- Available across browser tabs

---

## Error Handling Patterns

### Route Validation

```typescript
// Validate before processing
if (!body.query || body.query.trim().length === 0) {
  return new Response(
    JSON.stringify({
      error: 'Validation error',
      message: 'Query is required'
    }),
    { status: 400, headers: { 'Content-Type': 'application/json' } }
  );
}
```

### Timeout Handling

```typescript
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 60000);

try {
  const response = await fetch(url, { signal: controller.signal });
  clearTimeout(timeoutId);
  // Process response
} catch (error) {
  if (error.name === 'AbortError') {
    // Handle timeout
  }
}
```

### Backend Error Translation

```typescript
// Backend returns error
if (!response.ok) {
  const errorData = await response.json();
  return new Response(
    JSON.stringify({
      error: 'Backend error',
      message: errorData.message,
      statusCode: response.status,
      details: errorData.details
    }),
    { status: response.status }
  );
}
```

### Frontend Error Display

```svelte
<script>
  import { addNotification } from '$lib/stores';

  async function handleQuery() {
    const result = await processQuery(query);
    if (result.error) {
      addNotification({
        type: 'error',
        message: result.error.message,
        duration: 5000
      });
    }
  }
</script>

<!-- Or use Dialog component -->
<Dialog
  isOpen={showError}
  type="alert"
  title="Error"
  content={errorMessage}
/>
```

---

## Performance Optimization

### Code Splitting

SvelteKit automatically code-splits pages:
```
- Main page (chat)
- History page
- Query detail page
- News page
- API routes
```

Each loaded on demand.

### Image Optimization

```svelte
<img src={url} alt="description" width="100" height="100" loading="lazy" />
```

### Caching Strategy

**Server-side:**
- Pre-rendered static pages
- Cached query results with hash-based key
- Browser cache headers

**Client-side:**
- Svelte stores for state management
- LocalStorage for persistence
- API client with retry logic

### Monitoring

Add logging for performance tracking:

```typescript
console.time('query-processing');
const result = await processQuery(text);
console.timeEnd('query-processing');
```

---

## Testing

### Unit Tests

```bash
npm install -D vitest
```

Test components:
```typescript
import { render } from '@testing-library/svelte';
import QueryHistory from './+page.svelte';

describe('Query History', () => {
  it('renders queries', () => {
    const { getByText } = render(QueryHistory);
    expect(getByText('Historial')).toBeTruthy();
  });
});
```

### Integration Tests

```typescript
describe('Query API', () => {
  it('processes valid query', async () => {
    const response = await fetch('/api/query', {
      method: 'POST',
      body: JSON.stringify({ query: 'Test' })
    });

    expect(response.status).toBe(200);
  });
});
```

### E2E Tests

```bash
npm install -D playwright
```

---

## Deployment Checklist

- [ ] Build completes without errors: `npm run build`
- [ ] Environment variables configured
- [ ] Backend API URL correct
- [ ] CORS enabled on backend
- [ ] All routes tested
- [ ] Accessibility verified
- [ ] Mobile responsive verified
- [ ] Dark mode tested
- [ ] Error handling works
- [ ] Performance acceptable
- [ ] Security headers configured
- [ ] Rate limiting configured
- [ ] Error monitoring setup
- [ ] Analytics integrated

---

## Support Resources

### SvelteKit Documentation
- https://kit.svelte.dev
- https://kit.svelte.dev/docs

### Svelte Documentation
- https://svelte.dev
- https://svelte.dev/docs

### TypeScript
- https://www.typescriptlang.org/docs

### Accessibility
- https://www.w3.org/WAI/WCAG21/quickref
- https://www.a11y-101.com

### Performance
- https://web.dev/performance

---

## Troubleshooting

### Issue: Routes not working

**Solution:**
1. Check file structure matches SvelteKit conventions
2. Verify import paths use `$lib` alias
3. Check browser console for errors
4. Verify `svelte.config.js` configuration

### Issue: API calls failing

**Solution:**
1. Check backend is running on correct URL
2. Verify `VITE_API_URL` environment variable
3. Check network tab in DevTools
4. Verify CORS configuration
5. Check backend logs for errors

### Issue: Components not rendering

**Solution:**
1. Check component export syntax
2. Verify props are passed correctly
3. Check console for runtime errors
4. Verify TypeScript types match

### Issue: Store not persisting

**Solution:**
1. Check localStorage is enabled
2. Verify store created with `createLocalStorage`
3. Check localStorage key in DevTools
4. Verify JSON serialization works

---

## Next Steps

1. **Customize Styling**
   - Update color variables in `app.css`
   - Modify typography scale
   - Adjust breakpoints for your needs

2. **Add Components**
   - Create new components in `src/lib/components`
   - Export in `src/lib/components/index.ts`
   - Use in pages

3. **Extend API Routes**
   - Add new routes in `src/routes/api`
   - Follow established patterns
   - Include error handling

4. **Implement Features**
   - User authentication
   - Advanced analytics
   - Collaborative features
   - Export/import functionality

5. **Monitor and Improve**
   - Set up error monitoring
   - Track performance metrics
   - Gather user feedback
   - Iterate on design

---

**Generated: 2024**
**Version: 1.0.0**

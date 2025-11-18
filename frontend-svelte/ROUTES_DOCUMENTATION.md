# Svelte Frontend Routes and API Documentation

## Overview

This document provides comprehensive documentation for all 13 routes created for the Svelte frontend:
- 8 Page routes with server-side load functions
- 5 API proxy routes for backend communication

All routes follow SvelteKit conventions and include full TypeScript support, error handling, and accessibility features.

---

## Page Routes

### 1. Main Chat Page

**File:** `src/routes/+page.svelte` / `src/routes/+page.server.ts`

**Purpose:** Primary user interface for regulatory compliance queries

**Features:**
- Real-time chat interface with message history
- Integration with ChatInterface component
- Notification system for user feedback
- Responsive layout (mobile-first design)
- Dark mode support

**Server Load Function:**
- Fetches recent queries (last 10) from backend `/api/queries` endpoint
- Pre-loads data for quick sidebar access
- Graceful error handling with fallback to empty array

**Props:**
```typescript
// Data returned from server load
{
  recentQueries: Query[];
  timestamp: string;
  error?: string;
}
```

**Accessibility:**
- ARIA labels for all interactive elements
- Role attributes for semantic HTML
- Focus management
- Screen reader support

**Responsive Breakpoints:**
- Desktop: Full sidebar visible
- Tablet (768px): Sidebar toggleable
- Mobile (480px): Optimized compact layout

---

### 2. Query History Page

**File:** `src/routes/historial/+page.svelte` / `src/routes/historial/+page.server.ts`

**Purpose:** Browse, search, filter, and manage all regulatory queries

**Features:**
- Advanced search with real-time filtering
- Multi-dimensional filtering:
  - Sector (banking, insurance, telecoms, general)
  - Type (compliance, gap-analysis, report)
- Pagination support
- Query deletion with confirmation dialog
- Status badges (completed, pending, failed)
- Sort by date (newest first)

**Search Functionality:**
- Text search across query text and responses
- ID-based search for direct lookup
- Case-insensitive matching

**Filter Options:**
```typescript
interface FilterState {
  searchTerm: string;
  selectedSector: string | null;
  selectedType: Query['type'] | null;
}
```

**Server Load Function:**
- Fetches paginated queries from `/api/queries`
- Supports pagination parameters (page, pageSize)
- Returns 50 items per page by default
- Handles pagination metadata

**Accessibility:**
- Form fields with associated labels
- ARIA live regions for filter updates
- Keyboard navigation throughout
- Semantic list structure with role="list"

**Mobile Optimizations:**
- Responsive grid layout
- Touch-friendly button sizes (44px minimum)
- Stacked layout on small screens
- Simplified badge display

---

### 3. Query Detail Page

**File:** `src/routes/consulta/[id]/+page.svelte` / `src/routes/consulta/[id]/+page.server.ts`

**Purpose:** Display comprehensive analysis results for a specific query

**Features:**
- Full query information display
- Analysis results with sections:
  - Executive summary
  - Complete response
  - Source citations with relevance scores
- Report generation with multiple analysis types:
  - Comprehensive analysis
  - Quick analysis
  - GAP analysis
  - Executive summary
- Progress tracking for report generation
- Report download functionality
- Back navigation to history

**Dynamic Routes:**
- Route parameter: `[id]` - Query ID (UUID format)
- Server-side data fetching from `/api/queries/{id}`

**Report Generation Flow:**
```
1. User selects analysis type
2. Client sends POST to /api/report
3. Backend returns jobId
4. Poll /api/report status endpoint
5. Display progress to user
6. Enable download when complete
```

**Report Options:**
```typescript
enum AnalysisType {
  'comprehensive' = 'Análisis Completo',
  'quick' = 'Análisis Rápido',
  'gap-analysis' = 'Análisis de Brechas',
  'executive-summary' = 'Resumen Ejecutivo'
}
```

**Server Load Function:**
- Fetches specific query by ID
- Returns null if query not found
- Handles 404 gracefully
- Pre-loads all analysis data

**Error Handling:**
- Query not found state with CTA to return to history
- Report generation timeout (120 seconds)
- Network error recovery
- Detailed error messages

**Accessibility:**
- Semantic heading hierarchy
- ARIA roles for custom widgets
- Form labels for all inputs
- Error messages with role="alert"
- Loading states with aria-busy

---

### 4. News and Updates Page

**File:** `src/routes/novedades/+page.svelte` / `src/routes/novedades/+page.server.ts`

**Purpose:** Display regulatory news, updates, and alerts

**Features:**
- Categorized news feed with categories:
  - Regulation
  - Update
  - Announcement
  - Alert
- Priority levels (low, medium, high, critical)
- Search functionality
- Category filtering
- Date sorting (newest first)
- Source attribution
- External links to original sources

**Data Structure:**
```typescript
interface NewsItem {
  id: string;
  title: string;
  description: string;
  category: 'regulation' | 'update' | 'announcement' | 'alert';
  date: Date;
  source?: string;
  link?: string;
  priority?: 'low' | 'medium' | 'high' | 'critical';
}
```

**Server Load Function:**
- Attempts to fetch from `/api/news` endpoint
- Falls back to mock data if endpoint unavailable
- Graceful degradation when backend unavailable

**Frontend Mock Data:**
- Pre-populated with 4 sample news items
- Used when API endpoint not available
- Demonstrates expected data structure

**Styling Features:**
- Color-coded badges by category and priority
- Visual hierarchy with typography
- Icon indicators for news types
- Readable typography with appropriate line-height

**Accessibility:**
- Semantic HTML5 article elements
- Datetime attributes on time elements
- Links with aria-labels
- Proper color contrast ratios

---

## API Routes

### 1. Query Processing API

**File:** `src/routes/api/query/+server.ts`

**Endpoint:** `POST /api/query`

**Purpose:** Process regulatory queries and return analysis results

**Request:**
```typescript
interface QueryRequest {
  query: string;                      // 1-5000 characters
  sector?: string;                    // banking, insurance, telecoms, general
  type?: 'compliance' | 'gap-analysis' | 'report';
}
```

**Response:**
```typescript
interface OrchestrationResult {
  analysis: string;
  gaps?: string[];
  recommendations?: string[];
  sources?: DocumentSource[];
  metadata?: {
    processingTime?: number;
    agentsUsed?: string[];
    cacheHit?: boolean;
    [key: string]: unknown;
  };
}
```

**Validation:**
- Query text required and non-empty
- Query length between 1-5000 characters
- Valid sector values
- JSON parsing error handling

**Error Responses:**
- 400: Bad request / validation error
- 408: Request timeout (60 second timeout)
- 503: Backend connection error
- 500: Internal server error

**Error Response Format:**
```json
{
  "error": "Error type",
  "message": "Human-readable message",
  "statusCode": 400,
  "details": "Additional context"
}
```

**Timeout Handling:**
- 60-second timeout for complex analysis
- AbortController for request cancellation
- Timeout error response (408)

**Backend Proxy:**
- Forwards to `POST /query` on backend
- Transparent forwarding of request/response
- Error translation to consistent format

---

### 2. Report Generation API

**File:** `src/routes/api/report/+server.ts`

**Endpoints:**
- `POST /api/report` - Generate report
- `GET /api/report?jobId=...` - Check status

**Purpose:** Generate regulatory compliance reports in multiple formats

**Generation Request:**
```typescript
interface ReportGenerationRequest {
  queryId: string;
  analysisType: 'comprehensive' | 'quick' | 'gap-analysis' | 'executive-summary';
  sector: 'banking' | 'insurance' | 'telecoms' | 'general';
  format?: 'docx' | 'pdf' | 'html';
  includeExecutiveSummary?: boolean;
  includeGapAnalysis?: boolean;
  includeRecommendations?: boolean;
}
```

**Generation Response:**
```typescript
interface ReportJobResponse {
  jobId: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress?: number;
  resultPath?: string;
  error?: string;
}
```

**Status Check Request:**
```json
{
  "jobId": "uuid-string"
}
```

**Status Check Response:**
- Returns same format as generation response
- Includes progress percentage
- Error message if failed

**Validation:**
- All required fields must be present
- Valid enum values
- Query ID format validation

**Error Handling:**
- 400: Validation errors
- 408: Timeout (120 second limit)
- 503: Backend connection error
- 500: Internal error

**Polling Strategy:**
- Client-side polling recommended (5-10 second intervals)
- Server returns current progress percentage
- Maximum 60 polling attempts before timeout

**Backend Integration:**
- Forwards to `POST /api/reports/generate`
- Status checks to `GET /api/reports/status/{jobId}`

---

### 3. File Operations API

**File:** `src/routes/api/file/+server.ts`

**Endpoints:**
- `POST /api/file` - Upload file
- `GET /api/file?fileId=...` - Download file

**Purpose:** Handle file uploads and downloads for document analysis

**Upload Request:**
```
Content-Type: multipart/form-data
Form Fields:
  - file: File (required)
  - sector: string (optional)
```

**Upload Response:**
```json
{
  "fileId": "uuid-string",
  "fileName": "original-filename.pdf"
}
```

**Upload Validation:**
- Maximum file size: 50MB
- Allowed types:
  - application/pdf
  - application/msword
  - application/vnd.openxmlformats-officedocument.wordprocessingml.document
  - text/plain
- File presence required

**Download Request:**
```
GET /api/file?fileId=uuid-string
```

**Download Response:**
- Binary file data
- Content-Type header matches file type
- Content-Disposition header with filename
- Content-Length header

**Error Handling:**
- 400: Invalid form data / validation error
- 408: Upload timeout (60 seconds)
- 413: Payload too large
- 503: Backend connection error
- 500: Internal error

**Timeout:**
- 60-second timeout for uploads
- Appropriate for large document processing

**Backend Proxy:**
- Upload: `POST /api/upload`
- Download: `GET /api/files/{fileId}/download`

---

### 4. Query History API

**File:** `src/routes/api/history/+server.ts`

**Endpoints:**
- `GET /api/history` - List queries with pagination
- `DELETE /api/history?id=...` - Delete query

**Purpose:** Manage query history with filtering and pagination

**List Request Query Parameters:**
```typescript
{
  page?: number;              // 1-indexed, default 1
  pageSize?: number;          // 1-100, default 20
  sector?: string;            // Filter by sector
  type?: string;              // Filter by type
  search?: string;            // Full-text search
  startDate?: ISO8601;        // Filter by date range
  endDate?: ISO8601;
}
```

**List Response:**
```typescript
interface PaginatedResponse<Query> {
  data: Query[];
  meta: {
    total: number;            // Total items matching filters
    page: number;             // Current page
    pageSize: number;         // Items per page
    totalPages: number;       // Total pages available
  };
}
```

**Delete Request:**
```
DELETE /api/history?id=uuid-string
```

**Delete Response:**
```json
{
  "success": true
}
```

**Pagination Validation:**
- Page must be positive integer
- PageSize must be 1-100
- Helpful error messages

**Query Parameters:**
- All parameters optional
- Multiple filters can be combined
- Case-insensitive search

**Error Handling:**
- 400: Invalid pagination parameters
- 404: Query not found (for delete)
- 408: Request timeout (30 seconds)
- 503: Backend connection error
- 500: Internal error

**Backend Integration:**
- List: `GET /api/queries` with all parameters
- Delete: `DELETE /api/queries/{id}`
- Transparent parameter forwarding

**Performance:**
- Default page size 20 items
- Maximum 100 items per page
- 30-second timeout for complex queries

---

## Error Handling

### Consistent Error Format

All API routes return errors in consistent format:

```typescript
interface APIError {
  error: string;              // Error type (e.g., "Validation error")
  message: string;            // Human-readable message
  statusCode: number;         // HTTP status code
  details?: string | object;  // Additional context
}
```

### HTTP Status Codes

| Status | Use Case |
|--------|----------|
| 400 | Validation error, invalid parameters |
| 404 | Resource not found |
| 408 | Request timeout |
| 413 | Payload too large |
| 500 | Unexpected server error |
| 503 | Backend service unavailable |

### Error Recovery

**Client-side:**
- Automatic retry with exponential backoff
- User-friendly error notifications
- Fallback UI states
- Clear error messages

**Timeout Handling:**
- AbortController for request cancellation
- Appropriate timeout per operation:
  - Query processing: 60s
  - Report generation: 120s
  - File upload: 60s
  - History fetch: 30s

---

## Integration Points

### Frontend ↔ SvelteKit Routes

1. **Chat Interface** → `POST /api/query`
   - User submits query
   - Route processes and forwards to backend
   - Returns analysis results

2. **History Page** → `GET /api/history`
   - Load queries with filters
   - Apply pagination
   - Forward all parameters

3. **Query Detail** → `POST /api/report` / `GET /api/report`
   - Initiate report generation
   - Poll status endpoint
   - Track progress

4. **File Upload** → `POST /api/file`
   - User selects file
   - Validate size/type
   - Forward to backend

### SvelteKit Routes ↔ Backend API

All routes proxy to backend at `VITE_API_URL`:

```typescript
const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:8000';
```

Routes preserve:
- Request method (GET, POST, DELETE)
- Query parameters
- Request body (with validation)
- Timeout configuration

---

## Testing Checklist

### Page Routes

- [ ] **Main Page (`/`)**
  - [ ] Page loads with recent queries
  - [ ] ChatInterface component renders
  - [ ] Notifications display correctly
  - [ ] Dark mode toggle works
  - [ ] Mobile layout responsive
  - [ ] No console errors

- [ ] **History Page (`/historial`)**
  - [ ] Queries load and display
  - [ ] Search filters work
  - [ ] Sector filter works
  - [ ] Type filter works
  - [ ] Pagination works
  - [ ] Delete confirmation shows
  - [ ] Delete removes query from list
  - [ ] Clear filters resets all filters
  - [ ] Empty state shows when no queries
  - [ ] No results state shows for filters

- [ ] **Query Detail (`/consulta/[id]`)**
  - [ ] Query details load
  - [ ] Analysis displays with sections
  - [ ] Sources show with relevance scores
  - [ ] Report generation starts
  - [ ] Progress updates during generation
  - [ ] Download button works after completion
  - [ ] Back button returns to history
  - [ ] 404 state shows for invalid ID
  - [ ] Timestamps format correctly

- [ ] **News Page (`/novedades`)**
  - [ ] News items load
  - [ ] Category filter works
  - [ ] Search works
  - [ ] Priority badges display
  - [ ] External links work
  - [ ] Empty state shows correctly

### API Routes

- [ ] **Query API (`POST /api/query`)**
  - [ ] Valid request succeeds
  - [ ] Invalid query rejected (400)
  - [ ] Empty query rejected (400)
  - [ ] Query > 5000 chars rejected (400)
  - [ ] Timeout handled (408)
  - [ ] Backend error translated properly
  - [ ] Response format correct

- [ ] **Report API (`POST /api/report`)**
  - [ ] Generation starts successfully
  - [ ] JobId returned
  - [ ] Status check works
  - [ ] Progress updates
  - [ ] Validation catches missing fields
  - [ ] Timeout handled (120s)

- [ ] **File API (`POST /api/file`)**
  - [ ] Valid file uploads
  - [ ] Large file rejected (413)
  - [ ] Invalid type rejected (400)
  - [ ] Timeout handled (60s)
  - [ ] Download works with valid fileId

- [ ] **History API (`GET /api/history`)**
  - [ ] Queries load with pagination
  - [ ] Page parameter works
  - [ ] PageSize parameter works
  - [ ] Sector filter works
  - [ ] Type filter works
  - [ ] Search works
  - [ ] Date range filters work
  - [ ] Invalid page rejected (400)
  - [ ] Invalid pageSize rejected (400)

- [ ] **History Delete (`DELETE /api/history`)**
  - [ ] Valid delete succeeds
  - [ ] Missing ID rejected (400)
  - [ ] Invalid ID handled gracefully
  - [ ] 404 for non-existent query

### Accessibility

- [ ] All pages WCAG 2.1 AA compliant
- [ ] Keyboard navigation works
- [ ] Screen reader announces content
- [ ] Focus visible on all interactive elements
- [ ] Form labels associated with inputs
- [ ] Error messages announced
- [ ] Loading states accessible

### Mobile Testing

- [ ] All pages responsive
- [ ] Touch targets 44px minimum
- [ ] Text readable without zoom
- [ ] Navigation accessible
- [ ] Forms usable on mobile
- [ ] Modals/dialogs work on mobile
- [ ] Notifications don't overlap content

### Performance

- [ ] Page load time < 3s
- [ ] API responses < 2s (query < 60s)
- [ ] No excessive re-renders
- [ ] Proper error boundaries
- [ ] Memory leaks addressed
- [ ] Images optimized

### Security

- [ ] Input validation on all routes
- [ ] XSS prevention (Svelte built-in)
- [ ] CORS headers correct
- [ ] No sensitive data in URLs
- [ ] File upload type validation
- [ ] Timeout prevents DoS

---

## Environment Configuration

### Required Environment Variables

Create `.env.local` or `.env` in project root:

```bash
# Backend API URL
VITE_API_URL=http://localhost:8000

# Optional: Custom timeouts
API_REQUEST_TIMEOUT=30000
API_REPORT_TIMEOUT=120000
API_UPLOAD_TIMEOUT=60000
```

### Development

```bash
npm run dev
# Server runs on http://localhost:5173
# Proxies to backend at http://localhost:8000
```

### Production Build

```bash
npm run build
npm run preview
# Build output in build/ directory
```

---

## File Structure

```
src/routes/
├── +page.svelte                 # Main chat page
├── +page.server.ts              # Load recent queries
├── historial/
│   ├── +page.svelte            # Query history list
│   └── +page.server.ts         # Load paginated queries
├── consulta/
│   └── [id]/
│       ├── +page.svelte        # Query detail view
│       └── +page.server.ts     # Load query by ID
├── novedades/
│   ├── +page.svelte            # News page
│   └── +page.server.ts         # Load news items
└── api/
    ├── query/
    │   └── +server.ts          # POST /api/query
    ├── report/
    │   └── +server.ts          # POST/GET /api/report
    ├── file/
    │   └── +server.ts          # POST/GET /api/file
    └── history/
        └── +server.ts          # GET/DELETE /api/history
```

---

## Deployment Notes

### SvelteKit Adapter

Currently configured with default SvelteKit adapter. For production, consider:

**Node.js Adapter:**
```bash
npm install -D @sveltejs/adapter-node
```

Update `svelte.config.js`:
```javascript
import adapter from '@sveltejs/adapter-node';

export default {
  kit: {
    adapter: adapter()
  }
};
```

**Environment Variables in Production:**
- Set `VITE_API_URL` to backend URL
- Use production backend URL
- Configure CORS if different domains

### Docker Deployment

Example Dockerfile:

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
ENV VITE_API_URL=http://backend:8000
EXPOSE 3000
CMD ["node", "build"]
```

---

## Support and Troubleshooting

### Common Issues

**Routes not found (404):**
- Verify file structure matches SvelteKit conventions
- Check file names (case-sensitive on Linux)
- Ensure `+page.svelte` and `+server.ts` naming

**API proxy not working:**
- Check `VITE_API_URL` environment variable
- Verify backend is running
- Check network tab in browser DevTools
- Verify CORS configuration on backend

**Timeout errors:**
- Increase timeout in route file
- Check backend performance
- Monitor network latency
- Review backend logs

**Components not loading:**
- Check import paths (use `$lib` alias)
- Verify component exports
- Check for circular dependencies

---

## Future Enhancements

- [ ] WebSocket support for real-time updates
- [ ] Batch query processing
- [ ] Advanced caching strategies
- [ ] GraphQL support alongside REST
- [ ] Analytics and monitoring integration
- [ ] Rate limiting and quota management
- [ ] User session management
- [ ] Multi-language support

/**
 * Core TypeScript interfaces for RAG Regulatory Analysis System
 * Matches backend schema from backend/agents/orchestrator_agent.py
 */

/**
 * User message in chat conversation
 */
export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  artifact?: Artifact;
  sources?: DocumentSource[];
  metadata?: Record<string, unknown>;
}

/**
 * Single document source used in analysis
 */
export interface DocumentSource {
  title: string;
  url?: string;
  relevanceScore: number;
  excerpt: string;
  chunk?: number;
}

/**
 * Query history entry
 */
export interface Query {
  id: string;
  text: string;
  timestamp: Date;
  status: 'pending' | 'completed' | 'failed';
  response?: string;
  analysis?: AnalysisResult;
  sector?: string;
  type?: 'compliance' | 'gap-analysis' | 'report';
  metadata?: Record<string, unknown>;
}

/**
 * Analysis result from orchestrator agent
 */
export interface AnalysisResult {
  summary: string;
  compliance: ComplianceAnalysis;
  gaps?: GapAnalysis[];
  recommendations?: string[];
  relatedRegulations?: RegulationRef[];
}

/**
 * Compliance analysis details
 */
export interface ComplianceAnalysis {
  status: 'compliant' | 'partial' | 'non-compliant' | 'unknown';
  requirements: ComplianceRequirement[];
  score?: number;
  riskLevel?: 'low' | 'medium' | 'high' | 'critical';
  details: string;
}

/**
 * Individual compliance requirement
 */
export interface ComplianceRequirement {
  id: string;
  name: string;
  regulation: string;
  status: 'met' | 'partial' | 'not-met' | 'not-applicable';
  description: string;
  evidenceProvided?: string;
  gap?: string;
}

/**
 * GAP analysis item
 */
export interface GapAnalysis {
  area: string;
  currentState: string;
  requiredState: string;
  gap: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  estimatedEffort?: string;
  recommendations?: string[];
}

/**
 * Reference to related regulation
 */
export interface RegulationRef {
  id: string;
  title: string;
  article?: string;
  relevantSections?: string[];
  applicability: string;
}

/**
 * Generated artifact (document, analysis, etc.)
 */
export interface Artifact {
  id: string;
  type: 'document' | 'analysis' | 'report' | 'export';
  name: string;
  content: string | ArrayBuffer;
  mimeType: string;
  source: 'ai-analysis' | 'template' | 'generated' | 'uploaded';
  metadata?: {
    size?: number;
    createdAt?: Date;
    queryId?: string;
    reportId?: string;
    [key: string]: unknown;
  };
}

/**
 * Report generation request
 */
export interface ReportRequest {
  query: string;
  analysisType: 'comprehensive' | 'quick' | 'gap-analysis' | 'executive-summary';
  sector: 'banking' | 'insurance' | 'telecoms' | 'general';
  format?: 'docx' | 'pdf' | 'html';
  includeExecutiveSummary?: boolean;
  includeGapAnalysis?: boolean;
  includeRecommendations?: boolean;
}

/**
 * Orchestration result from backend
 * Matches backend/agents/orchestrator_agent.py OrchestrationResult
 */
export interface OrchestrationResult {
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

/**
 * Report generation job response
 */
export interface ReportJobResponse {
  jobId: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress?: number;
  resultPath?: string;
  error?: string;
}

/**
 * Report progress update via WebSocket
 */
export interface ReportProgressUpdate {
  jobId: string;
  status: 'processing' | 'completed' | 'failed' | 'cancelled';
  progress?: number;
  stage?: string;
  message?: string;
  resultPath?: string;
  error?: string;
  timestamp: Date;
}

/**
 * Chat store state
 */
export interface ChatStoreState {
  messages: Message[];
  loading: boolean;
  error: string | null;
  autoScroll: boolean;
  currentQueryId: string | null;
}

/**
 * Query store state
 */
export interface QueryStoreState {
  queries: Query[];
  currentQuery: Query | null;
  loading: boolean;
  error: string | null;
  selectedSector: string | null;
  selectedType: Query['type'] | null;
}

/**
 * Report store state
 */
export interface ReportStoreState {
  reports: (Query & { artifact?: Artifact })[];
  currentReport: (Query & { artifact?: Artifact }) | null;
  generating: boolean;
  error: string | null;
  jobId: string | null;
  progress: number;
}

/**
 * UI store state
 */
export interface UIStoreState {
  theme: 'light' | 'dark';
  sidebarOpen: boolean;
  notifications: Notification[];
  modal: {
    isOpen: boolean;
    title?: string;
    content?: string;
    type?: 'confirm' | 'alert' | 'info';
  };
}

/**
 * Notification item
 */
export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
  dismissible?: boolean;
  action?: {
    label: string;
    callback: () => void;
  };
}

/**
 * API error response
 */
export interface APIError {
  statusCode: number;
  message: string;
  error?: string;
  details?: Record<string, unknown>;
  timestamp?: Date;
}

/**
 * Pagination metadata
 */
export interface PaginationMeta {
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

/**
 * Paginated response wrapper
 */
export interface PaginatedResponse<T> {
  data: T[];
  meta: PaginationMeta;
}

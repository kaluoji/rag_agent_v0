// src/lib/types/index.ts

export type Role = 'user' | 'assistant';

export type QueryType = 'consultation' | 'gap_analysis';

export interface Query {
  id: string;
  text: string;
  timestamp: string;
  response: string;
  type: QueryType;
  hasDocuments: boolean;
  metadata?: Record<string, any>;
}

export interface ChatMessage {
  id: string;
  role: Role;
  content: string;
}

export interface DocumentData {
  name: string;
  type: string;
  size: number;
  content: string; // base64
}

export interface QueryResponse {
  response: string;
  sources?: Array<{
    title: string;
    summary: string;
    content: string;
    metadata?: Record<string, any>;
  }>;
  metadata?: Record<string, any>;
}

export interface ReportData {
  reportPath: string;
  reportHtml?: string;
  metadata?: Record<string, any>;
}

export interface Annotation {
  id: string;
  reportId: string;
  text: string;
  comment: string;
  position: number;
  timestamp: string;
}

export type ReportStatus = 'idle' | 'generating' | 'ready' | 'error';

export interface WebSocketMessage {
  type: 'status' | 'progress' | 'complete' | 'error';
  data?: any;
  message?: string;
  progress?: number;
}

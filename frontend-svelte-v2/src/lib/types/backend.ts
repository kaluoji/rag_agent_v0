/**
 * Tipos TypeScript para la integración con el backend FastAPI
 */

// Respuesta de una consulta
export interface QueryResponse {
	response: string;
	query: string;
	query_id: string;
	timestamp: string;
	session_id?: string; 
	metadata: Record<string, unknown>;
}

// Datos de un documento para GAP analysis
export interface DocumentData {
	name: string;
	type: string;
	content: string; // base64
	size: number;
}

// Request para consultas con documentos
export interface QueryWithDocumentsRequest {
	query: string;
	documents?: DocumentData[];
}

// Status de una query
export interface QueryStatus {
	query_id: string;
	status: 'pending' | 'processing' | 'completed' | 'error';
	progress?: number;
	message?: string;
}

// Request para generar reporte
export interface GenerateReportRequest {
	query: string;
	format?: 'docx' | 'pdf';
}

// Respuesta de generación de reporte
export interface GenerateReportResponse {
	success: boolean;
	report_id: string;
	report_path: string;
	filename: string;
	message?: string;
}

// Contenido de reporte por ID
export interface ReportContent {
	success: boolean;
	filename: string;
	base64Content: string;
}

// HTML de reporte para preview
export interface ReportHtmlResponse {
	html: string;
}

// Anotaciones de reporte
export interface ReportAnnotation {
	id: string;
	type: 'highlight' | 'comment';
	color?: string;
	content?: string;
	position?: {
		start: number;
		end: number;
	};
	timestamp: string;
}

// Response de anotaciones
export interface AnnotationsResponse {
	annotations: ReportAnnotation[];
}

// WebSocket message types
export interface WebSocketMessage {
	type: 'status' | 'progress' | 'complete' | 'error';
	status?: string;
	progress?: number;
	data?: any;
	message?: string;
	reportPath?: string;
	reportHtml?: string;
	filename?: string;
}

// Error response del backend
export interface ApiError {
	detail: string;
	error?: string;
	status_code?: number;
}
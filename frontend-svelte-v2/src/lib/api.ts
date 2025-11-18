/**
 * API Service - Cliente para comunicarse con el backend FastAPI
 * Incluye todos los endpoints: queries, reports, annotations
 */

import type {
	QueryResponse,
	DocumentData,
	QueryStatus,
	GenerateReportResponse,
	ReportContent,
	AnnotationsResponse,
	ReportAnnotation,
	ApiError
} from './types/backend';

// URL base del API (configurable via env)
const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

/**
 * Helper para requests POST
 */
async function post<T>(path: string, body: unknown): Promise<T> {
	const res = await fetch(`${API_URL}${path}`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body)
	});

	if (!res.ok) {
		const errorData = (await res.json().catch(() => ({}))) as ApiError;
		throw new Error(errorData.detail || errorData.error || `Error HTTP ${res.status}`);
	}

	return res.json();
}

/**
 * Helper para requests GET
 */
async function get<T>(path: string, params?: Record<string, string>): Promise<T> {
	const url = new URL(`${API_URL}${path}`);
	if (params) {
		Object.entries(params).forEach(([key, value]) => {
			url.searchParams.append(key, value);
		});
	}

	const res = await fetch(url.toString());

	if (!res.ok) {
		const errorData = (await res.json().catch(() => ({}))) as ApiError;
		throw new Error(errorData.detail || errorData.error || `Error HTTP ${res.status}`);
	}

	return res.json();
}

// ==================== QUERY SERVICE ====================

/**
 * Enviar consulta normativa simple
 */
export async function submitQuery(query: string): Promise<QueryResponse> {
	return post<QueryResponse>('/api/query', { query });
}

/**
 * Enviar consulta con documentos (GAP analysis)
 */
export async function submitQueryWithDocuments(
	query: string,
	documents: DocumentData[]
): Promise<QueryResponse> {
	return post<QueryResponse>('/api/query/with-documents', { query, documents });
}

/**
 * Obtener status de una query por ID
 */
export async function getQueryStatus(queryId: string): Promise<QueryStatus> {
	return get<QueryStatus>(`/api/query/${queryId}/status`);
}

// ==================== REPORT SERVICE ====================

/**
 * Generar reporte en formato DOCX
 */
export async function generateReport(
	query: string,
	format: 'docx' | 'pdf' = 'docx'
): Promise<GenerateReportResponse> {
	return post<GenerateReportResponse>('/api/report/generate', { query, format });
}

/**
 * Guardar anotaciones de un reporte
 */
export async function saveAnnotations(
	reportId: string,
	annotations: ReportAnnotation[]
): Promise<{ success: boolean; message: string }> {
	return post(`/api/report/annotations/${reportId}`, { annotations });
}

/**
 * Obtener anotaciones de un reporte
 */
export async function getAnnotations(reportId: string): Promise<AnnotationsResponse> {
	return get<AnnotationsResponse>(`/api/report/annotations/${reportId}`);
}

/**
 * Obtener preview de un reporte por path
 */
export async function getReportPreview(reportPath: string): Promise<{ html: string }> {
	return get<{ html: string }>('/api/report/preview', { path: reportPath });
}

/**
 * Obtener contenido de reporte por ID (base64)
 */
export async function getReportContentById(reportId: string): Promise<ReportContent> {
	return get<ReportContent>(`/api/report/content_by_id/${reportId}`);
}

// ==================== FILE HELPERS ====================

/**
 * Convertir File a DocumentData (base64)
 */
export async function fileToDocumentData(file: File): Promise<DocumentData> {
	return new Promise((resolve, reject) => {
		const reader = new FileReader();

		reader.onload = () => {
			const base64 = (reader.result as string).split(',')[1]; // Remover prefix "data:..."
			resolve({
				name: file.name,
				type: file.type,
				size: file.size,
				content: base64
			});
		};

		reader.onerror = () => reject(new Error('Error al leer el archivo'));
		reader.readAsDataURL(file);
	});
}

/**
 * Convertir múltiples Files a DocumentData[]
 */
export async function filesToDocumentData(files: File[]): Promise<DocumentData[]> {
	return Promise.all(files.map((file) => fileToDocumentData(file)));
}

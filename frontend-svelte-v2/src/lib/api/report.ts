/**
 * Report API Service
 * Maneja la comunicación con el backend para generación y descarga de reportes
 */

import type {
	GenerateReportRequest,
	GenerateReportResponse,
	ReportContent,
	ReportHtmlResponse,
	ReportAnnotation,
	AnnotationsResponse
} from '$lib/types/backend';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Genera un nuevo reporte basado en una consulta
 */
export async function generateReport(
	query: string,
	format: 'docx' | 'pdf' = 'docx'
): Promise<GenerateReportResponse> {
	const response = await fetch(`${API_URL}/api/report/generate`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({ query, format })
	});

	if (!response.ok) {
		const error = await response.json().catch(() => ({ detail: 'Error desconocido' }));
		throw new Error(error.detail || 'Error al generar el reporte');
	}

	return response.json();
}


/**
 * Obtiene el contenido del reporte en base64 para descarga
 */
export async function getReportContent(reportId: string): Promise<ReportContent> {
	const response = await fetch(`${API_URL}/api/report/content_by_id/${reportId}`);

	if (!response.ok) {
		throw new Error('Error al obtener el contenido del reporte');
	}

	const data = await response.json();

	if (!data.success) {
		throw new Error(data.message || 'Error al obtener contenido del reporte');
	}

	return data;
}

/**
 * Descarga un reporte en el navegador
 */
export async function downloadReport(reportId: string): Promise<void> {
	try {
		const reportContent = await getReportContent(reportId);

		// Convertir base64 a blob
		const byteCharacters = atob(reportContent.base64Content);
		const byteNumbers = new Array(byteCharacters.length);

		for (let i = 0; i < byteCharacters.length; i++) {
			byteNumbers[i] = byteCharacters.charCodeAt(i);
		}

		const byteArray = new Uint8Array(byteNumbers);
		const blob = new Blob([byteArray], {
			type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
		});

		// Crear enlace de descarga
		const url = window.URL.createObjectURL(blob);
		const link = document.createElement('a');
		link.href = url;
		link.download = reportContent.filename || 'reporte.docx';
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
		window.URL.revokeObjectURL(url);
	} catch (error) {
		console.error('Error al descargar el reporte:', error);
		throw error;
	}
}

/**
 * Obtiene el contenido HTML de previsualización de un reporte
 */
export async function getReportHtml(reportId: string): Promise<string> {
	const response = await fetch(`${API_URL}/api/report/html/${reportId}`);

	if (!response.ok) {
		throw new Error('Error al obtener la previsualización del reporte');
	}

	const data = await response.json();
	return data.html || '';
}

/**
 * Guarda anotaciones de un reporte
 */
export async function saveAnnotations(
	reportId: string,
	annotations: Omit<ReportAnnotation, 'id' | 'timestamp'>[]
): Promise<ReportAnnotation[]> {
	const response = await fetch(`${API_URL}/api/report/annotations/${reportId}`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({ annotations })
	});

	if (!response.ok) {
		throw new Error('Error al guardar las anotaciones');
	}

	const data = await response.json();
	return data.annotations || [];
}

/**
 * Obtiene las anotaciones de un reporte
 */
export async function getAnnotations(reportId: string): Promise<ReportAnnotation[]> {
	try {
		const response = await fetch(`${API_URL}/api/report/annotations/${reportId}`);

		if (!response.ok) {
			return [];
		}

		const data: AnnotationsResponse = await response.json();
		return data.annotations || [];
	} catch (error) {
		console.error('Error al obtener anotaciones:', error);
		return [];
	}
}

/**
 * Crea una conexión WebSocket para recibir actualizaciones de progreso
 */
export function createReportWebSocket(reportId: string) {
	const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
	const host = import.meta.env.VITE_API_WS_HOST || window.location.host.replace(':5173', ':8000');
	const wsURL = `${protocol}//${host}/ws/report/${reportId}`;

	console.log('Conectando WebSocket a:', wsURL);

	try {
		const socket = new WebSocket(wsURL);

		return {
			socket,

			onMessage: (callback: (data: any) => void) => {
				socket.onmessage = (event) => {
					try {
						const data = JSON.parse(event.data);
						callback(data);
					} catch (error) {
						console.error('Error parsing WebSocket message:', error);
					}
				};
			},

			onError: (callback: (error: Event) => void) => {
				socket.onerror = callback;
			},

			onOpen: (callback: () => void) => {
				socket.onopen = callback;
			},

			onClose: (callback: () => void) => {
				socket.onclose = callback;
			},

			close: () => {
				if (socket && socket.readyState === WebSocket.OPEN) {
					socket.close();
				}
			}
		};
	} catch (error) {
		console.error('Error al crear conexión WebSocket:', error);
		return {
			socket: null,
			onMessage: () => {},
			onError: () => {},
			onOpen: () => {},
			onClose: () => {},
			close: () => {}
		};
	}
}
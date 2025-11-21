/**
 * Enhanced Report Store - Maneja generación, preview y descarga de reportes
 * Compatible con el sistema de templates del backend
 */

export interface Annotation {
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

export type ReportStatus = 'idle' | 'generating' | 'ready' | 'error';

interface ReportState {
	reportId: string | null;
	reportData: any;
	reportHtml: string;
	reportPath: string;
	status: ReportStatus;
	annotations: Annotation[];
	selectedText: string;
	errorMessage: string | null;
	progress: number;
	// Nuevos campos para preview
	showPreview: boolean;
	filename: string;
	base64Content: string;
}

class ReportStore {
	private state = $state<ReportState>({
		reportId: null,
		reportData: null,
		reportHtml: '',
		reportPath: '',
		status: 'idle',
		annotations: [],
		selectedText: '',
		errorMessage: null,
		progress: 0,
		showPreview: false,
		filename: '',
		base64Content: ''
	});

	// Getters reactivos
	get reportId() {
		return this.state.reportId;
	}

	get reportData() {
		return this.state.reportData;
	}

	get reportHtml() {
		return this.state.reportHtml;
	}

	get reportPath() {
		return this.state.reportPath;
	}

	get status() {
		return this.state.status;
	}

	get annotations() {
		return this.state.annotations;
	}

	get selectedText() {
		return this.state.selectedText;
	}

	get errorMessage() {
		return this.state.errorMessage;
	}

	get progress() {
		return this.state.progress;
	}

	get showPreview() {
		return this.state.showPreview;
	}

	get filename() {
		return this.state.filename;
	}

	get base64Content() {
		return this.state.base64Content;
	}

	// Derived: indica si está generando
	get isGenerating() {
		return this.state.status === 'generating';
	}

	// Derived: indica si está listo
	get isReady() {
		return this.state.status === 'ready';
	}

	// Derived: indica si hay error
	get hasError() {
		return this.state.status === 'error';
	}

	// Métodos de actualización básicos
	setReportId(reportId: string) {
		this.state.reportId = reportId;
	}

	setReportData(reportData: any) {
		this.state.reportData = reportData;
		this.state.errorMessage = null;
	}

	setReportHtml(reportHtml: string) {
		this.state.reportHtml = reportHtml;
	}

	setReportPath(reportPath: string) {
		this.state.reportPath = reportPath;
	}

	setStatus(status: ReportStatus) {
		this.state.status = status;
		if (status === 'idle' || status === 'generating') {
			this.state.errorMessage = null;
		}
	}

	setError(errorMessage: string) {
		this.state.status = 'error';
		this.state.errorMessage = errorMessage;
		this.state.progress = 0;
	}

	setProgress(progress: number) {
		this.state.progress = Math.min(100, Math.max(0, progress));
	}

	// Métodos para preview
	setFilename(filename: string) {
		this.state.filename = filename;
	}

	setBase64Content(base64Content: string) {
		this.state.base64Content = base64Content;
	}

	togglePreview() {
		this.state.showPreview = !this.state.showPreview;
	}

	openPreview() {
		this.state.showPreview = true;
	}

	closePreview() {
		this.state.showPreview = false;
	}

	// Método para iniciar generación
	startGeneration(query: string, reportId?: string) {
		this.state.status = 'generating';
		this.state.errorMessage = null;
		this.state.progress = 0;
		this.state.reportId = reportId || crypto.randomUUID();
		this.state.reportData = { query };
	}

	// Método para completar generación exitosamente
	completeGeneration(data: {
		reportPath: string;
		reportHtml: string;
		filename?: string;
		base64Content?: string;
	}) {
		this.state.status = 'ready';
		this.state.reportPath = data.reportPath;
		this.state.reportHtml = data.reportHtml;
		this.state.progress = 100;

		if (data.filename) {
			this.state.filename = data.filename;
		}

		if (data.base64Content) {
			this.state.base64Content = data.base64Content;
		}

		// Abrir preview automáticamente cuando está listo
		this.state.showPreview = true;
	}

	// Métodos de anotaciones
	addAnnotation(annotation: Omit<Annotation, 'id' | 'timestamp'>) {
		const newAnnotation: Annotation = {
			...annotation,
			id: crypto.randomUUID(),
			timestamp: new Date().toISOString()
		};

		this.state.annotations = [...this.state.annotations, newAnnotation];
		return newAnnotation;
	}

	updateAnnotation(id: string, updatedAnnotation: Partial<Annotation>) {
		this.state.annotations = this.state.annotations.map((ann) =>
			ann.id === id ? { ...ann, ...updatedAnnotation } : ann
		);
	}

	deleteAnnotation(id: string) {
		this.state.annotations = this.state.annotations.filter((ann) => ann.id !== id);
	}

	getAnnotationById(id: string): Annotation | undefined {
		return this.state.annotations.find((ann) => ann.id === id);
	}

	clearAnnotations() {
		this.state.annotations = [];
	}

	// Métodos de texto seleccionado
	setSelectedText(selectedText: string) {
		this.state.selectedText = selectedText;
	}

	clearSelectedText() {
		this.state.selectedText = '';
	}

	// Reset completo
	reset() {
		this.state.reportId = null;
		this.state.reportData = null;
		this.state.reportHtml = '';
		this.state.reportPath = '';
		this.state.status = 'idle';
		this.state.annotations = [];
		this.state.selectedText = '';
		this.state.errorMessage = null;
		this.state.progress = 0;
		this.state.showPreview = false;
		this.state.filename = '';
		this.state.base64Content = '';
	}

	// Reset solo status (mantiene datos)
	resetStatus() {
		this.state.status = 'idle';
		this.state.errorMessage = null;
		this.state.progress = 0;
	}
}

// Exportar instancia única del store
export const reportStore = new ReportStore();
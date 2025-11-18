/**
 * Report Store - Maneja el estado de reportes, anotaciones y generación
 * Usa Svelte 5 runes para reactividad moderna
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
	reportData: any;
	reportHtml: string;
	reportPath: string;
	status: ReportStatus;
	annotations: Annotation[];
	selectedText: string;
	errorMessage: string | null;
}

class ReportStore {
	private state = $state<ReportState>({
		reportData: null,
		reportHtml: '',
		reportPath: '',
		status: 'idle',
		annotations: [],
		selectedText: '',
		errorMessage: null
	});

	// Getters reactivos
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

	// Derived: indica si está generando
	get isGenerating() {
		return this.state.status === 'generating';
	}

	// Derived: indica si está listo
	get isReady() {
		return this.state.status === 'ready';
	}

	// Métodos de actualización
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
		this.state.reportData = null;
		this.state.reportHtml = '';
		this.state.reportPath = '';
		this.state.status = 'idle';
		this.state.annotations = [];
		this.state.selectedText = '';
		this.state.errorMessage = null;
	}

	// Reset solo status (mantiene datos)
	resetStatus() {
		this.state.status = 'idle';
		this.state.errorMessage = null;
	}
}

// Exportar instancia única del store
export const reportStore = new ReportStore();

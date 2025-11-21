/**
 * Query Store - Maneja el estado de consultas, historial y loading
 * Usa Svelte 5 runes ($state, $derived) para reactividad moderna
 * Auto-persiste en localStorage
 */

export interface Query {
	id: string;
	text: string;
	timestamp: string;
	response: string;
	type: 'consultation' | 'gap_analysis';
	hasDocuments: boolean;
	metadata?: Record<string, any>;
}

interface QueryState {
	query: string;
	response: any;
	isLoading: boolean;
	error: string | null;
	recentQueries: Query[];
}

class QueryStore {
	// Estado reactivo con Svelte 5 runes
	private state = $state<QueryState>({
		query: '',
		response: null,
		isLoading: false,
		error: null,
		recentQueries: []
	});

	constructor() {
		// Cargar datos guardados al inicializar
		if (typeof window !== 'undefined') {
			this.loadStoredQueries();
		}
	}

	// Getters reactivos
	get query() {
		return this.state.query;
	}

	get response() {
		return this.state.response;
	}

	get isLoading() {
		return this.state.isLoading;
	}

	get error() {
		return this.state.error;
	}

	get recentQueries() {
		return this.state.recentQueries;
	}

	// Derived: total de consultas
	get totalQueries() {
		return this.state.recentQueries.length;
	}

	// Métodos de actualización
	setQuery(query: string) {
		this.state.query = query;
	}

	setResponse(response: any) {
		this.state.response = response;
		this.state.error = null;

		// Auto-agregar al historial cuando hay una respuesta
		if (this.state.query && response) {
			this.addToHistory({
				id: crypto.randomUUID(),
				text: this.state.query,
				timestamp: new Date().toISOString(),
				response: typeof response === 'string' ? response : response.response || '',
				type: response.type || 'consultation',
				hasDocuments: response.hasDocuments || false,
				metadata: typeof response === 'object' ? response.metadata : {}
			});
		}
	}

	startLoading() {
		this.state.isLoading = true;
		this.state.error = null;
	}

	stopLoading() {
		this.state.isLoading = false;
	}

	setError(error: string) {
		this.state.error = error;
		this.state.isLoading = false;
	}

	reset() {
		this.state.query = '';
		this.state.response = null;
		this.state.isLoading = false;
		this.state.error = null;
	}

	// Métodos de historial
	addToHistory(queryObj: Query) {
		// Agregar al inicio del array (más reciente primero)
		this.state.recentQueries = [queryObj, ...this.state.recentQueries];

		// Limitar a 100 consultas máximo
		if (this.state.recentQueries.length > 100) {
			this.state.recentQueries = this.state.recentQueries.slice(0, 100);
		}

		// Persistir inmediatamente
		this.saveToLocalStorage();
	}

	loadStoredQueries() {
		try {
			const stored = localStorage.getItem('recentQueries');
			if (stored) {
				this.state.recentQueries = JSON.parse(stored);
			}
		} catch (error) {
			console.error('Error loading stored queries:', error);
			this.state.recentQueries = [];
		}
	}

	private saveToLocalStorage() {
		if (typeof window !== 'undefined') {
			try {
				localStorage.setItem('recentQueries', JSON.stringify(this.state.recentQueries));
			} catch (error) {
				console.error('Error saving to localStorage:', error);
			}
		}
	}

	getQueryById(id: string): Query | undefined {
		return this.state.recentQueries.find((q) => q.id === id);
	}

	removeQueryFromHistory(id: string) {
		this.state.recentQueries = this.state.recentQueries.filter((q) => q.id !== id);
		this.saveToLocalStorage();
	}

	clearAllHistory() {
		this.state.recentQueries = [];
		if (typeof window !== 'undefined') {
			localStorage.removeItem('recentQueries');
		}
	}

	searchInHistory(searchTerm: string): Query[] {
		if (!searchTerm.trim()) {
			return this.state.recentQueries;
		}

		const term = searchTerm.toLowerCase();
		return this.state.recentQueries.filter(
			(q) =>
				q.text.toLowerCase().includes(term) ||
				q.response.toLowerCase().includes(term) ||
				q.type.toLowerCase().includes(term)
		);
	}

	// Filtrar por tipo
	filterByType(type: 'all' | 'consultation' | 'gap_analysis'): Query[] {
		if (type === 'all') {
			return this.state.recentQueries;
		}
		return this.state.recentQueries.filter((q) => q.type === type);
	}
}

// Exportar instancia única del store
export const queryStore = new QueryStore();
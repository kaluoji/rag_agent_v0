/**
 * Barrel export para todos los stores
 * Permite importar con: import { queryStore, reportStore } from '$lib/stores'
 */

export { queryStore } from './query-store.svelte.js';
export { reportStore } from './report-store.svelte.js';

// Re-exportar tipos
export type { Query } from './query-store.svelte.js';
export type { Annotation, ReportStatus } from './report-store.svelte.js';

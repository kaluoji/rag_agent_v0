<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { goto } from '$app/navigation';
  import { queryStore, setQueryLoading, setQueryError, setSelectedSector, setSelectedType } from '$lib/stores';
  import { deleteQueryAPI } from '$lib/api';
  import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
  import Dialog from '$lib/components/Dialog.svelte';
  import type { Query } from '$lib/types';

  /**
   * Query history page - Browse and manage all queries
   * Features: search, filtering, pagination, delete
   * Accessible with keyboard navigation and screen readers
   */

  let queries: Query[] = [];
  let filteredQueries: Query[] = [];
  let loading = false;
  let error: string | null = null;
  let searchTerm = '';
  let selectedSector: string | null = null;
  let selectedType: Query['type'] | null = null;
  let totalQueries = 0;
  let showDeleteDialog = false;
  let queryToDelete: Query | null = null;

  // Subscribe to query store
  const unsubscribe = queryStore.subscribe((state) => {
    queries = state.queries;
    error = state.error;
    loading = state.loading;
    selectedSector = state.selectedSector;
    selectedType = state.selectedType;
    applyFilters();
  });

  /**
   * Apply search and filter logic
   */
  function applyFilters(): void {
    let filtered = [...queries];

    // Apply search term
    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(
        (q) =>
          q.text.toLowerCase().includes(term) ||
          q.response?.toLowerCase().includes(term) ||
          q.id.includes(term)
      );
    }

    // Apply sector filter
    if (selectedSector) {
      filtered = filtered.filter((q) => q.sector === selectedSector);
    }

    // Apply type filter
    if (selectedType) {
      filtered = filtered.filter((q) => q.type === selectedType);
    }

    filteredQueries = filtered;
    totalQueries = filtered.length;
  }

  /**
   * Handle search input change
   */
  function handleSearch(event: Event): void {
    const target = event.target as HTMLInputElement;
    searchTerm = target.value;
    applyFilters();
  }

  /**
   * Handle sector filter change
   */
  function handleSectorChange(event: Event): void {
    const target = event.target as HTMLSelectElement;
    const newSector = target.value || null;
    setSelectedSector(newSector);
  }

  /**
   * Handle type filter change
   */
  function handleTypeChange(event: Event): void {
    const target = event.target as HTMLSelectElement;
    const newType = (target.value || null) as Query['type'] | null;
    setSelectedType(newType);
  }

  /**
   * Clear all filters
   */
  function clearFilters(): void {
    searchTerm = '';
    setSelectedSector(null);
    setSelectedType(null);
    applyFilters();
  }

  /**
   * Navigate to query detail view
   */
  function viewQuery(queryId: string): void {
    goto(`/consulta/${queryId}`);
  }

  /**
   * Confirm delete action
   */
  function confirmDelete(query: Query): void {
    queryToDelete = query;
    showDeleteDialog = true;
  }

  /**
   * Delete a query
   */
  async function deleteQuery(): Promise<void> {
    if (!queryToDelete) return;

    try {
      setQueryLoading(true);
      const result = await deleteQueryAPI(queryToDelete.id);

      if (result.error) {
        setQueryError(`Failed to delete query: ${result.error.message}`);
      } else {
        // Query will be removed from store by parent component
        setQueryError(null);
      }
    } catch (err) {
      setQueryError(err instanceof Error ? err.message : 'Failed to delete query');
    } finally {
      setQueryLoading(false);
      showDeleteDialog = false;
      queryToDelete = null;
    }
  }

  /**
   * Format timestamp for display
   */
  function formatDate(date: Date | string): string {
    const d = typeof date === 'string' ? new Date(date) : date;
    return d.toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  onMount(() => {
    document.title = 'Historial de Consultas - RAG Regulatory';
  });

  onDestroy(() => {
    unsubscribe();
  });
</script>

<svelte:head>
  <title>Historial de Consultas - RAG Regulatory</title>
  <meta name="description" content="Browse and manage regulatory compliance queries" />
</svelte:head>

<div class="historial-container">
  <!-- Header -->
  <div class="page-header">
    <div>
      <h1>Historial de Consultas</h1>
      <p class="subtitle">Busca y gestiona tus consultas regulatorias</p>
    </div>
    <div class="header-stats">
      <span class="stat-item" aria-label="Total queries">
        <span class="stat-value">{totalQueries}</span>
        <span class="stat-label">Consultas</span>
      </span>
    </div>
  </div>

  <!-- Filter and Search Section -->
  <div class="filter-section" role="search" aria-label="Search and filter queries">
    <!-- Search Input -->
    <div class="search-group">
      <input
        type="text"
        class="search-input"
        placeholder="Buscar por texto, ID..."
        value={searchTerm}
        on:input={handleSearch}
        aria-label="Search queries"
      />
      <svg class="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"></circle>
        <path d="m21 21-4.35-4.35"></path>
      </svg>
    </div>

    <!-- Filter Controls -->
    <div class="filter-controls">
      <div class="filter-group">
        <label for="sector-select" class="filter-label">Sector:</label>
        <select
          id="sector-select"
          class="filter-select"
          value={selectedSector || ''}
          on:change={handleSectorChange}
          aria-label="Filter by sector"
        >
          <option value="">Todos</option>
          <option value="banking">Banca</option>
          <option value="insurance">Seguros</option>
          <option value="telecoms">Telecomunicaciones</option>
          <option value="general">General</option>
        </select>
      </div>

      <div class="filter-group">
        <label for="type-select" class="filter-label">Tipo:</label>
        <select
          id="type-select"
          class="filter-select"
          value={selectedType || ''}
          on:change={handleTypeChange}
          aria-label="Filter by analysis type"
        >
          <option value="">Todos</option>
          <option value="compliance">Cumplimiento</option>
          <option value="gap-analysis">Análisis de Brechas</option>
          <option value="report">Reporte</option>
        </select>
      </div>

      <button
        class="clear-filters-btn"
        on:click={clearFilters}
        aria-label="Clear all filters"
        title="Clear all filters"
      >
        Limpiar filtros
      </button>
    </div>
  </div>

  <!-- Error Message -->
  {#if error}
    <div class="error-message" role="alert" aria-live="polite">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="8" x2="12" y2="12"></line>
        <line x1="12" y1="16" x2="12.01" y2="16"></line>
      </svg>
      <span>{error}</span>
    </div>
  {/if}

  <!-- Loading State -->
  {#if loading}
    <div class="loading-container">
      <LoadingSpinner />
      <p>Cargando consultas...</p>
    </div>
  {/if}

  <!-- Queries List -->
  {#if !loading && filteredQueries.length > 0}
    <div class="queries-list" role="list">
      {#each filteredQueries as query (query.id)}
        <div class="query-card" role="listitem">
          <div class="query-header">
            <div class="query-title-section">
              <h3 class="query-text">{query.text.substring(0, 80)}...</h3>
              <div class="query-badges">
                <span class="badge status" class:completed={query.status === 'completed'} class:pending={query.status === 'pending'} class:failed={query.status === 'failed'}>
                  {query.status === 'completed' ? 'Completada' : query.status === 'pending' ? 'Pendiente' : 'Error'}
                </span>
                {#if query.sector}
                  <span class="badge sector">{query.sector}</span>
                {/if}
                {#if query.type}
                  <span class="badge type">{query.type}</span>
                {/if}
              </div>
            </div>
            <div class="query-date">
              {formatDate(query.timestamp)}
            </div>
          </div>

          {#if query.response}
            <p class="query-preview">{query.response.substring(0, 150)}...</p>
          {/if}

          <div class="query-actions">
            <button
              class="action-btn view-btn"
              on:click={() => viewQuery(query.id)}
              aria-label="View query details"
              title="Ver detalles"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                <circle cx="12" cy="12" r="3"></circle>
              </svg>
              Ver
            </button>
            <button
              class="action-btn delete-btn"
              on:click={() => confirmDelete(query)}
              aria-label="Delete query"
              title="Eliminar"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"></polyline>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              </svg>
              Eliminar
            </button>
          </div>
        </div>
      {/each}
    </div>
  {/if}

  <!-- Empty State -->
  {#if !loading && filteredQueries.length === 0 && queries.length === 0}
    <div class="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"></circle>
        <path d="m21 21-4.35-4.35"></path>
      </svg>
      <h3>No hay consultas</h3>
      <p>Comienza a hacer consultas regulatorias desde la página principal</p>
    </div>
  {/if}

  <!-- No Results State -->
  {#if !loading && filteredQueries.length === 0 && queries.length > 0}
    <div class="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M9.59 0h1.42A2 2 0 0 1 13 2v16a2 2 0 0 1-2 2H9.59a2 2 0 0 1-2-2V2A2 2 0 0 1 9.59 0z"></path>
        <path d="M5 9h3m6 0h3"></path>
      </svg>
      <h3>Sin resultados</h3>
      <p>Intenta cambiar tus filtros de búsqueda</p>
    </div>
  {/if}
</div>

<!-- Delete Confirmation Dialog -->
<Dialog
  isOpen={showDeleteDialog}
  title="Eliminar consulta"
  type="confirm"
  onConfirm={deleteQuery}
  onCancel={() => {
    showDeleteDialog = false;
    queryToDelete = null;
  }}
>
  <p slot="content">
    ¿Estás seguro de que deseas eliminar esta consulta? Esta acción no se puede deshacer.
  </p>
</Dialog>

<style>
  .historial-container {
    display: flex;
    flex-direction: column;
    gap: 2rem;
    max-width: 1400px;
    margin: 0 auto;
    width: 100%;
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 2rem;
  }

  .page-header h1 {
    margin: 0;
    font-size: 2rem;
    color: var(--color-text-primary);
  }

  .subtitle {
    margin: 0.5rem 0 0 0;
    color: var(--color-text-secondary);
    font-size: 1rem;
  }

  .header-stats {
    display: flex;
    gap: 2rem;
    align-items: center;
  }

  .stat-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
  }

  .stat-value {
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--color-primary);
  }

  .stat-label {
    font-size: 0.875rem;
    color: var(--color-text-secondary);
  }

  /* Filter Section */
  .filter-section {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1.5rem;
    background-color: var(--color-bg-elevated);
    border-radius: 8px;
    border: 1px solid var(--color-border);
  }

  .search-group {
    position: relative;
    display: flex;
    align-items: center;
  }

  .search-input {
    flex: 1;
    padding: 0.75rem 1rem 0.75rem 2.5rem;
    border: 1px solid var(--color-border);
    border-radius: 6px;
    background-color: var(--color-bg);
    color: var(--color-text-primary);
    font-size: 1rem;
    transition: all var(--transition-fast);
  }

  .search-input:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(0, 84, 143, 0.1);
  }

  .search-icon {
    position: absolute;
    left: 0.75rem;
    color: var(--color-text-secondary);
    pointer-events: none;
  }

  .filter-controls {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    align-items: flex-end;
  }

  .filter-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .filter-label {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--color-text-secondary);
  }

  .filter-select {
    padding: 0.75rem 1rem;
    border: 1px solid var(--color-border);
    border-radius: 6px;
    background-color: var(--color-bg);
    color: var(--color-text-primary);
    font-size: 1rem;
    cursor: pointer;
    transition: all var(--transition-fast);
    min-width: 150px;
  }

  .filter-select:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(0, 84, 143, 0.1);
  }

  .filter-select:hover {
    border-color: var(--color-primary);
  }

  .clear-filters-btn {
    padding: 0.75rem 1.5rem;
    background-color: transparent;
    color: var(--color-primary);
    border: 1px solid var(--color-primary);
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
    transition: all var(--transition-fast);
  }

  .clear-filters-btn:hover {
    background-color: var(--color-primary);
    color: white;
  }

  .clear-filters-btn:active {
    transform: scale(0.98);
  }

  /* Error Message */
  .error-message {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    background-color: rgba(220, 38, 38, 0.1);
    border: 1px solid rgba(220, 38, 38, 0.3);
    border-radius: 6px;
    color: #991b1b;
  }

  /* Queries List */
  .queries-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .query-card {
    padding: 1.5rem;
    background-color: var(--color-bg-elevated);
    border: 1px solid var(--color-border);
    border-radius: 8px;
    transition: all var(--transition-fast);
  }

  .query-card:hover {
    border-color: var(--color-primary);
    box-shadow: var(--shadow-md);
  }

  .query-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .query-title-section {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .query-text {
    margin: 0;
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--color-text-primary);
  }

  .query-badges {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }

  .badge {
    display: inline-block;
    padding: 0.375rem 0.75rem;
    font-size: 0.8125rem;
    font-weight: 500;
    border-radius: 4px;
    white-space: nowrap;
  }

  .badge.status {
    background-color: rgba(34, 197, 94, 0.1);
    color: #166534;
  }

  .badge.status.completed {
    background-color: rgba(34, 197, 94, 0.1);
    color: #166534;
  }

  .badge.status.pending {
    background-color: rgba(245, 158, 11, 0.1);
    color: #92400e;
  }

  .badge.status.failed {
    background-color: rgba(220, 38, 38, 0.1);
    color: #991b1b;
  }

  .badge.sector {
    background-color: rgba(59, 130, 246, 0.1);
    color: #1e40af;
  }

  .badge.type {
    background-color: rgba(168, 85, 247, 0.1);
    color: #6b21a8;
  }

  .query-date {
    font-size: 0.875rem;
    color: var(--color-text-secondary);
    white-space: nowrap;
  }

  .query-preview {
    margin: 0 0 1rem 0;
    color: var(--color-text-secondary);
    font-size: 0.95rem;
    line-height: 1.5;
  }

  .query-actions {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
  }

  .action-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    border: 1px solid var(--color-border);
    border-radius: 6px;
    background-color: transparent;
    color: var(--color-text-secondary);
    cursor: pointer;
    font-weight: 500;
    font-size: 0.875rem;
    transition: all var(--transition-fast);
  }

  .action-btn:hover {
    border-color: var(--color-primary);
    color: var(--color-primary);
    background-color: var(--color-bg-alt);
  }

  .action-btn.delete-btn:hover {
    border-color: #dc2626;
    color: #dc2626;
  }

  .action-btn:active {
    transform: scale(0.95);
  }

  /* Loading Container */
  .loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    padding: 3rem;
    color: var(--color-text-secondary);
  }

  /* Empty State */
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    padding: 3rem;
    text-align: center;
    color: var(--color-text-secondary);
  }

  .empty-state svg {
    color: var(--color-text-secondary);
    opacity: 0.5;
  }

  .empty-state h3 {
    margin: 0;
    color: var(--color-text-primary);
    font-size: 1.25rem;
  }

  .empty-state p {
    margin: 0.5rem 0 0 0;
    max-width: 400px;
  }

  /* Responsive Design */
  @media (max-width: 1024px) {
    .page-header {
      flex-direction: column;
      gap: 1rem;
    }

    .header-stats {
      flex-direction: column;
      align-items: flex-start;
    }

    .filter-controls {
      flex-direction: column;
      align-items: stretch;
    }

    .filter-group {
      width: 100%;
    }

    .filter-select {
      min-width: 100%;
    }

    .clear-filters-btn {
      width: 100%;
    }
  }

  @media (max-width: 768px) {
    .historial-container {
      gap: 1.5rem;
    }

    .page-header h1 {
      font-size: 1.5rem;
    }

    .query-header {
      flex-direction: column;
    }

    .query-date {
      font-size: 0.8rem;
    }

    .query-actions {
      justify-content: flex-start;
    }
  }

  @media (max-width: 480px) {
    .page-header {
      gap: 0.5rem;
    }

    .page-header h1 {
      font-size: 1.25rem;
    }

    .subtitle {
      display: none;
    }

    .search-input {
      padding: 0.625rem 1rem 0.625rem 2rem;
    }

    .filter-controls {
      flex-direction: column;
    }

    .query-card {
      padding: 1rem;
    }

    .query-badges {
      gap: 0.375rem;
    }

    .badge {
      padding: 0.25rem 0.5rem;
      font-size: 0.75rem;
    }

    .action-btn {
      padding: 0.375rem 0.75rem;
      font-size: 0.75rem;
    }

    .action-btn svg {
      width: 14px;
      height: 14px;
    }
  }

  /* Accessibility */
  :focus-visible {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
  }

  /* Dark mode */
  :global([data-theme='dark']) .error-message {
    background-color: rgba(220, 38, 38, 0.15);
    color: #fecaca;
  }

  :global([data-theme='dark']) .badge.status.completed {
    background-color: rgba(34, 197, 94, 0.15);
    color: #86efac;
  }

  :global([data-theme='dark']) .badge.status.pending {
    background-color: rgba(245, 158, 11, 0.15);
    color: #fcd34d;
  }

  :global([data-theme='dark']) .badge.status.failed {
    background-color: rgba(220, 38, 38, 0.15);
    color: #fecaca;
  }

  :global([data-theme='dark']) .badge.sector {
    background-color: rgba(59, 130, 246, 0.15);
    color: #93c5fd;
  }

  :global([data-theme='dark']) .badge.type {
    background-color: rgba(168, 85, 247, 0.15);
    color: #d8b4fe;
  }
</style>

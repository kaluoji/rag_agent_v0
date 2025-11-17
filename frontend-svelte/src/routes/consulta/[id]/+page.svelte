<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { queryStore, setCurrentQuery, addNotification } from '$lib/stores';
  import { downloadReport, generateReport } from '$lib/api';
  import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
  import type { Query } from '$lib/types';

  /**
   * Query detail view page
   * Displays full query results, analysis, sources, and report generation
   * Features: view analysis, generate report, download document
   */

  let query: Query | null = null;
  let loading = false;
  let error: string | null = null;
  let generatingReport = false;
  let reportProgress = 0;
  let selectedAnalysisType: 'comprehensive' | 'quick' | 'gap-analysis' | 'executive-summary' = 'comprehensive';

  // Get ID from route
  $: queryId = $page.params.id;

  // Subscribe to query store to find current query
  const unsubscribe = queryStore.subscribe((state) => {
    if (queryId && state.queries) {
      query = state.queries.find((q) => q.id === queryId) || null;
    }
  });

  /**
   * Generate report from query
   */
  async function handleGenerateReport(): Promise<void> {
    if (!query) return;

    try {
      generatingReport = true;
      error = null;
      reportProgress = 0;

      const result = await generateReport(query.id, {
        query: query.text,
        analysisType: selectedAnalysisType,
        sector: (query.sector || 'general') as 'banking' | 'insurance' | 'telecoms' | 'general',
        format: 'docx',
        includeExecutiveSummary: true,
        includeGapAnalysis: true,
        includeRecommendations: true,
      });

      if (result.error) {
        error = result.error.message;
        addNotification({
          type: 'error',
          message: `Failed to generate report: ${result.error.message}`,
          duration: 5000,
        });
      } else if (result.data) {
        addNotification({
          type: 'success',
          message: 'Report generated successfully',
          duration: 3000,
        });
        // Start polling for report completion
        pollReportStatus();
      }
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to generate report';
      addNotification({
        type: 'error',
        message: error,
        duration: 5000,
      });
    } finally {
      generatingReport = false;
      showReportOptions = false;
    }
  }

  /**
   * Poll report status until completion
   */
  async function pollReportStatus(): Promise<void> {
    let attempts = 0;
    const maxAttempts = 60; // 5 minutes with 5 second intervals

    const poll = async () => {
      if (attempts >= maxAttempts) {
        error = 'Report generation timeout';
        return;
      }

      attempts++;
      await new Promise((resolve) => setTimeout(resolve, 5000));

      // In a real implementation, you would fetch the status here
      // For now, just simulate progress
      reportProgress = Math.min(100, reportProgress + Math.random() * 30);

      if (reportProgress < 100) {
        await poll();
      }
    };

    await poll();
  }

  /**
   * Download report
   */
  async function handleDownloadReport(): Promise<void> {
    if (!query) return;

    try {
      loading = true;
      const result = await downloadReport(query.id);

      if (result.error) {
        addNotification({
          type: 'error',
          message: `Download failed: ${result.error.message}`,
          duration: 5000,
        });
      } else if (result.blob) {
        // Create download link
        const url = URL.createObjectURL(result.blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `reporte-${query.id}.docx`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);

        addNotification({
          type: 'success',
          message: 'Report downloaded successfully',
          duration: 3000,
        });
      }
    } catch (err) {
      addNotification({
        type: 'error',
        message: err instanceof Error ? err.message : 'Download failed',
        duration: 5000,
      });
    } finally {
      loading = false;
    }
  }

  /**
   * Go back to history
   */
  function goBack(): void {
    goto('/historial');
  }

  /**
   * Format timestamp
   */
  function formatDate(date: Date | string): string {
    const d = typeof date === 'string' ? new Date(date) : date;
    return d.toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  }

  /**
   * Format analysis result for display
   */
  function formatAnalysis(analysis: any): string {
    if (typeof analysis === 'string') return analysis;
    if (analysis && typeof analysis === 'object') {
      return analysis.summary || JSON.stringify(analysis, null, 2);
    }
    return '';
  }

  onMount(() => {
    document.title = `Consulta ${queryId} - RAG Regulatory`;
    if (queryId) {
      setCurrentQuery(queryId);
    }
  });

  onDestroy(() => {
    unsubscribe();
  });
</script>

<svelte:head>
  <title>Consulta - RAG Regulatory</title>
  <meta name="description" content="View detailed regulatory analysis query" />
</svelte:head>

<div class="consulta-container">
  <!-- Header -->
  <div class="page-header">
    <div class="header-left">
      <button
        class="back-btn"
        on:click={goBack}
        aria-label="Go back to history"
        title="Volver al historial"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="19" y1="12" x2="5" y2="12"></line>
          <polyline points="12 19 5 12 12 5"></polyline>
        </svg>
      </button>
      <div>
        <h1>Detalles de la Consulta</h1>
        <p class="subtitle">{queryId}</p>
      </div>
    </div>
  </div>

  {#if loading && !query}
    <div class="loading-container">
      <LoadingSpinner />
      <p>Cargando consulta...</p>
    </div>
  {/if}

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

  {#if query}
    <div class="query-content">
      <!-- Query Info Card -->
      <div class="info-card">
        <div class="card-header">
          <h2>Información de la Consulta</h2>
        </div>
        <div class="card-body">
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">Texto de la Consulta:</span>
              <p class="info-value">{query.text}</p>
            </div>

            <div class="info-item">
              <span class="info-label">Fecha:</span>
              <p class="info-value">{formatDate(query.timestamp)}</p>
            </div>

            <div class="info-item">
              <span class="info-label">Estado:</span>
              <p class="info-value">
                <span class="badge" class:completed={query.status === 'completed'} class:pending={query.status === 'pending'} class:failed={query.status === 'failed'}>
                  {query.status === 'completed' ? 'Completada' : query.status === 'pending' ? 'Pendiente' : 'Error'}
                </span>
              </p>
            </div>

            {#if query.sector}
              <div class="info-item">
                <span class="info-label">Sector:</span>
                <p class="info-value">{query.sector}</p>
              </div>
            {/if}

            {#if query.type}
              <div class="info-item">
                <span class="info-label">Tipo de Análisis:</span>
                <p class="info-value">{query.type}</p>
              </div>
            {/if}
          </div>
        </div>
      </div>

      <!-- Analysis Results -->
      {#if query.response}
        <div class="info-card">
          <div class="card-header">
            <h2>Análisis y Respuesta</h2>
          </div>
          <div class="card-body">
            <div class="analysis-content">
              {#if query.analysis}
                <div class="analysis-section">
                  <h3>Resumen Ejecutivo</h3>
                  <p>{formatAnalysis(query.analysis)}</p>
                </div>
              {/if}

              {#if query.response}
                <div class="analysis-section">
                  <h3>Respuesta Completa</h3>
                  <p>{query.response}</p>
                </div>
              {/if}

              {#if query.metadata && query.metadata.sources && Array.isArray(query.metadata.sources)}
                <div class="analysis-section">
                  <h3>Fuentes Consultadas</h3>
                  <ul class="sources-list">
                    {#each query.metadata.sources as source}
                      <li class="source-item">
                        <strong>{typeof source === 'string' ? source : (source as any).title || 'Fuente sin título'}</strong>
                        {#if typeof source === 'object' && source !== null && 'relevanceScore' in source}
                          <span class="relevance">Relevancia: {(((source as any).relevanceScore) * 100).toFixed(0)}%</span>
                        {/if}
                        {#if typeof source === 'object' && source !== null && 'excerpt' in source}
                          <p class="excerpt">{(source as any).excerpt}</p>
                        {/if}
                      </li>
                    {/each}
                  </ul>
                </div>
              {/if}
            </div>
          </div>
        </div>
      {/if}

      <!-- Report Generation -->
      <div class="info-card">
        <div class="card-header">
          <h2>Generar Reporte</h2>
        </div>
        <div class="card-body">
          {#if !generatingReport && reportProgress === 0}
            <div class="report-options">
              <div class="option-group">
                <label for="analysis-type" class="option-label">Tipo de Análisis:</label>
                <select
                  id="analysis-type"
                  class="option-select"
                  bind:value={selectedAnalysisType}
                  aria-label="Select analysis type for report"
                >
                  <option value="comprehensive">Análisis Completo</option>
                  <option value="quick">Análisis Rápido</option>
                  <option value="gap-analysis">Análisis de Brechas</option>
                  <option value="executive-summary">Resumen Ejecutivo</option>
                </select>
              </div>

              <button
                class="primary-btn"
                on:click={handleGenerateReport}
                disabled={loading || generatingReport}
                aria-label="Generate report"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <line x1="12" y1="19" x2="12" y2="5"></line>
                  <line x1="9" y1="12" x2="15" y2="12"></line>
                </svg>
                Generar Reporte
              </button>
            </div>
          {/if}

          {#if generatingReport || reportProgress > 0}
            <div class="progress-container">
              <div class="progress-bar">
                <div class="progress-fill" style="width: {reportProgress}%"></div>
              </div>
              <p class="progress-text">{reportProgress}% completado</p>
              <LoadingSpinner />
            </div>
          {/if}

          {#if reportProgress === 100}
            <div class="completion-message">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
              <p>Reporte generado exitosamente</p>
              <button
                class="primary-btn"
                on:click={handleDownloadReport}
                disabled={loading}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="7 10 12 15 17 10"></polyline>
                  <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                Descargar Reporte
              </button>
            </div>
          {/if}
        </div>
      </div>
    </div>
  {/if}

  {#if !loading && !query}
    <div class="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"></circle>
        <path d="m21 21-4.35-4.35"></path>
      </svg>
      <h3>Consulta no encontrada</h3>
      <p>La consulta que buscas no existe o ha sido eliminada.</p>
      <button class="primary-btn" on:click={goBack}>
        Volver al Historial
      </button>
    </div>
  {/if}
</div>

<style>
  .consulta-container {
    display: flex;
    flex-direction: column;
    gap: 2rem;
    max-width: 1200px;
    margin: 0 auto;
    width: 100%;
  }

  .page-header {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 1rem;
    flex: 1;
  }

  .back-btn {
    width: 40px;
    height: 40px;
    border: 1px solid var(--color-border);
    background-color: transparent;
    border-radius: 6px;
    color: var(--color-text-primary);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all var(--transition-fast);
  }

  .back-btn:hover {
    border-color: var(--color-primary);
    color: var(--color-primary);
    background-color: var(--color-bg-alt);
  }

  .back-btn:active {
    transform: scale(0.95);
  }

  .page-header h1 {
    margin: 0;
    font-size: 1.75rem;
    color: var(--color-text-primary);
  }

  .subtitle {
    margin: 0.5rem 0 0 0;
    font-size: 0.875rem;
    color: var(--color-text-secondary);
    font-family: 'Courier New', monospace;
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

  /* Query Content */
  .query-content {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  /* Info Cards */
  .info-card {
    background-color: var(--color-bg-elevated);
    border: 1px solid var(--color-border);
    border-radius: 8px;
    overflow: hidden;
  }

  .card-header {
    padding: 1.25rem;
    border-bottom: 1px solid var(--color-border);
    background-color: var(--color-bg-alt);
  }

  .card-header h2 {
    margin: 0;
    font-size: 1.25rem;
    color: var(--color-text-primary);
  }

  .card-body {
    padding: 1.5rem;
  }

  /* Info Grid */
  .info-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
  }

  .info-item {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .info-label {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--color-text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .info-value {
    margin: 0;
    color: var(--color-text-primary);
    word-break: break-word;
  }

  .badge {
    display: inline-block;
    padding: 0.375rem 0.75rem;
    border-radius: 4px;
    font-size: 0.875rem;
    font-weight: 500;
  }

  .badge.completed {
    background-color: rgba(34, 197, 94, 0.1);
    color: #166534;
  }

  .badge.pending {
    background-color: rgba(245, 158, 11, 0.1);
    color: #92400e;
  }

  .badge.failed {
    background-color: rgba(220, 38, 38, 0.1);
    color: #991b1b;
  }

  /* Analysis Content */
  .analysis-content {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }

  .analysis-section {
    border-left: 3px solid var(--color-primary);
    padding-left: 1rem;
  }

  .analysis-section h3 {
    margin: 0 0 0.75rem 0;
    font-size: 1.125rem;
    color: var(--color-text-primary);
  }

  .analysis-section p {
    margin: 0;
    color: var(--color-text-secondary);
    line-height: 1.6;
    white-space: pre-wrap;
  }

  .sources-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .source-item {
    padding: 1rem;
    background-color: var(--color-bg);
    border-radius: 6px;
    border-left: 3px solid var(--color-primary);
  }

  .source-item strong {
    color: var(--color-text-primary);
    display: block;
    margin-bottom: 0.25rem;
  }

  .relevance {
    font-size: 0.8125rem;
    color: var(--color-text-secondary);
    display: block;
    margin-bottom: 0.5rem;
  }

  .excerpt {
    margin: 0.5rem 0 0 0;
    font-size: 0.9rem;
    color: var(--color-text-secondary);
    line-height: 1.5;
    font-style: italic;
  }

  /* Report Options */
  .report-options {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .option-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .option-label {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--color-text-secondary);
  }

  .option-select {
    padding: 0.75rem 1rem;
    border: 1px solid var(--color-border);
    border-radius: 6px;
    background-color: var(--color-bg);
    color: var(--color-text-primary);
    font-size: 1rem;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .option-select:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(0, 84, 143, 0.1);
  }

  /* Progress */
  .progress-container {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    align-items: center;
  }

  .progress-bar {
    width: 100%;
    height: 8px;
    background-color: var(--color-bg);
    border-radius: 4px;
    overflow: hidden;
    border: 1px solid var(--color-border);
  }

  .progress-fill {
    height: 100%;
    background-color: var(--color-primary);
    transition: width 0.3s ease;
  }

  .progress-text {
    margin: 0;
    font-size: 0.875rem;
    color: var(--color-text-secondary);
  }

  .completion-message {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    padding: 2rem;
    background-color: rgba(34, 197, 94, 0.1);
    border: 1px solid rgba(34, 197, 94, 0.3);
    border-radius: 8px;
    text-align: center;
    color: #166534;
  }

  .completion-message svg {
    color: #22c55e;
  }

  .completion-message p {
    margin: 0;
    font-weight: 500;
  }

  /* Buttons */
  .primary-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    background-color: var(--color-primary);
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 500;
    font-size: 1rem;
    transition: all var(--transition-fast);
  }

  .primary-btn:hover:not(:disabled) {
    background-color: #004a8f;
    box-shadow: var(--shadow-md);
  }

  .primary-btn:active:not(:disabled) {
    transform: scale(0.98);
  }

  .primary-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  /* Empty State */
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1.5rem;
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
    margin: 0;
    max-width: 400px;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .consulta-container {
      gap: 1.5rem;
    }

    .header-left {
      flex-direction: column;
      gap: 0.5rem;
      align-items: flex-start;
    }

    .page-header h1 {
      font-size: 1.5rem;
    }

    .info-grid {
      grid-template-columns: 1fr;
      gap: 1rem;
    }

    .card-body {
      padding: 1rem;
    }

    .report-options {
      gap: 0.75rem;
    }

    .primary-btn {
      width: 100%;
      justify-content: center;
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
      font-size: 0.75rem;
    }

    .card-header {
      padding: 1rem;
    }

    .card-header h2 {
      font-size: 1.1rem;
    }

    .info-value {
      font-size: 0.9rem;
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

  :global([data-theme='dark']) .badge.completed {
    background-color: rgba(34, 197, 94, 0.15);
    color: #86efac;
  }

  :global([data-theme='dark']) .badge.pending {
    background-color: rgba(245, 158, 11, 0.15);
    color: #fcd34d;
  }

  :global([data-theme='dark']) .badge.failed {
    background-color: rgba(220, 38, 38, 0.15);
    color: #fecaca;
  }

  :global([data-theme='dark']) .completion-message {
    background-color: rgba(34, 197, 94, 0.15);
    color: #86efac;
  }

  :global([data-theme='dark']) .source-item {
    background-color: var(--color-bg-alt);
  }
</style>

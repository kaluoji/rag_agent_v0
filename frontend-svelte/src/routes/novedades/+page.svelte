<script lang="ts">
  import { onMount } from 'svelte';

  /**
   * News and updates page - Display regulatory news, updates, and announcements
   * Features: categorized news, filtering, search
   * Placeholder for news/updates feed
   */

  interface NewsItem {
    id: string;
    title: string;
    description: string;
    category: 'regulation' | 'update' | 'announcement' | 'alert';
    date: Date;
    source?: string;
    link?: string;
    priority?: 'low' | 'medium' | 'high' | 'critical';
  }

  let news: NewsItem[] = [];
  let filteredNews: NewsItem[] = [];
  let selectedCategory: NewsItem['category'] | null = null;
  let searchTerm = '';
  let loading = false;

  // Mock data - replace with API call
  const mockNews: NewsItem[] = [
    {
      id: '1',
      title: 'Nueva regulación de protección de datos',
      description: 'Se ha publicado una nueva regulación que afecta el procesamiento de datos personales en el sector financiero.',
      category: 'regulation',
      date: new Date('2024-11-15'),
      priority: 'high',
    },
    {
      id: '2',
      title: 'Actualización de requisitos de cumplimiento',
      description: 'Actualización importante en los requisitos de cumplimiento para instituciones de telecomunicaciones.',
      category: 'update',
      date: new Date('2024-11-14'),
      priority: 'medium',
    },
    {
      id: '3',
      title: 'Anuncio de cambios en la fecha límite',
      description: 'Se ha extendido la fecha límite de implementación para ciertos requisitos regulatorios.',
      category: 'announcement',
      date: new Date('2024-11-13'),
    },
    {
      id: '4',
      title: 'Alerta de incumplimiento potencial',
      description: 'Alerta sobre posibles incumplimientos en el sector de seguros respecto a nuevas regulaciones.',
      category: 'alert',
      date: new Date('2024-11-12'),
      priority: 'critical',
    },
  ];

  /**
   * Apply filters and search
   */
  function applyFilters(): void {
    let filtered = [...news];

    // Apply category filter
    if (selectedCategory) {
      filtered = filtered.filter((n) => n.category === selectedCategory);
    }

    // Apply search
    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(
        (n) =>
          n.title.toLowerCase().includes(term) ||
          n.description.toLowerCase().includes(term)
      );
    }

    // Sort by date (newest first)
    filtered.sort((a, b) => b.date.getTime() - a.date.getTime());

    filteredNews = filtered;
  }

  /**
   * Handle category filter change
   */
  function handleCategoryChange(event: Event): void {
    const target = event.target as HTMLSelectElement;
    selectedCategory = (target.value || null) as NewsItem['category'] | null;
    applyFilters();
  }

  /**
   * Handle search input
   */
  function handleSearch(event: Event): void {
    const target = event.target as HTMLInputElement;
    searchTerm = target.value;
    applyFilters();
  }

  /**
   * Clear all filters
   */
  function clearFilters(): void {
    searchTerm = '';
    selectedCategory = null;
    applyFilters();
  }

  /**
   * Get category label in Spanish
   */
  function getCategoryLabel(category: NewsItem['category']): string {
    const labels: Record<NewsItem['category'], string> = {
      regulation: 'Regulación',
      update: 'Actualización',
      announcement: 'Anuncio',
      alert: 'Alerta',
    };
    return labels[category];
  }

  /**
   * Get priority badge color
   */
  function getPriorityColor(priority: NewsItem['priority'] | undefined): string {
    const colors: Record<string, string> = {
      low: '#22c55e',
      medium: '#f59e0b',
      high: '#ef4444',
      critical: '#991b1b',
    };
    return colors[priority || 'low'] || '#cccccc';
  }

  /**
   * Format date
   */
  function formatDate(date: Date): string {
    return date.toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  }

  onMount(() => {
    document.title = 'Novedades - RAG Regulatory';
    loading = true;
    // Simulate loading
    setTimeout(() => {
      news = mockNews;
      loading = false;
      applyFilters();
    }, 500);
  });
</script>

<svelte:head>
  <title>Novedades - RAG Regulatory</title>
  <meta name="description" content="Stay updated with regulatory news and announcements" />
</svelte:head>

<div class="novedades-container">
  <!-- Header -->
  <div class="page-header">
    <div>
      <h1>Novedades y Actualizaciones</h1>
      <p class="subtitle">Mantente informado sobre cambios regulatorios importantes</p>
    </div>
  </div>

  <!-- Filter Section -->
  <div class="filter-section" role="search" aria-label="Search and filter news">
    <!-- Search Input -->
    <div class="search-group">
      <input
        type="text"
        class="search-input"
        placeholder="Buscar novedades..."
        value={searchTerm}
        on:input={handleSearch}
        aria-label="Search news"
      />
      <svg class="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"></circle>
        <path d="m21 21-4.35-4.35"></path>
      </svg>
    </div>

    <!-- Category Filter -->
    <div class="filter-controls">
      <div class="filter-group">
        <label for="category-select" class="filter-label">Categoría:</label>
        <select
          id="category-select"
          class="filter-select"
          value={selectedCategory || ''}
          on:change={handleCategoryChange}
          aria-label="Filter by category"
        >
          <option value="">Todas</option>
          <option value="regulation">Regulación</option>
          <option value="update">Actualización</option>
          <option value="announcement">Anuncio</option>
          <option value="alert">Alerta</option>
        </select>
      </div>

      <button
        class="clear-filters-btn"
        on:click={clearFilters}
        aria-label="Clear all filters"
      >
        Limpiar filtros
      </button>
    </div>
  </div>

  <!-- Loading State -->
  {#if loading}
    <div class="loading-container">
      <div class="spinner"></div>
      <p>Cargando novedades...</p>
    </div>
  {/if}

  <!-- News List -->
  {#if !loading && filteredNews.length > 0}
    <div class="news-list" role="list">
      {#each filteredNews as item (item.id)}
        <article class="news-card" role="listitem">
          <div class="news-header">
            <div class="news-badges">
              <span class="badge category" class:regulation={item.category === 'regulation'} class:update={item.category === 'update'} class:announcement={item.category === 'announcement'} class:alert={item.category === 'alert'}>
                {getCategoryLabel(item.category)}
              </span>
              {#if item.priority}
                <span
                  class="badge priority"
                  title="Prioridad: {item.priority}"
                  style="--priority-color: {getPriorityColor(item.priority)}"
                >
                  {item.priority.charAt(0).toUpperCase() + item.priority.slice(1)}
                </span>
              {/if}
            </div>
            <time class="news-date" datetime={item.date.toISOString()}>
              {formatDate(item.date)}
            </time>
          </div>

          <h2 class="news-title">{item.title}</h2>
          <p class="news-description">{item.description}</p>

          {#if item.source || item.link}
            <div class="news-footer">
              {#if item.source}
                <span class="source">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"></path>
                    <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"></path>
                  </svg>
                  {item.source}
                </span>
              {/if}
              {#if item.link}
                <a href={item.link} class="read-more" target="_blank" rel="noopener noreferrer">
                  Leer más
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                    <polyline points="12 5 19 12 12 19"></polyline>
                  </svg>
                </a>
              {/if}
            </div>
          {/if}
        </article>
      {/each}
    </div>
  {/if}

  <!-- Empty State -->
  {#if !loading && filteredNews.length === 0}
    <div class="empty-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
      </svg>
      <h3>No hay novedades</h3>
      <p>
        {searchTerm || selectedCategory
          ? 'Intenta cambiar tus filtros de búsqueda'
          : 'No hay novedades disponibles en este momento'}
      </p>
    </div>
  {/if}
</div>

<style>
  .novedades-container {
    display: flex;
    flex-direction: column;
    gap: 2rem;
    max-width: 900px;
    margin: 0 auto;
    width: 100%;
  }

  /* Page Header */
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
    flex: 1;
    min-width: 150px;
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
  }

  .filter-select:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(0, 84, 143, 0.1);
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
    white-space: nowrap;
  }

  .clear-filters-btn:hover {
    background-color: var(--color-primary);
    color: white;
  }

  .clear-filters-btn:active {
    transform: scale(0.98);
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

  .spinner {
    width: 40px;
    height: 40px;
    border: 3px solid var(--color-border);
    border-top-color: var(--color-primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  /* News List */
  .news-list {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .news-card {
    padding: 1.5rem;
    background-color: var(--color-bg-elevated);
    border: 1px solid var(--color-border);
    border-radius: 8px;
    transition: all var(--transition-fast);
  }

  .news-card:hover {
    border-color: var(--color-primary);
    box-shadow: var(--shadow-md);
  }

  .news-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  .news-badges {
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

  .badge.category {
    background-color: rgba(59, 130, 246, 0.1);
    color: #1e40af;
  }

  .badge.category.regulation {
    background-color: rgba(0, 84, 143, 0.1);
    color: #004a8f;
  }

  .badge.category.update {
    background-color: rgba(59, 130, 246, 0.1);
    color: #1e40af;
  }

  .badge.category.announcement {
    background-color: rgba(34, 197, 94, 0.1);
    color: #166534;
  }

  .badge.category.alert {
    background-color: rgba(239, 68, 68, 0.1);
    color: #991b1b;
  }

  .badge.priority {
    background-color: var(--priority-color, #ccc);
    color: white;
  }

  .news-date {
    font-size: 0.875rem;
    color: var(--color-text-secondary);
    white-space: nowrap;
  }

  .news-title {
    margin: 0 0 0.75rem 0;
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--color-text-primary);
    line-height: 1.4;
  }

  .news-description {
    margin: 0 0 1rem 0;
    color: var(--color-text-secondary);
    font-size: 0.95rem;
    line-height: 1.6;
  }

  .news-footer {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    padding-top: 1rem;
    border-top: 1px solid var(--color-border);
  }

  .source {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.8125rem;
    color: var(--color-text-secondary);
  }

  .read-more {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    color: var(--color-primary);
    text-decoration: none;
    font-weight: 500;
    transition: all var(--transition-fast);
    cursor: pointer;
  }

  .read-more:hover {
    color: #004a8f;
    gap: 0.75rem;
  }

  .read-more:focus-visible {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
    border-radius: 3px;
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
  @media (max-width: 768px) {
    .novedades-container {
      gap: 1.5rem;
    }

    .page-header h1 {
      font-size: 1.5rem;
    }

    .subtitle {
      display: none;
    }

    .filter-controls {
      flex-direction: column;
      align-items: stretch;
    }

    .filter-group {
      width: 100%;
    }

    .filter-select {
      width: 100%;
    }

    .clear-filters-btn {
      width: 100%;
    }

    .news-card {
      padding: 1rem;
    }

    .news-header {
      flex-direction: column;
      gap: 0.5rem;
    }

    .news-title {
      font-size: 1.1rem;
    }

    .news-footer {
      flex-wrap: wrap;
      gap: 1rem;
    }
  }

  @media (max-width: 480px) {
    .page-header h1 {
      font-size: 1.25rem;
    }

    .search-input {
      padding: 0.625rem 1rem 0.625rem 2rem;
    }

    .badge {
      padding: 0.25rem 0.5rem;
      font-size: 0.75rem;
    }

    .news-card {
      padding: 0.75rem;
    }

    .news-title {
      font-size: 1rem;
    }

    .news-description {
      font-size: 0.875rem;
    }
  }

  /* Accessibility */
  :focus-visible {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
  }

  /* Dark mode */
  :global([data-theme='dark']) .badge.category.regulation {
    background-color: rgba(0, 84, 143, 0.15);
    color: #93c5fd;
  }

  :global([data-theme='dark']) .badge.category.update {
    background-color: rgba(59, 130, 246, 0.15);
    color: #93c5fd;
  }

  :global([data-theme='dark']) .badge.category.announcement {
    background-color: rgba(34, 197, 94, 0.15);
    color: #86efac;
  }

  :global([data-theme='dark']) .badge.category.alert {
    background-color: rgba(239, 68, 68, 0.15);
    color: #fecaca;
  }
</style>

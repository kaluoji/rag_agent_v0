{#if sources.length > 0}
  <div class="source-citation-container" role="region" aria-label="Document sources">
    <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>
      Sources ({sources.length})
    </h3>

    <div class="space-y-2">
      {#each displayedSources as source, index (source.title + index)}
        <button
          on:click={() => handleSourceClick(source)}
          class="source-item"
          aria-label="View source: {source.title}"
        >
          <div class="flex items-start gap-3 w-full">
            <!-- File Icon -->
            <span class="text-2xl flex-shrink-0" aria-hidden="true">
              {getFileIcon(source.title)}
            </span>

            <!-- Source Info -->
            <div class="flex-1 min-w-0 text-left">
              <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
                {source.title}
              </p>

              {#if source.excerpt}
                <p class="text-xs text-gray-600 dark:text-gray-400 line-clamp-2 mt-1">
                  {source.excerpt}
                </p>
              {/if}

              <div class="flex items-center gap-3 mt-1">
                {#if source.chunk !== undefined}
                  <span class="text-xs text-gray-500 dark:text-gray-500">
                    Chunk {source.chunk}
                  </span>
                {/if}

                {#if source.relevanceScore}
                  <span class="text-xs font-medium text-green-600 dark:text-green-400">
                    {formatRelevanceScore(source.relevanceScore)} relevant
                  </span>
                {/if}
              </div>
            </div>

            <!-- Arrow Icon -->
            <svg
              class="w-5 h-5 text-gray-400 flex-shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 5l7 7-7 7"
              />
            </svg>
          </div>
        </button>
      {/each}
    </div>

    <!-- Show More/Less Button -->
    {#if hasMore}
      <button
        on:click={() => (expanded = !expanded)}
        class="show-more-button"
        aria-expanded={expanded}
      >
        {#if expanded}
          Show less
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M5 15l7-7 7 7"
            />
          </svg>
        {:else}
          Show {sources.length - maxDisplay} more
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M19 9l-7 7-7-7"
            />
          </svg>
        {/if}
      </button>
    {/if}
  </div>
{/if}

<script lang="ts">
  /**
   * Citation component for document sources
   * Shows limited sources with expand/collapse functionality
   */

  import { createEventDispatcher } from 'svelte';
  import type { DocumentSource } from '$lib/types';

  export let sources: DocumentSource[] = [];
  export let maxDisplay = 3;

  const dispatch = createEventDispatcher<{
    sourceClick: { source: DocumentSource };
  }>();

  let expanded = false;

  $: displayedSources = expanded ? sources : sources.slice(0, maxDisplay);
  $: hasMore = sources.length > maxDisplay;

  function handleSourceClick(source: DocumentSource) {
    dispatch('sourceClick', { source });
  }

  function getFileIcon(title: string): string {
    const lowerTitle = title.toLowerCase();
    if (lowerTitle.includes('.pdf')) return '📄';
    if (lowerTitle.includes('.docx') || lowerTitle.includes('.doc')) return '📝';
    if (lowerTitle.includes('.xlsx') || lowerTitle.includes('.xls')) return '📊';
    return '📋';
  }

  function formatRelevanceScore(score: number): string {
    return `${Math.round(score * 100)}%`;
  }
</script>

<style>
  .source-citation-container {
    background-color: var(--color-bg-alt);
    border: 1px solid var(--color-border);
    border-radius: 8px;
    padding: 1rem;
  }

  .source-item {
    width: 100%;
    background-color: var(--color-bg-elevated);
    border: 1px solid var(--color-border);
    border-radius: 6px;
    padding: 0.75rem;
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .source-item:hover {
    border-color: var(--color-primary);
    box-shadow: var(--shadow-md);
    transform: translateY(-1px);
  }

  .source-item:active {
    transform: translateY(0);
  }

  .source-item:focus {
    outline: none;
    box-shadow: 0 0 0 3px rgba(0, 84, 143, 0.2);
  }

  .show-more-button {
    width: 100%;
    margin-top: 0.5rem;
    padding: 0.5rem;
    background-color: transparent;
    color: var(--color-primary);
    font-size: 0.875rem;
    font-weight: 600;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    transition: background-color var(--transition-fast);
  }

  .show-more-button:hover {
    background-color: var(--color-bg-elevated);
  }

  .show-more-button:focus {
    outline: none;
    box-shadow: 0 0 0 3px rgba(0, 84, 143, 0.2);
  }

  .line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>

{#if suggestions.length > 0}
  <div class="quick-suggestions-container" role="group" aria-label="Quick suggestions">
    <div class="flex gap-2 overflow-x-auto pb-2 scrollbar-thin">
      {#each suggestions as suggestion, index (suggestion)}
        <button
          on:click={() => handleSelect(suggestion)}
          on:keydown={(e) => handleKeydown(e, suggestion)}
          class="suggestion-pill"
          tabindex="0"
          aria-label="Suggestion: {suggestion}"
        >
          <span class="truncate max-w-[250px]">
            {suggestion}
          </span>
        </button>
      {/each}
    </div>
  </div>
{/if}

<script lang="ts">
  /**
   * Quick suggestion pills for common queries
   * Horizontal scrollable, keyboard accessible
   */

  import { createEventDispatcher } from 'svelte';

  export let suggestions: string[] = [];

  const dispatch = createEventDispatcher<{
    select: { suggestion: string };
  }>();

  function handleSelect(suggestion: string) {
    dispatch('select', { suggestion });
  }

  function handleKeydown(event: KeyboardEvent, suggestion: string) {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleSelect(suggestion);
    }
  }
</script>

<style>
  .quick-suggestions-container {
    width: 100%;
  }

  .suggestion-pill {
    flex-shrink: 0;
    display: inline-flex;
    align-items: center;
    padding: 0.5rem 1rem;
    background-color: var(--color-bg-elevated);
    border: 1px solid var(--color-border);
    border-radius: 9999px;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--color-text-secondary);
    cursor: pointer;
    transition: all var(--transition-fast);
    white-space: nowrap;
  }

  .suggestion-pill:hover {
    background-color: var(--color-primary);
    color: white;
    border-color: var(--color-primary);
    box-shadow: var(--shadow-md);
    transform: translateY(-1px);
  }

  .suggestion-pill:active {
    transform: translateY(0);
    box-shadow: var(--shadow-sm);
  }

  .suggestion-pill:focus {
    outline: none;
    box-shadow: 0 0 0 3px rgba(0, 84, 143, 0.3);
  }

  .scrollbar-thin::-webkit-scrollbar {
    height: 6px;
  }

  .scrollbar-thin::-webkit-scrollbar-thumb {
    background-color: var(--color-border);
    border-radius: 3px;
  }

  .scrollbar-thin::-webkit-scrollbar-thumb:hover {
    background-color: var(--color-text-tertiary);
  }

  /* Hide scrollbar on mobile */
  @media (max-width: 768px) {
    .scrollbar-thin::-webkit-scrollbar {
      display: none;
    }

    .suggestion-pill {
      font-size: 0.8125rem;
      padding: 0.4rem 0.875rem;
    }
  }
</style>

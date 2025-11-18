<div class="docx-viewer">
  <!-- Header with Actions -->
  <div class="viewer-header">
    <div class="flex items-center gap-2">
      <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>
      <h3 class="font-semibold text-gray-900 dark:text-white truncate">
        {fileName}
      </h3>
    </div>

    <div class="action-buttons">
      <button
        on:click={handleCopyText}
        disabled={loading || !!error}
        class="action-btn"
        aria-label="Copy text"
        title="Copy text"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
          />
        </svg>
      </button>

      <button
        on:click={handlePrint}
        disabled={loading || !!error}
        class="action-btn"
        aria-label="Print document"
        title="Print"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"
          />
        </svg>
      </button>

      <button
        on:click={handleDownload}
        class="action-btn"
        aria-label="Download document"
        title="Download"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
          />
        </svg>
      </button>
    </div>
  </div>

  <!-- Content Area -->
  <div class="viewer-content">
    {#if loading}
      <div class="flex items-center justify-center h-full">
        <LoadingSpinner size="medium" message="Rendering document..." />
      </div>
    {:else if error}
      <div class="error-state">
        <svg
          class="w-12 h-12 text-red-500 mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <p class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Failed to Load Document
        </p>
        <p class="text-sm text-gray-600 dark:text-gray-400">
          {error}
        </p>
      </div>
    {:else}
      <div bind:this={containerElement} class="document-content prose dark:prose-invert">
        {@html htmlContent}
      </div>
    {/if}
  </div>
</div>

<script lang="ts">
  /**
   * DOCX document viewer using mammoth library
   * Supports download, copy, and dark mode
   */

  import { onMount } from 'svelte';
  import { addNotification } from '$lib/stores';
  import LoadingSpinner from './LoadingSpinner.svelte';

  export let docxBlob: Blob;
  export let fileName = 'document.docx';

  let htmlContent = '';
  let loading = true;
  let error: string | null = null;
  let containerElement: HTMLDivElement;

  onMount(async () => {
    await renderDocument();
  });

  async function renderDocument() {
    loading = true;
    error = null;

    try {
      // Dynamically import mammoth
      const mammoth = await import('mammoth');

      // Convert Blob to ArrayBuffer
      const arrayBuffer = await docxBlob.arrayBuffer();

      // Convert to HTML
      const result = await mammoth.convertToHtml({ arrayBuffer });

      htmlContent = result.value;

      // Check for any conversion messages/warnings
      if (result.messages.length > 0) {
        console.warn('Document conversion warnings:', result.messages);
      }
    } catch (err) {
      console.error('Failed to render DOCX:', err);
      error = 'Failed to render document. The file may be corrupted or unsupported.';
      addNotification({
        type: 'error',
        message: error,
        duration: 5000,
      });
    } finally {
      loading = false;
    }
  }

  async function handleDownload() {
    try {
      const url = URL.createObjectURL(docxBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      addNotification({
        type: 'success',
        message: 'Download started',
        duration: 3000,
      });
    } catch (err) {
      addNotification({
        type: 'error',
        message: 'Download failed',
        duration: 5000,
      });
    }
  }

  async function handleCopyText() {
    try {
      if (!containerElement) return;

      const text = containerElement.innerText;
      await navigator.clipboard.writeText(text);

      addNotification({
        type: 'success',
        message: 'Text copied to clipboard',
        duration: 3000,
      });
    } catch (err) {
      addNotification({
        type: 'error',
        message: 'Failed to copy text',
        duration: 5000,
      });
    }
  }

  function handlePrint() {
    window.print();
  }
</script>

<style>
  .docx-viewer {
    display: flex;
    flex-direction: column;
    height: 100%;
    background-color: var(--color-bg-elevated);
    border-radius: 8px;
    overflow: hidden;
  }

  .viewer-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem;
    border-bottom: 1px solid var(--color-border);
    background-color: var(--color-bg-alt);
  }

  .action-buttons {
    display: flex;
    gap: 0.5rem;
  }

  .action-btn {
    padding: 0.5rem;
    background-color: transparent;
    border: 1px solid var(--color-border);
    border-radius: 6px;
    color: var(--color-text-secondary);
    cursor: pointer;
    transition: all var(--transition-fast);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .action-btn:hover:not(:disabled) {
    background-color: var(--color-bg-elevated);
    border-color: var(--color-primary);
    color: var(--color-primary);
  }

  .action-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .viewer-content {
    flex: 1;
    overflow-y: auto;
    padding: 2rem;
    background-color: white;
  }

  [data-theme='dark'] .viewer-content {
    background-color: #1a1a1a;
  }

  .document-content {
    max-width: 800px;
    margin: 0 auto;
  }

  .document-content :global(img) {
    max-width: 100%;
    height: auto;
    border-radius: 4px;
  }

  .document-content :global(table) {
    width: 100%;
    border-collapse: collapse;
    margin: 1em 0;
  }

  .document-content :global(table td),
  .document-content :global(table th) {
    border: 1px solid var(--color-border);
    padding: 0.5em;
  }

  .document-content :global(table th) {
    background-color: var(--color-bg-alt);
    font-weight: 600;
  }

  .error-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    text-align: center;
    padding: 2rem;
  }

  @media (max-width: 768px) {
    .viewer-content {
      padding: 1rem;
    }

    .document-content {
      font-size: 0.9rem;
    }
  }

  @media print {
    .viewer-header {
      display: none;
    }

    .viewer-content {
      padding: 0;
      overflow: visible;
    }
  }
</style>

{#if isOpen}
  <!-- Backdrop -->
  <div
    class="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 animate-fadeIn"
    on:click={handleBackdropClick}
    aria-hidden="true"
  />

  <!-- Dialog -->
  <div
    class="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fadeIn"
    role="dialog"
    aria-modal="true"
    aria-labelledby="dialog-title"
  >
    <div
      bind:this={dialogElement}
      class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] flex flex-col animate-slideInUp"
    >
      <!-- Header -->
      <div
        class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700"
      >
        <h2 id="dialog-title" class="text-xl font-bold text-gray-900 dark:text-white">
          {title}
        </h2>

        {#if showClose}
          <button
            on:click={handleClose}
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            aria-label="Close dialog"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        {/if}
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-y-auto px-6 py-4">
        <slot />
      </div>

      <!-- Footer (optional slot) -->
      {#if $$slots.footer}
        <div class="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
          <slot name="footer" />
        </div>
      {/if}
    </div>
  </div>
{/if}

<script lang="ts">
  /**
   * Modal dialog component with backdrop, focus trap, keyboard support
   */

  import { onMount, onDestroy, createEventDispatcher } from 'svelte';

  export let isOpen = false;
  export let title: string;
  export let showClose = true;

  const dispatch = createEventDispatcher<{
    close: void;
  }>();

  let dialogElement: HTMLDivElement | undefined;
  let previousFocus: HTMLElement | null = null;

  function handleClose() {
    dispatch('close');
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Escape' && isOpen) {
      handleClose();
    }
  }

  function handleBackdropClick(event: MouseEvent) {
    if (event.target === event.currentTarget) {
      handleClose();
    }
  }

  // Focus trap logic
  function trapFocus(): (() => void) | undefined {
    if (!dialogElement) return;

    const focusableElements = dialogElement.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    if (focusableElements.length === 0) return;

    const firstElement: HTMLElement | undefined = focusableElements[0];
    const lastElement: HTMLElement | undefined = focusableElements[focusableElements.length - 1];

    if (!firstElement || !lastElement) return;

    function handleTabKey(e: KeyboardEvent) {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        if (document.activeElement === firstElement && firstElement) {
          lastElement.focus();
          e.preventDefault();
        }
      } else {
        if (document.activeElement === lastElement && lastElement) {
          firstElement.focus();
          e.preventDefault();
        }
      }
    }

    dialogElement.addEventListener('keydown', handleTabKey);
    firstElement.focus();

    return () => {
      dialogElement?.removeEventListener('keydown', handleTabKey);
    };
  }

  // Track current cleanup function
  let currentCleanup: (() => void) | undefined;

  $: {
    if (isOpen && dialogElement) {
      previousFocus = document.activeElement as HTMLElement;
      currentCleanup = trapFocus();

      // Prevent body scroll
      document.body.style.overflow = 'hidden';
    } else {
      // Cleanup when dialog closes
      if (currentCleanup) {
        currentCleanup();
        currentCleanup = undefined;
      }
      document.body.style.overflow = '';
      previousFocus?.focus();
    }
  }

  onMount(() => {
    document.addEventListener('keydown', handleKeydown);
  });

  onDestroy(() => {
    document.removeEventListener('keydown', handleKeydown);
    document.body.style.overflow = '';
  });
</script>

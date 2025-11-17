<div
  class="notification-container pointer-events-auto max-w-sm w-full border-l-4 rounded-lg shadow-lg p-4 transition-all duration-300 {typeClasses[
    notification.type
  ]}"
  class:closing
  role="alert"
  aria-live={notification.type === 'error' ? 'assertive' : 'polite'}
  aria-atomic="true"
>
  <div class="flex items-start gap-3">
    <!-- Icon -->
    <div class="flex-shrink-0 w-6 h-6 flex items-center justify-center font-bold text-lg">
      {icons[notification.type]}
    </div>

    <!-- Content -->
    <div class="flex-1 min-w-0">
      <p class="text-sm font-medium break-words">
        {notification.message}
      </p>

      <!-- Optional Action Button -->
      {#if notification.action}
        <button
          on:click={() => {
            notification.action?.callback();
            handleClose();
          }}
          class="mt-2 text-sm font-semibold underline hover:no-underline focus:outline-none focus:ring-2 focus:ring-offset-2 rounded"
        >
          {notification.action.label}
        </button>
      {/if}
    </div>

    <!-- Close Button -->
    {#if notification.dismissible !== false}
      <button
        on:click={handleClose}
        class="flex-shrink-0 w-5 h-5 flex items-center justify-center hover:opacity-70 transition-opacity focus:outline-none focus:ring-2 focus:ring-offset-2 rounded"
        aria-label="Close notification"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
</div>

<script lang="ts">
  /**
   * Toast notification component
   * Auto-dismisses after duration, supports different types
   */

  import { onMount, onDestroy } from 'svelte';
  import { dismissNotification } from '$lib/stores';
  import type { Notification } from '$lib/types';

  export let notification: Notification;

  let timeoutId: number | undefined;
  let closing = false;

  // Type-based styling
  const typeClasses = {
    success: 'bg-green-50 dark:bg-green-900/20 border-green-500 text-green-800 dark:text-green-200',
    error: 'bg-red-50 dark:bg-red-900/20 border-red-500 text-red-800 dark:text-red-200',
    warning:
      'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-500 text-yellow-800 dark:text-yellow-200',
    info: 'bg-blue-50 dark:bg-blue-900/20 border-blue-500 text-blue-800 dark:text-blue-200',
  };

  // Icons for each type
  const icons = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ',
  };

  function handleClose() {
    closing = true;
    setTimeout(() => {
      dismissNotification(notification.id);
    }, 300); // Match animation duration
  }

  onMount(() => {
    const duration = notification.duration ?? 5000;
    if (duration > 0) {
      timeoutId = window.setTimeout(handleClose, duration);
    }
  });

  onDestroy(() => {
    if (timeoutId !== undefined) {
      clearTimeout(timeoutId);
    }
  });
</script>

<style>
  .notification-container {
    animation: slideInRight 300ms ease-out;
  }

  .notification-container.closing {
    animation: slideOutRight 300ms ease-out;
    opacity: 0;
    transform: translateX(100%);
  }

  @keyframes slideInRight {
    from {
      opacity: 0;
      transform: translateX(100%);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }

  @keyframes slideOutRight {
    from {
      opacity: 1;
      transform: translateX(0);
    }
    to {
      opacity: 0;
      transform: translateX(100%);
    }
  }
</style>

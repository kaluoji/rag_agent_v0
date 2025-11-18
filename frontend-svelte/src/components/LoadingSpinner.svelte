<div
  class="flex flex-col items-center justify-center {containerClasses[size]}"
  role="status"
  aria-live="polite"
  aria-busy="true"
>
  <!-- SVG Spinner -->
  <svg
    class="{sizeClasses[size]} animate-spin"
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    aria-hidden="true"
  >
    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
    <path
      class="opacity-75"
      fill="currentColor"
      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
    />
  </svg>

  <!-- Optional Message -->
  {#if message}
    <p class="text-sm text-gray-600 dark:text-gray-400 text-center">
      {message}
    </p>
  {/if}

  <!-- Screen reader text -->
  <span class="sr-only">Loading...</span>
</div>

<script lang="ts">
  /**
   * Reusable loading spinner component
   * Props: size - spinner size (small/medium/large)
   *        message - optional loading message
   */

  export let size: 'small' | 'medium' | 'large' = 'medium';
  export let message: string | undefined = undefined;

  // Size configurations
  const sizeClasses = {
    small: 'w-6 h-6',
    medium: 'w-12 h-12',
    large: 'w-16 h-16',
  };

  const containerClasses = {
    small: 'gap-2',
    medium: 'gap-3',
    large: 'gap-4',
  };
</script>

<style>
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border-width: 0;
  }
</style>

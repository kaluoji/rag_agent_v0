<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import ChatInterface from '$lib/components/ChatInterface.svelte';
  import Notification from '$lib/components/Notification.svelte';
  import { messageStore, uiStore } from '$lib/stores';
  import type { Message } from '$lib/types';

  /**
   * Main chat page - Primary user interface for regulatory queries
   * Displays chat interface with message history and controls
   * Responsive design with mobile-first approach
   */

  let isMounted = false;
  let messages: Message[] = [];
  let notifications: any[] = [];

  // Subscribe to message store
  const unsubscribeMessages = messageStore.subscribe((state) => {
    messages = state.messages;
  });

  // Subscribe to UI store for notifications
  const unsubscribeUI = uiStore.subscribe((state) => {
    notifications = state.notifications;
  });

  onMount(() => {
    isMounted = true;
    // Set page meta for accessibility
    document.title = 'RAG Regulatory - Analysis';
  });

  onDestroy(() => {
    unsubscribeMessages();
    unsubscribeUI();
  });
</script>

<svelte:head>
  <title>RAG Regulatory - Analysis</title>
  <meta name="description" content="RAG-powered regulatory compliance analysis and reporting" />
</svelte:head>

<div class="page-container">
  <!-- Main chat interface -->
  <div class="chat-container" role="main" aria-label="Chat interface">
    {#if isMounted}
      <ChatInterface />
    {:else}
      <div class="loading-state" aria-busy="true">
        <div class="spinner"></div>
        <p>Initializing chat interface...</p>
      </div>
    {/if}
  </div>

  <!-- Notification container (bottom-right) -->
  {#if notifications.length > 0}
    <div
      class="notifications-container"
      role="region"
      aria-label="Notifications"
      aria-live="polite"
    >
      {#each notifications as notification (notification.id)}
        <Notification
          type={notification.type}
          message={notification.message}
          dismissible={notification.dismissible !== false}
        />
      {/each}
    </div>
  {/if}
</div>

<style>
  .page-container {
    display: flex;
    flex-direction: column;
    height: 100%;
    width: 100%;
    position: relative;
  }

  .chat-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background-color: var(--color-bg);
    color: var(--color-text-primary);
  }

  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    gap: 1rem;
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

  .notifications-container {
    position: fixed;
    bottom: 1rem;
    right: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    z-index: 1000;
    max-width: 400px;
  }

  /* Responsive design */
  @media (max-width: 768px) {
    .notifications-container {
      bottom: 0.75rem;
      right: 0.75rem;
      max-width: 320px;
    }
  }

  @media (max-width: 480px) {
    .notifications-container {
      bottom: 0.5rem;
      right: 0.5rem;
      max-width: 280px;
    }
  }

  /* Dark mode support */
  :global([data-theme='dark']) .chat-container {
    background-color: var(--color-bg-dark);
  }

  /* Focus management */
  :focus-visible {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
  }
</style>

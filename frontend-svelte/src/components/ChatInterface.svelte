<div class="chat-interface">
  <!-- Messages Area -->
  <div
    bind:this={messagesContainer}
    on:scroll={handleScroll}
    class="messages-container"
    role="log"
    aria-live="polite"
    aria-atomic="false"
    aria-label="Chat messages"
  >
    {#if messages.length === 0}
      <!-- Empty State -->
      <div class="empty-state">
        <div class="empty-state-icon">
          <svg class="w-20 h-20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
            />
          </svg>
        </div>
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Welcome to RAG Regulatory Analysis
        </h2>
        <p class="text-gray-600 dark:text-gray-400 mb-6 max-w-md text-center">
          Ask questions about regulatory compliance, data protection laws, and financial
          regulations. I'll analyze your queries and provide detailed, source-backed answers.
        </p>

        <!-- Quick Suggestions in Empty State -->
        <div class="w-full max-w-2xl">
          <p class="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
            Try these questions:
          </p>
          <QuickSuggestions {suggestions} on:select={handleSuggestionSelect} />
        </div>
      </div>
    {:else}
      <!-- Messages List -->
      {#each messages as message (message.id)}
        <ChatMessage {message} isOwn={message.role === 'user'} />
      {/each}

      <!-- Loading Indicator -->
      {#if loading}
        <div class="loading-message">
          <LoadingSpinner size="small" />
          <span class="text-sm text-gray-600 dark:text-gray-400 ml-3">
            Analyzing your query...
          </span>
        </div>
      {/if}
    {/if}
  </div>

  <!-- Scroll to Bottom Button -->
  {#if !isNearBottom && messages.length > 0}
    <button
      on:click={handleScrollToBottom}
      class="scroll-to-bottom-btn"
      aria-label="Scroll to bottom"
      title="Scroll to bottom"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M19 14l-7 7m0 0l-7-7m7 7V3"
        />
      </svg>
    </button>
  {/if}

  <!-- Input Area -->
  <div class="input-area">
    <!-- Quick Suggestions (when messages exist) -->
    {#if messages.length > 0}
      <div class="mb-3">
        <QuickSuggestions
          suggestions={suggestions.slice(0, 3)}
          on:select={handleSuggestionSelect}
        />
      </div>
    {/if}

    <!-- Message Input -->
    <MessageInput disabled={loading} on:submit={handleSubmit} />

    <!-- Disclaimer -->
    <p class="disclaimer">
      AI-generated responses may contain errors. Always verify regulatory information with official
      sources.
    </p>
  </div>
</div>

<script lang="ts">
  /**
   * Main chat interface component
   * Handles message display, input, auto-scrolling, quick suggestions
   */

  import { onMount, afterUpdate, tick } from 'svelte';
  import { messageStore, setMessageLoading, setMessageError, addMessage } from '$lib/stores';
  import { processQuery } from '$lib/api';
  import type { Message } from '$lib/types';
  import ChatMessage from './ChatMessage.svelte';
  import MessageInput from './MessageInput.svelte';
  import QuickSuggestions from './QuickSuggestions.svelte';
  import LoadingSpinner from './LoadingSpinner.svelte';

  let messagesContainer: HTMLDivElement;
  let shouldAutoScroll = true;
  let isNearBottom = true;

  // Quick suggestions
  const suggestions = [
    'What are the GDPR compliance requirements for data processing?',
    'Analyze Basel III capital requirements for banking',
    'Explain PCI-DSS requirements for payment processing',
    'What are the key provisions of CCPA?',
    'Compare GDPR and CCPA data protection requirements',
  ];

  // Subscribe to store
  $: messages = $messageStore.messages;
  $: loading = $messageStore.loading;
  $: error = $messageStore.error;

  // Auto-scroll logic
  function checkIfNearBottom() {
    if (!messagesContainer) return;

    const { scrollTop, scrollHeight, clientHeight } = messagesContainer;
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;

    isNearBottom = distanceFromBottom < 100;
    shouldAutoScroll = isNearBottom;
  }

  function scrollToBottom(smooth = true) {
    if (!messagesContainer) return;

    messagesContainer.scrollTo({
      top: messagesContainer.scrollHeight,
      behavior: smooth ? 'smooth' : 'auto',
    });
  }

  // Handle scroll events
  function handleScroll() {
    checkIfNearBottom();
  }

  // Auto-scroll after messages update
  afterUpdate(() => {
    if (shouldAutoScroll) {
      scrollToBottom(true);
    }
  });

  // Handle message submission
  async function handleSubmit(event: CustomEvent<{ text: string; fileId?: string }>) {
    const { text, fileId } = event.detail;

    if (!text.trim()) return;

    // Add user message
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      timestamp: new Date(),
      metadata: fileId ? { fileId } : undefined,
    };

    addMessage(userMessage);
    setMessageLoading(true);
    setMessageError(null);

    // Scroll to bottom
    await tick();
    scrollToBottom(true);

    try {
      // Call API
      const result = await processQuery(text);

      if (result.error) {
        setMessageError(result.error.message);

        // Add error message
        const errorMessage: Message = {
          id: crypto.randomUUID(),
          role: 'system',
          content: `Error: ${result.error.message}`,
          timestamp: new Date(),
        };
        addMessage(errorMessage);
      } else if (result.data) {
        // Add assistant response
        const assistantMessage: Message = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: result.data.analysis,
          timestamp: new Date(),
          sources: result.data.sources,
          metadata: result.data.metadata,
        };
        addMessage(assistantMessage);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'An unexpected error occurred';
      setMessageError(errorMsg);

      const errorMessage: Message = {
        id: crypto.randomUUID(),
        role: 'system',
        content: `Error: ${errorMsg}`,
        timestamp: new Date(),
      };
      addMessage(errorMessage);
    } finally {
      setMessageLoading(false);
    }
  }

  // Handle suggestion click
  function handleSuggestionSelect(event: CustomEvent<{ suggestion: string }>) {
    handleSubmit(
      new CustomEvent('submit', {
        detail: { text: event.detail.suggestion },
      })
    );
  }

  // Handle scroll to bottom button
  function handleScrollToBottom() {
    shouldAutoScroll = true;
    scrollToBottom(true);
  }

  // Initial scroll
  onMount(() => {
    scrollToBottom(false);
  });
</script>

<style>
  .chat-interface {
    display: flex;
    flex-direction: column;
    height: 100%;
    background-color: var(--color-bg);
    position: relative;
  }

  .messages-container {
    flex: 1;
    overflow-y: auto;
    scroll-behavior: smooth;
    padding: 1rem 0;
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    padding: 2rem;
    text-align: center;
  }

  .empty-state-icon {
    color: var(--color-primary);
    opacity: 0.3;
    margin-bottom: 1.5rem;
  }

  .loading-message {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    animation: fadeIn 300ms ease-out;
  }

  .scroll-to-bottom-btn {
    position: absolute;
    bottom: calc(100px + 2rem);
    right: 2rem;
    width: 48px;
    height: 48px;
    background-color: var(--color-primary);
    color: white;
    border: none;
    border-radius: 50%;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: var(--shadow-lg);
    transition: all var(--transition-fast);
    z-index: 10;
    animation: slideInUp 300ms ease-out;
  }

  .scroll-to-bottom-btn:hover {
    background-color: var(--color-primary-light);
    transform: translateY(-2px);
    box-shadow: var(--shadow-xl);
  }

  .scroll-to-bottom-btn:active {
    transform: translateY(0);
  }

  .input-area {
    flex-shrink: 0;
    background-color: var(--color-bg-elevated);
    border-top: 1px solid var(--color-border);
    padding: 1rem;
  }

  .disclaimer {
    margin-top: 0.75rem;
    text-align: center;
    font-size: 0.75rem;
    color: var(--color-text-tertiary);
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  @keyframes slideInUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @media (max-width: 768px) {
    .scroll-to-bottom-btn {
      bottom: calc(120px + 1rem);
      right: 1rem;
      width: 40px;
      height: 40px;
    }

    .input-area {
      padding: 0.75rem;
    }

    .empty-state {
      padding: 1rem;
    }

    .empty-state h2 {
      font-size: 1.5rem;
    }
  }
</style>

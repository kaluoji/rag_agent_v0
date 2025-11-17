<div
  class="chat-message"
  class:message-own={isOwn}
  data-message-id={message.id}
  role="article"
  aria-label="{getRoleLabel()} message"
>
  <div class="message-container">
    <!-- Avatar -->
    <div class="message-avatar" aria-hidden="true">
      <span class="text-2xl">{getAvatarIcon()}</span>
    </div>

    <!-- Content -->
    <div class="message-content">
      <!-- Header -->
      <div class="message-header">
        <span class="role-badge {getRoleBadgeClass()}">
          {getRoleLabel()}
        </span>
        <time
          class="message-timestamp"
          datetime={message.timestamp.toISOString()}
          title={message.timestamp.toLocaleString()}
        >
          {formatTimestamp(message.timestamp)}
        </time>
      </div>

      <!-- Body -->
      <div class="message-body prose dark:prose-invert">
        {@html renderedContent}
      </div>

      <!-- Artifact Button -->
      {#if message.artifact}
        <button on:click={handleViewArtifact} class="artifact-button">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          View Document: {message.artifact.name}
        </button>
      {/if}

      <!-- Source Citations -->
      {#if message.sources && message.sources.length > 0}
        <div class="mt-4">
          <SourceCitation sources={message.sources} maxDisplay={3} />
        </div>
      {/if}
    </div>
  </div>
</div>

<!-- Artifact Modal -->
{#if message.artifact && showArtifactModal}
  <Dialog
    isOpen={showArtifactModal}
    title={message.artifact.name}
    on:close={() => (showArtifactModal = false)}
  >
    {#if message.artifact.mimeType.includes('word') || message.artifact.name.endsWith('.docx')}
      <div class="h-[70vh]">
        <DocxViewer
          docxBlob={new Blob([message.artifact.content], { type: message.artifact.mimeType })}
          fileName={message.artifact.name}
        />
      </div>
    {:else}
      <div class="p-4">
        <p class="text-gray-600 dark:text-gray-400">Preview not available for this file type.</p>
      </div>
    {/if}
  </Dialog>
{/if}

<script lang="ts">
  /**
   * Individual chat message component
   * Supports markdown rendering, code highlighting, artifact display, source citations
   */

  import { onMount } from 'svelte';
  import type { Message } from '$lib/types';
  import SourceCitation from './SourceCitation.svelte';
  import Dialog from './Dialog.svelte';
  import DocxViewer from './DocxViewer.svelte';

  export let message: Message;
  export let isOwn = false;

  let renderedContent = '';
  let showArtifactModal = false;

  // Format timestamp to relative time
  function formatTimestamp(date: Date): string {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (seconds < 60) return 'just now';
    if (minutes < 60) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    if (days < 7) return `${days} day${days > 1 ? 's' : ''} ago`;

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
    });
  }

  // Convert markdown to HTML
  async function renderMarkdown(content: string): Promise<string> {
    try {
      // Dynamically import marked
      const { marked } = await import('marked');

      // Configure marked options
      marked.setOptions({
        breaks: true,
        gfm: true,
      });

      // Convert to HTML
      let html = await marked.parse(content);

      // Add syntax highlighting class to code blocks
      html = html.replace(
        /<pre><code class="language-(\w+)">/g,
        '<pre><code class="language-$1 hljs">'
      );
      html = html.replace(/<pre><code>/g, '<pre><code class="hljs">');

      return html;
    } catch (error) {
      console.error('Failed to render markdown:', error);
      return content;
    }
  }

  // Apply syntax highlighting
  async function highlightCode() {
    try {
      // Dynamically import highlight.js
      const hljs = await import('highlight.js');

      // Find all code blocks
      const codeBlocks = document.querySelectorAll(`[data-message-id="${message.id}"] pre code`);

      codeBlocks.forEach((block) => {
        hljs.default.highlightElement(block as HTMLElement);

        // Add copy button to code blocks
        addCopyButton(block as HTMLElement);
      });
    } catch (error) {
      console.error('Failed to highlight code:', error);
    }
  }

  // Add copy button to code block
  function addCopyButton(codeBlock: HTMLElement) {
    const pre = codeBlock.parentElement;
    if (!pre || pre.querySelector('.copy-button')) return;

    const button = document.createElement('button');
    button.className = 'copy-button';
    button.innerHTML = `
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
      </svg>
    `;
    button.setAttribute('aria-label', 'Copy code');
    button.onclick = async () => {
      try {
        await navigator.clipboard.writeText(codeBlock.textContent || '');
        button.innerHTML = `
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
        `;
        setTimeout(() => {
          button.innerHTML = `
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          `;
        }, 2000);
      } catch (err) {
        console.error('Failed to copy:', err);
      }
    };

    pre.style.position = 'relative';
    pre.appendChild(button);
  }

  onMount(async () => {
    renderedContent = await renderMarkdown(message.content);

    // Apply syntax highlighting after DOM update
    setTimeout(() => {
      highlightCode();
    }, 0);
  });

  function handleViewArtifact() {
    if (message.artifact) {
      showArtifactModal = true;
    }
  }

  function getAvatarIcon(): string {
    if (message.role === 'user') return '👤';
    if (message.role === 'assistant') return '🤖';
    return 'ℹ️';
  }

  function getRoleBadgeClass(): string {
    if (message.role === 'user') return 'role-badge-user';
    if (message.role === 'assistant') return 'role-badge-assistant';
    return 'role-badge-system';
  }

  function getRoleLabel(): string {
    if (message.role === 'user') return 'User';
    if (message.role === 'assistant') return 'AI Assistant';
    return 'System';
  }
</script>

<style>
  .chat-message {
    width: 100%;
    padding: 1.5rem 1rem;
    animation: slideInUp 300ms ease-out;
  }

  .message-container {
    display: flex;
    gap: 1rem;
    max-width: 900px;
    margin: 0 auto;
  }

  .message-own .message-container {
    flex-direction: row-reverse;
  }

  .message-avatar {
    flex-shrink: 0;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .message-own .message-avatar {
    background: linear-gradient(135deg, var(--color-secondary), var(--color-secondary-light));
  }

  .message-content {
    flex: 1;
    min-width: 0;
  }

  .message-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.5rem;
  }

  .role-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .role-badge-user {
    background-color: rgba(77, 10, 46, 0.1);
    color: var(--color-secondary);
  }

  .role-badge-assistant {
    background-color: rgba(0, 84, 143, 0.1);
    color: var(--color-primary);
  }

  .role-badge-system {
    background-color: rgba(59, 130, 246, 0.1);
    color: var(--color-info);
  }

  [data-theme='dark'] .role-badge-user {
    background-color: rgba(77, 10, 46, 0.3);
    color: var(--color-secondary-light);
  }

  [data-theme='dark'] .role-badge-assistant {
    background-color: rgba(0, 84, 143, 0.3);
    color: var(--color-primary-light);
  }

  [data-theme='dark'] .role-badge-system {
    background-color: rgba(59, 130, 246, 0.3);
    color: var(--color-info);
  }

  .message-timestamp {
    font-size: 0.75rem;
    color: var(--color-text-tertiary);
  }

  .message-body {
    background-color: var(--color-bg-elevated);
    border: 1px solid var(--color-border);
    border-radius: 12px;
    padding: 1rem;
    word-wrap: break-word;
  }

  .message-own .message-body {
    background-color: rgba(0, 84, 143, 0.05);
    border-color: rgba(0, 84, 143, 0.2);
  }

  .message-body :global(pre) {
    position: relative;
    background-color: var(--color-bg-alt);
    border: 1px solid var(--color-border);
    border-radius: 6px;
    padding: 1rem;
    overflow-x: auto;
    margin: 1rem 0;
  }

  .message-body :global(pre code) {
    background-color: transparent;
    padding: 0;
    border-radius: 0;
    font-family: 'Courier New', monospace;
    font-size: 0.875rem;
    line-height: 1.5;
  }

  .message-body :global(.copy-button) {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    padding: 0.5rem;
    background-color: var(--color-bg-elevated);
    border: 1px solid var(--color-border);
    border-radius: 4px;
    cursor: pointer;
    opacity: 0;
    transition: opacity var(--transition-fast);
  }

  .message-body :global(pre:hover .copy-button) {
    opacity: 1;
  }

  .message-body :global(.copy-button:hover) {
    background-color: var(--color-primary);
    color: white;
    border-color: var(--color-primary);
  }

  .message-body :global(a) {
    color: var(--color-primary);
    text-decoration: underline;
  }

  .message-body :global(a:hover) {
    color: var(--color-primary-light);
  }

  .artifact-button {
    margin-top: 1rem;
    padding: 0.75rem 1rem;
    background-color: var(--color-primary);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    transition: all var(--transition-fast);
  }

  .artifact-button:hover {
    background-color: var(--color-primary-light);
    box-shadow: var(--shadow-md);
    transform: translateY(-1px);
  }

  .artifact-button:active {
    transform: translateY(0);
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
    .chat-message {
      padding: 1rem 0.5rem;
    }

    .message-container {
      gap: 0.75rem;
    }

    .message-avatar {
      width: 32px;
      height: 32px;
      font-size: 1.25rem;
    }

    .message-body {
      padding: 0.75rem;
      font-size: 0.9rem;
    }
  }
</style>

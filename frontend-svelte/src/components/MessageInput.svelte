<div
  class="message-input-container"
  class:dragging={isDragging}
  on:dragenter={handleDragEnter}
  on:dragover={handleDragEnter}
  on:dragleave={handleDragLeave}
  on:drop={handleDrop}
>
  <!-- Uploaded File Badge -->
  {#if uploadedFileName}
    <div class="uploaded-file-badge">
      <span class="flex items-center gap-2">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
          />
        </svg>
        {uploadedFileName}
      </span>
      <button
        on:click={removeFile}
        class="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
        aria-label="Remove file"
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
    </div>
  {/if}

  <div class="input-wrapper">
    <!-- Textarea -->
    <textarea
      bind:this={textarea}
      bind:value
      on:keydown={handleKeydown}
      {placeholder}
      {disabled}
      maxlength={maxLength}
      rows="1"
      class="message-textarea"
      aria-label="Message input"
      aria-describedby="char-count"
    />

    <!-- Action Buttons -->
    <div class="action-buttons">
      <!-- Clear Button -->
      {#if value.length > 0}
        <button on:click={handleClear} class="action-btn" aria-label="Clear input" type="button">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      {/if}

      <!-- File Upload Button -->
      <button
        on:click={() => fileInput.click()}
        class="action-btn"
        aria-label="Upload file"
        disabled={disabled || uploading}
        type="button"
      >
        {#if uploading}
          <svg class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle
              class="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              stroke-width="4"
            />
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        {:else}
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
            />
          </svg>
        {/if}
      </button>

      <!-- Submit Button -->
      <button
        on:click={handleSubmit}
        disabled={!canSubmit}
        class="submit-btn"
        aria-label="Send message (Ctrl+Enter)"
        title="Send message (Ctrl+Enter)"
        type="button"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
          />
        </svg>
      </button>
    </div>
  </div>

  <!-- Character Counter -->
  <div class="character-counter" id="char-count">
    <span class:text-red-600={isOverLimit}>
      {characterCount} / {maxLength}
    </span>
    <span class="text-gray-500 text-xs"> Press Ctrl+Enter to send </span>
  </div>

  <!-- Hidden File Input -->
  <input
    bind:this={fileInput}
    on:change={handleFileSelect}
    type="file"
    accept=".pdf,.doc,.docx"
    class="hidden"
    aria-label="File input"
  />
</div>

<script lang="ts">
  /**
   * Message input area with auto-grow textarea, file upload, character counter
   */

  import { createEventDispatcher } from 'svelte';
  import { uploadFile } from '$lib/api';
  import { addNotification } from '$lib/stores';

  export let disabled = false;
  export let placeholder = 'Ask a regulatory compliance question...';
  export let maxLength = 5000;
  export let value = '';

  const dispatch = createEventDispatcher<{
    submit: { text: string; fileId?: string };
    clear: void;
  }>();

  let textarea: HTMLTextAreaElement;
  let fileInput: HTMLInputElement;
  let uploading = false;
  let uploadedFileId: string | undefined;
  let uploadedFileName: string | undefined;

  // Auto-grow textarea (max 5 rows)
  $: if (textarea) {
    textarea.style.height = 'auto';
    const scrollHeight = textarea.scrollHeight;
    const maxHeight = parseFloat(getComputedStyle(textarea).lineHeight) * 5;
    textarea.style.height = Math.min(scrollHeight, maxHeight) + 'px';
  }

  $: characterCount = value.length;
  $: isOverLimit = characterCount > maxLength;
  $: canSubmit = value.trim().length > 0 && !disabled && !isOverLimit;

  function handleSubmit() {
    if (!canSubmit) return;

    dispatch('submit', {
      text: value.trim(),
      fileId: uploadedFileId,
    });

    // Reset
    value = '';
    uploadedFileId = undefined;
    uploadedFileName = undefined;
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
      event.preventDefault();
      handleSubmit();
    }
  }

  function handleClear() {
    value = '';
    uploadedFileId = undefined;
    uploadedFileName = undefined;
    dispatch('clear');
  }

  async function handleFileSelect(event: Event) {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];

    if (!file) return;

    // Validate file type
    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/msword',
    ];

    if (!allowedTypes.includes(file.type)) {
      addNotification({
        type: 'error',
        message: 'Only PDF and DOCX files are supported',
        duration: 5000,
      });
      target.value = '';
      return;
    }

    // Validate file size (max 10MB)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      addNotification({
        type: 'error',
        message: 'File size must be less than 10MB',
        duration: 5000,
      });
      target.value = '';
      return;
    }

    uploading = true;

    try {
      const result = await uploadFile(file);

      if (result.error) {
        addNotification({
          type: 'error',
          message: `Upload failed: ${result.error.message}`,
          duration: 5000,
        });
      } else if (result.data) {
        uploadedFileId = result.data.fileId;
        uploadedFileName = result.data.fileName;
        addNotification({
          type: 'success',
          message: `File "${file.name}" uploaded successfully`,
          duration: 3000,
        });
      }
    } catch (error) {
      addNotification({
        type: 'error',
        message: 'Upload failed. Please try again.',
        duration: 5000,
      });
    } finally {
      uploading = false;
      target.value = '';
    }
  }

  function removeFile() {
    uploadedFileId = undefined;
    uploadedFileName = undefined;
  }

  // Handle drag and drop
  let isDragging = false;

  function handleDragEnter(event: DragEvent) {
    event.preventDefault();
    isDragging = true;
  }

  function handleDragLeave(event: DragEvent) {
    event.preventDefault();
    isDragging = false;
  }

  function handleDrop(event: DragEvent) {
    event.preventDefault();
    isDragging = false;

    const file = event.dataTransfer?.files[0];
    if (file && fileInput) {
      const dt = new DataTransfer();
      dt.items.add(file);
      fileInput.files = dt.files;
      handleFileSelect({ target: fileInput } as any);
    }
  }
</script>

<style>
  .message-input-container {
    width: 100%;
    background-color: var(--color-bg-elevated);
    border: 2px solid var(--color-border);
    border-radius: 12px;
    padding: 0.75rem;
    transition: border-color var(--transition-fast);
  }

  .message-input-container:focus-within {
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(0, 84, 143, 0.1);
  }

  .message-input-container.dragging {
    border-color: var(--color-primary);
    background-color: rgba(0, 84, 143, 0.05);
    border-style: dashed;
  }

  .uploaded-file-badge {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background-color: var(--color-bg-alt);
    border: 1px solid var(--color-border);
    border-radius: 6px;
    padding: 0.5rem 0.75rem;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
    color: var(--color-text-secondary);
  }

  .input-wrapper {
    display: flex;
    align-items: flex-end;
    gap: 0.5rem;
  }

  .message-textarea {
    flex: 1;
    min-height: 24px;
    max-height: 120px;
    padding: 0;
    border: none;
    background: transparent;
    color: var(--color-text-primary);
    font-family: inherit;
    font-size: 1rem;
    line-height: 1.5;
    resize: none;
    overflow-y: auto;
  }

  .message-textarea:focus {
    outline: none;
  }

  .message-textarea::placeholder {
    color: var(--color-text-tertiary);
  }

  .action-buttons {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .action-btn {
    padding: 0.5rem;
    border-radius: 6px;
    background-color: transparent;
    color: var(--color-text-secondary);
    border: none;
    cursor: pointer;
    transition: all var(--transition-fast);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .action-btn:hover:not(:disabled) {
    background-color: var(--color-bg-alt);
    color: var(--color-text-primary);
  }

  .action-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .submit-btn {
    padding: 0.5rem;
    border-radius: 6px;
    background-color: var(--color-primary);
    color: white;
    border: none;
    cursor: pointer;
    transition: all var(--transition-fast);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .submit-btn:hover:not(:disabled) {
    background-color: var(--color-primary-light);
    box-shadow: var(--shadow-md);
  }

  .submit-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .character-counter {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 0.5rem;
    font-size: 0.75rem;
    color: var(--color-text-tertiary);
  }

  .hidden {
    display: none;
  }

  @media (max-width: 768px) {
    .character-counter span:last-child {
      display: none;
    }
  }
</style>

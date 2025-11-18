/**
 * Utility functions for text processing, document handling, and formatting
 */

// ============================================================================
// TEXT FORMATTING
// ============================================================================

/**
 * Format timestamp to readable date string
 * @param date - Date to format
 * @param format - Format style: 'short' | 'long' | 'time'
 */
export function formatTimestamp(date: Date, format: 'short' | 'long' | 'time' = 'short'): string {
  const d = date instanceof Date ? date : new Date(date);

  switch (format) {
    case 'short':
      return d.toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });

    case 'long':
      return d.toLocaleDateString('es-ES', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });

    case 'time':
      return d.toLocaleTimeString('es-ES', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });

    default:
      return d.toISOString();
  }
}

/**
 * Format file size to human readable format
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Truncate text with ellipsis
 */
export function truncateText(text: string, maxLength: number, suffix = '...'): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - suffix.length) + suffix;
}

/**
 * Extract plain text from markdown
 */
export function extractMarkdown(content: string): string {
  // Remove markdown syntax
  return (
    content
      // Remove HTML tags
      .replace(/<[^>]*>/g, '')
      // Remove markdown bold/italic
      .replace(/[*_]{1,3}(.+?)[*_]{1,3}/g, '$1')
      // Remove markdown links
      .replace(/\[(.+?)\]\(.+?\)/g, '$1')
      // Remove markdown headers
      .replace(/^#+\s+/gm, '')
      // Remove markdown code blocks
      .replace(/```[\s\S]*?```/g, '')
      // Remove markdown inline code
      .replace(/`(.+?)`/g, '$1')
      // Remove extra whitespace
      .replace(/\n{2,}/g, '\n')
      .trim()
  );
}

/**
 * Calculate reading time for text
 * Average reading speed: 200-250 words per minute
 */
export function calculateReadingTime(text: string): number {
  const wordCount = text.split(/\s+/).length;
  const readingSpeed = 225; // words per minute
  const minutes = Math.ceil(wordCount / readingSpeed);
  return Math.max(1, minutes);
}

/**
 * Highlight syntax for code blocks
 * Requires highlight.js to be available
 */
export function highlightSyntax(code: string, language: string = 'plaintext'): string {
  try {
    // @ts-ignore - hljs might not be typed
    if (typeof window !== 'undefined' && window.hljs) {
      // @ts-ignore
      return window.hljs.highlight(code, { language, ignoreIllegals: true }).value;
    }
  } catch (error) {
    console.warn('Syntax highlighting failed:', error);
  }
  return code;
}

/**
 * Escape HTML special characters
 */
export function escapeHTML(text: string): string {
  const map: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;',
  };
  return text.replace(/[&<>"']/g, (char) => map[char]);
}

// ============================================================================
// DOCUMENT HANDLING
// ============================================================================

/**
 * Parse DOCX file content
 * Requires mammoth library
 */
export async function parseDocxContent(docxBuffer: ArrayBuffer): Promise<string> {
  try {
    // @ts-ignore - mammoth is dynamically loaded
    const { extractRawText } = await import('mammoth');
    const result = await extractRawText({ arrayBuffer: docxBuffer });
    return result.value;
  } catch (error) {
    console.error('Failed to parse DOCX:', error);
    throw new Error('Failed to parse document');
  }
}

/**
 * Convert ArrayBuffer to Base64 string
 */
export function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

/**
 * Convert Base64 string to ArrayBuffer
 */
export function base64ToArrayBuffer(base64: string): ArrayBuffer {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
}

/**
 * Convert Blob to ArrayBuffer
 */
export async function blobToArrayBuffer(blob: Blob): Promise<ArrayBuffer> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as ArrayBuffer);
    reader.onerror = reject;
    reader.readAsArrayBuffer(blob);
  });
}

/**
 * Convert Blob to Data URL
 */
export async function blobToDataUrl(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}

/**
 * Download file from URL or Blob
 */
export function downloadFile(
  data: Blob | string,
  filename: string,
  mimeType: string = 'application/octet-stream'
): void {
  const blob = typeof data === 'string' ? new Blob([data], { type: mimeType }) : data;
  const url = URL.createObjectURL(blob);

  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);

  link.click();

  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// ============================================================================
// ARRAY OPERATIONS
// ============================================================================

/**
 * Remove duplicates from array
 */
export function removeDuplicates<T>(array: T[], key?: keyof T): T[] {
  if (!key) {
    return Array.from(new Set(array));
  }

  const seen = new Set();
  return array.filter((item) => {
    const value = item[key];
    if (seen.has(value)) return false;
    seen.add(value);
    return true;
  });
}

/**
 * Group array by key
 */
export function groupBy<T>(array: T[], key: keyof T): Record<string, T[]> {
  return array.reduce(
    (acc, item) => {
      const groupKey = String(item[key]);
      if (!acc[groupKey]) {
        acc[groupKey] = [];
      }
      acc[groupKey].push(item);
      return acc;
    },
    {} as Record<string, T[]>
  );
}

/**
 * Flatten nested arrays
 */
export function flatten<T>(array: (T | T[])[]): T[] {
  return array.reduce((acc: T[], item) => {
    if (Array.isArray(item)) {
      return acc.concat(flatten(item));
    }
    return acc.concat(item);
  }, []);
}

// ============================================================================
// VALIDATION
// ============================================================================

/**
 * Validate email address
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Validate URL
 */
export function isValidURL(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

/**
 * Check if file is image
 */
export function isImageFile(file: File): boolean {
  return file.type.startsWith('image/');
}

/**
 * Check if file is PDF
 */
export function isPdfFile(file: File): boolean {
  return file.type === 'application/pdf';
}

/**
 * Check if file is DOCX
 */
export function isDocxFile(file: File): boolean {
  return (
    file.type ===
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  );
}

// ============================================================================
// PROMISES & ASYNC
// ============================================================================

/**
 * Wait for specified milliseconds
 */
export function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Retry async function with exponential backoff
 */
export async function retryAsync<T>(
  fn: () => Promise<T>,
  options: {
    maxAttempts?: number;
    initialDelay?: number;
    maxDelay?: number;
    backoffMultiplier?: number;
  } = {}
): Promise<T> {
  const {
    maxAttempts = 3,
    initialDelay = 1000,
    maxDelay = 30000,
    backoffMultiplier = 2,
  } = options;

  let lastError: Error | null = null;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;

      if (attempt === maxAttempts) break;

      const delay = Math.min(
        initialDelay * Math.pow(backoffMultiplier, attempt - 1),
        maxDelay
      );

      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }

  throw lastError || new Error('Retry failed');
}

/**
 * Race between async function and timeout
 */
export async function withTimeout<T>(
  promise: Promise<T>,
  timeoutMs: number,
  timeoutError = new Error('Operation timeout')
): Promise<T> {
  return Promise.race([
    promise,
    new Promise<T>((_, reject) =>
      setTimeout(() => reject(timeoutError), timeoutMs)
    ),
  ]);
}

// ============================================================================
// OBJECT OPERATIONS
// ============================================================================

/**
 * Deep clone an object
 */
export function deepClone<T>(obj: T): T {
  if (obj === null || typeof obj !== 'object') return obj;

  if (obj instanceof Date) {
    return new Date(obj.getTime()) as any;
  }

  if (obj instanceof Array) {
    return obj.map((item) => deepClone(item)) as any;
  }

  if (obj instanceof Object) {
    const clonedObj: any = {};
    for (const key in obj) {
      if (Object.prototype.hasOwnProperty.call(obj, key)) {
        clonedObj[key] = deepClone((obj as any)[key]);
      }
    }
    return clonedObj;
  }

  return obj;
}

/**
 * Merge objects deeply
 */
export function deepMerge<T extends Record<string, any>>(target: T, ...sources: any[]): T {
  if (!sources.length) return target;

  const source = sources.shift();

  if (typeof target === 'object' && typeof source === 'object') {
    for (const key in source) {
      if (typeof source[key] === 'object' && typeof target[key] === 'object') {
        deepMerge(target[key], source[key]);
      } else {
        target[key] = source[key];
      }
    }
  }

  return deepMerge(target, ...sources);
}

// ============================================================================
// LOGGING
// ============================================================================

/**
 * Log with timestamp and context
 */
export function log(level: 'log' | 'warn' | 'error', message: string, data?: any): void {
  const timestamp = new Date().toISOString();
  const prefix = `[${timestamp}]`;

  if (data) {
    console[level](prefix, message, data);
  } else {
    console[level](prefix, message);
  }
}

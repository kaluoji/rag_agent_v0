/**
 * WebSocket client for real-time report generation updates
 * Auto-reconnect with exponential backoff, message queuing
 */

import type { ReportProgressUpdate } from './types';

// ============================================================================
// TYPES
// ============================================================================

type MessageHandler<T = unknown> = (data: T) => void;

interface QueuedMessage {
  type: string;
  data: unknown;
  timestamp: number;
}

interface WSConfig {
  host: string;
  port: number;
  path: string;
  reconnectDelay: number;
  maxReconnectDelay: number;
  maxReconnectAttempts: number;
  messageQueueSize: number;
}

// ============================================================================
// WEBSOCKET CLIENT
// ============================================================================

export class WSClient {
  private ws: WebSocket | null = null;
  private config: WSConfig;
  private messageQueue: QueuedMessage[] = [];
  private handlers: Map<string, Set<MessageHandler>> = new Map();
  private reconnectAttempts = 0;
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  private heartbeatInterval: ReturnType<typeof setInterval> | null = null;
  private isIntentionallyClosed = false;
  private lastMessageTime = Date.now();

  constructor(config: Partial<WSConfig> = {}) {
    this.config = {
      host: import.meta.env.VITE_WS_HOST || 'localhost',
      port: parseInt(import.meta.env.VITE_WS_PORT || '8000', 10),
      path: '/ws/report',
      reconnectDelay: 1000,
      maxReconnectDelay: 30000,
      maxReconnectAttempts: 10,
      messageQueueSize: 100,
      ...config,
    };
  }

  /**
   * Connect to WebSocket server
   */
  public connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${protocol}//${this.config.host}:${this.config.port}${this.config.path}`;

        console.log(`[WebSocket] Connecting to ${url}`);

        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
          console.log('[WebSocket] Connected');
          this.isIntentionallyClosed = false;
          this.reconnectAttempts = 0;
          this.flushMessageQueue();
          this.startHeartbeat();
          this.emit('connect', { timestamp: new Date() });
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.lastMessageTime = Date.now();
          this.handleMessage(event.data);
        };

        this.ws.onerror = (event) => {
          console.error('[WebSocket] Error:', event);
          this.emit('error', { message: 'WebSocket error occurred' });
          reject(new Error('WebSocket connection failed'));
        };

        this.ws.onclose = () => {
          console.log('[WebSocket] Disconnected');
          this.stopHeartbeat();
          this.emit('disconnect', { timestamp: new Date() });

          if (!this.isIntentionallyClosed) {
            this.attemptReconnect();
          }
        };

        // Timeout if connection takes too long
        const connectTimeout = setTimeout(() => {
          if (this.ws?.readyState === WebSocket.CONNECTING) {
            this.ws?.close();
            reject(new Error('WebSocket connection timeout'));
          }
        }, 10000);

        const originalResolve = resolve;
        resolve = () => {
          clearTimeout(connectTimeout);
          originalResolve();
        };
      } catch (error) {
        console.error('[WebSocket] Connection error:', error);
        reject(error);
      }
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  public disconnect(): void {
    this.isIntentionallyClosed = true;
    this.stopHeartbeat();
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    console.log('[WebSocket] Intentionally disconnected');
  }

  /**
   * Send message to server
   */
  public send(type: string, data?: unknown): void {
    const message: QueuedMessage = {
      type,
      data: data || {},
      timestamp: Date.now(),
    };

    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
      console.log(`[WebSocket] Sent: ${type}`, data);
    } else {
      // Queue message if not connected
      if (this.messageQueue.length < this.config.messageQueueSize) {
        this.messageQueue.push(message);
        console.log(`[WebSocket] Queued: ${type} (${this.messageQueue.length} queued)`);
      } else {
        console.warn(`[WebSocket] Message queue full, dropping message: ${type}`);
      }
    }
  }

  /**
   * Subscribe to message type
   */
  public on<T = unknown>(type: string, handler: MessageHandler<T>): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }

    this.handlers.get(type)!.add(handler as MessageHandler);

    // Return unsubscribe function
    return () => {
      const handlers = this.handlers.get(type);
      if (handlers) {
        handlers.delete(handler as MessageHandler);
      }
    };
  }

  /**
   * Subscribe to message type once
   */
  public once<T = unknown>(type: string, handler: MessageHandler<T>): void {
    const unsubscribe = this.on(type, (data: T) => {
      unsubscribe();
      handler(data);
    });
  }

  /**
   * Subscribe to report progress updates
   */
  public onReportProgress(jobId: string, callback: (update: ReportProgressUpdate) => void): () => void {
    return this.on<{ jobId: string; [key: string]: unknown }>(
      'report_progress',
      (data) => {
        if (data.jobId === jobId) {
          callback({
            jobId: data.jobId,
            status: (data.status as any) || 'processing',
            progress: (data.progress as number) || 0,
            stage: (data.stage as string) || undefined,
            message: (data.message as string) || undefined,
            resultPath: (data.resultPath as string) || undefined,
            error: (data.error as string) || undefined,
            timestamp: new Date(),
          });
        }
      }
    );
  }

  /**
   * Subscribe to report completion
   */
  public onReportComplete(jobId: string, callback: (path: string) => void): () => void {
    return this.on<{ jobId: string; resultPath: string }>(
      'report_complete',
      (data) => {
        if (data.jobId === jobId) {
          callback(data.resultPath);
        }
      }
    );
  }

  /**
   * Subscribe to report error
   */
  public onReportError(jobId: string, callback: (error: string) => void): () => void {
    return this.on<{ jobId: string; error: string }>(
      'report_error',
      (data) => {
        if (data.jobId === jobId) {
          callback(data.error);
        }
      }
    );
  }

  /**
   * Get connection state
   */
  public isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Get readiness state
   */
  public getReadyState(): 'CONNECTING' | 'OPEN' | 'CLOSING' | 'CLOSED' {
    if (!this.ws) return 'CLOSED';

    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'CONNECTING';
      case WebSocket.OPEN:
        return 'OPEN';
      case WebSocket.CLOSING:
        return 'CLOSING';
      case WebSocket.CLOSED:
        return 'CLOSED';
      default:
        return 'CLOSED';
    }
  }

  // ============================================================================
  // PRIVATE METHODS
  // ============================================================================

  /**
   * Handle incoming message
   */
  private handleMessage(rawData: string): void {
    try {
      const message = JSON.parse(rawData) as { type: string; [key: string]: unknown };
      console.log(`[WebSocket] Received: ${message.type}`, message);

      this.emit(message.type, message);
    } catch (error) {
      console.error('[WebSocket] Failed to parse message:', error, rawData);
    }
  }

  /**
   * Emit message to all handlers
   */
  private emit(type: string, data: unknown): void {
    const handlers = this.handlers.get(type);
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(data);
        } catch (error) {
          console.error(`[WebSocket] Handler error for ${type}:`, error);
        }
      });
    }
  }

  /**
   * Flush queued messages
   */
  private flushMessageQueue(): void {
    if (this.messageQueue.length === 0) return;

    console.log(`[WebSocket] Flushing ${this.messageQueue.length} queued messages`);

    const queue = [...this.messageQueue];
    this.messageQueue = [];

    queue.forEach((msg) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify(msg));
      }
    });
  }

  /**
   * Attempt to reconnect
   */
  private attemptReconnect(): void {
    if (this.isIntentionallyClosed) return;

    if (this.reconnectAttempts >= this.config.maxReconnectAttempts) {
      console.error('[WebSocket] Max reconnection attempts reached');
      this.emit('reconnect_failed', { attempts: this.reconnectAttempts });
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(
      this.config.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      this.config.maxReconnectDelay
    );

    console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    this.reconnectTimeout = setTimeout(async () => {
      try {
        await this.connect();
      } catch (error) {
        console.warn('[WebSocket] Reconnect failed:', error);
        // Will be retried on next close
      }
    }, delay);
  }

  /**
   * Start heartbeat to detect stale connections
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();

    this.heartbeatInterval = setInterval(() => {
      if (!this.isConnected()) return;

      const timeSinceLastMessage = Date.now() - this.lastMessageTime;
      if (timeSinceLastMessage > 60000) {
        console.warn('[WebSocket] No messages for 60s, pinging server');
        this.send('ping');
      }
    }, 30000);
  }

  /**
   * Stop heartbeat
   */
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }
}

// ============================================================================
// SINGLETON INSTANCE
// ============================================================================

let instance: WSClient | null = null;

/**
 * Get or create WebSocket client instance
 */
export function getWSClient(): WSClient {
  if (!instance) {
    instance = new WSClient();
  }
  return instance;
}

/**
 * Initialize and connect WebSocket client
 */
export async function initWebSocket(): Promise<void> {
  const client = getWSClient();
  if (!client.isConnected()) {
    await client.connect();
  }
}

/**
 * Disconnect and destroy WebSocket client
 */
export function destroyWebSocket(): void {
  if (instance) {
    instance.disconnect();
    instance = null;
  }
}

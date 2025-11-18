/**
 * WebSocket Service - Conexión en tiempo real con el backend
 * Para actualizaciones de generación de reportes
 */

import type { WebSocketMessage } from './types/backend';

type MessageCallback = (message: WebSocketMessage) => void;
type ErrorCallback = (error: Event) => void;
type ConnectCallback = () => void;
type DisconnectCallback = (event: CloseEvent) => void;

export class ReportWebSocket {
	private ws: WebSocket | null = null;
	private reconnectAttempts = 0;
	private maxReconnectAttempts = 5;
	private reconnectDelay = 2000;
	private messageCallbacks: MessageCallback[] = [];
	private errorCallbacks: ErrorCallback[] = [];
	private connectCallbacks: ConnectCallback[] = [];
	private disconnectCallbacks: DisconnectCallback[] = [];

	constructor(private url: string = 'ws://localhost:8000/ws/report') {}

	/**
	 * Conectar al WebSocket
	 */
	connect(): void {
		if (this.ws?.readyState === WebSocket.OPEN) {
			console.warn('WebSocket already connected');
			return;
		}

		try {
			this.ws = new WebSocket(this.url);

			this.ws.onopen = () => {
				console.log('WebSocket connected');
				this.reconnectAttempts = 0;
				this.connectCallbacks.forEach((cb) => cb());
			};

			this.ws.onmessage = (event) => {
				try {
					const message: WebSocketMessage = JSON.parse(event.data);
					this.messageCallbacks.forEach((cb) => cb(message));
				} catch (error) {
					console.error('Error parsing WebSocket message:', error);
				}
			};

			this.ws.onerror = (error) => {
				console.error('WebSocket error:', error);
				this.errorCallbacks.forEach((cb) => cb(error));
			};

			this.ws.onclose = (event) => {
				console.log('WebSocket disconnected');
				this.disconnectCallbacks.forEach((cb) => cb(event));

				// Auto-reconectar si no fue cierre intencional
				if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
					this.reconnectAttempts++;
					console.log(
						`Reconnecting... (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`
					);
					setTimeout(() => this.connect(), this.reconnectDelay);
				}
			};
		} catch (error) {
			console.error('Error creating WebSocket:', error);
		}
	}

	/**
	 * Desconectar WebSocket
	 */
	disconnect(): void {
		if (this.ws) {
			this.ws.close();
			this.ws = null;
		}
	}

	/**
	 * Enviar mensaje al WebSocket
	 */
	send(message: any): void {
		if (this.ws?.readyState === WebSocket.OPEN) {
			this.ws.send(JSON.stringify(message));
		} else {
			console.warn('WebSocket not connected. Cannot send message.');
		}
	}

	/**
	 * Registrar callback para mensajes
	 */
	onMessage(callback: MessageCallback): () => void {
		this.messageCallbacks.push(callback);
		// Retornar función para desuscribirse
		return () => {
			this.messageCallbacks = this.messageCallbacks.filter((cb) => cb !== callback);
		};
	}

	/**
	 * Registrar callback para errores
	 */
	onError(callback: ErrorCallback): () => void {
		this.errorCallbacks.push(callback);
		return () => {
			this.errorCallbacks = this.errorCallbacks.filter((cb) => cb !== callback);
		};
	}

	/**
	 * Registrar callback para conexión
	 */
	onConnect(callback: ConnectCallback): () => void {
		this.connectCallbacks.push(callback);
		return () => {
			this.connectCallbacks = this.connectCallbacks.filter((cb) => cb !== callback);
		};
	}

	/**
	 * Registrar callback para desconexión
	 */
	onDisconnect(callback: DisconnectCallback): () => void {
		this.disconnectCallbacks.push(callback);
		return () => {
			this.disconnectCallbacks = this.disconnectCallbacks.filter((cb) => cb !== callback);
		};
	}

	/**
	 * Verificar si está conectado
	 */
	get isConnected(): boolean {
		return this.ws?.readyState === WebSocket.OPEN;
	}
}

/**
 * Crear instancia de WebSocket para reportes
 * Usar env var si está disponible, sino default a localhost
 */
export function createReportWebSocket(): ReportWebSocket {
	const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
	const host = import.meta.env.VITE_WS_HOST ?? 'localhost:8000';
	const url = `${protocol}//${host}/ws/report`;

	return new ReportWebSocket(url);
}

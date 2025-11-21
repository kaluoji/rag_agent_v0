// src/lib/api/client.ts
import type { QueryResponse, DocumentData } from '$lib/types/backend';

// Ajusta esta URL a donde corra tu backend
const API_BASE = 'http://localhost:8000';

// ✅ Variable global para mantener el session_id entre mensajes
let currentSessionId: string | null = null;

/**
 * Obtiene el session_id actual de la conversación
 */
export function getCurrentSessionId(): string | null {
  return currentSessionId;
}

/**
 * Establece un session_id específico (útil para cargar conversaciones)
 */
export function setSessionId(sessionId: string | null): void {
  currentSessionId = sessionId;
}

/**
 * Inicia una nueva conversación limpiando el session_id
 */
export function startNewConversation(): void {
  currentSessionId = null;
}

export async function askQuery(query: string): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/api/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      query,
      session_id: currentSessionId  // ✅ Enviar session_id si existe
    })
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || 'Error al realizar la consulta');
  }

  const response = await res.json();
  
  // ✅ Guardar session_id de la respuesta
  if (response.session_id) {
    currentSessionId = response.session_id;
  }

  return response;
}

export async function askQueryWithDocuments(
  query: string,
  documents: DocumentData[]
): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/api/query/with-documents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      query, 
      documents,
      session_id: currentSessionId  // ✅ También aquí
    })
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || 'Error al realizar la consulta con documentos');
  }

  const response = await res.json();
  
  // ✅ Guardar session_id de la respuesta
  if (response.session_id) {
    currentSessionId = response.session_id;
  }

  return response;
}

// Helper para convertir File → DocumentData (base64)
export async function fileToDocumentData(file: File): Promise<DocumentData> {
  const arrayBuffer = await file.arrayBuffer();
  const base64 = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)));

  return {
    name: file.name,
    type: file.type,
    content: base64,
    size: file.size
  };
}
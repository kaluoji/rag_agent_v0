// src/lib/api/client.ts
import type { QueryResponse, DocumentData } from '$lib/types/backend';

// Ajusta esta URL a donde corra tu backend
const API_BASE = 'http://localhost:8000';

export async function askQuery(query: string): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/api/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || 'Error al realizar la consulta');
  }

  return res.json();
}

export async function askQueryWithDocuments(
  query: string,
  documents: DocumentData[]
): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/api/query/with-documents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, documents })
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || 'Error al realizar la consulta con documentos');
  }

  return res.json();
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

import { API_BASE_URL } from './config'
import type { AskResult, ChatHistoryEntry, Collection, DocumentItem, UploadResult } from './types'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init)

  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = body?.detail ?? response.statusText
    throw new Error(typeof detail === 'string' ? detail : 'istek basarisiz oldu')
  }

  return response.json() as Promise<T>
}

export function listCollections(): Promise<Collection[]> {
  return request<Collection[]>('/collections')
}

export function createCollection(name: string): Promise<Collection> {
  return request<Collection>('/collections', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
}

export function listDocuments(collectionId: number): Promise<DocumentItem[]> {
  return request<DocumentItem[]>(`/documents?collection_id=${collectionId}`)
}

export function uploadDocument(collectionId: number, file: File): Promise<UploadResult> {
  const formData = new FormData()
  formData.append('collection_id', String(collectionId))
  formData.append('file', file)

  return request<UploadResult>('/documents/upload', {
    method: 'POST',
    body: formData,
  })
}

export function askQuestion(collectionId: number, question: string, topK = 5): Promise<AskResult> {
  return request<AskResult>('/chat/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ collection_id: collectionId, question, top_k: topK }),
  })
}

export function getChatHistory(collectionId: number): Promise<ChatHistoryEntry[]> {
  return request<ChatHistoryEntry[]>(`/chat/history?collection_id=${collectionId}`)
}

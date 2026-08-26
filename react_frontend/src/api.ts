import { API_BASE_URL } from './config'
import type {
  AnalyzeResult,
  AskResult,
  ChatHistoryEntry,
  Collection,
  Decision,
  DocumentItem,
  Milestone,
  ProjectStatus,
  Requirement,
  Risk,
  TestResult,
  TraceLink,
  UploadResult,
} from './types'

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

export function deleteCollection(collectionId: number): Promise<void> {
  return request<void>(`/collections/${collectionId}`, { method: 'DELETE' })
}

export function listDocuments(collectionId: number): Promise<DocumentItem[]> {
  return request<DocumentItem[]>(`/documents?collection_id=${collectionId}`)
}

export function deleteDocument(documentId: number): Promise<void> {
  return request<void>(`/documents/${documentId}`, { method: 'DELETE' })
}

export function uploadDocument(collectionId: number, file: File, docCategory = 'other'): Promise<UploadResult> {
  const formData = new FormData()
  formData.append('collection_id', String(collectionId))
  formData.append('doc_category', docCategory)
  formData.append('file', file)

  return request<UploadResult>('/documents/upload', {
    method: 'POST',
    body: formData,
  })
}

export function analyzeDocument(documentId: number): Promise<AnalyzeResult> {
  return request<AnalyzeResult>(`/documents/${documentId}/analyze`, { method: 'POST' })
}

export function listRisks(collectionId: number): Promise<Risk[]> {
  return request<Risk[]>(`/risks?collection_id=${collectionId}`)
}

export function listDecisions(collectionId: number): Promise<Decision[]> {
  return request<Decision[]>(`/decisions?collection_id=${collectionId}`)
}

export function listRequirements(collectionId: number): Promise<Requirement[]> {
  return request<Requirement[]>(`/requirements?collection_id=${collectionId}`)
}

export function listMilestones(collectionId: number): Promise<Milestone[]> {
  return request<Milestone[]>(`/milestones?collection_id=${collectionId}`)
}

export function listTestResults(collectionId: number): Promise<TestResult[]> {
  return request<TestResult[]>(`/test-results?collection_id=${collectionId}`)
}

export function listTraceLinks(collectionId: number): Promise<TraceLink[]> {
  return request<TraceLink[]>(`/trace-links?collection_id=${collectionId}`)
}

export function getProjectStatus(collectionId: number): Promise<ProjectStatus> {
  return request<ProjectStatus>(`/project-status?collection_id=${collectionId}`)
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

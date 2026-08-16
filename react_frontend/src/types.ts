export interface Collection {
  id: number
  name: string
  created_at: string
}

export interface DocumentItem {
  id: number
  collection_id: number
  filename: string
  file_type: string
  char_count: number | null
  word_count: number | null
  created_at: string
}

export interface UploadResult {
  document_id: number
  filename: string
  chunk_count: number
}

export interface Source {
  document_name: string
  chunk_index: number
  similarity_score: number
}

export interface AskResult {
  answer: string
  sources: Source[]
}

export interface ChatHistoryEntry {
  id: number
  collection_id: number
  question: string
  answer: string
  sources: Source[]
  response_time_ms: number | null
  created_at: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  pending?: boolean
  error?: boolean
}

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
  doc_category: string | null
  char_count: number | null
  word_count: number | null
  created_at: string
}

export interface UploadResult {
  document_id: number
  filename: string
  chunk_count: number
  doc_category: string
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

export interface Risk {
  id: number
  risk_ref: string
  document_id: number
  chunk_id: number | null
  description: string
  probability: string | null
  impact: string | null
  risk_level: string | null
  affected_milestone: string | null
  responsible: string | null
  evidence_text: string
  created_at: string
}

export interface Decision {
  id: number
  decision_ref: string
  document_id: number
  chunk_id: number | null
  decision_text: string
  decision_date: string | null
  reason: string | null
  affected_area: string | null
  evidence_text: string
  created_at: string
}

export interface Requirement {
  id: number
  requirement_ref: string
  document_id: number
  chunk_id: number | null
  requirement_text: string
  status: string | null
  evidence_text: string
  created_at: string
}

export interface Milestone {
  id: number
  milestone_ref: string
  document_id: number
  chunk_id: number | null
  name: string
  due_date: string | null
  status: string | null
  evidence_text: string
  created_at: string
}

export interface TestResult {
  id: number
  test_ref: string
  document_id: number
  chunk_id: number | null
  test_name: string
  requirement_ref: string | null
  test_status: string | null
  evidence_text: string
  created_at: string
}

export interface TraceLink {
  id: number
  source_type: string
  source_id: number
  target_type: string
  target_id: number
  match_basis: string | null
  created_at: string
}

export interface ProjectHealth {
  requirements: number
  schedule: number
  integration: number
  documentation: number
}

export interface RiskSummary {
  Critical: number
  High: number
  Medium: number
  Low: number
}

export interface StatusSummary {
  milestones_on_track: number
  milestones_delayed: number
  tests_passed: number
  tests_total: number
}

export interface RecentDecision {
  decision_ref: string
  decision_text: string
  decision_date: string | null
  created_at: string
}

export interface UpcomingMilestone {
  milestone_ref: string
  name: string
  due_date: string | null
  status: string | null
}

export interface ProjectStatus {
  health: ProjectHealth
  risk_summary: RiskSummary
  status_summary: StatusSummary
  recent_decisions: RecentDecision[]
  upcoming_milestones: UpcomingMilestone[]
}

export interface AnalyzeResult {
  document_id: number
  doc_category: string
  risks?: number
  decisions?: number
  requirements?: number
  milestones?: number
  test_results?: number
}

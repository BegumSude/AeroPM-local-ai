import { useEffect, useRef, useState } from 'react'
import type { ChangeEvent } from 'react'
import * as api from '../api'
import { useCollectionContext } from '../context/CollectionContext'
import type { AnalyzeResult, DocumentItem } from '../types'

const ACCEPTED_FILE_TYPES = '.pdf,.docx,.txt,.md'

const DOC_CATEGORIES = [
  { value: 'other', label: 'Other' },
  { value: 'project_charter', label: 'Project Charter' },
  { value: 'requirements', label: 'Requirements' },
  { value: 'project_plan', label: 'Project Plan' },
  { value: 'risk_register', label: 'Risk Register' },
  { value: 'meeting_minutes', label: 'Meeting Minutes' },
  { value: 'test_report', label: 'Test Report' },
  { value: 'change_requests', label: 'Change Requests' },
  { value: 'lessons_learned', label: 'Lessons Learned' },
]

function formatAnalyzeResult(result: AnalyzeResult): string {
  const counts = Object.entries(result)
    .filter(([key]) => key !== 'document_id' && key !== 'doc_category')
    .map(([key, value]) => `${value} ${key.replace(/_/g, ' ')}`)
  return counts.length > 0 ? counts.join(', ') : 'no items found'
}

export function DocumentsPage() {
  const { selectedCollectionId, selectedCollection } = useCollectionContext()
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [docCategory, setDocCategory] = useState('other')
  const [analyzingId, setAnalyzingId] = useState<number | null>(null)
  const [analyzeResults, setAnalyzeResults] = useState<Record<number, string>>({})
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const loadDocuments = (collectionId: number) => {
    setIsLoadingDocuments(true)
    api
      .listDocuments(collectionId)
      .then(setDocuments)
      .catch((err: Error) => setError(err.message))
      .finally(() => setIsLoadingDocuments(false))
  }

  useEffect(() => {
    if (selectedCollectionId === null) {
      setDocuments([])
      return
    }
    loadDocuments(selectedCollectionId)
  }, [selectedCollectionId])

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file || selectedCollectionId === null) return

    setIsUploading(true)
    setError(null)
    try {
      await api.uploadDocument(selectedCollectionId, file, docCategory)
      loadDocuments(selectedCollectionId)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setIsUploading(false)
    }
  }

  const handleAnalyze = async (documentId: number) => {
    setAnalyzingId(documentId)
    setError(null)
    try {
      const result = await api.analyzeDocument(documentId)
      setAnalyzeResults((previous) => ({ ...previous, [documentId]: formatAnalyzeResult(result) }))
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setAnalyzingId(null)
    }
  }

  const handleDelete = async (documentId: number, filename: string) => {
    if (!window.confirm(`Delete "${filename}" and any risks, decisions, requirements etc. extracted from it?`)) return
    if (selectedCollectionId === null) return

    setDeletingId(documentId)
    setError(null)
    try {
      await api.deleteDocument(documentId)
      loadDocuments(selectedCollectionId)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="page">
      <header className="page__header">
        <h1 className="page__title">Documents</h1>
        {selectedCollection && <p className="page__subtitle">{selectedCollection.name}</p>}
      </header>

      {error && <p className="page__error">{error}</p>}
      {!selectedCollectionId && <p className="page__hint">Select or create a collection to manage documents.</p>}

      {selectedCollectionId && (
        <>
          <div className="documents__upload">
            <select
              className="documents__category-select"
              value={docCategory}
              onChange={(event) => setDocCategory(event.target.value)}
              disabled={isUploading}
            >
              {DOC_CATEGORIES.map((category) => (
                <option key={category.value} value={category.value}>
                  {category.label}
                </option>
              ))}
            </select>
            <input
              ref={fileInputRef}
              type="file"
              accept={ACCEPTED_FILE_TYPES}
              className="documents__file-input"
              onChange={handleFileChange}
              disabled={isUploading}
            />
            <button
              type="button"
              className="documents__upload-button"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
            >
              {isUploading ? 'Uploading...' : '+ Upload document (PDF, DOCX, TXT, MD)'}
            </button>
          </div>

          <div className="documents__table-wrap">
            {isLoadingDocuments && <p className="page__hint">Loading...</p>}
            {!isLoadingDocuments && documents.length === 0 && (
              <p className="page__hint">No documents in this collection yet.</p>
            )}
            {!isLoadingDocuments && documents.length > 0 && (
              <table className="documents__table">
                <thead>
                  <tr>
                    <th>Filename</th>
                    <th>Category</th>
                    <th>Words</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {documents.map((document) => (
                    <tr key={document.id}>
                      <td>{document.filename}</td>
                      <td>{document.doc_category ?? 'other'}</td>
                      <td>{document.word_count ?? 0}</td>
                      <td className="documents__actions-cell">
                        <button
                          type="button"
                          className="documents__analyze-button"
                          onClick={() => handleAnalyze(document.id)}
                          disabled={analyzingId === document.id}
                        >
                          {analyzingId === document.id ? 'Analyzing...' : 'Analyze'}
                        </button>
                        {analyzeResults[document.id] && (
                          <span className="documents__analyze-result">{analyzeResults[document.id]}</span>
                        )}
                        <button
                          type="button"
                          className="documents__delete-button"
                          onClick={() => handleDelete(document.id, document.filename)}
                          disabled={deletingId === document.id}
                          aria-label={`Delete ${document.filename}`}
                        >
                          {deletingId === document.id ? 'Deleting...' : 'Delete'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </div>
  )
}

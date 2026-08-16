import { useEffect, useState } from 'react'
import './App.css'
import * as api from './api'
import { ChatPanel } from './components/ChatPanel'
import { Sidebar } from './components/Sidebar'
import { SourcesPanel } from './components/SourcesPanel'
import type { ChatHistoryEntry, ChatMessage, Collection, DocumentItem, Source } from './types'

function messagesFromHistory(history: ChatHistoryEntry[]): ChatMessage[] {
  return history.flatMap((entry) => [
    { id: `${entry.id}-question`, role: 'user' as const, content: entry.question },
    { id: `${entry.id}-answer`, role: 'assistant' as const, content: entry.answer, sources: entry.sources },
  ])
}

function App() {
  const [collections, setCollections] = useState<Collection[]>([])
  const [selectedCollectionId, setSelectedCollectionId] = useState<number | null>(null)
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [activeSources, setActiveSources] = useState<Source[]>([])
  const [activeMessageId, setActiveMessageId] = useState<string | null>(null)

  const [isLoadingCollections, setIsLoadingCollections] = useState(false)
  const [isCreatingCollection, setIsCreatingCollection] = useState(false)
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [isSourcesPanelOpen, setIsSourcesPanelOpen] = useState(false)

  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setIsLoadingCollections(true)
    api
      .listCollections()
      .then(setCollections)
      .catch((err: Error) => setError(err.message))
      .finally(() => setIsLoadingCollections(false))
  }, [])

  useEffect(() => {
    if (selectedCollectionId === null) {
      setDocuments([])
      setMessages([])
      setActiveSources([])
      setActiveMessageId(null)
      return
    }

    setIsLoadingDocuments(true)
    api
      .listDocuments(selectedCollectionId)
      .then(setDocuments)
      .catch((err: Error) => setError(err.message))
      .finally(() => setIsLoadingDocuments(false))

    setIsLoadingHistory(true)
    api
      .getChatHistory(selectedCollectionId)
      .then((history) => {
        const nextMessages = messagesFromHistory(history)
        setMessages(nextMessages)
        const lastAssistantMessage = [...nextMessages].reverse().find((message) => message.role === 'assistant')
        setActiveSources(lastAssistantMessage?.sources ?? [])
        setActiveMessageId(lastAssistantMessage?.id ?? null)
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setIsLoadingHistory(false))
  }, [selectedCollectionId])

  const handleCreateCollection = async (name: string) => {
    setIsCreatingCollection(true)
    setError(null)
    try {
      const collection = await api.createCollection(name)
      setCollections((previous) => [...previous, collection])
      setSelectedCollectionId(collection.id)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setIsCreatingCollection(false)
    }
  }

  const handleUploadDocument = async (file: File) => {
    if (selectedCollectionId === null) return
    setIsUploading(true)
    setError(null)
    try {
      await api.uploadDocument(selectedCollectionId, file)
      const refreshedDocuments = await api.listDocuments(selectedCollectionId)
      setDocuments(refreshedDocuments)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setIsUploading(false)
    }
  }

  const handleSend = async (question: string) => {
    if (selectedCollectionId === null) return

    const questionMessage: ChatMessage = {
      id: `pending-${Date.now()}-question`,
      role: 'user',
      content: question,
    }
    const pendingMessage: ChatMessage = {
      id: `pending-${Date.now()}-answer`,
      role: 'assistant',
      content: '',
      pending: true,
    }

    setMessages((previous) => [...previous, questionMessage, pendingMessage])
    setIsSending(true)
    setError(null)

    try {
      const result = await api.askQuestion(selectedCollectionId, question)
      const answerMessage: ChatMessage = {
        id: pendingMessage.id,
        role: 'assistant',
        content: result.answer,
        sources: result.sources,
      }
      setMessages((previous) => previous.map((message) => (message.id === pendingMessage.id ? answerMessage : message)))
      setActiveSources(result.sources)
      setActiveMessageId(answerMessage.id)
      setIsSourcesPanelOpen(true)
    } catch (err) {
      const errorMessage: ChatMessage = {
        id: pendingMessage.id,
        role: 'assistant',
        content: (err as Error).message,
        error: true,
      }
      setMessages((previous) => previous.map((message) => (message.id === pendingMessage.id ? errorMessage : message)))
    } finally {
      setIsSending(false)
    }
  }

  const handleSelectMessage = (message: ChatMessage) => {
    if (!message.sources) return
    setActiveSources(message.sources)
    setActiveMessageId(message.id)
    setIsSourcesPanelOpen(true)
  }

  const selectedCollection = collections.find((collection) => collection.id === selectedCollectionId)

  return (
    <div className="app">
      {error && (
        <div className="app__error-banner" role="alert">
          {error}
          <button type="button" onClick={() => setError(null)} aria-label="Kapat">
            x
          </button>
        </div>
      )}

      <div className="app__layout">
        <Sidebar
          collections={collections}
          selectedCollectionId={selectedCollectionId}
          onSelectCollection={setSelectedCollectionId}
          onCreateCollection={handleCreateCollection}
          isCreatingCollection={isCreatingCollection}
          documents={documents}
          isLoadingDocuments={isLoadingDocuments || isLoadingCollections}
          onUploadDocument={handleUploadDocument}
          isUploading={isUploading}
        />

        <ChatPanel
          collectionName={selectedCollection?.name ?? null}
          messages={messages}
          isSending={isSending}
          isLoadingHistory={isLoadingHistory}
          onSend={handleSend}
          onSelectMessage={handleSelectMessage}
          activeMessageId={activeMessageId}
          onToggleSources={() => setIsSourcesPanelOpen((previous) => !previous)}
        />

        <SourcesPanel
          sources={activeSources}
          isOpen={isSourcesPanelOpen}
          onClose={() => setIsSourcesPanelOpen(false)}
        />
      </div>
    </div>
  )
}

export default App

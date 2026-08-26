import { useEffect, useState } from 'react'
import * as api from '../api'
import { ChatPanel } from '../components/ChatPanel'
import { SourcesPanel } from '../components/SourcesPanel'
import { useCollectionContext } from '../context/CollectionContext'
import type { ChatHistoryEntry, ChatMessage, Source } from '../types'

function messagesFromHistory(history: ChatHistoryEntry[]): ChatMessage[] {
  return history.flatMap((entry) => [
    { id: `${entry.id}-question`, role: 'user' as const, content: entry.question },
    { id: `${entry.id}-answer`, role: 'assistant' as const, content: entry.answer, sources: entry.sources },
  ])
}

export function ProjectQAPage() {
  const { selectedCollectionId, selectedCollection } = useCollectionContext()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [activeSources, setActiveSources] = useState<Source[]>([])
  const [activeMessageId, setActiveMessageId] = useState<string | null>(null)
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [isSourcesPanelOpen, setIsSourcesPanelOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (selectedCollectionId === null) {
      setMessages([])
      setActiveSources([])
      setActiveMessageId(null)
      return
    }

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
      setMessages((previous) =>
        previous.map((message) => (message.id === pendingMessage.id ? answerMessage : message))
      )
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
      setMessages((previous) =>
        previous.map((message) => (message.id === pendingMessage.id ? errorMessage : message))
      )
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

  return (
    <div className="qa-page">
      {error && (
        <div className="app__error-banner" role="alert">
          {error}
          <button type="button" onClick={() => setError(null)} aria-label="Dismiss">
            x
          </button>
        </div>
      )}
      <div className="qa-page__layout">
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

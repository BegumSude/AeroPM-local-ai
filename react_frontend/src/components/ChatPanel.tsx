import { useEffect, useRef, useState } from 'react'
import type { ChatMessage } from '../types'

interface ChatPanelProps {
  collectionName: string | null
  messages: ChatMessage[]
  isSending: boolean
  isLoadingHistory: boolean
  onSend: (question: string) => void
  onSelectMessage: (message: ChatMessage) => void
  activeMessageId: string | null
  onToggleSources: () => void
}

export function ChatPanel({
  collectionName,
  messages,
  isSending,
  isLoadingHistory,
  onSend,
  onSelectMessage,
  activeMessageId,
  onToggleSources,
}: ChatPanelProps) {
  const [question, setQuestion] = useState('')
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight })
  }, [messages])

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    const trimmed = question.trim()
    if (!trimmed || isSending) return
    onSend(trimmed)
    setQuestion('')
  }

  return (
    <main className="chat">
      <header className="chat__header">
        <div>
          <h1 className="chat__title">{collectionName ?? 'Bir koleksiyon secin'}</h1>
          {collectionName && <p className="chat__subtitle">Yuklenen belgelere dayanarak soru sorun</p>}
        </div>
        <button type="button" className="chat__sources-toggle" onClick={onToggleSources}>
          Kaynaklar
        </button>
      </header>

      <div className="chat__messages" ref={scrollRef}>
        {!collectionName && (
          <div className="chat__empty-state">
            <p>Sohbete baslamak icin sol taraftan bir koleksiyon secin veya olusturun.</p>
          </div>
        )}

        {collectionName && isLoadingHistory && <div className="chat__empty-state">Gecmis yukleniyor...</div>}

        {collectionName && !isLoadingHistory && messages.length === 0 && (
          <div className="chat__empty-state">
            <p>Henuz mesaj yok. Belge yukleyip bir soru sorarak baslayin.</p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`chat__message chat__message--${message.role}`}
          >
            <div className="chat__message-role">{message.role === 'user' ? 'Siz' : 'Asistan'}</div>
            <button
              type="button"
              className={
                message.role === 'assistant' && message.id === activeMessageId
                  ? 'chat__bubble chat__bubble--assistant chat__bubble--active'
                  : `chat__bubble chat__bubble--${message.role}`
              }
              onClick={() => message.role === 'assistant' && onSelectMessage(message)}
              disabled={message.role === 'user' || !message.sources}
            >
              {message.pending ? <span className="chat__typing">Yaniti hazirliyor...</span> : message.content}
            </button>
          </div>
        ))}
      </div>

      <form className="chat__input-row" onSubmit={handleSubmit}>
        <input
          type="text"
          className="chat__input"
          placeholder={collectionName ? 'Bir soru sorun...' : 'Once bir koleksiyon secin'}
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          disabled={!collectionName || isSending}
        />
        <button
          type="submit"
          className="chat__send-button"
          disabled={!collectionName || isSending || question.trim().length === 0}
        >
          {isSending ? 'Gonderiliyor...' : 'Gonder'}
        </button>
      </form>
    </main>
  )
}

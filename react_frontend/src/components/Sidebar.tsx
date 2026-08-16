import { useRef, useState } from 'react'
import type { Collection, DocumentItem } from '../types'

const ACCEPTED_FILE_TYPES = '.pdf,.docx,.txt,.md'

interface SidebarProps {
  collections: Collection[]
  selectedCollectionId: number | null
  onSelectCollection: (id: number) => void
  onCreateCollection: (name: string) => Promise<void>
  isCreatingCollection: boolean
  documents: DocumentItem[]
  isLoadingDocuments: boolean
  onUploadDocument: (file: File) => Promise<void>
  isUploading: boolean
}

export function Sidebar({
  collections,
  selectedCollectionId,
  onSelectCollection,
  onCreateCollection,
  isCreatingCollection,
  documents,
  isLoadingDocuments,
  onUploadDocument,
  isUploading,
}: SidebarProps) {
  const [newCollectionName, setNewCollectionName] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const selectedCollection = collections.find((collection) => collection.id === selectedCollectionId)

  const handleCreateCollection = async (event: React.FormEvent) => {
    event.preventDefault()
    const name = newCollectionName.trim()
    if (!name) return
    await onCreateCollection(name)
    setNewCollectionName('')
  }

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    await onUploadDocument(file)
  }

  return (
    <aside className="sidebar">
      <div className="sidebar__brand">
        <span className="sidebar__brand-mark">RAG</span>
        <div>
          <div className="sidebar__brand-name">Local Document Assistant</div>
          <div className="sidebar__brand-sub">Foundry Local uzerinde calisir</div>
        </div>
      </div>

      <section className="sidebar__section">
        <h2 className="sidebar__heading">Koleksiyonlar</h2>

        <ul className="sidebar__list">
          {collections.length === 0 && <li className="sidebar__empty">Henuz koleksiyon yok</li>}
          {collections.map((collection) => (
            <li key={collection.id}>
              <button
                type="button"
                className={
                  collection.id === selectedCollectionId
                    ? 'sidebar__list-item sidebar__list-item--active'
                    : 'sidebar__list-item'
                }
                onClick={() => onSelectCollection(collection.id)}
              >
                {collection.name}
              </button>
            </li>
          ))}
        </ul>

        <form className="sidebar__create-form" onSubmit={handleCreateCollection}>
          <input
            type="text"
            value={newCollectionName}
            onChange={(event) => setNewCollectionName(event.target.value)}
            placeholder="Yeni koleksiyon adi"
            className="sidebar__input"
          />
          <button
            type="submit"
            className="sidebar__button"
            disabled={isCreatingCollection || newCollectionName.trim().length === 0}
          >
            {isCreatingCollection ? 'Olusturuluyor...' : 'Olustur'}
          </button>
        </form>
      </section>

      <section className="sidebar__section sidebar__section--grow">
        <div className="sidebar__section-header">
          <h2 className="sidebar__heading">Belgeler</h2>
          {selectedCollection && <span className="sidebar__active-badge">{selectedCollection.name}</span>}
        </div>

        {!selectedCollectionId && <p className="sidebar__hint">Belgeleri gormek icin bir koleksiyon secin.</p>}

        {selectedCollectionId && (
          <>
            <ul className="sidebar__list sidebar__list--documents">
              {isLoadingDocuments && <li className="sidebar__empty">Yukleniyor...</li>}
              {!isLoadingDocuments && documents.length === 0 && (
                <li className="sidebar__empty">Bu koleksiyonda belge yok</li>
              )}
              {!isLoadingDocuments &&
                documents.map((document) => (
                  <li key={document.id} className="sidebar__document">
                    <span className="sidebar__document-name">{document.filename}</span>
                    <span className="sidebar__document-meta">{document.file_type.toUpperCase()}</span>
                  </li>
                ))}
            </ul>

            <input
              ref={fileInputRef}
              type="file"
              accept={ACCEPTED_FILE_TYPES}
              className="sidebar__file-input"
              onChange={handleFileChange}
              disabled={isUploading}
            />
            <button
              type="button"
              className="sidebar__upload-button"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
            >
              {isUploading ? 'Yukleniyor...' : '+ Belge yukle (PDF, DOCX, TXT, MD)'}
            </button>
          </>
        )}
      </section>
    </aside>
  )
}

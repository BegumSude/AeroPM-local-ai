import type { Source } from '../types'

interface SourcesPanelProps {
  sources: Source[]
  isOpen: boolean
  onClose: () => void
}

export function SourcesPanel({ sources, isOpen, onClose }: SourcesPanelProps) {
  return (
    <>
      {isOpen && <div className="sources__overlay" onClick={onClose} />}
      <aside className={isOpen ? 'sources sources--open' : 'sources'}>
        <div className="sources__header">
          <h2 className="sources__heading">Kaynaklar</h2>
          <button type="button" className="sources__close" onClick={onClose} aria-label="Kaynaklari kapat">
            x
          </button>
        </div>

        {sources.length === 0 && (
          <p className="sources__empty">
            Bir soru sorduktan sonra kullanilan belge parcalari burada listelenir.
          </p>
        )}

        <ul className="sources__list">
          {sources.map((source, index) => (
            <li key={`${source.document_name}-${source.chunk_index}-${index}`} className="sources__item">
              <div className="sources__item-header">
                <span className="sources__document-name">{source.document_name}</span>
                <span className="sources__score">{Math.round(source.similarity_score * 100)}%</span>
              </div>
              <div className="sources__chunk-index">Parca #{source.chunk_index}</div>
            </li>
          ))}
        </ul>
      </aside>
    </>
  )
}

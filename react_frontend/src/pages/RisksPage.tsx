import { useEffect, useState } from 'react'
import * as api from '../api'
import { useCollectionContext } from '../context/CollectionContext'
import type { Risk } from '../types'

const LEVEL_ORDER: Record<string, number> = { Critical: 0, High: 1, Medium: 2, Low: 3 }

export function RisksPage() {
  const { selectedCollectionId, selectedCollection } = useCollectionContext()
  const [risks, setRisks] = useState<Risk[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (selectedCollectionId === null) {
      setRisks([])
      return
    }
    setIsLoading(true)
    api
      .listRisks(selectedCollectionId)
      .then((result) => {
        const sorted = [...result].sort(
          (a, b) => (LEVEL_ORDER[a.risk_level ?? ''] ?? 9) - (LEVEL_ORDER[b.risk_level ?? ''] ?? 9)
        )
        setRisks(sorted)
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setIsLoading(false))
  }, [selectedCollectionId])

  return (
    <div className="page">
      <header className="page__header">
        <h1 className="page__title">Risk Radar</h1>
        {selectedCollection && <p className="page__subtitle">{selectedCollection.name}</p>}
      </header>

      {error && <p className="page__error">{error}</p>}
      {!selectedCollectionId && <p className="page__hint">Select a collection to view risks.</p>}
      {selectedCollectionId && isLoading && <p className="page__hint">Loading...</p>}
      {selectedCollectionId && !isLoading && risks.length === 0 && (
        <p className="page__hint">No risks extracted yet. Analyze a document from the Documents page.</p>
      )}

      {risks.length > 0 && (
        <div className="cards">
          {risks.map((risk) => (
            <article key={risk.id} className={`risk-card risk-card--${(risk.risk_level ?? 'unknown').toLowerCase()}`}>
              <div className="risk-card__header">
                <span className="risk-card__ref">{risk.risk_ref}</span>
                <span className="risk-card__level">{risk.risk_level ?? 'Unknown'}</span>
              </div>
              <p className="risk-card__description">{risk.description}</p>
              <dl className="risk-card__meta">
                <div>
                  <dt>Probability</dt>
                  <dd>{risk.probability ?? '-'}</dd>
                </div>
                <div>
                  <dt>Impact</dt>
                  <dd>{risk.impact ?? '-'}</dd>
                </div>
                <div>
                  <dt>Milestone</dt>
                  <dd>{risk.affected_milestone ?? '-'}</dd>
                </div>
                <div>
                  <dt>Responsible</dt>
                  <dd>{risk.responsible ?? '-'}</dd>
                </div>
              </dl>
              <p className="risk-card__evidence">&quot;{risk.evidence_text}&quot;</p>
            </article>
          ))}
        </div>
      )}
    </div>
  )
}

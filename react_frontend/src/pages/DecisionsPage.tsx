import { useEffect, useState } from 'react'
import * as api from '../api'
import { useCollectionContext } from '../context/CollectionContext'
import type { Decision } from '../types'

export function DecisionsPage() {
  const { selectedCollectionId, selectedCollection } = useCollectionContext()
  const [decisions, setDecisions] = useState<Decision[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (selectedCollectionId === null) {
      setDecisions([])
      return
    }
    setIsLoading(true)
    api
      .listDecisions(selectedCollectionId)
      .then(setDecisions)
      .catch((err: Error) => setError(err.message))
      .finally(() => setIsLoading(false))
  }, [selectedCollectionId])

  return (
    <div className="page">
      <header className="page__header">
        <h1 className="page__title">Decisions</h1>
        {selectedCollection && <p className="page__subtitle">{selectedCollection.name}</p>}
      </header>

      {error && <p className="page__error">{error}</p>}
      {!selectedCollectionId && <p className="page__hint">Select a collection to view decisions.</p>}
      {selectedCollectionId && isLoading && <p className="page__hint">Loading...</p>}
      {selectedCollectionId && !isLoading && decisions.length === 0 && (
        <p className="page__hint">No decisions extracted yet. Analyze a document from the Documents page.</p>
      )}

      {decisions.length > 0 && (
        <div className="cards">
          {decisions.map((decision) => (
            <article key={decision.id} className="decision-card">
              <div className="decision-card__header">
                <span className="decision-card__ref">{decision.decision_ref}</span>
                {decision.decision_date && <span className="decision-card__date">{decision.decision_date}</span>}
              </div>
              <p className="decision-card__text">{decision.decision_text}</p>
              {decision.reason && <p className="decision-card__reason">Reason: {decision.reason}</p>}
              {decision.affected_area && <p className="decision-card__area">Affects: {decision.affected_area}</p>}
              <p className="decision-card__evidence">&quot;{decision.evidence_text}&quot;</p>
            </article>
          ))}
        </div>
      )}
    </div>
  )
}

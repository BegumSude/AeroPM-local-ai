import { useEffect, useState } from 'react'
import * as api from '../api'
import { useCollectionContext } from '../context/CollectionContext'
import type { Decision, Milestone, Requirement, Risk, TestResult, TraceLink } from '../types'

interface TraceEntry {
  type: string
  ref: string
  label: string
}

export function RequirementsPage() {
  const { selectedCollectionId, selectedCollection } = useCollectionContext()
  const [requirements, setRequirements] = useState<Requirement[]>([])
  const [testResults, setTestResults] = useState<TestResult[]>([])
  const [risks, setRisks] = useState<Risk[]>([])
  const [decisions, setDecisions] = useState<Decision[]>([])
  const [milestones, setMilestones] = useState<Milestone[]>([])
  const [traceLinks, setTraceLinks] = useState<TraceLink[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (selectedCollectionId === null) {
      setRequirements([])
      setTestResults([])
      setRisks([])
      setDecisions([])
      setMilestones([])
      setTraceLinks([])
      return
    }
    setIsLoading(true)
    Promise.all([
      api.listRequirements(selectedCollectionId),
      api.listTestResults(selectedCollectionId),
      api.listRisks(selectedCollectionId),
      api.listDecisions(selectedCollectionId),
      api.listMilestones(selectedCollectionId),
      api.listTraceLinks(selectedCollectionId),
    ])
      .then(([requirementsResult, testResultsResult, risksResult, decisionsResult, milestonesResult, traceLinksResult]) => {
        setRequirements(requirementsResult)
        setTestResults(testResultsResult)
        setRisks(risksResult)
        setDecisions(decisionsResult)
        setMilestones(milestonesResult)
        setTraceLinks(traceLinksResult)
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setIsLoading(false))
  }, [selectedCollectionId])

  const findLinkedItems = (sourceType: string, sourceId: number): TraceEntry[] => {
    return traceLinks
      .filter((link) => link.source_type === sourceType && link.source_id === sourceId)
      .map((link): TraceEntry | null => {
        if (link.target_type === 'test') {
          const test = testResults.find((item) => item.id === link.target_id)
          return test ? { type: 'test', ref: test.test_ref, label: test.test_name } : null
        }
        if (link.target_type === 'risk') {
          const risk = risks.find((item) => item.id === link.target_id)
          return risk ? { type: 'risk', ref: risk.risk_ref, label: risk.description } : null
        }
        if (link.target_type === 'decision') {
          const decision = decisions.find((item) => item.id === link.target_id)
          return decision ? { type: 'decision', ref: decision.decision_ref, label: decision.decision_text } : null
        }
        if (link.target_type === 'milestone') {
          const milestone = milestones.find((item) => item.id === link.target_id)
          return milestone ? { type: 'milestone', ref: milestone.milestone_ref, label: milestone.name } : null
        }
        return null
      })
      .filter((entry): entry is TraceEntry => entry !== null)
  }

  return (
    <div className="page">
      <header className="page__header">
        <h1 className="page__title">Requirements Traceability</h1>
        {selectedCollection && <p className="page__subtitle">{selectedCollection.name}</p>}
      </header>

      {error && <p className="page__error">{error}</p>}
      {!selectedCollectionId && <p className="page__hint">Select a collection to view requirements.</p>}
      {selectedCollectionId && isLoading && <p className="page__hint">Loading...</p>}
      {selectedCollectionId && !isLoading && requirements.length === 0 && (
        <p className="page__hint">No requirements extracted yet. Analyze a document from the Documents page.</p>
      )}

      {requirements.length > 0 && (
        <div className="cards">
          {requirements.map((requirement) => {
            const linkedItems = findLinkedItems('requirement', requirement.id)
            return (
              <article key={requirement.id} className="requirement-card">
                <div className="requirement-card__header">
                  <span className="requirement-card__ref">{requirement.requirement_ref}</span>
                  {requirement.status && <span className="requirement-card__status">{requirement.status}</span>}
                </div>
                <p className="requirement-card__text">{requirement.requirement_text}</p>
                <div className="requirement-card__trace">
                  {linkedItems.length === 0 && (
                    <span className="requirement-card__trace-empty">No linked tests found</span>
                  )}
                  {linkedItems.map((entry) => (
                    <span key={`${entry.type}-${entry.ref}`} className="requirement-card__trace-item">
                      → {entry.ref} {entry.label}
                    </span>
                  ))}
                </div>
                <p className="requirement-card__evidence">&quot;{requirement.evidence_text}&quot;</p>
              </article>
            )
          })}
        </div>
      )}
    </div>
  )
}

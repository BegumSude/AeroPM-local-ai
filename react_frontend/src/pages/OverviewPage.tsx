import { useEffect, useState } from 'react'
import * as api from '../api'
import { AircraftIcon } from '../components/AircraftIcon'
import { useCollectionContext } from '../context/CollectionContext'
import type { ProjectStatus } from '../types'

export function OverviewPage() {
  const { selectedCollectionId, selectedCollection } = useCollectionContext()
  const [status, setStatus] = useState<ProjectStatus | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (selectedCollectionId === null) {
      setStatus(null)
      return
    }
    setIsLoading(true)
    api
      .getProjectStatus(selectedCollectionId)
      .then(setStatus)
      .catch((err: Error) => setError(err.message))
      .finally(() => setIsLoading(false))
  }, [selectedCollectionId])

  return (
    <div className="page">
      <div className="banner">
        <AircraftIcon className="banner__icon" />
        <div className="banner__text">
          <h1 className="banner__title">AeroPM</h1>
          <p className="banner__subtitle">Local AI-Powered Project Intelligence for Aviation</p>
          {selectedCollection && <p className="banner__collection">{selectedCollection.name}</p>}
        </div>
      </div>

      <header className="page__header">
        <h2 className="page__title">Overview</h2>
        {selectedCollection && <p className="page__subtitle">{selectedCollection.name}</p>}
      </header>

      {error && <p className="page__error">{error}</p>}
      {!selectedCollectionId && <p className="page__hint">Select or create a collection to see project status.</p>}
      {selectedCollectionId && isLoading && <p className="page__hint">Loading...</p>}

      {status && (
        <div className="overview">
          <section className="overview__section">
            <h2 className="overview__section-title">Project Health</h2>
            <div className="health-grid">
              <HealthTile label="Requirements" value={status.health.requirements} />
              <HealthTile label="Schedule" value={status.health.schedule} />
              <HealthTile label="Integration" value={status.health.integration} />
              <HealthTile label="Documentation" value={status.health.documentation} />
            </div>
          </section>

          <section className="overview__section">
            <h2 className="overview__section-title">Risk Summary</h2>
            <div className="risk-summary">
              <RiskTile label="Critical" count={status.risk_summary.Critical} />
              <RiskTile label="High" count={status.risk_summary.High} />
              <RiskTile label="Medium" count={status.risk_summary.Medium} />
              <RiskTile label="Low" count={status.risk_summary.Low} />
            </div>
          </section>

          <section className="overview__section">
            <h2 className="overview__section-title">Project Status</h2>
            <div className="status-summary">
              <div className="status-summary__item">
                <span className="status-summary__value">{status.status_summary.milestones_on_track}</span>
                <span className="status-summary__label">Milestones on track</span>
              </div>
              <div className="status-summary__item">
                <span className="status-summary__value">{status.status_summary.milestones_delayed}</span>
                <span className="status-summary__label">Milestones delayed</span>
              </div>
              <div className="status-summary__item">
                <span className="status-summary__value">
                  {status.status_summary.tests_passed}/{status.status_summary.tests_total}
                </span>
                <span className="status-summary__label">Tests passed</span>
              </div>
            </div>
          </section>

          <div className="overview__columns">
            <section className="overview__section">
              <h2 className="overview__section-title">Recent Decisions</h2>
              {status.recent_decisions.length === 0 && <p className="page__hint">No decisions yet.</p>}
              <ul className="overview__list">
                {status.recent_decisions.map((decision) => (
                  <li key={decision.decision_ref} className="overview__list-item">
                    <span className="overview__list-ref">{decision.decision_ref}</span>
                    <span>{decision.decision_text}</span>
                  </li>
                ))}
              </ul>
            </section>

            <section className="overview__section">
              <h2 className="overview__section-title">Upcoming Milestones</h2>
              {status.upcoming_milestones.length === 0 && <p className="page__hint">No milestones yet.</p>}
              <ul className="overview__list">
                {status.upcoming_milestones.map((milestone) => (
                  <li key={milestone.milestone_ref} className="overview__list-item">
                    <span className="overview__list-ref">{milestone.milestone_ref}</span>
                    <span>
                      {milestone.name}
                      {milestone.due_date ? ` — ${milestone.due_date}` : ''}
                    </span>
                    {milestone.status && <span className="overview__list-status">{milestone.status}</span>}
                  </li>
                ))}
              </ul>
            </section>
          </div>
        </div>
      )}
    </div>
  )
}

function HealthTile({ label, value }: { label: string; value: number }) {
  return (
    <div className="health-tile">
      <div className="health-tile__value">{value}%</div>
      <div className="health-tile__label">{label}</div>
      <div className="health-tile__bar">
        <div className="health-tile__bar-fill" style={{ width: `${Math.min(value, 100)}%` }} />
      </div>
    </div>
  )
}

function RiskTile({ label, count }: { label: string; count: number }) {
  return (
    <div className={`risk-tile risk-tile--${label.toLowerCase()}`}>
      <div className="risk-tile__count">{count}</div>
      <div className="risk-tile__label">{label}</div>
    </div>
  )
}

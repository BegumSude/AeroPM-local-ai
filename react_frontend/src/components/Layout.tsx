import { useState } from 'react'
import type { FormEvent } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useCollectionContext } from '../context/CollectionContext'
import { useTheme } from '../hooks/useTheme'
import { AircraftIcon } from './AircraftIcon'
import { ThemeToggle } from './ThemeToggle'

const NAV_ITEMS = [
  { to: '/', label: 'Overview', end: true },
  { to: '/documents', label: 'Documents', end: false },
  { to: '/risks', label: 'Risks', end: false },
  { to: '/decisions', label: 'Decisions', end: false },
  { to: '/requirements', label: 'Requirements', end: false },
  { to: '/chat', label: 'Project Q&A', end: false },
]

export function Layout() {
  const {
    collections,
    selectedCollectionId,
    selectCollection,
    createCollection,
    deleteCollection,
    isCreatingCollection,
    isDeletingCollectionId,
    isLoadingCollections,
    error,
    clearError,
  } = useCollectionContext()
  const [newCollectionName, setNewCollectionName] = useState('')
  const { theme, toggleTheme } = useTheme()

  const handleCreateCollection = async (event: FormEvent) => {
    event.preventDefault()
    const name = newCollectionName.trim()
    if (!name) return
    await createCollection(name)
    setNewCollectionName('')
  }

  const handleDeleteCollection = async (id: number, name: string) => {
    if (!window.confirm(`Delete collection "${name}" and all of its documents and extracted data?`)) return
    await deleteCollection(id)
  }

  return (
    <div className="app">
      {error && (
        <div className="app__error-banner" role="alert">
          {error}
          <button type="button" onClick={clearError} aria-label="Dismiss">
            x
          </button>
        </div>
      )}

      <div className="shell">
        <aside className="shell__sidebar">
          <div className="shell__brand">
            <span className="shell__brand-mark">
              <AircraftIcon className="shell__brand-icon" />
            </span>
            <div className="shell__brand-text">
              <div className="shell__brand-name">AeroPM</div>
              <div className="shell__brand-sub">Local AI-Powered Project Intelligence for Aviation</div>
            </div>
            <ThemeToggle theme={theme} onToggle={toggleTheme} />
          </div>

          <nav className="shell__nav">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  isActive ? 'shell__nav-link shell__nav-link--active' : 'shell__nav-link'
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="shell__collections">
            <h2 className="shell__heading">Collections</h2>
            <ul className="shell__collection-list">
              {isLoadingCollections && <li className="shell__empty">Loading...</li>}
              {!isLoadingCollections && collections.length === 0 && (
                <li className="shell__empty">No collections yet</li>
              )}
              {collections.map((collection) => (
                <li key={collection.id} className="shell__collection-row">
                  <button
                    type="button"
                    className={
                      collection.id === selectedCollectionId
                        ? 'shell__collection-item shell__collection-item--active'
                        : 'shell__collection-item'
                    }
                    onClick={() => selectCollection(collection.id)}
                  >
                    {collection.name}
                  </button>
                  <button
                    type="button"
                    className="shell__collection-delete"
                    onClick={() => handleDeleteCollection(collection.id, collection.name)}
                    disabled={isDeletingCollectionId === collection.id}
                    aria-label={`Delete ${collection.name}`}
                  >
                    x
                  </button>
                </li>
              ))}
            </ul>

            <form className="shell__create-form" onSubmit={handleCreateCollection}>
              <input
                type="text"
                value={newCollectionName}
                onChange={(event) => setNewCollectionName(event.target.value)}
                placeholder="New collection name"
                className="shell__input"
              />
              <button
                type="submit"
                className="shell__button"
                disabled={isCreatingCollection || newCollectionName.trim().length === 0}
              >
                {isCreatingCollection ? 'Creating...' : 'Create'}
              </button>
            </form>
          </div>
        </aside>

        <main className="shell__content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

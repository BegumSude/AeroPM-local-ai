import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import * as api from '../api'
import type { Collection } from '../types'

interface CollectionContextValue {
  collections: Collection[]
  selectedCollectionId: number | null
  selectedCollection: Collection | null
  selectCollection: (id: number) => void
  createCollection: (name: string) => Promise<void>
  deleteCollection: (id: number) => Promise<void>
  isLoadingCollections: boolean
  isCreatingCollection: boolean
  isDeletingCollectionId: number | null
  error: string | null
  clearError: () => void
}

const CollectionContext = createContext<CollectionContextValue | undefined>(undefined)

export function CollectionProvider({ children }: { children: ReactNode }) {
  const [collections, setCollections] = useState<Collection[]>([])
  const [selectedCollectionId, setSelectedCollectionId] = useState<number | null>(null)
  const [isLoadingCollections, setIsLoadingCollections] = useState(false)
  const [isCreatingCollection, setIsCreatingCollection] = useState(false)
  const [isDeletingCollectionId, setIsDeletingCollectionId] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setIsLoadingCollections(true)
    api
      .listCollections()
      .then((result) => {
        setCollections(result)
        if (result.length > 0) {
          setSelectedCollectionId((current) => current ?? result[0].id)
        }
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setIsLoadingCollections(false))
  }, [])

  const createCollection = async (name: string) => {
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

  const deleteCollection = async (id: number) => {
    setIsDeletingCollectionId(id)
    setError(null)
    try {
      await api.deleteCollection(id)
      setCollections((previous) => previous.filter((collection) => collection.id !== id))
      setSelectedCollectionId((current) => {
        if (current !== id) return current
        const remaining = collections.filter((collection) => collection.id !== id)
        return remaining.length > 0 ? remaining[0].id : null
      })
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setIsDeletingCollectionId(null)
    }
  }

  const selectedCollection = collections.find((collection) => collection.id === selectedCollectionId) ?? null

  return (
    <CollectionContext.Provider
      value={{
        collections,
        selectedCollectionId,
        selectedCollection,
        selectCollection: setSelectedCollectionId,
        createCollection,
        deleteCollection,
        isLoadingCollections,
        isCreatingCollection,
        isDeletingCollectionId,
        error,
        clearError: () => setError(null),
      }}
    >
      {children}
    </CollectionContext.Provider>
  )
}

export function useCollectionContext(): CollectionContextValue {
  const context = useContext(CollectionContext)
  if (!context) {
    throw new Error('useCollectionContext must be used within a CollectionProvider')
  }
  return context
}

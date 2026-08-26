import { BrowserRouter, Route, Routes } from 'react-router-dom'
import './App.css'
import { Layout } from './components/Layout'
import { CollectionProvider } from './context/CollectionContext'
import { DecisionsPage } from './pages/DecisionsPage'
import { DocumentsPage } from './pages/DocumentsPage'
import { OverviewPage } from './pages/OverviewPage'
import { ProjectQAPage } from './pages/ProjectQAPage'
import { RequirementsPage } from './pages/RequirementsPage'
import { RisksPage } from './pages/RisksPage'

function App() {
  return (
    <CollectionProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<OverviewPage />} />
            <Route path="documents" element={<DocumentsPage />} />
            <Route path="risks" element={<RisksPage />} />
            <Route path="decisions" element={<DecisionsPage />} />
            <Route path="requirements" element={<RequirementsPage />} />
            <Route path="chat" element={<ProjectQAPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </CollectionProvider>
  )
}

export default App

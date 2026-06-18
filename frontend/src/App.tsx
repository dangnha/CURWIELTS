import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import AppShell from './components/layout/AppShell'
import Dashboard from './pages/Dashboard'
import NewEssay from './pages/NewEssay'
import EssayDetail from './pages/EssayDetail'
import EssayHistory from './pages/EssayHistory'
import VocabularyPage from './pages/VocabularyPage'
import ProgressPage from './pages/ProgressPage'
import SettingsPage from './pages/SettingsPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1 },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppShell>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/new-essay" element={<NewEssay />} />
            <Route path="/essays" element={<EssayHistory />} />
            <Route path="/essay/:essayId/edit" element={<NewEssay />} />
            <Route path="/essay/:essayId" element={<EssayDetail />} />
            <Route path="/vocabulary" element={<VocabularyPage />} />
            <Route path="/progress" element={<ProgressPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </AppShell>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

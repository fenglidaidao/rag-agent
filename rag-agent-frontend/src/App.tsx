// src/App.tsx
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import Sidebar from './components/Sidebar'
import LoginPage from './pages/LoginPage'
import ChatPage from './pages/ChatPage'
import KnowledgePage from './pages/KnowledgePage'
import ToolsPage from './pages/ToolsPage'

function ProtectedLayout() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-hidden bg-bg-base">
        <Routes>
          <Route path="/"          element={<ChatPage />} />
          <Route path="/knowledge" element={<KnowledgePage />} />
          <Route path="/tools"     element={<ToolsPage />} />
          <Route path="*"          element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}

export default function App() {
  const { isLoggedIn } = useAuthStore()

  return (
    <Routes>
      <Route path="/login" element={
        isLoggedIn() ? <Navigate to="/" replace /> : <LoginPage />
      } />
      <Route path="/*" element={
        isLoggedIn() ? <ProtectedLayout /> : <Navigate to="/login" replace />
      } />
    </Routes>
  )
}

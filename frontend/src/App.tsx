import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useAuthStore } from './store/authStore'
import Login from './pages/Login'
import ChatList from './pages/ChatList'
import ChatRoom from './pages/ChatRoom'
import * as analytics from './services/analytics'
import './App.css'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />
}

function App() {
  useEffect(() => {
    // Inicializar Amplitude cuando la app carga
    const AMPLITUDE_API_KEY = import.meta.env.VITE_AMPLITUDE_API_KEY
    if (AMPLITUDE_API_KEY) {
      console.log('✅ Amplitude inicializado correctamente')
    } else {
      console.warn('⚠️ VITE_AMPLITUDE_API_KEY no configurada. Analytics no funcionará.')
    }
  }, [])

  return (
    <Router
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/chats"
          element={
            <PrivateRoute>
              <ChatList />
            </PrivateRoute>
          }
        />
        <Route
          path="/chats/:chatId"
          element={
            <PrivateRoute>
              <ChatRoom />
            </PrivateRoute>
          }
        />
        <Route path="/" element={<Navigate to="/chats" />} />
      </Routes>
    </Router>
  )
}

// Frontend deployment trigger

export default App


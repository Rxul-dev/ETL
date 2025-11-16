import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { usersApi } from '../api/client'
import './Login.css'

function Login() {
  const [handle, setHandle] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const login = useAuthStore((state) => state.login)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const user = await usersApi.create(handle, displayName)
      login({
        id: user.id,
        handle: user.handle,
        display_name: user.display_name,
      })
      navigate('/chats')
    } catch (err: any) {
      if (err.response?.status === 409) {
        setError('Este handle ya existe. Por favor, elige otro.')
      } else {
        setError('Error al crear usuario. Por favor, intenta de nuevo.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>Rxul Chat</h1>
        <p className="subtitle">Inicia sesión para comenzar a chatear</p>
        
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="handle">Handle (usuario)</label>
            <input
              id="handle"
              type="text"
              value={handle}
              onChange={(e) => setHandle(e.target.value)}
              required
              placeholder="johndoe"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="displayName">Nombre para mostrar</label>
            <input
              id="displayName"
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              required
              placeholder="John Doe"
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" disabled={loading} className="submit-button">
            {loading ? 'Creando...' : 'Iniciar sesión'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default Login


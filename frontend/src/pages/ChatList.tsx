import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { chatsApi, Chat } from '../api/client'
import './ChatList.css'

function ChatList() {
  const [chats, setChats] = useState<Chat[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const user = useAuthStore((state) => state.user)
  const logout = useAuthStore((state) => state.logout)

  useEffect(() => {
    loadChats()
  }, [])

  const loadChats = async () => {
    try {
      setLoading(true)
      const response = await chatsApi.list(1, 50)
      setChats(response.items)
    } catch (err) {
      setError('Error al cargar los chats')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleChatClick = (chatId: number) => {
    navigate(`/chats/${chatId}`)
  }

  return (
    <div className="chat-list-container">
      <header className="chat-list-header">
        <h1>Rxul Chat</h1>
        <div className="user-info">
          <span>{user?.display_name}</span>
          <button onClick={logout} className="logout-button">
            Cerrar sesión
          </button>
        </div>
      </header>

      <main className="chat-list-main">
        <div className="chat-list-content">
          <h2>Chats</h2>
          
          {loading && <div className="loading">Cargando chats...</div>}
          {error && <div className="error">{error}</div>}
          
          {!loading && !error && chats.length === 0 && (
            <div className="empty-state">
              <p>No hay chats disponibles</p>
            </div>
          )}
          
          {!loading && !error && chats.length > 0 && (
            <div className="chat-list">
              {chats.map((chat) => (
                <div
                  key={chat.id}
                  className="chat-item"
                  onClick={() => handleChatClick(chat.id)}
                >
                  <div className="chat-item-content">
                    <h3>{chat.title || `Chat ${chat.type === 'dm' ? 'Directo' : 'Grupo'}`}</h3>
                    <p className="chat-meta">
                      {chat.type === 'dm' ? 'Mensaje directo' : 'Grupo'} • ID: {chat.id}
                    </p>
                  </div>
                  <div className="chat-arrow">→</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

export default ChatList


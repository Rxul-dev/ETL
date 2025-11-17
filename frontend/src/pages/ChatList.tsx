import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { chatsApi, usersApi, Chat, User } from '../api/client'
import './ChatList.css'

function ChatList() {
  const [chats, setChats] = useState<Chat[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showUserSearch, setShowUserSearch] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<User[]>([])
  const [searching, setSearching] = useState(false)
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

  const handleSearchUsers = async (query: string) => {
    setSearchQuery(query)
    if (query.trim().length < 2) {
      setSearchResults([])
      return
    }

    try {
      setSearching(true)
      const response = await usersApi.list(1, 20)
      // Filtrar en el frontend (el backend no tiene búsqueda aún)
      const filtered = response.items.filter(
        (u) =>
          u.id !== user?.id && // Excluir el usuario actual
          (u.handle.toLowerCase().includes(query.toLowerCase()) ||
            u.display_name.toLowerCase().includes(query.toLowerCase()))
      )
      setSearchResults(filtered)
    } catch (err) {
      console.error('Error searching users:', err)
      setSearchResults([])
    } finally {
      setSearching(false)
    }
  }

  const handleCreateDM = async (otherUserId: number) => {
    try {
      if (!user) return
      
      // Crear un chat DM con el usuario seleccionado
      const newChat = await chatsApi.create('dm', null, [user.id, otherUserId])
      setShowUserSearch(false)
      setSearchQuery('')
      setSearchResults([])
      navigate(`/chats/${newChat.id}`)
      // Recargar la lista de chats
      loadChats()
    } catch (err: any) {
      console.error('Error creating DM:', err)
      if (err.response?.status === 409) {
        alert('Ya existe un chat con este usuario')
      } else {
        alert('Error al crear el chat')
      }
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
          <div className="chat-list-header-actions">
            <h2>Chats</h2>
            <button
              onClick={() => setShowUserSearch(!showUserSearch)}
              className="new-chat-button"
            >
              {showUserSearch ? '✕ Cancelar' : '+ Nuevo chat'}
            </button>
          </div>

          {showUserSearch && (
            <div className="user-search-container">
              <input
                type="text"
                placeholder="Buscar usuario por nombre o handle..."
                value={searchQuery}
                onChange={(e) => handleSearchUsers(e.target.value)}
                className="user-search-input"
                autoFocus
              />
              {searching && <div className="searching">Buscando...</div>}
              {!searching && searchResults.length > 0 && (
                <div className="search-results">
                  {searchResults.map((userResult) => (
                    <div
                      key={userResult.id}
                      className="search-result-item"
                      onClick={() => handleCreateDM(userResult.id)}
                    >
                      <div className="user-avatar">
                        {userResult.display_name.charAt(0).toUpperCase()}
                      </div>
                      <div className="user-info">
                        <div className="user-name">{userResult.display_name}</div>
                        <div className="user-handle">@{userResult.handle}</div>
                      </div>
                      <div className="user-action">→</div>
                    </div>
                  ))}
                </div>
              )}
              {!searching && searchQuery.length >= 2 && searchResults.length === 0 && (
                <div className="no-results">No se encontraron usuarios</div>
              )}
            </div>
          )}
          
          {loading && <div className="loading">Cargando chats...</div>}
          {error && <div className="error">{error}</div>}
          
          {!loading && !error && chats.length === 0 && (
            <div className="empty-state">
              <p>No hay chats disponibles</p>
              <p className="empty-state-hint">Busca un usuario para iniciar una conversación</p>
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


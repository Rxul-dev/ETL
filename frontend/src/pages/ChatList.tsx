import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { chatsApi, usersApi, Chat, User } from '../api/client'
import { analytics } from '../services/analytics'
import './ChatList.css'

function ChatList() {
  const [chats, setChats] = useState<Chat[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [dmOtherUsers, setDmOtherUsers] = useState<Map<number, User>>(new Map())
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
      
      // Cargar información de otros usuarios para DMs
      const otherUsersMap = new Map<number, User>()
      for (const chat of response.items) {
        if (chat.type === 'dm') {
          try {
            const membersResponse = await chatsApi.getMembers(chat.id, 1, 50)
            const otherMember = membersResponse.items.find(
              (m) => m.user_id !== user?.id
            )
            if (otherMember) {
              try {
                const otherUser = await usersApi.get(otherMember.user_id)
                otherUsersMap.set(chat.id, otherUser)
              } catch (err) {
                console.error(`Error loading user ${otherMember.user_id}:`, err)
              }
            }
          } catch (err) {
            console.error(`Error loading members for chat ${chat.id}:`, err)
          }
        }
      }
      setDmOtherUsers(otherUsersMap)
    } catch (err) {
      setError('Error al cargar los chats')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleSearchUsers = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([])
      return
    }

    setSearching(true)
    try {
      const response = await usersApi.list(1, 100) // Obtener más usuarios para buscar
      // Filtrar en el frontend por ahora (el backend no tiene búsqueda)
      const filtered = response.items.filter(
        (u) =>
          u.id !== user?.id &&
          (u.handle.toLowerCase().includes(searchQuery.toLowerCase()) ||
            u.display_name.toLowerCase().includes(searchQuery.toLowerCase()))
      )
      setSearchResults(filtered)
      analytics.trackUserSearch(searchQuery, filtered.length)
    } catch (err) {
      console.error('Error searching users:', err)
      setSearchResults([])
    } finally {
      setSearching(false)
    }
  }

  useEffect(() => {
    if (!showUserSearch) {
      setSearchResults([])
      setSearchQuery('')
      return
    }

    if (!searchQuery.trim()) {
      setSearchResults([])
      return
    }

    const timeoutId = setTimeout(async () => {
      setSearching(true)
      try {
        const response = await usersApi.list(1, 100)
        const filtered = response.items.filter(
          (u) =>
            u.id !== user?.id &&
            (u.handle.toLowerCase().includes(searchQuery.toLowerCase()) ||
              u.display_name.toLowerCase().includes(searchQuery.toLowerCase()))
        )
        setSearchResults(filtered)
      } catch (err) {
        console.error('Error searching users:', err)
        setSearchResults([])
      } finally {
        setSearching(false)
      }
    }, 300) // Debounce de 300ms

    return () => clearTimeout(timeoutId)
  }, [searchQuery, showUserSearch, user?.id])

  const handleCreateDM = async (otherUserId: number) => {
    if (!user) return

    try {
      const newChat = await chatsApi.create('dm', null, [user.id, otherUserId])
      analytics.trackChatCreated('dm', newChat.id)
      setShowUserSearch(false)
      setSearchQuery('')
      setSearchResults([])
      navigate(`/chats/${newChat.id}`)
    } catch (err) {
      console.error('Error creating DM:', err)
      alert('Error al crear el chat. Puede que ya exista un chat con este usuario.')
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
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h2>Chats</h2>
            <button
              onClick={() => setShowUserSearch(!showUserSearch)}
              className="new-chat-button"
            >
              {showUserSearch ? 'Cancelar' : '+ Nuevo Chat'}
            </button>
          </div>

          {showUserSearch && (
            <div className="user-search-container">
              <div className="search-input-container">
                <input
                  type="text"
                  placeholder="Buscar usuario por handle o nombre..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleSearchUsers()
                    }
                  }}
                  className="search-input"
                />
                <button onClick={handleSearchUsers} disabled={searching} className="search-button">
                  {searching ? 'Buscando...' : 'Buscar'}
                </button>
              </div>
              
              {searchResults.length > 0 && (
                <div className="search-results">
                  {searchResults.map((resultUser) => (
                    <div
                      key={resultUser.id}
                      className="search-result-item"
                      onClick={() => handleCreateDM(resultUser.id)}
                    >
                      <div className="user-avatar">
                        {resultUser.display_name.charAt(0).toUpperCase()}
                      </div>
                      <div className="user-info">
                        <div className="user-name">{resultUser.display_name}</div>
                        <div className="user-handle">@{resultUser.handle}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              {searchQuery && searchResults.length === 0 && !searching && (
                <div className="no-results">No se encontraron usuarios</div>
              )}
            </div>
          )}
          
          {loading && <div className="loading">Cargando chats...</div>}
          {error && <div className="error">{error}</div>}
          
          {!loading && !error && chats.length === 0 && (
            <div className="empty-state">
              <p>No hay chats disponibles</p>
            </div>
          )}
          
          {!loading && !error && chats.length > 0 && (
            <div className="chat-list">
              {chats.map((chat) => {
                // Para chats directos, mostrar el nombre del otro usuario
                // Para grupos, mostrar el título del grupo
                const displayName = chat.type === 'dm' 
                  ? (dmOtherUsers.get(chat.id)?.display_name || 'Usuario desconocido')
                  : (chat.title || 'Grupo sin título')
                
                return (
                  <div
                    key={chat.id}
                    className="chat-item"
                    onClick={() => handleChatClick(chat.id)}
                  >
                    <div className="chat-item-content">
                      <h3>{displayName}</h3>
                      <p className="chat-meta">
                        {chat.type === 'dm' ? 'Mensaje directo' : 'Grupo'} • ID: {chat.id}
                      </p>
                    </div>
                    <div className="chat-arrow">→</div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

export default ChatList


import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { messagesApi, chatsApi, usersApi, Message, Chat, User } from '../api/client'
import { WebSocketService } from '../services/websocket'
import './ChatRoom.css'

function ChatRoom() {
  const { chatId } = useParams<{ chatId: string }>()
  const navigate = useNavigate()
  const user = useAuthStore((state) => state.user)
  const [messages, setMessages] = useState<Message[]>([])
  const [chat, setChat] = useState<Chat | null>(null)
  const [chatMembers, setChatMembers] = useState<{ user_id: number }[]>([])
  const [otherUser, setOtherUser] = useState<User | null>(null)
  const [usersMap, setUsersMap] = useState<Map<number, User>>(new Map())
  const [newMessage, setNewMessage] = useState('')
  const [replyingTo, setReplyingTo] = useState<Message | null>(null)
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const wsServiceRef = useRef<WebSocketService | null>(null)

  useEffect(() => {
    if (!chatId || !user) return

    let isMounted = true

    const loadChat = async () => {
      try {
        const chatData = await chatsApi.get(Number(chatId))
        if (isMounted) {
          setChat(chatData)
          
          // Si es un DM, cargar los miembros para obtener información del otro usuario
          if (chatData.type === 'dm' && user) {
            try {
              const membersResponse = await chatsApi.getMembers(Number(chatId))
              const members = membersResponse.items
              setChatMembers(members)
              
              // Encontrar el otro usuario (no el usuario actual)
              const otherUserId = members.find((m) => m.user_id !== user.id)?.user_id
              if (otherUserId) {
                try {
                  const otherUserData = await usersApi.get(otherUserId)
                  setOtherUser(otherUserData)
                } catch (err) {
                  console.error('Error loading other user:', err)
                }
              }
            } catch (err) {
              console.error('Error loading chat members:', err)
            }
          }
        }
      } catch (err) {
        console.error('Error loading chat:', err)
      }
    }

    const loadMessages = async () => {
      try {
        const response = await messagesApi.list(Number(chatId), 1, 100)
        if (isMounted) {
          const messagesList = response.items.reverse() // Mostrar más antiguos primero
          setMessages(messagesList)
          
          // Cargar información de usuarios para los mensajes
          const userIds = new Set<number>()
          messagesList.forEach((msg) => {
            if (msg.sender_id) userIds.add(msg.sender_id)
          })
          
          // Cargar usuarios en paralelo
          const usersPromises = Array.from(userIds).map((uid) =>
            usersApi.get(uid).catch(() => null)
          )
          const users = await Promise.all(usersPromises)
          const newUsersMap = new Map<number, User>()
          users.forEach((u) => {
            if (u) newUsersMap.set(u.id, u)
          })
          setUsersMap(newUsersMap)
        }
      } catch (err) {
        console.error('Error loading messages:', err)
      } finally {
        if (isMounted) {
          setLoading(false)
        }
      }
    }

    loadChat()
    loadMessages()

    // Conectar WebSocket solo si no hay una conexión existente para este chat
    if (!wsServiceRef.current || wsServiceRef.current.chatId !== Number(chatId)) {
      // Desconectar conexión anterior si existe
      if (wsServiceRef.current) {
        wsServiceRef.current.disconnect()
      }

      const ws = new WebSocketService()
      wsServiceRef.current = ws

      ws.onMessage((message) => {
        if (isMounted) {
          // Verificar que el mensaje no esté duplicado
          setMessages((prev) => {
            const exists = prev.some((m) => m.id === message.id)
            if (exists) {
              return prev // No agregar si ya existe
            }
            return [...prev, message]
          })
        }
      })

      ws.onError((error) => {
        // Solo mostrar errores críticos, no errores transitorios durante la conexión
        if (error.type === 'max_reconnect_attempts') {
          console.error('WebSocket: Max reconnection attempts reached')
          if (isMounted) {
            alert('No se pudo conectar al chat. Por favor, recarga la página.')
          }
        } else {
          // Solo registrar como warning, no como error, ya que la conexión puede establecerse después
          console.warn('WebSocket warning:', error)
        }
      })

      ws.connect(Number(chatId), user.id).catch((error) => {
        // Solo mostrar errores si realmente no se pudo conectar
        if (error.message === 'Connection timeout') {
          console.error('WebSocket: Connection timeout')
          if (isMounted) {
            alert('No se pudo conectar al chat. Por favor, verifica tu conexión.')
          }
        } else {
          console.warn('WebSocket connection issue:', error)
        }
      })
    }

    return () => {
      isMounted = false
      if (wsServiceRef.current) {
        wsServiceRef.current.disconnect()
        wsServiceRef.current = null
      }
    }
  }, [chatId, user])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newMessage.trim() || !chatId || !user || sending) return

    setSending(true)
    try {
      await messagesApi.send(Number(chatId), newMessage, user.id)
      setNewMessage('')
    } catch (err) {
      console.error('Error sending message:', err)
      alert('Error al enviar el mensaje')
    } finally {
      setSending(false)
    }
  }

  if (loading) {
    return <div className="chat-room-loading">Cargando...</div>
  }

  return (
    <div className="chat-room-container">
      <header className="chat-room-header">
        <button onClick={() => navigate('/chats')} className="back-button">
          ← Volver
        </button>
        <h2>{chat?.title || `Chat ${chat?.type === 'dm' ? 'Directo' : 'Grupo'}`}</h2>
      </header>

      <main className="chat-room-main">
        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="empty-messages">No hay mensajes aún</div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`message ${message.sender_id === user?.id ? 'own-message' : ''}`}
              >
                <div className="message-content">
                  <div className="message-body">{message.body}</div>
                  <div className="message-time">
                    {new Date(message.created_at).toLocaleTimeString('es-ES', {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </div>
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSendMessage} className="message-input-form">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Escribe un mensaje..."
            className="message-input"
            disabled={sending}
          />
          <button type="submit" disabled={sending || !newMessage.trim()} className="send-button">
            Enviar
          </button>
        </form>
      </main>
    </div>
  )
}

export default ChatRoom


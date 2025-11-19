import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { messagesApi, chatsApi, reactionsApi, bookingsApi, Message, Chat, Reaction, Booking } from '../api/client'
import { WebSocketService } from '../services/websocket'
import './ChatRoom.css'

function ChatRoom() {
  const { chatId } = useParams<{ chatId: string }>()
  const navigate = useNavigate()
  const user = useAuthStore((state) => state.user)
  const [messages, setMessages] = useState<Message[]>([])
  const [chat, setChat] = useState<Chat | null>(null)
  const [newMessage, setNewMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [messageReactions, setMessageReactions] = useState<Map<number, Reaction[]>>(new Map())
  const [showReactionPicker, setShowReactionPicker] = useState<number | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const wsServiceRef = useRef<WebSocketService | null>(null)
  
  // Emojis comunes para reacciones
  const commonEmojis = ['👍', '❤️', '😂', '😮', '😢', '🔥', '🎉', '✅']

  useEffect(() => {
    if (!chatId || !user) return

    const loadChat = async () => {
      try {
        const chatData = await chatsApi.get(Number(chatId))
        setChat(chatData)
      } catch (err) {
        console.error('Error loading chat:', err)
      }
    }

    const loadMessages = async () => {
      try {
        const response = await messagesApi.list(Number(chatId), 1, 100)
        const messagesList = response.items.reverse() // Mostrar más antiguos primero
        setMessages(messagesList)
        
        // Cargar reacciones para cada mensaje
        const reactionsMap = new Map<number, Reaction[]>()
        for (const message of messagesList) {
          try {
            const reactionsResponse = await reactionsApi.list(message.id, 1, 50)
            reactionsMap.set(message.id, reactionsResponse.items)
          } catch (err) {
            console.error(`Error loading reactions for message ${message.id}:`, err)
            reactionsMap.set(message.id, [])
          }
        }
        setMessageReactions(reactionsMap)
      } catch (err) {
        console.error('Error loading messages:', err)
      } finally {
        setLoading(false)
      }
    }

    loadChat()
    loadMessages()

    // Desconectar WebSocket anterior si existe y es para un chat diferente
    if (wsServiceRef.current && wsServiceRef.current.chatId !== Number(chatId)) {
      wsServiceRef.current.disconnect()
      wsServiceRef.current = null
    }

    // Conectar WebSocket solo si no hay uno activo para este chat
    if (!wsServiceRef.current || wsServiceRef.current.chatId !== Number(chatId)) {
      const ws = new WebSocketService()
      wsServiceRef.current = ws

      ws.onMessage((message) => {
        // Solo agregar mensajes si no existen ya (evitar duplicados)
        setMessages((prev) => {
          const exists = prev.some((m) => m.id === message.id)
          return exists ? prev : [...prev, message]
        })
      })

      ws.onError((error) => {
        console.error('WebSocket error:', error)
      })

      ws.connect(Number(chatId), user.id).catch((err) => {
        console.error('Failed to connect WebSocket:', err)
      })
    }

    return () => {
      // Solo desconectar si el chatId coincide (evitar desconectar cuando cambia el chat)
      const currentChatId = Number(chatId)
      if (wsServiceRef.current && wsServiceRef.current.chatId === currentChatId) {
        try {
          wsServiceRef.current.disconnect()
        } catch (error) {
          // Ignorar errores al desconectar (puede estar ya cerrado)
          console.warn('Error disconnecting WebSocket (ignored):', error)
        }
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
      
      // Detectar si el mensaje contiene palabras clave de booking
      const bookingKeywords = [
        'reservar', 'reserva', 'reservación', 'reservacion',
        'booking', 'book',
        'agendar', 'agenda', 'agendamiento',
        'cita', 'citas',
        'reservar sala', 'reservar habitación', 'reservar cuarto',
        'sala disponible', 'habitación disponible',
        'necesito sala', 'necesito habitación',
        'disponible', 'disponibilidad'
      ]
      const lowerMessage = newMessage.toLowerCase().trim()
      const hasBookingKeyword = bookingKeywords.some(keyword => 
        lowerMessage.includes(keyword.toLowerCase())
      )
      
      if (hasBookingKeyword) {
        // Crear booking automáticamente
        try {
          // Esperar un momento para que el mensaje se guarde en la BD
          setTimeout(async () => {
            try {
              const messagesResponse = await messagesApi.list(Number(chatId), 1, 1)
              if (messagesResponse.items.length > 0) {
                const lastMessage = messagesResponse.items[0]
                await bookingsApi.create(lastMessage.id, user.id, Number(chatId))
                alert('✅ Booking creado automáticamente')
              }
            } catch (bookingErr) {
              console.error('Error creating booking:', bookingErr)
            }
          }, 500) // Esperar 500ms para que el mensaje se guarde
        } catch (bookingErr) {
          console.error('Error creating booking:', bookingErr)
        }
      }
    } catch (err) {
      console.error('Error sending message:', err)
      alert('Error al enviar el mensaje')
    } finally {
      setSending(false)
    }
  }

  const handleAddReaction = async (messageId: number, emoji: string) => {
    if (!user) return
    
    try {
      // Verificar si el usuario ya tiene esta reacción
      const reactions = messageReactions.get(messageId) || []
      const existingReaction = reactions.find(r => r.user_id === user.id && r.emoji === emoji)
      
      if (existingReaction) {
        // Remover reacción
        await reactionsApi.remove(messageId, emoji, user.id)
        setMessageReactions(prev => {
          const newMap = new Map(prev)
          const updatedReactions = (newMap.get(messageId) || []).filter(
            r => !(r.user_id === user.id && r.emoji === emoji)
          )
          newMap.set(messageId, updatedReactions)
          return newMap
        })
      } else {
        // Agregar reacción
        await reactionsApi.add(messageId, emoji, user.id)
        const reactionsResponse = await reactionsApi.list(messageId, 1, 50)
        setMessageReactions(prev => {
          const newMap = new Map(prev)
          newMap.set(messageId, reactionsResponse.items)
          return newMap
        })
      }
      setShowReactionPicker(null)
    } catch (err) {
      console.error('Error adding reaction:', err)
    }
  }
  


  const getReactionCounts = (messageId: number): Map<string, number> => {
    const reactions = messageReactions.get(messageId) || []
    const counts = new Map<string, number>()
    reactions.forEach(reaction => {
      const current = counts.get(reaction.emoji) || 0
      counts.set(reaction.emoji, current + 1)
    })
    return counts
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
            messages.map((message) => {
              const reactionCounts = getReactionCounts(message.id)
              const userReactions = (messageReactions.get(message.id) || []).filter(
                r => r.user_id === user?.id
              )
              const isOwnMessage = message.sender_id === user?.id
              
              return (
                <div
                  key={`message-${message.id}`}
                  className={`message ${isOwnMessage ? 'own-message' : ''}`}
                  data-message-id={message.id}
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
                  
                  {/* Reacciones */}
                  <div className="message-reactions">
                    {Array.from(reactionCounts.entries()).map(([emoji, count]) => {
                      const hasUserReaction = userReactions.some(r => r.emoji === emoji)
                      return (
                        <button
                          key={emoji}
                          className={`reaction-button ${hasUserReaction ? 'active' : ''}`}
                          onClick={() => handleAddReaction(message.id, emoji)}
                          title={`${count} reacción${count > 1 ? 'es' : ''}`}
                        >
                          {emoji} {count}
                        </button>
                      )
                    })}
                    <button
                      className="add-reaction-button"
                      onClick={() => setShowReactionPicker(
                        showReactionPicker === message.id ? null : message.id
                      )}
                      title="Agregar reacción"
                    >
                      +
                    </button>
                    
                    {/* Picker de reacciones */}
                    {showReactionPicker === message.id && (
                      <div className="reaction-picker">
                        {commonEmojis.map(emoji => (
                          <button
                            key={emoji}
                            className="emoji-button"
                            onClick={() => handleAddReaction(message.id, emoji)}
                          >
                            {emoji}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  
                </div>
              )
            })
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


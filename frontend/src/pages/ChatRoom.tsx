import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { messagesApi, chatsApi, Message, Chat } from '../api/client'
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
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const wsServiceRef = useRef<WebSocketService | null>(null)

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
        setMessages(response.items.reverse()) // Mostrar más antiguos primero
      } catch (err) {
        console.error('Error loading messages:', err)
      } finally {
        setLoading(false)
      }
    }

    loadChat()
    loadMessages()

    // Conectar WebSocket
    const ws = new WebSocketService()
    wsServiceRef.current = ws

    ws.onMessage((message) => {
      setMessages((prev) => [...prev, message])
    })

    ws.onError((error) => {
      console.error('WebSocket error:', error)
    })

    ws.connect(Number(chatId), user.id).catch(console.error)

    return () => {
      ws.disconnect()
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


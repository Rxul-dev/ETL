import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface User {
  id: number
  handle: string
  display_name: string
  created_at: string
}

export interface Chat {
  id: number
  type: 'dm' | 'group'
  title: string | null
  created_at: string
}

export interface Message {
  id: number
  chat_id: number
  sender_id: number | null
  body: string
  created_at: string
  edited_at: string | null
  reply_to_id: number | null
}

export interface PageResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// Users API
export const usersApi = {
  create: async (handle: string, display_name: string): Promise<User> => {
    const response = await apiClient.post<User>('/users', { handle, display_name })
    return response.data
  },
  get: async (id: number): Promise<User> => {
    const response = await apiClient.get<User>(`/users/${id}`)
    return response.data
  },
  getByHandle: async (handle: string): Promise<User | null> => {
    try {
      const response = await apiClient.get<User>(`/users/by-handle/${handle}`)
      return response.data
    } catch (err: any) {
      if (err.response?.status === 404) {
        return null
      }
      throw err
    }
  },
  list: async (page: number = 1, page_size: number = 50, search?: string): Promise<PageResponse<User>> => {
    const params: any = { page, page_size }
    // Nota: El backend no tiene búsqueda aún, pero podemos filtrar en el frontend
    const response = await apiClient.get<PageResponse<User>>('/users', { params })
    return response.data
  },
}

// Chats API
export const chatsApi = {
  create: async (type: 'dm' | 'group', title: string | null, members: number[]): Promise<Chat> => {
    const response = await apiClient.post<Chat>('/chats', { type, title, members })
    return response.data
  },
  get: async (id: number): Promise<Chat> => {
    const response = await apiClient.get<Chat>(`/chats/${id}`)
    return response.data
  },
  list: async (page: number = 1, page_size: number = 50): Promise<PageResponse<Chat>> => {
    const response = await apiClient.get<PageResponse<Chat>>('/chats', {
      params: { page, page_size },
    })
    return response.data
  },
  getMembers: async (chatId: number, page: number = 1, page_size: number = 50): Promise<PageResponse<{ chat_id: number; user_id: number; role: string; joined_at: string }>> => {
    const response = await apiClient.get(`/chats/${chatId}/members`, {
      params: { page, page_size },
    })
    return response.data
  },
}

// Messages API
export const messagesApi = {
  send: async (chatId: number, body: string, senderId: number, replyToId?: number): Promise<Message> => {
    const response = await apiClient.post<Message>(`/chats/${chatId}/messages`, {
      body,
      sender_id: senderId,
      reply_to_id: replyToId,
    })
    return response.data
  },
  list: async (chatId: number, page: number = 1, page_size: number = 50): Promise<PageResponse<Message>> => {
    const response = await apiClient.get<PageResponse<Message>>(`/chats/${chatId}/messages`, {
      params: { page, page_size },
    })
    return response.data
  },
}


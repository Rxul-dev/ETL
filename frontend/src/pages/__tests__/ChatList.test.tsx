import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'

const mockChatsApiList = vi.fn()

vi.mock('../../api/client', () => ({
  chatsApi: {
    list: mockChatsApiList,
  },
}))

vi.mock('../../store/authStore')

// Importar el componente después de configurar los mocks básicos
import ChatList from '../ChatList'

describe('ChatList', () => {
  const mockUser = { id: 1, handle: 'testuser', display_name: 'Test User' }
  const mockChats = [
    { id: 1, type: 'group' as const, title: 'Chat 1', created_at: new Date().toISOString() },
    { id: 2, type: 'dm' as const, title: null, created_at: new Date().toISOString() },
  ]
  const mockLogout = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    mockLogout.mockClear()
    mockChatsApiList.mockClear()
    
    vi.mocked(useAuthStore).mockReturnValue({
      user: mockUser,
      isAuthenticated: true,
      login: vi.fn(),
      logout: mockLogout,
    } as any)
  })

  it('renders chat list', async () => {
    mockChatsApiList.mockResolvedValue({
      items: mockChats,
      total: 2,
      page: 1,
      page_size: 50,
      total_pages: 1,
    })

    render(
      <BrowserRouter>
        <ChatList />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Chat 1')).toBeInTheDocument()
    })
  })

  it('shows loading state', () => {
    mockChatsApiList.mockImplementation(() => new Promise(() => {}))

    render(
      <BrowserRouter>
        <ChatList />
      </BrowserRouter>
    )

    expect(screen.getByText(/cargando chats/i)).toBeInTheDocument()
  })

  it('shows empty state when no chats', async () => {
    mockChatsApiList.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      total_pages: 0,
    })

    render(
      <BrowserRouter>
        <ChatList />
      </BrowserRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/no hay chats disponibles/i)).toBeInTheDocument()
    })
  })
})

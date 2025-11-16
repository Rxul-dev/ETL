import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'

const mockNavigate = vi.fn()
const mockUsersApiCreate = vi.fn()
const mockLogin = vi.fn()

// Mock del módulo completo ANTES de cualquier importación
vi.mock('../../api/client', () => ({
  apiClient: {},
  usersApi: {
    create: (...args: any[]) => mockUsersApiCreate(...args),
    get: vi.fn(),
    list: vi.fn(),
  },
  chatsApi: {
    create: vi.fn(),
    get: vi.fn(),
    list: vi.fn(),
  },
  messagesApi: {
    send: vi.fn(),
    list: vi.fn(),
  },
}))

vi.mock('../../store/authStore', () => ({
  useAuthStore: vi.fn(),
}))

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// Importar después de los mocks
import Login from '../Login'
import { useAuthStore } from '../../store/authStore'

describe('Login', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockNavigate.mockClear()
    mockUsersApiCreate.mockClear()
    mockLogin.mockClear()
    
    vi.mocked(useAuthStore).mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: mockLogin,
      logout: vi.fn(),
    } as any)
  })

  it('renders login form', () => {
    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    )
    
    expect(screen.getByLabelText(/handle/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/nombre para mostrar/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /iniciar sesión/i })).toBeInTheDocument()
  })

  it('submits form with valid data', async () => {
    const user = userEvent.setup()
    const mockUser = { id: 1, handle: 'testuser', display_name: 'Test User', created_at: new Date().toISOString() }
    
    mockUsersApiCreate.mockResolvedValue(mockUser)

    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    )

    await user.type(screen.getByLabelText(/handle/i), 'testuser')
    await user.type(screen.getByLabelText(/nombre para mostrar/i), 'Test User')
    await user.click(screen.getByRole('button', { name: /iniciar sesión/i }))

    await waitFor(() => {
      expect(mockUsersApiCreate).toHaveBeenCalledWith('testuser', 'Test User')
    }, { timeout: 3000 })
    
    // Esperar a que se complete el login
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        id: mockUser.id,
        handle: mockUser.handle,
        display_name: mockUser.display_name,
      })
    }, { timeout: 3000 })
  })

  it('shows error on duplicate handle', async () => {
    const user = userEvent.setup()
    const error: any = { response: { status: 409 } }
    
    mockUsersApiCreate.mockRejectedValue(error)

    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    )

    await user.type(screen.getByLabelText(/handle/i), 'testuser')
    await user.type(screen.getByLabelText(/nombre para mostrar/i), 'Test User')
    await user.click(screen.getByRole('button', { name: /iniciar sesión/i }))

    await waitFor(() => {
      expect(screen.getByText(/este handle ya existe/i)).toBeInTheDocument()
    }, { timeout: 3000 })
  })
})

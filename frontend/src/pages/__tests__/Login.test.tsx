import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'

// Usar vi.hoisted() para asegurar que los mocks funcionen correctamente
const { mockNavigate, mockLogin, mockUsersApiCreate, mockUsersApiGetByHandle, mockStoreRef } = vi.hoisted(() => {
  const storeRef: { current: any } = {
    current: {
      user: null,
      isAuthenticated: false,
      login: vi.fn(),
      logout: vi.fn(),
    },
  }
  return {
    mockNavigate: vi.fn(),
    mockLogin: vi.fn(),
    mockUsersApiCreate: vi.fn(),
    mockUsersApiGetByHandle: vi.fn(),
    mockStoreRef: storeRef,
  }
})

// Mock del módulo completo ANTES de cualquier importación
vi.mock('../../api/client', () => ({
  apiClient: {},
  usersApi: {
    create: mockUsersApiCreate,
    get: vi.fn(),
    getByHandle: mockUsersApiGetByHandle,
    list: vi.fn(),
  },
  chatsApi: {
    create: vi.fn(),
    get: vi.fn(),
    list: vi.fn(),
    getMembers: vi.fn(),
  },
  messagesApi: {
    send: vi.fn(),
    list: vi.fn(),
  },
}))

vi.mock('../../store/authStore', () => {
  return {
    useAuthStore: vi.fn((selector?: (state: any) => any) => {
      const store = mockStoreRef.current
      if (selector) {
        return selector(store)
      }
      return store
    }),
  }
})

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// Importar después de los mocks
import Login from '../Login'

describe('Login', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockNavigate.mockClear()
    mockUsersApiCreate.mockClear()
    mockUsersApiGetByHandle.mockClear()
    mockLogin.mockClear()
    
    // Actualizar el mockStore con nuevos mocks para cada test
    mockStoreRef.current = {
      user: null,
      isAuthenticated: false,
      login: mockLogin,
      logout: vi.fn(),
    }
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

  it('submits form with valid data - new user', async () => {
    const user = userEvent.setup()
    const mockUser = { id: 1, handle: 'testuser', display_name: 'Test User', created_at: new Date().toISOString() }
    
    // Usuario no existe, se crea uno nuevo
    mockUsersApiGetByHandle.mockResolvedValue(null)
    mockUsersApiCreate.mockResolvedValue(mockUser)

    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    )

    const handleInput = screen.getByLabelText(/handle/i)
    const displayNameInput = screen.getByLabelText(/nombre para mostrar/i)
    const submitButton = screen.getByRole('button', { name: /iniciar sesión/i })

    await user.clear(handleInput)
    await user.type(handleInput, 'testuser')
    await user.clear(displayNameInput)
    await user.type(displayNameInput, 'Test User')
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockUsersApiGetByHandle).toHaveBeenCalledWith('testuser')
    }, { timeout: 3000 })
    
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

  it('submits form with existing handle - logs in automatically', async () => {
    const user = userEvent.setup()
    const existingUser = { id: 2, handle: 'testuser', display_name: 'Existing User', created_at: new Date().toISOString() }
    
    // Usuario existe, se hace login automático
    mockUsersApiGetByHandle.mockResolvedValue(existingUser)

    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    )

    const handleInput = screen.getByLabelText(/handle/i)
    const displayNameInput = screen.getByLabelText(/nombre para mostrar/i)
    const submitButton = screen.getByRole('button', { name: /iniciar sesión/i })

    await user.clear(handleInput)
    await user.type(handleInput, 'testuser')
    await user.clear(displayNameInput)
    await user.type(displayNameInput, 'Test User')
    await user.click(submitButton)

    await waitFor(() => {
      expect(mockUsersApiGetByHandle).toHaveBeenCalledWith('testuser')
    }, { timeout: 3000 })
    
    // No debe crear un nuevo usuario
    expect(mockUsersApiCreate).not.toHaveBeenCalled()
    
    // Debe hacer login con el usuario existente
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        id: existingUser.id,
        handle: existingUser.handle,
        display_name: existingUser.display_name,
      })
    }, { timeout: 3000 })
  })

  it('handles error when getByHandle fails', async () => {
    const user = userEvent.setup()
    const mockUser = { id: 1, handle: 'testuser', display_name: 'Test User', created_at: new Date().toISOString() }
    
    // Error al obtener usuario, pero luego se crea exitosamente
    mockUsersApiGetByHandle.mockRejectedValue(new Error('Network error'))
    mockUsersApiCreate.mockResolvedValue(mockUser)

    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    )

    const handleInput = screen.getByLabelText(/handle/i)
    const displayNameInput = screen.getByLabelText(/nombre para mostrar/i)
    const submitButton = screen.getByRole('button', { name: /iniciar sesión/i })

    await user.clear(handleInput)
    await user.type(handleInput, 'testuser')
    await user.clear(displayNameInput)
    await user.type(displayNameInput, 'Test User')
    await user.click(submitButton)

    // Debe mostrar un error
    await waitFor(() => {
      expect(screen.getByText(/error al crear usuario/i)).toBeInTheDocument()
    }, { timeout: 3000 })
  })
})

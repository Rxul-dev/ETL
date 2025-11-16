import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import * as apiClient from '../../api/client'
import { useAuthStore } from '../../store/authStore'

const mockNavigate = vi.fn()

vi.mock('../../store/authStore')
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// Importar el componente después de configurar los mocks básicos
import Login from '../Login'

describe('Login', () => {
  const mockLogin = vi.fn()
  let createSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    vi.clearAllMocks()
    mockNavigate.mockClear()
    
    // Usar spyOn para mockear después de importar
    createSpy = vi.spyOn(apiClient.usersApi, 'create')
    
    vi.mocked(useAuthStore).mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: mockLogin,
      logout: vi.fn(),
    } as any)
  })

  afterEach(() => {
    createSpy.mockRestore()
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
    
    createSpy.mockResolvedValue(mockUser)

    render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    )

    await user.type(screen.getByLabelText(/handle/i), 'testuser')
    await user.type(screen.getByLabelText(/nombre para mostrar/i), 'Test User')
    await user.click(screen.getByRole('button', { name: /iniciar sesión/i }))

    await waitFor(() => {
      expect(createSpy).toHaveBeenCalledWith('testuser', 'Test User')
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
    
    createSpy.mockRejectedValue(error)

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

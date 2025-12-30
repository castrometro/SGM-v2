import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileText, Loader2 } from 'lucide-react'
import { useAuth } from '../../../contexts/AuthContext'
import toast from 'react-hot-toast'

const LoginPage = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      await login(email, password)
      toast.success('¡Bienvenido!')
      navigate('/dashboard')
    } catch (error) {
      const message = error.response?.data?.detail || 'Error al iniciar sesión'
      toast.error(message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-secondary-950 px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="mb-8 flex flex-col items-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary-600 shadow-lg shadow-primary-600/30">
            <FileText className="h-10 w-10 text-white" />
          </div>
          <h1 className="mt-4 text-2xl font-bold text-white">SGM v2</h1>
          <p className="text-secondary-400">Sistema de Gestión de Nómina</p>
        </div>

        {/* Login form */}
        <div className="card">
          <h2 className="mb-6 text-center text-xl font-semibold text-white">
            Iniciar Sesión
          </h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="label mb-1.5 block">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input"
                placeholder="tu@email.com"
                required
                disabled={isLoading}
              />
            </div>

            <div>
              <label htmlFor="password" className="label mb-1.5 block">
                Contraseña
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input"
                placeholder="••••••••"
                required
                disabled={isLoading}
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary btn-md w-full"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Iniciando sesión...
                </>
              ) : (
                'Iniciar Sesión'
              )}
            </button>
          </form>
        </div>

        <p className="mt-6 text-center text-sm text-secondary-500">
          © {new Date().getFullYear()} BDO Chile. Todos los derechos reservados.
        </p>
      </div>
    </div>
  )
}

export default LoginPage

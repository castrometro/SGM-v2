/**
 * Error Boundary Component
 * Captura errores de JavaScript en cualquier parte del árbol de componentes,
 * registra esos errores y muestra una UI de respaldo en lugar de que la app se rompa.
 */
import { Component } from 'react'
import { AlertTriangle, RefreshCw, Home } from 'lucide-react'

class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    }
  }

  static getDerivedStateFromError(error) {
    // Actualizar estado para que el siguiente render muestre la UI de respaldo
    return { hasError: true }
  }

  componentDidCatch(error, errorInfo) {
    // Log del error a un servicio de logging
    console.error('Error capturado por ErrorBoundary:', error, errorInfo)
    
    this.setState({
      error,
      errorInfo,
    })

    // TODO: Enviar error a servicio de logging (Sentry, LogRocket, etc.)
    // if (window.errorLogger) {
    //   window.errorLogger.logError(error, errorInfo)
    // }
  }

  handleReload = () => {
    window.location.reload()
  }

  handleGoHome = () => {
    window.location.href = '/'
  }

  render() {
    if (this.state.hasError) {
      const { error, errorInfo } = this.state
      const isDevelopment = import.meta.env.DEV

      return (
        <div className="min-h-screen bg-secondary-950 flex items-center justify-center p-4">
          <div className="max-w-2xl w-full bg-secondary-900 rounded-lg shadow-xl border border-secondary-800 p-8">
            {/* Header */}
            <div className="flex items-center gap-4 mb-6">
              <div className="p-3 bg-red-500/10 rounded-lg">
                <AlertTriangle className="w-8 h-8 text-red-500" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">
                  ¡Algo salió mal!
                </h1>
                <p className="text-secondary-400 mt-1">
                  Ha ocurrido un error inesperado
                </p>
              </div>
            </div>

            {/* Error Message */}
            <div className="mb-6 p-4 bg-secondary-800 rounded-lg border border-secondary-700">
              <p className="text-red-400 font-mono text-sm">
                {error?.message || 'Error desconocido'}
              </p>
            </div>

            {/* Error Details (Solo en desarrollo) */}
            {isDevelopment && errorInfo && (
              <details className="mb-6">
                <summary className="cursor-pointer text-secondary-300 hover:text-white mb-2 font-medium">
                  Ver detalles técnicos
                </summary>
                <div className="mt-2 p-4 bg-secondary-800 rounded-lg border border-secondary-700 overflow-auto max-h-64">
                  <pre className="text-xs text-secondary-300 font-mono whitespace-pre-wrap">
                    {errorInfo.componentStack}
                  </pre>
                </div>
              </details>
            )}

            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={this.handleReload}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors"
              >
                <RefreshCw className="w-5 h-5" />
                Recargar página
              </button>
              <button
                onClick={this.handleGoHome}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-secondary-700 hover:bg-secondary-600 text-white font-medium rounded-lg transition-colors"
              >
                <Home className="w-5 h-5" />
                Ir al inicio
              </button>
            </div>

            {/* Help Text */}
            <div className="mt-6 pt-6 border-t border-secondary-800">
              <p className="text-secondary-400 text-sm text-center">
                Si el problema persiste, contacta al equipo de soporte técnico
              </p>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary

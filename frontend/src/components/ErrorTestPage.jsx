/**
 * Componente de prueba para verificar el Error Boundary
 * Solo para desarrollo - eliminar en producción
 */
import { useState } from 'react'

const ErrorTestPage = () => {
  const [shouldThrow, setShouldThrow] = useState(false)

  if (shouldThrow) {
    throw new Error('¡Error de prueba! El Error Boundary debería capturar esto.')
  }

  return (
    <div className="p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold text-white mb-4">
          Prueba de Error Boundary
        </h1>
        
        <div className="bg-secondary-800 rounded-lg p-6 mb-6">
          <p className="text-secondary-300 mb-4">
            Este componente es solo para desarrollo. Permite probar que el Error Boundary
            funciona correctamente capturando errores.
          </p>
          
          <button
            onClick={() => setShouldThrow(true)}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors"
          >
            Lanzar Error de Prueba
          </button>
        </div>

        <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4">
          <p className="text-yellow-400 text-sm">
            ⚠️ <strong>Nota:</strong> Eliminar esta ruta antes de ir a producción
          </p>
        </div>
      </div>
    </div>
  )
}

export default ErrorTestPage

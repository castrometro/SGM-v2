/**
 * Suspense Fallback Component
 * Muestra un spinner de carga mientras los componentes lazy se cargan
 */
const SuspenseFallback = () => (
  <div className="flex items-center justify-center min-h-[400px]">
    <div className="flex flex-col items-center gap-4">
      <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-500"></div>
      <p className="text-secondary-400 text-sm">Cargando...</p>
    </div>
  </div>
)

export default SuspenseFallback

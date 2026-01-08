---
description: 'ReactJS development standards and best practices for SGM-v2'
applyTo: 'frontend/**/*.jsx, frontend/**/*.js, frontend/**/*.css'
---

# ReactJS Development Instructions - SGM v2

Instructions for building high-quality ReactJS applications with modern patterns, hooks, and best practices following the official React documentation at https://react.dev.

## Project Context
- React 18 with Vite as build tool
- Functional components with hooks as default
- Zustand for global state management
- TanStack Query (React Query) for server state
- Tailwind CSS for styling
- React Router v6 for routing
- React Hook Form for form handling
- Follow React's official style guide and best practices

## Current Stack Summary

### Core Libraries
- **React**: 18.2+ (functional components, hooks)
- **Build Tool**: Vite 5
- **State Management**: Zustand with persist middleware
- **Data Fetching**: TanStack Query (React Query) v5
- **Routing**: React Router v6
- **Styling**: Tailwind CSS 3.4+
- **Forms**: React Hook Form
- **Icons**: Lucide React
- **HTTP Client**: Axios

### Project Structure
```
frontend/
├── src/
│   ├── components/       # Reusable components
│   │   ├── layout/       # Layout components (MainLayout, Sidebar, etc.)
│   │   └── ui/           # UI primitives (Button, Modal, Card, etc.)
│   ├── features/         # Feature-based modules
│   │   ├── admin/        # Admin pages & components
│   │   ├── auth/         # Authentication
│   │   ├── clientes/     # Clients management
│   │   ├── dashboard/    # Dashboard
│   │   ├── incidencias/  # Incidents
│   │   ├── supervisor/   # Supervisor tools
│   │   └── validador/    # Validator (core business logic)
│   ├── contexts/         # React Context (minimal usage)
│   ├── hooks/            # Custom hooks
│   ├── stores/           # Zustand stores
│   ├── api/              # API client configuration
│   └── utils/            # Utilities (cn, formatters, etc.)
```

## Development Standards

### Architecture Patterns

#### Feature-Based Organization
Cada feature debe tener su propia estructura:
```
features/validador/
├── components/     # Componentes específicos del feature
├── hooks/          # Custom hooks del feature
├── pages/          # Páginas/vistas
└── index.js        # Public exports
```

**Rules:**
- Mantener componentes pequeños y enfocados (Single Responsibility)
- Exportar solo lo necesario desde `index.js`
- Evitar imports circulares entre features

#### Component Composition
- Preferir composición sobre herencia
- Usar `children` prop para flexibilidad
- Implementar compound components para componentes relacionados
- Usar render props cuando sea necesario compartir lógica con UI dinámica

### Component Design

#### Functional Components Pattern
```jsx
/**
 * Descripción del componente
 * @param {Object} props - Props del componente
 */
const MiComponente = ({ prop1, prop2, onAction }) => {
  // Hooks primero
  const [state, setState] = useState(initialValue)
  const queryResult = useQuery({ ... })
  
  // Event handlers
  const handleClick = () => {
    // lógica
  }
  
  // Early returns para loading/error
  if (queryResult.isLoading) return <LoadingSpinner />
  if (queryResult.error) return <ErrorMessage />
  
  // Render principal
  return (
    <div>
      {/* JSX */}
    </div>
  )
}

export default MiComponente
```

**Best Practices:**
- Destructuring de props en parámetros
- Hooks al inicio del componente
- Event handlers con prefijo `handle`
- Early returns para estados especiales
- Documentar con JSDoc para componentes complejos

#### Naming Conventions
- **Componentes**: PascalCase (`UserCard.jsx`, `CierreDetail.jsx`)
- **Hooks**: camelCase con prefijo `use` (`useAuth.js`, `useCierres.js`)
- **Utils**: camelCase (`formatDate.js`, `cn.js`)
- **Constantes**: UPPER_SNAKE_CASE (`API_BASE_URL`)
- **Event Handlers**: `handle` + acción (`handleSubmit`, `handleClick`)

### State Management

#### Local State (useState)
Usar para estado específico del componente:
```jsx
const [isOpen, setIsOpen] = useState(false)
const [formData, setFormData] = useState({ name: '', email: '' })
```

**Cuándo usar:**
- Estado UI local (modals, dropdowns, tabs)
- Formularios simples
- Toggle states

#### Complex State (useReducer)
Para estado complejo con múltiples transiciones:
```jsx
const [state, dispatch] = useReducer(reducer, initialState)

// Actions
dispatch({ type: 'SET_LOADING' })
dispatch({ type: 'SET_DATA', payload: data })
```

**Cuándo usar:**
- Múltiples sub-valores relacionados
- Lógica de estado compleja
- Siguiente estado depende del anterior

#### Global State (Zustand)
Para estado compartido entre componentes:
```javascript
// stores/authStore.js
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useAuthStore = create(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      setAuth: (user, tokens) => set({ user, isAuthenticated: true }),
      logout: () => set({ user: null, isAuthenticated: false }),
    }),
    { name: 'auth-storage' }
  )
)
```

**Cuándo usar:**
- Autenticación (user, tokens)
- Preferencias de usuario
- Estado que persiste entre sesiones
- Compartir estado entre features distantes

**Avoid:**
- No usar para server state (usa React Query)
- No abusar de stores (preferir props cuando sea posible)

#### Server State (TanStack Query)
Para datos del servidor:
```javascript
// hooks/useCierres.js
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { cierreService } from '../api/services'

export const useCierres = (filters) => {
  return useQuery({
    queryKey: ['cierres', filters],
    queryFn: () => cierreService.getAll(filters),
    staleTime: 5 * 60 * 1000, // 5 minutos
  })
}

export const useCreateCierre = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data) => cierreService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cierres'] })
    },
  })
}
```

**Best Practices:**
- Usar `queryKey` descriptivos con arrays
- Invalidar queries relacionadas después de mutations
- Configurar `staleTime` apropiado
- Manejar estados de loading y error

### Hooks and Effects

#### useEffect Guidelines
```jsx
// ✅ GOOD: Dependency array completa
useEffect(() => {
  fetchData(userId)
}, [userId])

// ✅ GOOD: Cleanup function
useEffect(() => {
  const subscription = api.subscribe(data)
  return () => subscription.unsubscribe()
}, [])

// ❌ BAD: Missing dependencies
useEffect(() => {
  fetchData(userId) // userId no está en dependencies
}, [])

// ❌ BAD: Infinite loop
useEffect(() => {
  setCount(count + 1) // Se actualiza en cada render
}, [count])
```

**Rules:**
- Siempre incluir todas las dependencias
- Implementar cleanup cuando sea necesario
- Evitar lógica compleja en effects (extraer a funciones)

#### Custom Hooks
Para lógica reutilizable:
```javascript
// hooks/useDebounce.js
export const useDebounce = (value, delay) => {
  const [debouncedValue, setDebouncedValue] = useState(value)
  
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])
  
  return debouncedValue
}
```

**Best Practices:**
- Prefijo `use` obligatorio
- Retornar valores útiles
- Documentar parámetros y retorno
- Un hook, una responsabilidad

#### Performance Hooks

**useMemo** - Para cálculos costosos:
```jsx
const sortedData = useMemo(() => {
  return data.sort((a, b) => a.value - b.value)
}, [data])
```

**useCallback** - Para funciones que se pasan como props:
```jsx
const handleSubmit = useCallback((values) => {
  saveData(values)
}, [saveData])
```

**Cuándo usar:**
- useMemo: Cálculos pesados, transformaciones de listas grandes
- useCallback: Funciones pasadas a componentes memoizados
- **No optimizar prematuramente** - medir primero

### Styling with Tailwind CSS

#### Utility Classes
```jsx
// ✅ GOOD: Classes ordenadas y legibles
<button className="
  flex items-center gap-2
  px-4 py-2
  bg-primary-600 hover:bg-primary-700
  text-white font-medium
  rounded-lg
  transition-colors
">
  Submit
</button>
```

#### Conditional Classes with cn()
```jsx
import { cn } from '@/utils/cn'

<div className={cn(
  'base-classes',
  isActive && 'active-classes',
  isDisabled && 'disabled-classes',
  className // Allow external override
)} />
```

#### Theme Colors
Usar colores del tema definidos:
```javascript
// tailwind.config.js tiene:
primary: { 50-950 }    // Blues corporativos
secondary: { 50-950 }  // Grays
```

**Usage:**
- `bg-primary-600` para botones principales
- `text-secondary-700` para texto
- `border-secondary-200` para bordes

#### Responsive Design
```jsx
<div className="
  w-full md:w-1/2 lg:w-1/3
  p-4 md:p-6 lg:p-8
  text-sm md:text-base
">
```

**Breakpoints:**
- `sm:` 640px
- `md:` 768px
- `lg:` 1024px
- `xl:` 1280px

### Data Fetching Patterns

#### Query Pattern
```jsx
const CierresPage = () => {
  const { data: cierres, isLoading, error } = useCierres()
  
  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage error={error} />
  
  return (
    <div>
      {cierres.map(cierre => (
        <CierreCard key={cierre.id} cierre={cierre} />
      ))}
    </div>
  )
}
```

#### Mutation Pattern
```jsx
const CrearCierreForm = () => {
  const createMutation = useCreateCierre()
  
  const handleSubmit = async (data) => {
    try {
      await createMutation.mutateAsync(data)
      toast.success('Cierre creado')
      navigate('/cierres')
    } catch (error) {
      toast.error(error.message)
    }
  }
  
  return (
    <form onSubmit={handleSubmit}>
      {/* form fields */}
      <button disabled={createMutation.isPending}>
        {createMutation.isPending ? 'Creando...' : 'Crear'}
      </button>
    </form>
  )
}
```

#### Optimistic Updates
```javascript
export const useUpdateCierre = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data) => cierreService.update(data.id, data),
    onMutate: async (newData) => {
      // Cancel outgoing queries
      await queryClient.cancelQueries({ queryKey: ['cierres'] })
      
      // Snapshot previous value
      const previous = queryClient.getQueryData(['cierres'])
      
      // Optimistically update
      queryClient.setQueryData(['cierres'], (old) => 
        old.map(c => c.id === newData.id ? newData : c)
      )
      
      return { previous }
    },
    onError: (err, newData, context) => {
      // Rollback on error
      queryClient.setQueryData(['cierres'], context.previous)
    },
  })
}
```

### Error Handling

#### Error Boundaries
**CRITICAL:** Implementar Error Boundaries para rutas principales:
```jsx
// components/ErrorBoundary.jsx
import { Component } from 'react'

class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }
  
  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }
  
  componentDidCatch(error, errorInfo) {
    console.error('Error capturado:', error, errorInfo)
    // Enviar a servicio de logging si existe
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-red-600 mb-4">
              Algo salió mal
            </h1>
            <p className="text-secondary-600 mb-4">
              {this.state.error?.message}
            </p>
            <button 
              onClick={() => window.location.reload()}
              className="btn-primary"
            >
              Recargar página
            </button>
          </div>
        </div>
      )
    }
    
    return this.props.children
  }
}

export default ErrorBoundary
```

**Usage:**
```jsx
// App.jsx
<ErrorBoundary>
  <Routes>
    {/* routes */}
  </Routes>
</ErrorBoundary>
```

#### API Error Handling
```javascript
// api/axios.js
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login
    }
    return Promise.reject(error)
  }
)
```

### Performance Optimization

#### Code Splitting
**Implementar lazy loading en rutas:**
```jsx
import { lazy, Suspense } from 'react'

// Lazy load route components
const AdminPage = lazy(() => import('./features/admin/pages/AdminPage'))
const CierreDetail = lazy(() => import('./features/validador/pages/CierreDetailPage'))

// In Routes
<Route 
  path="/admin" 
  element={
    <Suspense fallback={<LoadingSpinner />}>
      <AdminPage />
    </Suspense>
  } 
/>
```

#### Component Memoization
Para componentes que renderizan frecuentemente:
```jsx
import { memo } from 'react'

const CierreCard = memo(({ cierre, onSelect }) => {
  return (
    <div onClick={() => onSelect(cierre)}>
      {/* card content */}
    </div>
  )
}, (prevProps, nextProps) => {
  // Custom comparison
  return prevProps.cierre.id === nextProps.cierre.id
})
```

#### Virtual Scrolling
Para listas muy largas (100+ items):
```jsx
import { useVirtualizer } from '@tanstack/react-virtual'

const LargeCierresList = ({ cierres }) => {
  const parentRef = useRef()
  
  const virtualizer = useVirtualizer({
    count: cierres.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80,
  })
  
  return (
    <div ref={parentRef} style={{ height: '600px', overflow: 'auto' }}>
      <div style={{ height: `${virtualizer.getTotalSize()}px` }}>
        {virtualizer.getVirtualItems().map(virtualRow => (
          <CierreCard 
            key={cierres[virtualRow.index].id}
            cierre={cierres[virtualRow.index]}
          />
        ))}
      </div>
    </div>
  )
}
```

### Forms and Validation

#### React Hook Form Pattern
```jsx
import { useForm } from 'react-hook-form'

const CierreForm = ({ onSubmit }) => {
  const { 
    register, 
    handleSubmit, 
    formState: { errors, isSubmitting } 
  } = useForm()
  
  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div>
        <label htmlFor="nombre">Nombre</label>
        <input
          id="nombre"
          {...register('nombre', { 
            required: 'Nombre es requerido',
            minLength: { value: 3, message: 'Mínimo 3 caracteres' }
          })}
        />
        {errors.nombre && (
          <span className="text-red-500 text-sm">{errors.nombre.message}</span>
        )}
      </div>
      
      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Guardando...' : 'Guardar'}
      </button>
    </form>
  )
}
```

### Routing Patterns

#### Protected Routes
```jsx
const ProtectedRoute = ({ children, requiredRole }) => {
  const { user, isAuthenticated } = useAuth()
  const hasPermission = usePermissions()
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  if (requiredRole && !hasPermission(requiredRole)) {
    return <Navigate to="/unauthorized" replace />
  }
  
  return children
}

// Usage
<Route 
  path="/admin" 
  element={
    <ProtectedRoute requiredRole="gerente">
      <AdminPage />
    </ProtectedRoute>
  } 
/>
```

#### Nested Routes
```jsx
<Route path="/cierres" element={<CierresLayout />}>
  <Route index element={<CierresListPage />} />
  <Route path=":id" element={<CierreDetailPage />} />
  <Route path="nuevo" element={<NuevoCierrePage />} />
</Route>
```

### Accessibility

#### Semantic HTML
```jsx
// ✅ GOOD
<nav>
  <ul>
    <li><a href="/home">Inicio</a></li>
  </ul>
</nav>

<main>
  <article>
    <h1>Título</h1>
    <p>Contenido</p>
  </article>
</main>

// ❌ BAD
<div className="nav">
  <div className="link">Inicio</div>
</div>
```

#### ARIA Attributes
```jsx
<button
  aria-label="Cerrar modal"
  aria-expanded={isOpen}
  onClick={handleClose}
>
  <X className="w-5 h-5" />
</button>

<input
  type="text"
  aria-describedby="email-error"
  aria-invalid={!!errors.email}
/>
{errors.email && (
  <span id="email-error" role="alert">
    {errors.email.message}
  </span>
)}
```

#### Keyboard Navigation
```jsx
const Modal = ({ isOpen, onClose, children }) => {
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose()
    }
    
    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      return () => document.removeEventListener('keydown', handleEscape)
    }
  }, [isOpen, onClose])
  
  // Trap focus, manage focus
}
```

### Testing (To Implement)

#### Component Testing
```javascript
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect } from 'vitest'

describe('CierreCard', () => {
  it('renders cierre information', () => {
    const cierre = { id: 1, nombre: 'Enero 2026', estado: 'pendiente' }
    render(<CierreCard cierre={cierre} />)
    
    expect(screen.getByText('Enero 2026')).toBeInTheDocument()
    expect(screen.getByText('pendiente')).toBeInTheDocument()
  })
  
  it('calls onSelect when clicked', () => {
    const handleSelect = vi.fn()
    const cierre = { id: 1, nombre: 'Enero 2026' }
    render(<CierreCard cierre={cierre} onSelect={handleSelect} />)
    
    fireEvent.click(screen.getByRole('button'))
    expect(handleSelect).toHaveBeenCalledWith(cierre)
  })
})
```

### Security Best Practices

#### Input Sanitization
```jsx
// ✅ GOOD: React escapa por defecto
<div>{userInput}</div>

// ⚠️ DANGER: Solo cuando sea absolutamente necesario
<div dangerouslySetInnerHTML={{ __html: sanitizedHTML }} />
```

#### Authentication
```javascript
// api/axios.js
axios.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

#### Environment Variables
```javascript
// ✅ GOOD: Usar import.meta.env
const API_URL = import.meta.env.VITE_API_URL

// ❌ BAD: Hardcodear
const API_URL = 'http://localhost:8000'
```

## Common Patterns

### Loading States
```jsx
const LoadingSpinner = () => (
  <div className="flex items-center justify-center p-8">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
  </div>
)
```

### Empty States
```jsx
const EmptyState = ({ title, description, action }) => (
  <div className="text-center py-12">
    <h3 className="text-lg font-medium text-secondary-900">{title}</h3>
    <p className="text-secondary-600 mt-2">{description}</p>
    {action && <div className="mt-6">{action}</div>}
  </div>
)
```

### Toast Notifications
```javascript
import toast from 'react-hot-toast'

toast.success('Operación exitosa')
toast.error('Error al procesar')
toast.loading('Procesando...')
```

## Things to Avoid

1. **No mezclar Context API y Zustand** - Preferir Zustand para estado global
2. **No usar inline functions en JSX** - Extraer event handlers
3. **No optimizar prematuramente** - Medir antes de optimizar
4. **No abusar de useEffect** - Considerar si realmente es necesario
5. **No mutar estado directamente** - Siempre crear nuevos objetos
6. **No hardcodear valores** - Usar constantes o variables de entorno
7. **No ignorar warnings de dependencias** - Corregirlos apropiadamente
8. **No usar índices como keys** - Usar IDs únicos

## Implementation Checklist

### New Component
- [ ] Componente funcional con JSDoc
- [ ] Props destructuring
- [ ] Hooks al inicio
- [ ] Event handlers con prefijo `handle`
- [ ] Early returns para loading/error
- [ ] Tailwind classes ordenadas
- [ ] ARIA attributes si es interactivo
- [ ] Export en index.js del feature

### New Page
- [ ] Lazy loading en routes
- [ ] Protected route si requiere auth
- [ ] Loading state
- [ ] Error boundary
- [ ] Responsive design
- [ ] Page title (document.title)

### New Hook
- [ ] Prefijo `use`
- [ ] JSDoc con params y return
- [ ] Cleanup si es necesario
- [ ] Tests si es complejo

### New API Integration
- [ ] React Query hook
- [ ] Loading/error states
- [ ] Optimistic updates si aplica
- [ ] Error handling
- [ ] Query invalidation en mutations

## Useful Commands

```bash
# Development
npm run dev

# Build
npm run build

# Lint
npm run lint

# Preview production build
npm run preview

# Install new dependency
npm install package-name

# Update dependencies
npm update
```

## Additional Resources

- [React Docs](https://react.dev)
- [TanStack Query Docs](https://tanstack.com/query/latest)
- [Zustand Docs](https://docs.pmnd.rs/zustand)
- [Tailwind CSS Docs](https://tailwindcss.com)
- [React Router Docs](https://reactrouter.com)

---

## Priority Summary

### 🔴 CRITICAL (Implement Now)
- Error Boundaries en rutas principales
- Lazy loading para code splitting
- Security best practices (sanitization, HTTPS)

### 🟡 HIGH PRIORITY (Next Sprint)
- Testing setup (Vitest + Testing Library)
- Performance optimization (memoization, virtualization)
- Accessibility audit (ARIA, keyboard navigation)

### 🟢 NICE TO HAVE (Future)
- Storybook para componentes
- E2E testing con Playwright
- Advanced performance monitoring

---

**Last Updated:** 2026-01-08
**Version:** 1.0.0

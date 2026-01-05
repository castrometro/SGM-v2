/**
 * Componente Table reutilizable
 */
import { cn } from '../../utils/cn'

const Table = ({ children, className }) => (
  <div className={cn('w-full overflow-x-auto', className)}>
    <table className="w-full">
      {children}
    </table>
  </div>
)

const TableHeader = ({ children, className }) => (
  <thead className={cn('bg-secondary-800/50', className)}>
    {children}
  </thead>
)

const TableBody = ({ children, className }) => (
  <tbody className={cn('divide-y divide-secondary-800', className)}>
    {children}
  </tbody>
)

const TableRow = ({ children, className, onClick, hoverable = true }) => (
  <tr 
    className={cn(
      'transition-colors',
      hoverable && 'hover:bg-secondary-800/50',
      onClick && 'cursor-pointer',
      className
    )}
    onClick={onClick}
  >
    {children}
  </tr>
)

const TableHead = ({ children, className, align = 'left' }) => (
  <th 
    className={cn(
      'px-4 py-3 text-xs font-semibold text-secondary-400 uppercase tracking-wider',
      align === 'left' && 'text-left',
      align === 'center' && 'text-center',
      align === 'right' && 'text-right',
      className
    )}
  >
    {children}
  </th>
)

const TableCell = ({ children, className, align = 'left' }) => (
  <td 
    className={cn(
      'px-4 py-4 text-sm text-secondary-300',
      align === 'left' && 'text-left',
      align === 'center' && 'text-center',
      align === 'right' && 'text-right',
      className
    )}
  >
    {children}
  </td>
)

const TableEmpty = ({ message = 'No hay datos disponibles', colSpan = 1 }) => (
  <tr>
    <td 
      colSpan={colSpan} 
      className="px-4 py-12 text-center text-secondary-500"
    >
      {message}
    </td>
  </tr>
)

Table.Header = TableHeader
Table.Body = TableBody
Table.Row = TableRow
Table.Head = TableHead
Table.Cell = TableCell
Table.Empty = TableEmpty

export default Table

/** Table component */

import { HTMLAttributes, forwardRef, ReactNode } from 'react';
import { cn } from '../../lib/utils';

export interface Column<T> {
  key: string;
  header: string;
  render?: (row: T) => ReactNode;
  className?: string;
  width?: string;
}

export interface TableProps<T> extends HTMLAttributes<HTMLTableElement> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (row: T) => string | number;
  emptyMessage?: string;
  loading?: boolean;
  onRowClick?: (row: T) => void;
  striped?: boolean;
}

export function Table<T>({
  columns,
  data,
  keyExtractor,
  emptyMessage = 'No data available',
  loading,
  onRowClick,
  striped = true,
  className,
  ...props
}: TableProps<T>) {
  if (loading) {
    return (
      <div className="overflow-x-auto" {...props}>
        <table className="w-full" role="table">
          <thead>
            <tr className="border-b border-slate-200">
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={cn('px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider', col.className)}
                  style={{ width: col.width }}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {Array.from({ length: 5 }).map((_, i) => (
              <tr key={i} className={cn(striped && i % 2 === 0 ? 'bg-slate-50' : '')}>
                {columns.map((col) => (
                  <td key={col.key} className={cn('px-4 py-3 text-slate-500 animate-pulse', col.className)}>
                    <div className="h-4 bg-slate-200 rounded w-3/4" />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="text-center py-12 text-slate-500" {...props}>
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto" {...props}>
      <table className="w-full" role="table">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50">
            {columns.map((col) => (
              <th
                key={col.key}
                className={cn('px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider', col.className)}
                style={{ width: col.width }}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200">
          {data.map((row) => (
            <tr
              key={keyExtractor(row)}
              className={cn(
                'transition-colors',
                striped && 'even:bg-slate-50',
                onRowClick && 'cursor-pointer hover:bg-slate-50'
              )}
              onClick={() => onRowClick?.(row)}
            >
              {columns.map((col) => (
                <td key={col.key} className={cn('px-4 py-3 text-sm text-slate-900', col.className)}>
                  {col.render ? col.render(row) : String((row as Record<string, unknown>)[col.key] ?? '')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
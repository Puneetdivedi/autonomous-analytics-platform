import { ReactNode } from 'react';
import clsx from 'clsx';
import { LucideIcon, TrendingUp, TrendingDown } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: ReactNode;
  icon?: LucideIcon;
  delta?: number;
  hint?: string;
  accent?: 'brand' | 'emerald' | 'amber' | 'sky' | 'violet';
}

const accents: Record<NonNullable<StatCardProps['accent']>, string> = {
  brand: 'bg-brand-50 text-brand-600 dark:bg-brand-900/30 dark:text-brand-300',
  emerald:
    'bg-emerald-50 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-300',
  amber: 'bg-amber-50 text-amber-600 dark:bg-amber-900/30 dark:text-amber-300',
  sky: 'bg-sky-50 text-sky-600 dark:bg-sky-900/30 dark:text-sky-300',
  violet:
    'bg-violet-50 text-violet-600 dark:bg-violet-900/30 dark:text-violet-300',
};

export default function StatCard({
  label,
  value,
  icon: Icon,
  delta,
  hint,
  accent = 'brand',
}: StatCardProps) {
  const positive = (delta ?? 0) >= 0;
  return (
    <div className="surface rounded-xl p-5 shadow-card">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
            {label}
          </p>
          <p className="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-100">
            {value}
          </p>
        </div>
        {Icon && (
          <div className={clsx('rounded-lg p-2', accents[accent])}>
            <Icon className="h-5 w-5" />
          </div>
        )}
      </div>
      {(delta !== undefined || hint) && (
        <div className="mt-3 flex items-center gap-1 text-xs">
          {delta !== undefined && (
            <span
              className={clsx(
                'inline-flex items-center gap-0.5 font-medium',
                positive ? 'text-emerald-600' : 'text-red-500'
              )}
            >
              {positive ? (
                <TrendingUp className="h-3.5 w-3.5" />
              ) : (
                <TrendingDown className="h-3.5 w-3.5" />
              )}
              {Math.abs(delta)}%
            </span>
          )}
          {hint && <span className="text-slate-400">{hint}</span>}
        </div>
      )}
    </div>
  );
}

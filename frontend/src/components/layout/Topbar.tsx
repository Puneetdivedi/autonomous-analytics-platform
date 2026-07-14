import { Menu, Moon, Sun } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useTheme } from '@/context/ThemeContext';
import { useProjects } from '@/hooks/useProjects';
import { useSelectedProject } from '@/hooks/useSelectedProject';

interface TopbarProps {
  onMenuClick: () => void;
}

export default function Topbar({ onMenuClick }: TopbarProps) {
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { data: projects } = useProjects();
  const { projectId, select } = useSelectedProject();

  const displayName = user?.full_name || 'Guest';
  const initials = displayName
    .split(' ')
    .map((p) => p[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200 bg-white/80 px-4 backdrop-blur dark:border-slate-800 dark:bg-slate-900/80">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="rounded-md p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 lg:hidden"
          aria-label="Toggle menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        <div className="hidden sm:block">
          <label className="sr-only" htmlFor="project-select">
            Active project
          </label>
          <select
            id="project-select"
            value={projectId ?? ''}
            onChange={(e) => select(e.target.value || null)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
          >
            <option value="">All projects</option>
            {projects?.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={toggleTheme}
          className="rounded-md p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? (
            <Sun className="h-5 w-5" />
          ) : (
            <Moon className="h-5 w-5" />
          )}
        </button>

        <div className="flex items-center gap-2 rounded-full py-1 pl-1 pr-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-600 text-xs font-semibold text-white">
            {initials}
          </div>
          <div className="hidden text-right leading-tight sm:block">
            <p className="text-sm font-medium text-slate-800 dark:text-slate-200">
              {displayName}
            </p>
            <p className="text-[11px] capitalize text-slate-400">
              guest session
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}

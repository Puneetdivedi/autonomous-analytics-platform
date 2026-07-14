import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import { useAuth } from '@/hooks/useAuth';

const ANALYZER_URL =
  'https://puneetdivedi.github.io/autonomous-analytics-platform/analyzer.html';

export default function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { demoMode } = useAuth();

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 dark:bg-slate-950">
      <Sidebar open={sidebarOpen} onNavigate={() => setSidebarOpen(false)} />

      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-slate-900/40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden
        />
      )}

      <div className="flex flex-1 flex-col overflow-hidden">
        <Topbar onMenuClick={() => setSidebarOpen((v) => !v)} />
        {demoMode && (
          <div className="flex flex-wrap items-center justify-center gap-x-2 gap-y-1 bg-amber-50 px-4 py-2 text-center text-sm text-amber-800 dark:bg-amber-950/40 dark:text-amber-300">
            <span>
              Demo mode — no backend connected, so accounts &amp; live analysis
              are unavailable here.
            </span>
            <a
              href={ANALYZER_URL}
              target="_blank"
              rel="noreferrer"
              className="font-semibold underline underline-offset-2 hover:text-amber-900 dark:hover:text-amber-200"
            >
              Open the working analyzer →
            </a>
          </div>
        )}
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}

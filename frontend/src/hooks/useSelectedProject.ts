import { useCallback, useEffect, useState } from 'react';

const STORAGE_KEY = 'ada_selected_project';
const EVENT = 'ada:selected-project-changed';

/**
 * Lightweight cross-component selected-project state, backed by localStorage
 * and synced across hook instances via a custom window event.
 */
export function useSelectedProject() {
  const [projectId, setProjectId] = useState<string | null>(() =>
    localStorage.getItem(STORAGE_KEY)
  );

  useEffect(() => {
    const handler = () => setProjectId(localStorage.getItem(STORAGE_KEY));
    window.addEventListener(EVENT, handler);
    window.addEventListener('storage', handler);
    return () => {
      window.removeEventListener(EVENT, handler);
      window.removeEventListener('storage', handler);
    };
  }, []);

  const select = useCallback((id: string | null) => {
    if (id) localStorage.setItem(STORAGE_KEY, id);
    else localStorage.removeItem(STORAGE_KEY);
    window.dispatchEvent(new Event(EVENT));
    setProjectId(id);
  }, []);

  return { projectId, select };
}

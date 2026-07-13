import { Moon, Sun, User as UserIcon, Cpu, Bell } from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useTheme } from '@/context/ThemeContext';
import Card, { CardHeader } from '@/components/common/Card';
import Input from '@/components/common/Input';
import Badge from '@/components/common/Badge';
import Button from '@/components/common/Button';

export default function SettingsPage() {
  const { user } = useAuth();
  const { theme, setTheme } = useTheme();
  const [prefs, setPrefs] = useState({
    emailReports: true,
    streamResponses: true,
    defaultFormat: 'pdf',
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
          Settings
        </h1>
        <p className="text-sm text-slate-500">
          Manage your profile, appearance, and preferences.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="Profile" subtitle="Your account details" />
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-600 text-white">
              <UserIcon className="h-6 w-6" />
            </div>
            <div>
              <p className="font-medium text-slate-800 dark:text-slate-100">
                {user?.full_name}
              </p>
              <Badge tone="brand">{user?.role}</Badge>
            </div>
          </div>
          <div className="space-y-4">
            <Input label="Full name" defaultValue={user?.full_name} readOnly />
            <Input label="Email" defaultValue={user?.email} readOnly />
          </div>
        </Card>

        <Card>
          <CardHeader title="Appearance" subtitle="Theme preference" />
          <div className="flex gap-3">
            <button
              onClick={() => setTheme('light')}
              className={`flex flex-1 items-center justify-center gap-2 rounded-lg border px-4 py-3 text-sm font-medium transition-colors ${
                theme === 'light'
                  ? 'border-brand-500 bg-brand-50 text-brand-700 dark:bg-brand-900/30'
                  : 'border-slate-300 text-slate-600 dark:border-slate-700 dark:text-slate-300'
              }`}
            >
              <Sun className="h-4 w-4" /> Light
            </button>
            <button
              onClick={() => setTheme('dark')}
              className={`flex flex-1 items-center justify-center gap-2 rounded-lg border px-4 py-3 text-sm font-medium transition-colors ${
                theme === 'dark'
                  ? 'border-brand-500 bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300'
                  : 'border-slate-300 text-slate-600 dark:border-slate-700 dark:text-slate-300'
              }`}
            >
              <Moon className="h-4 w-4" /> Dark
            </button>
          </div>
        </Card>

        <Card>
          <CardHeader
            title="Preferences"
            subtitle="Control notifications and defaults"
          />
          <div className="space-y-3">
            <label className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                <Bell className="h-4 w-4" /> Email me finished reports
              </span>
              <input
                type="checkbox"
                checked={prefs.emailReports}
                onChange={(e) =>
                  setPrefs({ ...prefs, emailReports: e.target.checked })
                }
                className="h-4 w-4 accent-brand-600"
              />
            </label>
            <label className="flex items-center justify-between">
              <span className="text-sm text-slate-700 dark:text-slate-300">
                Stream assistant responses
              </span>
              <input
                type="checkbox"
                checked={prefs.streamResponses}
                onChange={(e) =>
                  setPrefs({ ...prefs, streamResponses: e.target.checked })
                }
                className="h-4 w-4 accent-brand-600"
              />
            </label>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-700 dark:text-slate-300">
                Default report format
              </span>
              <select
                value={prefs.defaultFormat}
                onChange={(e) =>
                  setPrefs({ ...prefs, defaultFormat: e.target.value })
                }
                className="rounded-lg border border-slate-300 bg-white px-2 py-1 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
              >
                <option value="pdf">PDF</option>
                <option value="pptx">PPTX</option>
                <option value="docx">DOCX</option>
                <option value="html">HTML</option>
              </select>
            </div>
            <Button size="sm" className="mt-2">
              Save preferences
            </Button>
          </div>
        </Card>

        <Card>
          <CardHeader
            title="Provider"
            subtitle="Model and infrastructure info"
          />
          <div className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
                <Cpu className="h-4 w-4" /> LLM provider
              </span>
              <Badge tone="info">Anthropic Claude</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-600 dark:text-slate-300">
                Orchestration
              </span>
              <Badge tone="neutral">LangGraph</Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-600 dark:text-slate-300">
                API endpoint
              </span>
              <span className="font-mono text-xs text-slate-400">
                {import.meta.env.VITE_API_BASE_URL ||
                  'http://localhost:8000/api/v1'}
              </span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}

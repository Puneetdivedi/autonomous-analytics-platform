import { FormEvent, useRef, useState } from 'react';
import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';
import {
  FolderKanban,
  Plus,
  Database,
  Upload,
  Trash2,
  RefreshCw,
  CheckCircle2,
} from 'lucide-react';
import clsx from 'clsx';
import {
  useProjects,
  useCreateProject,
  useDeleteProject,
} from '@/hooks/useProjects';
import { useSelectedProject } from '@/hooks/useSelectedProject';
import { datasourceService } from '@/services/datasourceService';
import Card, { CardHeader } from '@/components/common/Card';
import Button from '@/components/common/Button';
import Input from '@/components/common/Input';
import Modal from '@/components/common/Modal';
import Spinner from '@/components/common/Spinner';
import EmptyState from '@/components/common/EmptyState';
import Badge from '@/components/common/Badge';

function DataSourcesPanel({ projectId }: { projectId: string }) {
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [connOpen, setConnOpen] = useState(false);
  const [conn, setConn] = useState({
    name: '',
    type: 'postgres',
    connection_string: '',
  });

  const { data: sources, isLoading } = useQuery({
    queryKey: ['datasources', projectId],
    queryFn: () => datasourceService.list(projectId),
  });

  const invalidate = () =>
    qc.invalidateQueries({ queryKey: ['datasources', projectId] });

  const uploadMut = useMutation({
    mutationFn: (file: File) => datasourceService.upload(projectId, file),
    onSuccess: invalidate,
  });

  const connMut = useMutation({
    mutationFn: () =>
      datasourceService.createConnection({ project_id: projectId, ...conn }),
    onSuccess: () => {
      invalidate();
      setConnOpen(false);
      setConn({ name: '', type: 'postgres', connection_string: '' });
    },
  });

  const introspectMut = useMutation({
    mutationFn: (id: string) => datasourceService.introspect(id),
    onSuccess: invalidate,
  });

  return (
    <Card>
      <CardHeader
        title="Data sources"
        subtitle="Connect a database or upload a file"
        action={
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => fileRef.current?.click()}
              loading={uploadMut.isPending}
            >
              <Upload className="h-4 w-4" /> Upload
            </Button>
            <Button size="sm" onClick={() => setConnOpen(true)}>
              <Database className="h-4 w-4" /> Connect
            </Button>
          </div>
        }
      />

      <input
        ref={fileRef}
        type="file"
        className="hidden"
        accept=".csv,.xlsx,.xls,.json,.parquet"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) uploadMut.mutate(file);
          e.target.value = '';
        }}
      />

      {isLoading ? (
        <Spinner label="Loading data sources..." />
      ) : !sources || sources.length === 0 ? (
        <EmptyState
          icon={Database}
          title="No data sources"
          description="Upload a dataset or connect a database to begin analysis."
        />
      ) : (
        <ul className="space-y-2">
          {sources.map((ds) => (
            <li
              key={ds.id}
              className="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2 dark:border-slate-800"
            >
              <div className="flex items-center gap-3">
                <Database className="h-4 w-4 text-brand-600" />
                <div>
                  <p className="text-sm font-medium text-slate-800 dark:text-slate-100">
                    {ds.name}
                  </p>
                  <p className="text-xs text-slate-400">{ds.type}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {ds.status && (
                  <Badge tone={ds.status === 'ready' ? 'success' : 'neutral'}>
                    {ds.status === 'ready' && (
                      <CheckCircle2 className="h-3 w-3" />
                    )}
                    {ds.status}
                  </Badge>
                )}
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => introspectMut.mutate(ds.id)}
                  loading={
                    introspectMut.isPending &&
                    introspectMut.variables === ds.id
                  }
                >
                  <RefreshCw className="h-3.5 w-3.5" /> Introspect
                </Button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <Modal
        open={connOpen}
        onClose={() => setConnOpen(false)}
        title="Connect a database"
        footer={
          <>
            <Button variant="ghost" onClick={() => setConnOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => connMut.mutate()}
              loading={connMut.isPending}
              disabled={!conn.name || !conn.connection_string}
            >
              Connect
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input
            label="Name"
            value={conn.name}
            onChange={(e) => setConn({ ...conn, name: e.target.value })}
            placeholder="Production warehouse"
          />
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-300">
              Type
            </label>
            <select
              value={conn.type}
              onChange={(e) => setConn({ ...conn, type: e.target.value })}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
            >
              <option value="postgres">PostgreSQL</option>
              <option value="mysql">MySQL</option>
              <option value="snowflake">Snowflake</option>
              <option value="bigquery">BigQuery</option>
              <option value="sqlite">SQLite</option>
            </select>
          </div>
          <Input
            label="Connection string"
            value={conn.connection_string}
            onChange={(e) =>
              setConn({ ...conn, connection_string: e.target.value })
            }
            placeholder="postgresql://user:pass@host:5432/db"
          />
        </div>
      </Modal>
    </Card>
  );
}

export default function ProjectsPage() {
  const { data: projects, isLoading } = useProjects();
  const createMut = useCreateProject();
  const deleteMut = useDeleteProject();
  const { projectId, select } = useSelectedProject();

  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState({ name: '', description: '' });

  const activeId = projectId ?? projects?.[0]?.id ?? null;

  const onCreate = async (e: FormEvent) => {
    e.preventDefault();
    const created = await createMut.mutateAsync(form);
    setCreateOpen(false);
    setForm({ name: '', description: '' });
    select(created.id);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
            Projects
          </h1>
          <p className="text-sm text-slate-500">
            Organize your data sources and analyses.
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="h-4 w-4" /> New project
        </Button>
      </div>

      {isLoading ? (
        <Spinner fullscreen label="Loading projects..." />
      ) : !projects || projects.length === 0 ? (
        <EmptyState
          icon={FolderKanban}
          title="No projects yet"
          description="Create your first project to start connecting data and asking questions."
          action={
            <Button onClick={() => setCreateOpen(true)}>
              <Plus className="h-4 w-4" /> Create project
            </Button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="lg:col-span-1">
            <Card>
              <CardHeader title="All projects" />
              <ul className="space-y-1">
                {projects.map((p) => (
                  <li key={p.id}>
                    <button
                      onClick={() => select(p.id)}
                      className={clsx(
                        'w-full rounded-lg px-3 py-2 text-left transition-colors',
                        p.id === activeId
                          ? 'bg-brand-50 dark:bg-brand-900/30'
                          : 'hover:bg-slate-50 dark:hover:bg-slate-800'
                      )}
                    >
                      <div className="flex items-center justify-between">
                        <span className="truncate text-sm font-medium text-slate-800 dark:text-slate-100">
                          {p.name}
                        </span>
                        <Trash2
                          className="h-4 w-4 shrink-0 text-slate-300 hover:text-red-500"
                          onClick={(e) => {
                            e.stopPropagation();
                            if (confirm(`Delete project "${p.name}"?`)) {
                              deleteMut.mutate(p.id);
                              if (p.id === projectId) select(null);
                            }
                          }}
                        />
                      </div>
                      {p.description && (
                        <p className="truncate text-xs text-slate-400">
                          {p.description}
                        </p>
                      )}
                    </button>
                  </li>
                ))}
              </ul>
            </Card>
          </div>

          <div className="lg:col-span-2">
            {activeId ? (
              <DataSourcesPanel projectId={activeId} />
            ) : (
              <EmptyState
                icon={Database}
                title="Select a project"
                description="Choose a project to manage its data sources."
              />
            )}
          </div>
        </div>
      )}

      <Modal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        title="Create project"
        footer={
          <>
            <Button variant="ghost" onClick={() => setCreateOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={onCreate}
              loading={createMut.isPending}
              disabled={!form.name}
            >
              Create
            </Button>
          </>
        }
      >
        <form onSubmit={onCreate} className="space-y-4">
          <Input
            label="Name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="Q3 Revenue Analysis"
          />
          <Input
            label="Description"
            value={form.description}
            onChange={(e) =>
              setForm({ ...form, description: e.target.value })
            }
            placeholder="Optional description"
          />
        </form>
      </Modal>
    </div>
  );
}

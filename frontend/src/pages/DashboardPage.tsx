import { Link } from 'react-router-dom';
import {
  FolderKanban,
  MessageSquare,
  FileText,
  Coins,
  ArrowRight,
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { useProjects } from '@/hooks/useProjects';
import { useChats } from '@/hooks/useChats';
import { useReports } from '@/hooks/useReports';
import { useSelectedProject } from '@/hooks/useSelectedProject';
import { useAuth } from '@/hooks/useAuth';
import StatCard from '@/components/charts/StatCard';
import Card, { CardHeader } from '@/components/common/Card';
import Spinner from '@/components/common/Spinner';
import EmptyState from '@/components/common/EmptyState';

const activityData = [
  { day: 'Mon', queries: 12 },
  { day: 'Tue', queries: 19 },
  { day: 'Wed', queries: 15 },
  { day: 'Thu', queries: 27 },
  { day: 'Fri', queries: 32 },
  { day: 'Sat', queries: 9 },
  { day: 'Sun', queries: 6 },
];

export default function DashboardPage() {
  const { user } = useAuth();
  const { data: projects, isLoading: projectsLoading } = useProjects();
  const { projectId } = useSelectedProject();
  const { data: chats } = useChats(projectId ?? undefined);
  const { data: reports } = useReports(projectId ?? undefined);

  const firstName = user?.full_name?.split(' ')[0] ?? 'there';

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
          Welcome back, {firstName}
        </h1>
        <p className="text-sm text-slate-500">
          Here is an overview of your analytics workspace.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Projects"
          value={projects?.length ?? 0}
          icon={FolderKanban}
          accent="brand"
          delta={8}
          hint="vs last week"
        />
        <StatCard
          label="Conversations"
          value={chats?.length ?? 0}
          icon={MessageSquare}
          accent="sky"
          delta={12}
          hint="vs last week"
        />
        <StatCard
          label="Reports"
          value={reports?.length ?? 0}
          icon={FileText}
          accent="violet"
        />
        <StatCard
          label="Est. spend"
          value="$4.82"
          icon={Coins}
          accent="emerald"
          delta={-3}
          hint="this month"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader
            title="Query activity"
            subtitle="Questions asked over the last 7 days"
          />
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={activityData}>
              <defs>
                <linearGradient id="q" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#3366ff" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#3366ff" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(148,163,184,0.2)"
              />
              <XAxis dataKey="day" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Area
                type="monotone"
                dataKey="queries"
                stroke="#3366ff"
                fill="url(#q)"
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <CardHeader title="Recent projects" />
          {projectsLoading ? (
            <Spinner label="Loading..." />
          ) : !projects || projects.length === 0 ? (
            <EmptyState
              icon={FolderKanban}
              title="No projects yet"
              description="Create a project to get started."
            />
          ) : (
            <ul className="space-y-2">
              {projects.slice(0, 5).map((p) => (
                <li key={p.id}>
                  <Link
                    to="/projects"
                    className="flex items-center justify-between rounded-lg px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-800"
                  >
                    <span className="truncate">{p.name}</span>
                    <ArrowRight className="h-4 w-4 text-slate-400" />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}

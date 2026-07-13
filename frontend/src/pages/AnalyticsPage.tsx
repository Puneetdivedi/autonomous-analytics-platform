import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { Activity, Coins, Cpu, Gauge } from 'lucide-react';
import { useProjects } from '@/hooks/useProjects';
import { useChats } from '@/hooks/useChats';
import { useSelectedProject } from '@/hooks/useSelectedProject';
import Card, { CardHeader } from '@/components/common/Card';
import StatCard from '@/components/charts/StatCard';

const PALETTE = ['#3366ff', '#00b8a9', '#f6a609', '#8b5cf6', '#e8618c'];

const usageByDay = [
  { day: 'Mon', queries: 12, tokens: 48000 },
  { day: 'Tue', queries: 19, tokens: 71000 },
  { day: 'Wed', queries: 15, tokens: 55000 },
  { day: 'Thu', queries: 27, tokens: 98000 },
  { day: 'Fri', queries: 32, tokens: 121000 },
  { day: 'Sat', queries: 9, tokens: 33000 },
  { day: 'Sun', queries: 6, tokens: 21000 },
];

const costByModel = [
  { name: 'Claude Opus', value: 3.1 },
  { name: 'Claude Sonnet', value: 1.2 },
  { name: 'Embeddings', value: 0.4 },
];

const latencyByNode = [
  { node: 'Planner', latency: 820 },
  { node: 'SQL Gen', latency: 1450 },
  { node: 'Executor', latency: 640 },
  { node: 'Charting', latency: 910 },
  { node: 'Insights', latency: 1980 },
  { node: 'Report', latency: 1220 },
];

export default function AnalyticsPage() {
  const { data: projects } = useProjects();
  const { projectId } = useSelectedProject();
  const { data: chats } = useChats(projectId ?? undefined);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
          Analytics
        </h1>
        <p className="text-sm text-slate-500">
          Aggregate usage, cost, and performance across your workspace.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total queries"
          value={120}
          icon={Activity}
          accent="brand"
          delta={14}
          hint="this week"
        />
        <StatCard
          label="Tokens used"
          value="447K"
          icon={Cpu}
          accent="violet"
          delta={9}
          hint="this week"
        />
        <StatCard
          label="Total cost"
          value="$4.72"
          icon={Coins}
          accent="emerald"
          delta={-2}
          hint="this week"
        />
        <StatCard
          label="Avg latency"
          value="1.2s"
          icon={Gauge}
          accent="amber"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader
            title="Query volume"
            subtitle="Questions asked per day"
          />
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={usageByDay}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(148,163,184,0.2)"
              />
              <XAxis dataKey="day" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="queries" fill="#3366ff" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <CardHeader title="Token usage" subtitle="Tokens consumed per day" />
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={usageByDay}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(148,163,184,0.2)"
              />
              <XAxis dataKey="day" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Line
                type="monotone"
                dataKey="tokens"
                stroke="#8b5cf6"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <CardHeader title="Cost by model" subtitle="Spend distribution" />
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Pie
                data={costByModel}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={100}
                paddingAngle={2}
              >
                {costByModel.map((_, i) => (
                  <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <CardHeader
            title="Latency by agent node"
            subtitle="Average execution time (ms)"
          />
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={latencyByNode} layout="vertical">
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(148,163,184,0.2)"
              />
              <XAxis type="number" tick={{ fontSize: 12 }} />
              <YAxis
                type="category"
                dataKey="node"
                width={80}
                tick={{ fontSize: 12 }}
              />
              <Tooltip />
              <Bar dataKey="latency" fill="#00b8a9" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <p className="text-xs text-slate-400">
        Showing aggregate metrics
        {projectId
          ? ` for the selected project (${chats?.length ?? 0} conversations).`
          : ` across ${projects?.length ?? 0} projects.`}
      </p>
    </div>
  );
}

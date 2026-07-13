import { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import {
  Database,
  Lightbulb,
  ListChecks,
  FileDown,
  BarChart3,
  Sigma,
  ThumbsUp,
  ThumbsDown,
} from 'lucide-react';
import { Artifacts } from '@/types';
import ChartRenderer from '@/components/charts/ChartRenderer';
import Badge from '@/components/common/Badge';
import { reportService } from '@/services/reportService';
import { feedbackService } from '@/services/feedbackService';

interface MessageArtifactsProps {
  artifacts: Artifacts;
  messageId: string;
}

function Section({
  icon,
  title,
  children,
}: {
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="surface mt-3 rounded-xl p-4 shadow-card">
      <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-800 dark:text-slate-100">
        {icon}
        {title}
      </div>
      {children}
    </div>
  );
}

function StatisticsTable({ stats }: { stats: Record<string, unknown> }) {
  const entries = Object.entries(stats);
  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-xs">
        <tbody>
          {entries.map(([key, value]) => (
            <tr
              key={key}
              className="border-b border-slate-100 last:border-0 dark:border-slate-800"
            >
              <td className="py-1.5 pr-4 font-medium text-slate-600 dark:text-slate-300">
                {key}
              </td>
              <td className="py-1.5 font-mono text-slate-800 dark:text-slate-100">
                {typeof value === 'object'
                  ? JSON.stringify(value)
                  : String(value)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function MessageArtifacts({
  artifacts,
  messageId,
}: MessageArtifactsProps) {
  const [feedback, setFeedback] = useState<number | null>(null);
  const { sql, charts, statistics, insights, recommendations, report } =
    artifacts;

  const hasAny =
    sql || charts?.length || statistics || insights || recommendations?.length || report;
  if (!hasAny) return null;

  const submitFeedback = async (rating: number) => {
    setFeedback(rating);
    try {
      await feedbackService.submit({ message_id: messageId, rating });
    } catch {
      // Non-blocking; keep optimistic state.
    }
  };

  return (
    <div className="mt-1 w-full">
      {sql && (
        <Section
          icon={<Database className="h-4 w-4 text-brand-600" />}
          title="Generated SQL"
        >
          <SyntaxHighlighter
            style={oneDark}
            language="sql"
            customStyle={{ borderRadius: 8, fontSize: 12.5, margin: 0 }}
          >
            {sql}
          </SyntaxHighlighter>
        </Section>
      )}

      {charts && charts.length > 0 && (
        <Section
          icon={<BarChart3 className="h-4 w-4 text-brand-600" />}
          title="Visualizations"
        >
          <div className="grid grid-cols-1 gap-6">
            {charts.map((chart, i) => (
              <div key={i}>
                <p className="mb-2 text-xs font-medium text-slate-500 dark:text-slate-400">
                  {chart.title}
                </p>
                <ChartRenderer spec={chart} />
              </div>
            ))}
          </div>
        </Section>
      )}

      {statistics && Object.keys(statistics).length > 0 && (
        <Section
          icon={<Sigma className="h-4 w-4 text-brand-600" />}
          title="Statistics"
        >
          <StatisticsTable stats={statistics} />
        </Section>
      )}

      {insights && (
        <Section
          icon={<Lightbulb className="h-4 w-4 text-amber-500" />}
          title="Insights"
        >
          {insights.executive_summary && (
            <p className="mb-3 text-sm text-slate-700 dark:text-slate-300">
              {insights.executive_summary}
            </p>
          )}
          {insights.key_findings?.length > 0 && (
            <div className="mb-3">
              <p className="mb-1 text-xs font-semibold uppercase text-slate-400">
                Key findings
              </p>
              <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700 dark:text-slate-300">
                {insights.key_findings.map((f, i) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
            </div>
          )}
          {insights.root_cause && (
            <p className="mb-3 text-sm text-slate-700 dark:text-slate-300">
              <span className="font-semibold">Root cause: </span>
              {insights.root_cause}
            </p>
          )}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {insights.risks?.length > 0 && (
              <div>
                <p className="mb-1 text-xs font-semibold uppercase text-red-500">
                  Risks
                </p>
                <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700 dark:text-slate-300">
                  {insights.risks.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            )}
            {insights.opportunities?.length > 0 && (
              <div>
                <p className="mb-1 text-xs font-semibold uppercase text-emerald-600">
                  Opportunities
                </p>
                <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700 dark:text-slate-300">
                  {insights.opportunities.map((o, i) => (
                    <li key={i}>{o}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </Section>
      )}

      {recommendations && recommendations.length > 0 && (
        <Section
          icon={<ListChecks className="h-4 w-4 text-emerald-600" />}
          title="Recommendations"
        >
          <div className="space-y-3">
            {recommendations.map((rec, i) => (
              <div
                key={i}
                className="rounded-lg border border-slate-200 p-3 dark:border-slate-800"
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium text-slate-800 dark:text-slate-100">
                    {rec.title}
                  </p>
                  <div className="flex shrink-0 gap-1.5">
                    <Badge tone="info">Impact: {rec.impact}</Badge>
                    <Badge tone="warning">Effort: {rec.effort}</Badge>
                  </div>
                </div>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                  {rec.detail}
                </p>
              </div>
            ))}
          </div>
        </Section>
      )}

      {report && (
        <Section
          icon={<FileDown className="h-4 w-4 text-brand-600" />}
          title="Report"
        >
          <a
            href={reportService.downloadUrl(report.report_id)}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-3 py-2 text-sm font-medium text-white hover:bg-brand-700"
          >
            <FileDown className="h-4 w-4" />
            Download {report.format?.toUpperCase()} report
          </a>
        </Section>
      )}

      <div className="mt-2 flex items-center gap-2 pl-1">
        <span className="text-xs text-slate-400">Was this helpful?</span>
        <button
          onClick={() => submitFeedback(1)}
          className={`rounded p-1 hover:bg-slate-100 dark:hover:bg-slate-800 ${
            feedback === 1 ? 'text-emerald-600' : 'text-slate-400'
          }`}
          aria-label="Helpful"
        >
          <ThumbsUp className="h-3.5 w-3.5" />
        </button>
        <button
          onClick={() => submitFeedback(0)}
          className={`rounded p-1 hover:bg-slate-100 dark:hover:bg-slate-800 ${
            feedback === 0 ? 'text-red-500' : 'text-slate-400'
          }`}
          aria-label="Not helpful"
        >
          <ThumbsDown className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}

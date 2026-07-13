import { Clock, Coins, Cpu } from 'lucide-react';
import { TraceSummary } from '@/types';
import Badge from '@/components/common/Badge';

const statusTone = (status: TraceSummary['status']) => {
  switch (status) {
    case 'success':
      return 'success' as const;
    case 'error':
      return 'danger' as const;
    case 'running':
      return 'info' as const;
    default:
      return 'neutral' as const;
  }
};

export default function TraceView({ trace }: { trace: TraceSummary }) {
  const maxLatency =
    trace.spans && trace.spans.length > 0
      ? Math.max(...trace.spans.map((s) => s.latency_ms), 1)
      : 1;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="surface flex items-center gap-3 rounded-xl p-4 shadow-card">
          <Clock className="h-5 w-5 text-brand-600" />
          <div>
            <p className="text-xs text-slate-400">Total latency</p>
            <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              {trace.total_latency_ms} ms
            </p>
          </div>
        </div>
        <div className="surface flex items-center gap-3 rounded-xl p-4 shadow-card">
          <Cpu className="h-5 w-5 text-violet-600" />
          <div>
            <p className="text-xs text-slate-400">Total tokens</p>
            <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              {trace.total_tokens.toLocaleString()}
            </p>
          </div>
        </div>
        <div className="surface flex items-center gap-3 rounded-xl p-4 shadow-card">
          <Coins className="h-5 w-5 text-emerald-600" />
          <div>
            <p className="text-xs text-slate-400">Total cost</p>
            <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              ${trace.total_cost_usd.toFixed(4)}
            </p>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-xs text-slate-400">
          Trace {trace.trace_id.slice(0, 12)}
        </span>
        <Badge tone={statusTone(trace.status)}>{trace.status}</Badge>
      </div>

      {trace.spans && trace.spans.length > 0 && (
        <div className="surface rounded-xl p-4 shadow-card">
          <p className="mb-3 text-sm font-semibold text-slate-800 dark:text-slate-100">
            Span timeline
          </p>
          <div className="space-y-2">
            {trace.spans.map((span) => (
              <div key={span.span_id} className="flex items-center gap-3">
                <div className="w-40 shrink-0 truncate text-xs text-slate-600 dark:text-slate-300">
                  {span.name}
                </div>
                <div className="h-4 flex-1 overflow-hidden rounded bg-slate-100 dark:bg-slate-800">
                  <div
                    className={`h-full rounded ${
                      span.status === 'error'
                        ? 'bg-red-500'
                        : 'bg-brand-500'
                    }`}
                    style={{
                      width: `${Math.max(
                        (span.latency_ms / maxLatency) * 100,
                        4
                      )}%`,
                    }}
                  />
                </div>
                <div className="w-20 shrink-0 text-right text-xs text-slate-500">
                  {span.latency_ms} ms
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

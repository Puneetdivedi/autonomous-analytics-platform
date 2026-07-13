import { AgentExecution } from '@/types';
import Badge from '@/components/common/Badge';

const statusTone: Record<
  AgentExecution['status'],
  'success' | 'danger' | 'info' | 'warning' | 'neutral'
> = {
  success: 'success',
  error: 'danger',
  running: 'info',
  retrying: 'warning',
  pending: 'neutral',
};

export default function ExecutionRow({ exec }: { exec: AgentExecution }) {
  const totalTokens = exec.prompt_tokens + exec.completion_tokens;
  return (
    <tr className="border-b border-slate-100 dark:border-slate-800/60">
      <td className="px-3 py-2">
        <div className="font-medium text-slate-800 dark:text-slate-100">
          {exec.node_name}
        </div>
        <div className="text-xs text-slate-400">{exec.agent_name}</div>
      </td>
      <td className="px-3 py-2">
        <Badge tone={statusTone[exec.status] ?? 'neutral'}>{exec.status}</Badge>
      </td>
      <td className="px-3 py-2 text-slate-600 dark:text-slate-300">
        {exec.attempt}
      </td>
      <td className="px-3 py-2 text-slate-600 dark:text-slate-300">
        {exec.latency_ms} ms
      </td>
      <td className="px-3 py-2 text-slate-600 dark:text-slate-300">
        {totalTokens.toLocaleString()}
        <span className="ml-1 text-xs text-slate-400">
          ({exec.prompt_tokens}/{exec.completion_tokens})
        </span>
      </td>
      <td className="px-3 py-2 text-slate-600 dark:text-slate-300">
        ${exec.cost_usd.toFixed(4)}
      </td>
      <td className="px-3 py-2">
        {exec.error ? (
          <span className="text-xs text-red-500">{exec.error}</span>
        ) : (
          <span className="text-xs text-slate-400">—</span>
        )}
      </td>
    </tr>
  );
}

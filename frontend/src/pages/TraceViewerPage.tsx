import { FormEvent, useState } from 'react';
import { Activity, Search } from 'lucide-react';
import { useAgentExecutions } from '@/hooks/useAgentExecutions';
import { useTraceByMessage } from '@/hooks/useTraces';
import Card, { CardHeader } from '@/components/common/Card';
import Input from '@/components/common/Input';
import Button from '@/components/common/Button';
import Spinner from '@/components/common/Spinner';
import EmptyState from '@/components/common/EmptyState';
import ExecutionRow from '@/components/traces/ExecutionRow';
import TraceView from '@/components/traces/TraceView';

export default function TraceViewerPage() {
  const [input, setInput] = useState('');
  const [messageId, setMessageId] = useState<string | undefined>(undefined);

  const {
    data: executions,
    isLoading: execLoading,
    isError: execError,
  } = useAgentExecutions(messageId);
  const { data: trace } = useTraceByMessage(messageId);

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    setMessageId(input.trim() || undefined);
  };

  const totals = executions?.reduce(
    (acc, e) => {
      acc.tokens += e.prompt_tokens + e.completion_tokens;
      acc.cost += e.cost_usd;
      acc.latency += e.latency_ms;
      return acc;
    },
    { tokens: 0, cost: 0, latency: 0 }
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
          Trace Viewer
        </h1>
        <p className="text-sm text-slate-500">
          Inspect agent executions, latency, token usage, and cost for a
          message.
        </p>
      </div>

      <Card>
        <form onSubmit={onSubmit} className="flex items-end gap-3">
          <div className="flex-1">
            <Input
              label="Message ID"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Paste a message ID to inspect its execution trace"
            />
          </div>
          <Button type="submit">
            <Search className="h-4 w-4" /> Inspect
          </Button>
        </form>
      </Card>

      {!messageId ? (
        <EmptyState
          icon={Activity}
          title="No trace selected"
          description="Enter a message ID above to view its agent execution timeline and cost breakdown."
        />
      ) : (
        <>
          {trace && <TraceView trace={trace} />}

          <Card padded={false}>
            <div className="p-5">
              <CardHeader
                title="Agent executions"
                subtitle={
                  totals
                    ? `${executions?.length ?? 0} nodes • ${totals.tokens.toLocaleString()} tokens • $${totals.cost.toFixed(4)} • ${totals.latency} ms`
                    : undefined
                }
              />
            </div>
            {execLoading ? (
              <div className="p-6">
                <Spinner label="Loading executions..." />
              </div>
            ) : execError ? (
              <div className="p-6">
                <EmptyState
                  icon={Activity}
                  title="Could not load executions"
                  description="No execution data found for this message ID."
                />
              </div>
            ) : !executions || executions.length === 0 ? (
              <div className="p-6">
                <EmptyState
                  icon={Activity}
                  title="No executions"
                  description="This message has no recorded agent executions."
                />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 dark:border-slate-800">
                      {[
                        'Node / Agent',
                        'Status',
                        'Attempt',
                        'Latency',
                        'Tokens',
                        'Cost',
                        'Error',
                      ].map((h) => (
                        <th
                          key={h}
                          className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400"
                        >
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {executions.map((exec, i) => (
                      <ExecutionRow key={`${exec.node_name}-${i}`} exec={exec} />
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  );
}

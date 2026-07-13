import clsx from 'clsx';
import { CheckCircle2, Loader2, AlertCircle, Circle } from 'lucide-react';
import { NodeEvent } from '@/hooks/useChatStream';

interface AgentTimelineProps {
  events: NodeEvent[];
  active?: boolean;
}

const prettyNode = (node: string) =>
  node
    .replace(/[_-]/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());

export default function AgentTimeline({ events, active }: AgentTimelineProps) {
  if (events.length === 0) {
    return (
      <p className="text-xs text-slate-400">
        {active ? 'Initializing agent pipeline...' : 'No agent activity yet.'}
      </p>
    );
  }

  return (
    <ol className="space-y-2">
      {events.map((event, i) => (
        <li key={`${event.node}-${i}`} className="flex items-center gap-2">
          {event.status === 'done' ? (
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          ) : event.status === 'error' ? (
            <AlertCircle className="h-4 w-4 text-red-500" />
          ) : event.status === 'running' ? (
            <Loader2 className="h-4 w-4 animate-spin text-brand-500" />
          ) : (
            <Circle className="h-4 w-4 text-slate-300" />
          )}
          <span
            className={clsx(
              'text-xs',
              event.status === 'running'
                ? 'font-medium text-slate-800 dark:text-slate-100'
                : 'text-slate-500 dark:text-slate-400'
            )}
          >
            {prettyNode(event.node)}
          </span>
        </li>
      ))}
    </ol>
  );
}

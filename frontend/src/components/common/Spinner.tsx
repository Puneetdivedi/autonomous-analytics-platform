import clsx from 'clsx';
import { Loader2 } from 'lucide-react';

interface SpinnerProps {
  className?: string;
  label?: string;
  fullscreen?: boolean;
}

export default function Spinner({ className, label, fullscreen }: SpinnerProps) {
  const content = (
    <div className="flex flex-col items-center justify-center gap-2 text-slate-500 dark:text-slate-400">
      <Loader2 className={clsx('h-6 w-6 animate-spin', className)} />
      {label && <span className="text-sm">{label}</span>}
    </div>
  );

  if (fullscreen) {
    return (
      <div className="flex h-full min-h-[50vh] w-full items-center justify-center">
        {content}
      </div>
    );
  }
  return content;
}

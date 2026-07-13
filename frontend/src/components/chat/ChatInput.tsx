import { KeyboardEvent, useRef, useState } from 'react';
import { Send, Paperclip, Square, X } from 'lucide-react';
import clsx from 'clsx';
import { DataSource } from '@/types';

interface ChatInputProps {
  onSend: (question: string) => void;
  onUpload?: (file: File) => void;
  onStop?: () => void;
  disabled?: boolean;
  streaming?: boolean;
  datasources?: DataSource[];
  selectedDatasourceId?: string;
  onSelectDatasource?: (id: string | undefined) => void;
}

export default function ChatInput({
  onSend,
  onUpload,
  onStop,
  disabled,
  streaming,
  datasources,
  selectedDatasourceId,
  onSelectDatasource,
}: ChatInputProps) {
  const [value, setValue] = useState('');
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const submit = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    if (pendingFile && onUpload) {
      onUpload(pendingFile);
      setPendingFile(null);
    }
    onSend(trimmed);
    setValue('');
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="border-t border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
      {(datasources?.length || pendingFile) && (
        <div className="mb-2 flex flex-wrap items-center gap-2">
          {datasources && datasources.length > 0 && (
            <select
              value={selectedDatasourceId ?? ''}
              onChange={(e) =>
                onSelectDatasource?.(e.target.value || undefined)
              }
              className="rounded-lg border border-slate-300 bg-white px-2 py-1 text-xs text-slate-600 focus:outline-none focus:ring-2 focus:ring-brand-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
            >
              <option value="">Auto-select data source</option>
              {datasources.map((ds) => (
                <option key={ds.id} value={ds.id}>
                  {ds.name}
                </option>
              ))}
            </select>
          )}
          {pendingFile && (
            <span className="inline-flex items-center gap-1 rounded-full bg-brand-50 px-2 py-1 text-xs text-brand-700 dark:bg-brand-900/30 dark:text-brand-300">
              {pendingFile.name}
              <button
                onClick={() => setPendingFile(null)}
                aria-label="Remove file"
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          )}
        </div>
      )}

      <div className="flex items-end gap-2">
        {onUpload && (
          <>
            <button
              onClick={() => fileRef.current?.click()}
              className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800"
              aria-label="Attach file"
              type="button"
            >
              <Paperclip className="h-5 w-5" />
            </button>
            <input
              ref={fileRef}
              type="file"
              className="hidden"
              accept=".csv,.xlsx,.xls,.json,.parquet"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) setPendingFile(file);
                e.target.value = '';
              }}
            />
          </>
        )}

        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={onKeyDown}
          rows={1}
          placeholder="Ask a question about your data..."
          className="max-h-40 min-h-[44px] flex-1 resize-none rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-brand-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
        />

        {streaming ? (
          <button
            onClick={onStop}
            className="flex h-11 items-center gap-1.5 rounded-lg bg-slate-200 px-4 text-sm font-medium text-slate-700 hover:bg-slate-300 dark:bg-slate-700 dark:text-slate-100"
            type="button"
          >
            <Square className="h-4 w-4" /> Stop
          </button>
        ) : (
          <button
            onClick={submit}
            disabled={disabled || !value.trim()}
            className={clsx(
              'flex h-11 items-center gap-1.5 rounded-lg px-4 text-sm font-medium text-white transition-colors',
              'bg-brand-600 hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50'
            )}
            type="button"
          >
            <Send className="h-4 w-4" /> Send
          </button>
        )}
      </div>
    </div>
  );
}

import { FileText, Download } from 'lucide-react';
import { Report } from '@/types';
import Badge from '@/components/common/Badge';
import { reportService } from '@/services/reportService';

export default function ReportCard({ report }: { report: Report }) {
  const created = report.created_at
    ? new Date(report.created_at).toLocaleString()
    : '';

  return (
    <div className="surface flex items-center justify-between rounded-xl p-4 shadow-card">
      <div className="flex min-w-0 items-center gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-900/30 dark:text-brand-300">
          <FileText className="h-5 w-5" />
        </div>
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-slate-800 dark:text-slate-100">
            {report.title || `Report ${report.id.slice(0, 8)}`}
          </p>
          <div className="mt-1 flex items-center gap-2">
            <Badge tone="brand">{report.format?.toUpperCase()}</Badge>
            <span className="text-xs text-slate-400">{created}</span>
          </div>
        </div>
      </div>
      <a
        href={reportService.downloadUrl(report.id)}
        target="_blank"
        rel="noreferrer"
        className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
      >
        <Download className="h-4 w-4" /> Download
      </a>
    </div>
  );
}

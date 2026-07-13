import { FileText } from 'lucide-react';
import { useReports } from '@/hooks/useReports';
import { useSelectedProject } from '@/hooks/useSelectedProject';
import ReportCard from '@/components/reports/ReportCard';
import Spinner from '@/components/common/Spinner';
import EmptyState from '@/components/common/EmptyState';

export default function ReportsPage() {
  const { projectId } = useSelectedProject();
  const { data: reports, isLoading, isError } = useReports(
    projectId ?? undefined
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
          Reports
        </h1>
        <p className="text-sm text-slate-500">
          Generated analytics reports for the selected project.
        </p>
      </div>

      {!projectId ? (
        <EmptyState
          icon={FileText}
          title="Select a project"
          description="Choose an active project from the top bar to view its reports."
        />
      ) : isLoading ? (
        <Spinner fullscreen label="Loading reports..." />
      ) : isError ? (
        <EmptyState
          icon={FileText}
          title="Could not load reports"
          description="Something went wrong while fetching reports. Please try again."
        />
      ) : !reports || reports.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No reports yet"
          description="Reports generated from your analyses will appear here."
        />
      ) : (
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          {reports.map((r) => (
            <ReportCard key={r.id} report={r} />
          ))}
        </div>
      )}
    </div>
  );
}

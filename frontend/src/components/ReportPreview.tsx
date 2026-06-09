import type { Report } from "../api/types";

interface ReportPreviewProps {
  report: Report | null;
}

export function ReportPreview({ report }: ReportPreviewProps) {
  return (
    <pre className="report-preview">{report?.markdown || "No report persisted for this run."}</pre>
  );
}

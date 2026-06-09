import type { Report } from "../api/types";

interface ReportPreviewProps {
  report: Report | null;
}

export function ReportPreview({ report }: ReportPreviewProps) {
  return (
    <pre className="report-preview">{report?.markdown || "当前运行暂无持久化报告。"}</pre>
  );
}

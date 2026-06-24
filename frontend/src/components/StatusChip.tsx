interface StatusChipProps {
  children: string;
  tone?: "neutral" | "success" | "warning" | "danger";
}

export function StatusChip({ children, tone = "neutral" }: StatusChipProps) {
  return <span className={`status-chip status-chip--${tone}`}>{children}</span>;
}

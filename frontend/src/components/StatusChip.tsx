interface StatusChipProps {
  children: string;
}

export function StatusChip({ children }: StatusChipProps) {
  return <span className="status-chip">{children}</span>;
}

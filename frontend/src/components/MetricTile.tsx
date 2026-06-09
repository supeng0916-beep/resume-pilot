import type { ReactNode } from "react";

interface MetricTileProps {
  icon: ReactNode;
  label: string;
  value: string | number;
}

export function MetricTile({ icon, label, value }: MetricTileProps) {
  return (
    <article className="metric-tile">
      {icon}
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

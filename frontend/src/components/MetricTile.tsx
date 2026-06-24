import type { ReactNode } from "react";

interface MetricTileProps {
  icon: ReactNode;
  label: string;
  value: string | number;
  hint?: string;
}

export function MetricTile({ icon, label, value, hint }: MetricTileProps) {
  return (
    <article className="metric-tile">
      <div className="metric-tile__icon">{icon}</div>
      <div>
        <span>{label}</span>
        {hint ? <p>{hint}</p> : null}
      </div>
      <strong>{value}</strong>
    </article>
  );
}

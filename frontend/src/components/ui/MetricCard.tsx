import type { ReactNode } from "react";

type MetricCardProps = {
  label: string;
  value: number | string;
  helper?: string;
  icon?: ReactNode;
};

export function MetricCard({ label, value, helper, icon }: MetricCardProps) {
  return (
    <article className="metric-card">
      <div className="metric-card__top">
        <span>{label}</span>
        {icon ? <span className="metric-card__icon">{icon}</span> : null}
      </div>
      <strong>{value}</strong>
      {helper ? <small>{helper}</small> : null}
    </article>
  );
}

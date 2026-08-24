import type { ReactNode } from "react";

export type TabItem = {
  value: string;
  label: string;
  icon?: ReactNode;
};

type TabsProps = {
  items: TabItem[];
  value: string;
  onChange: (value: string) => void;
  label: string;
};

export function Tabs({ items, value, onChange, label }: TabsProps) {
  return (
    <div className="ui-tabs" role="tablist" aria-label={label}>
      {items.map((item) => (
        <button
          aria-selected={item.value === value}
          className="ui-tab"
          key={item.value}
          onClick={() => onChange(item.value)}
          role="tab"
          type="button"
        >
          {item.icon ? <span className="ui-tab__icon">{item.icon}</span> : null}
          <span>{item.label}</span>
        </button>
      ))}
    </div>
  );
}

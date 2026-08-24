import type { LucideIcon } from "lucide-react";

export type AppTab = "today" | "catalog" | "guide" | "island";

export type BottomNavItem = {
  value: AppTab;
  label: string;
  icon: LucideIcon;
};

type BottomNavigationProps = {
  items: BottomNavItem[];
  value: AppTab;
  onChange: (value: AppTab) => void;
};

export function BottomNavigation({ items, value, onChange }: BottomNavigationProps) {
  return (
    <nav className="bottom-nav" aria-label="하단 메뉴">
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <button
            className={item.value === value ? "is-active" : ""}
            key={item.value}
            onClick={() => onChange(item.value)}
            type="button"
          >
            <Icon aria-hidden="true" size={18} />
            <span>{item.label}</span>
          </button>
        );
      })}
    </nav>
  );
}

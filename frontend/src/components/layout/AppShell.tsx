import type { LucideIcon } from "lucide-react";
import { Leaf } from "lucide-react";
import type { ReactNode } from "react";

export type NavItem = {
  key: string;
  label: string;
  icon: LucideIcon;
};

type AppShellProps = {
  navItems: NavItem[];
  activeKey?: string;
  onNavigate?: (key: string) => void;
  children: ReactNode;
};

export function AppShell({ navItems, activeKey, onNavigate, children }: AppShellProps) {
  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Primary navigation">
        <div className="brand">
          <Leaf aria-hidden="true" />
          <span>ACNH Diary</span>
        </div>
        <nav className="nav-list">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                aria-current={item.key === activeKey ? "page" : undefined}
                className={item.key === activeKey ? "nav-button is-active" : "nav-button"}
                key={item.key}
                onClick={() => onNavigate?.(item.key)}
                type="button"
                title={item.label}
              >
                <Icon aria-hidden="true" size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>
      {children}
    </div>
  );
}

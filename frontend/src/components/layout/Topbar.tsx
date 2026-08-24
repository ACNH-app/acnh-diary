import type { ReactNode } from "react";

type TopbarProps = {
  eyebrow?: string;
  title: string;
  action?: ReactNode;
};

export function Topbar({ eyebrow, title, action }: TopbarProps) {
  return (
    <header className="topbar">
      <div>
        {eyebrow ? <p className="ui-eyebrow">{eyebrow}</p> : null}
        <h1>{title}</h1>
      </div>
      {action ? <div className="topbar__action">{action}</div> : null}
    </header>
  );
}

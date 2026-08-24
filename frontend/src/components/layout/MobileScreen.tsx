import type { ReactNode } from "react";

type MobileScreenProps = {
  title: string;
  subtitle: string;
  action?: ReactNode;
  children: ReactNode;
  footer: ReactNode;
  tone?: "green" | "blue" | "rose" | "yellow";
};

export function MobileScreen({ title, subtitle, action, children, footer, tone = "green" }: MobileScreenProps) {
  return (
    <section className={`phone-frame app-phone app-phone--${tone}`} aria-label={title}>
      <header className="screen-header">
        <div>
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
        {action}
      </header>
      <div className="screen-content">{children}</div>
      {footer}
    </section>
  );
}

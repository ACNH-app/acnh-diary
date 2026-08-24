import type { HTMLAttributes, ReactNode } from "react";

type PillTone = "mint" | "sun" | "sky" | "violet" | "leaf" | "rose" | "neutral";

type PillProps = HTMLAttributes<HTMLSpanElement> & {
  tone?: PillTone;
  icon?: ReactNode;
};

export function Pill({ className = "", tone = "neutral", icon, children, ...props }: PillProps) {
  const classes = ["pill", `pill--${tone}`, className].filter(Boolean).join(" ");

  return (
    <span className={classes} {...props}>
      {icon ? <span className="pill__icon">{icon}</span> : null}
      {children}
    </span>
  );
}

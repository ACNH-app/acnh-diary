import type { HTMLAttributes, ReactNode } from "react";

type CardProps = HTMLAttributes<HTMLElement> & {
  as?: "article" | "section" | "div";
  eyebrow?: string;
  title?: string;
  action?: ReactNode;
};

export function Card({
  as: Component = "article",
  className = "",
  eyebrow,
  title,
  action,
  children,
  ...props
}: CardProps) {
  const classes = ["ui-card", className].filter(Boolean).join(" ");

  return (
    <Component className={classes} {...props}>
      {eyebrow || title || action ? (
        <div className="ui-card__header">
          <div>
            {eyebrow ? <p className="ui-eyebrow">{eyebrow}</p> : null}
            {title ? <h2 className="ui-card__title">{title}</h2> : null}
          </div>
          {action ? <div className="ui-card__action">{action}</div> : null}
        </div>
      ) : null}
      {children}
    </Component>
  );
}

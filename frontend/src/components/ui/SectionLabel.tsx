type SectionLabelTone = "orange" | "green" | "yellow" | "blue" | "indigo" | "rose";

type SectionLabelProps = {
  children: string;
  tone?: SectionLabelTone;
};

export function SectionLabel({ children, tone = "green" }: SectionLabelProps) {
  return <div className={`section-label section-label--${tone}`}>{children}</div>;
}

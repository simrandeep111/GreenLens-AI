interface ReportSectionProps {
  id: string;
  num: string;
  eyebrow: string;
  title: string;
  children: React.ReactNode;
}

export default function ReportSection({ id, num, eyebrow, title, children }: ReportSectionProps) {
  return (
    <div className="report-section" id={`section-${id}`}>
      <div className="report-section-eyebrow">
        <div className="report-section-num">{num}</div>
        {eyebrow}
      </div>
      <h2 className="report-section-title">{title}</h2>
      {children}
    </div>
  );
}

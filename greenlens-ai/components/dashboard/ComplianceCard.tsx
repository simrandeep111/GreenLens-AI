import { ComplianceItem } from '@/lib/types';

interface ComplianceCardProps {
  items: ComplianceItem[];
  readinessPct: number;
}

function getIcon(status: ComplianceItem['status']) {
  if (status === 'pass') {
    return (
      <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.2">
        <path d="M3 8l3 3 7-7"/>
      </svg>
    );
  }

  if (status === 'warn') {
    return (
      <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M8 3l6 10H2L8 3z"/><path d="M8 7v3M8 12h.01"/>
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.2">
      <path d="M4 4l8 8M12 4l-8 8"/>
    </svg>
  );
}

export default function ComplianceCard({ items, readinessPct }: ComplianceCardProps) {
  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">Compliance &amp; Regulatory Readiness</span>
        <span className="card-meta">{items.length} frameworks assessed · {readinessPct}% ready</span>
      </div>
      <div className="card-body">
        <div className="compliance-status">
          {items.map((item) => (
            <div className="comp-item" key={item.framework}>
              <div className={`comp-icon ${item.status}`}>{getIcon(item.status)}</div>
              <div>
                <div className="comp-name">{item.framework}</div>
                <div className="comp-detail">{item.detail}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

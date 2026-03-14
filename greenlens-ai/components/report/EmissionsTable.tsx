import { EmissionEntry } from '@/lib/types';

interface EmissionsTableProps {
  breakdown: EmissionEntry[];
  total: number;
}

function getScopeColor(scope: string): string {
  if (scope === 'Scope 1') {
    return 'var(--accent)';
  }

  if (scope === 'Scope 2') {
    return 'var(--accent-mid)';
  }

  return 'var(--text-tertiary)';
}

export default function EmissionsTable({ breakdown, total }: EmissionsTableProps) {
  return (
    <div className="report-data-table emissions-table">
      <div className="rdt-header" style={{ gridTemplateColumns: '2fr 1.2fr 1fr 1fr' }}>
        <span>Category</span>
        <span>Scope</span>
        <span>tCO₂e</span>
        <span>% of Total</span>
      </div>
      {breakdown.map((row) => (
        <div key={`${row.category}-${row.scope}`} className="rdt-row" style={{ gridTemplateColumns: '2fr 1.2fr 1fr 1fr' }}>
          <span>{row.category}</span>
          <span style={{ color: getScopeColor(row.scope), fontWeight: 500 }}>{row.scope}</span>
          <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '12.5px' }}>{row.tCO2e.toFixed(1)}</span>
          <span>{row.percentOfTotal.toFixed(1)}%</span>
        </div>
      ))}
      <div className="rdt-row" style={{ gridTemplateColumns: '2fr 1.2fr 1fr 1fr', fontWeight: 600, borderTop: '1.5px solid var(--border)' }}>
        <span>Total</span>
        <span></span>
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: '12.5px' }}>{total.toFixed(1)}</span>
        <span>100%</span>
      </div>
    </div>
  );
}

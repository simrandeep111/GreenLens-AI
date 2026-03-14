import { Recommendation } from '@/lib/types';

interface RecommendationListProps {
  recommendations: Recommendation[];
}

export default function RecommendationList({ recommendations }: RecommendationListProps) {
  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">Priority Recommendations</span>
      </div>
      <div className="card-body" style={{ paddingTop: '4px' }}>
        <div className="rec-list">
          {recommendations.map((rec, i) => (
            <div className="rec-item" key={i}>
              <div className="rec-num">{i + 1}</div>
              <div>
                <div className="rec-text">{rec.text}</div>
                <div className="rec-impact">
                  <svg viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M6 9V3M3 6l3-3 3 3"/>
                  </svg>
                  {rec.impactLabel}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

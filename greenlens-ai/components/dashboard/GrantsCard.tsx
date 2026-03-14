import { Grant } from '@/lib/types';

interface GrantsCardProps {
  grants: Grant[];
}

export default function GrantsCard({ grants }: GrantsCardProps) {
  return (
    <div className="card">
      <div className="card-header">
        <span className="card-title">Matched Funding Programs</span>
        <span className="card-meta">{grants.length} eligible</span>
      </div>
      <div className="card-body">
        {grants.map((grant) => (
          <div className="grant-card" key={grant.name}>
            <div className="grant-header">
              <div className="grant-name">{grant.name}</div>
              <div className="grant-amount">{grant.amount}</div>
            </div>
            <div className="grant-desc">{grant.description}</div>
            <div className="grant-tags">
              {grant.tags.map((tag) => (
                <div className="grant-tag" key={tag}>{tag}</div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

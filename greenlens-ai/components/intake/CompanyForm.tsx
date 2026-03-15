import { CompanyData } from '@/lib/types';

interface CompanyFormProps {
  company: CompanyData;
  disabled?: boolean;
  onChange: (company: CompanyData) => void;
}

export default function CompanyForm({ company, disabled = false, onChange }: CompanyFormProps) {
  const updateField = <K extends keyof CompanyData>(key: K, value: CompanyData[K]) => {
    onChange({ ...company, [key]: value });
  };

  return (
    <div className="form-section">
      <div className="form-section-label">
        Company Information
        <div className="form-section-num">1</div>
      </div>
      <div className="form-grid-2" style={{ marginBottom: '16px' }}>
        <div className="form-group">
          <label className="form-label">Legal Business Name</label>
          <input
            className="form-input"
            type="text"
            placeholder="e.g. Maple Leaf Catering Co."
            value={company.name}
            disabled={disabled}
            onChange={(event) => updateField('name', event.target.value)}
          />
        </div>
        <div className="form-group">
          <label className="form-label">Province of Operation</label>
          <select
            className="form-select"
            value={company.province}
            disabled={disabled}
            onChange={(event) => updateField('province', event.target.value)}
          >
            <option value="">Select province</option>
            <option value="Ontario">Ontario</option>
            <option value="British Columbia">British Columbia</option>
            <option value="Alberta">Alberta</option>
            <option value="Quebec">Quebec</option>
          </select>
        </div>
      </div>
      <div className="form-grid-3">
        <div className="form-group">
          <label className="form-label">Industry Sector</label>
          <select
            className="form-select"
            value={company.industry}
            disabled={disabled}
            onChange={(event) => updateField('industry', event.target.value)}
          >
            <option value="">Select industry</option>
            <option value="Food &amp; Beverage">Food &amp; Beverage</option>
            <option value="Technology">Technology</option>
            <option value="Manufacturing">Manufacturing</option>
            <option value="Retail">Retail</option>
          </select>
        </div>
        <div className="form-group">
          <label className="form-label">Number of Employees</label>
          <input
            className="form-input"
            type="number"
            min="1"
            placeholder="e.g. 48"
            value={company.employees || ''}
            disabled={disabled}
            onChange={(event) => updateField('employees', Number(event.target.value) || 0)}
          />
        </div>
        <div className="form-group">
          <label className="form-label">Annual Revenue (CAD)</label>
          <input
            className="form-input"
            type="text"
            placeholder="e.g. $2,400,000"
            value={company.revenue}
            disabled={disabled}
            onChange={(event) => updateField('revenue', event.target.value)}
          />
        </div>
      </div>
    </div>
  );
}

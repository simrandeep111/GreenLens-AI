'use client';

import { ChangeEvent, ReactNode, useRef } from 'react';

interface UploadCardProps {
  csvFile: File | null;
  pdfFiles: File[];
  disabled?: boolean;
  onCsvChange: (file: File | null) => void;
  onPdfChange: (files: File[]) => void;
}

interface UploadZoneProps {
  type: 'csv' | 'pdf';
  title: string;
  subtitle: string;
  badge: 'required' | 'optional';
  addedLabel: string | null;
  icon: ReactNode;
  disabled: boolean;
  onFilesSelected: (files: File[]) => void;
}

function SingleUploadZone({
  type,
  title,
  subtitle,
  badge,
  addedLabel,
  icon,
  disabled,
  onFilesSelected,
}: UploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files ?? []);
    onFilesSelected(files);
  };

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        accept={type === 'csv' ? '.csv,text/csv' : '.pdf,application/pdf'}
        multiple={type === 'pdf'}
        hidden
        onChange={handleChange}
        disabled={disabled}
      />
      <div
        className="upload-zone"
        onClick={() => !disabled && inputRef.current?.click()}
        onKeyDown={(event) => {
          if (!disabled && (event.key === 'Enter' || event.key === ' ')) {
            event.preventDefault();
            inputRef.current?.click();
          }
        }}
        role="button"
        tabIndex={disabled ? -1 : 0}
        style={{ cursor: disabled ? 'not-allowed' : 'pointer', opacity: disabled ? 0.7 : 1 }}
      >
        <div className="upload-icon">{icon}</div>
        <div className="upload-title">{title}</div>
        <div className="upload-sub">{subtitle}</div>
        <span className={`upload-badge ${badge}`}>{badge === 'required' ? 'Required' : 'Optional'}</span>
      </div>
      {addedLabel && (
        <div className="upload-file-added">
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" width="14" height="14">
            <path d="M3 8l3 3 7-7"/>
          </svg>
          {addedLabel}
        </div>
      )}
    </div>
  );
}

function formatSelectedPdfs(files: File[]): string | null {
  if (files.length === 0) {
    return null;
  }

  if (files.length === 1) {
    return files[0].name;
  }

  if (files.length === 2) {
    return `${files[0].name}, ${files[1].name}`;
  }

  return `${files[0].name} + ${files.length - 1} more`;
}

export default function UploadCard({
  csvFile,
  pdfFiles,
  disabled = false,
  onCsvChange,
  onPdfChange,
}: UploadCardProps) {
  return (
    <div className="form-section">
      <div className="form-section-label">
        Document Upload
        <div className="form-section-num">2</div>
      </div>
      <div className="upload-grids">
        <SingleUploadZone
          type="csv"
          title="Financial Data Export"
          subtitle="QuickBooks CSV or equivalent"
          badge="required"
          addedLabel={csvFile?.name ?? null}
          disabled={disabled}
          onFilesSelected={(files) => onCsvChange(files[0] ?? null)}
          icon={
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
              <path d="M3 4a1 1 0 011-1h4l2 2h6a1 1 0 011 1v9a1 1 0 01-1 1H4a1 1 0 01-1-1V4z"/>
              <path d="M10 8v6M7 11l3-3 3 3"/>
            </svg>
          }
        />
        <SingleUploadZone
          type="pdf"
          title="Supporting Documents"
          subtitle="Utility bills, fuel receipts, invoices"
          badge="optional"
          addedLabel={formatSelectedPdfs(pdfFiles)}
          disabled={disabled}
          onFilesSelected={onPdfChange}
          icon={
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
              <path d="M4 2h8l4 4v12a1 1 0 01-1 1H4a1 1 0 01-1-1V3a1 1 0 011-1z"/>
              <path d="M12 2v4h4"/>
            </svg>
          }
        />
      </div>
    </div>
  );
}

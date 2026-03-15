import { normalizeReport } from '@/lib/report';
import { AnalysisSession, CompanyData } from '@/lib/types';

const STORAGE_KEY = 'greenlens-analysis-session';
const CHAT_STORAGE_PREFIX = 'greenlens-report-chat:';
const CHAT_OPEN_PREFIX = 'greenlens-report-chat-open:';

export const DEFAULT_COMPANY: CompanyData = {
  name: '',
  province: '',
  industry: '',
  employees: 0,
  revenue: '',
};

export const DEFAULT_GOVERNANCE_ANSWERS = ['No', 'No', 'No', 'No'];

export function createEmptySession(): AnalysisSession {
  return {
    company: { ...DEFAULT_COMPANY },
    governanceAnswers: [...DEFAULT_GOVERNANCE_ANSWERS],
    csvFileName: null,
    pdfFileNames: [],
    uploadId: null,
    jobId: null,
    status: null,
    report: null,
    backendBootId: null,
  };
}

function hasPersistedAnalysis(session: AnalysisSession): boolean {
  return Boolean(session.uploadId || session.jobId || session.status || session.report);
}

export function loadSession(): AnalysisSession | null {
  if (typeof window === 'undefined') {
    return null;
  }

  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as Partial<AnalysisSession>;
    return {
      ...createEmptySession(),
      ...parsed,
      company: { ...DEFAULT_COMPANY, ...parsed.company },
      governanceAnswers: parsed.governanceAnswers ?? [...DEFAULT_GOVERNANCE_ANSWERS],
      pdfFileNames: parsed.pdfFileNames ?? [],
      report: normalizeReport(parsed.report),
    };
  } catch {
    return null;
  }
}

export function saveSession(session: AnalysisSession): void {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({
      ...session,
      company: { ...DEFAULT_COMPANY, ...session.company },
      governanceAnswers: session.governanceAnswers ?? [...DEFAULT_GOVERNANCE_ANSWERS],
      pdfFileNames: session.pdfFileNames ?? [],
      report: normalizeReport(session.report),
    }),
  );
}

export function updateSession(patch: Partial<AnalysisSession>): AnalysisSession | null {
  const current = loadSession() ?? createEmptySession();
  const next: AnalysisSession = {
    ...current,
    ...patch,
    company: patch.company ? { ...current.company, ...patch.company } : current.company,
    report: patch.report !== undefined ? normalizeReport(patch.report) : current.report,
  };

  saveSession(next);
  return next;
}

export function loadSessionForBackend(backendBootId: string): AnalysisSession | null {
  const stored = loadSession();
  if (!stored) {
    return null;
  }

  if (!stored.backendBootId) {
    if (hasPersistedAnalysis(stored)) {
      clearSession();
      return null;
    }

    return stored;
  }

  if (stored.backendBootId !== backendBootId) {
    clearSession();
    return null;
  }

  return stored;
}

export function clearSession(): void {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.removeItem(STORAGE_KEY);
  Object.keys(window.localStorage)
    .filter((key) => key.startsWith(CHAT_STORAGE_PREFIX))
    .forEach((key) => window.localStorage.removeItem(key));
  Object.keys(window.sessionStorage)
    .filter((key) => key.startsWith(CHAT_OPEN_PREFIX))
    .forEach((key) => window.sessionStorage.removeItem(key));
}

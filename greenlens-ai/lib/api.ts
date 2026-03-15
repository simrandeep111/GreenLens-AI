import { normalizeReport } from '@/lib/report';
import { BackendMeta, CompanyData, JobStatus, ReportChatMessage, ReportChatResponse, ReportResponse } from '@/lib/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://127.0.0.1:8000';

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as { detail?: string };
    return data.detail ?? `Request failed with status ${response.status}`;
  } catch {
    return `Request failed with status ${response.status}`;
  }
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new ApiError(await readErrorMessage(response), response.status);
  }

  return (await response.json()) as T;
}

export async function uploadFiles(input: {
  csvFile: File;
  pdfFiles: File[];
}): Promise<{ uploadId: string }> {
  const formData = new FormData();
  formData.append('csv_file', input.csvFile);

  input.pdfFiles.forEach((file) => {
    formData.append('pdf_files', file);
  });

  return requestJson<{ uploadId: string }>('/api/upload', {
    method: 'POST',
    body: formData,
  });
}

export async function analyzeData(input: {
  uploadId: string;
  company: CompanyData;
  governanceAnswers: string[];
}): Promise<{ jobId: string }> {
  return requestJson<{ jobId: string }>('/api/analyze', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      uploadId: input.uploadId,
      company: input.company,
      governance_answers: input.governanceAnswers,
    }),
  });
}

export async function getAnalysisStatus(jobId: string): Promise<JobStatus> {
  return requestJson<JobStatus>(`/api/status/${jobId}`);
}

export async function getBackendMeta(): Promise<BackendMeta> {
  return requestJson<BackendMeta>('/');
}

export async function getReport(jobId: string): Promise<ReportResponse> {
  const report = await requestJson<Partial<ReportResponse>>(`/api/report/${jobId}`);
  return normalizeReport(report) as ReportResponse;
}

export async function postReportChat(input: {
  jobId: string;
  question: string;
  history: ReportChatMessage[];
}): Promise<ReportChatResponse> {
  return requestJson<ReportChatResponse>(`/api/report-chat/${input.jobId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question: input.question,
      history: input.history.map((message) => ({
        role: message.role,
        content: message.content,
      })),
    }),
  });
}

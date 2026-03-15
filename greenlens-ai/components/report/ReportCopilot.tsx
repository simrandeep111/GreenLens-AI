'use client';

import { FormEvent, KeyboardEvent, useEffect, useMemo, useRef, useState } from 'react';

import { postReportChat } from '@/lib/api';
import { ReportChatMessage } from '@/lib/types';

const SUGGESTED_QUESTIONS = [
  'What are all the categories in Scope 1',
  'Which grant should this company pursue first?',
  'What is the fastest way to improve the ESG score?',
];

function normalizeKey(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
}

function buildChatKey(jobId: string | null, companyName: string) {
  return jobId ? `job-${jobId}` : `company-${normalizeKey(companyName)}`;
}

function buildStorageKey(jobId: string | null, companyName: string) {
  return `greenlens-report-chat:${buildChatKey(jobId, companyName)}`;
}

function buildOpenStateKey(jobId: string | null, companyName: string) {
  return `greenlens-report-chat-open:${buildChatKey(jobId, companyName)}`;
}

function createWelcomeMessage(companyName: string): ReportChatMessage {
  return {
    id: 'welcome',
    role: 'assistant',
    content: `Ask me anything about ${companyName}'s ESG report, emissions drivers, grants, or compliance obligations. I’ll stay grounded in this report and the GreenLens knowledge base.`,
    citations: [],
    answerSource: 'llm',
  };
}

function loadChatHistory(jobId: string | null, companyName: string): ReportChatMessage[] {
  if (typeof window === 'undefined') {
    return [createWelcomeMessage(companyName)];
  }

  const raw = window.localStorage.getItem(buildStorageKey(jobId, companyName));
  if (!raw) {
    return [createWelcomeMessage(companyName)];
  }

  try {
    const parsed = JSON.parse(raw) as ReportChatMessage[];
    return parsed.length > 0 ? parsed : [createWelcomeMessage(companyName)];
  } catch {
    return [createWelcomeMessage(companyName)];
  }
}

function saveChatHistory(jobId: string | null, companyName: string, messages: ReportChatMessage[]) {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.setItem(buildStorageKey(jobId, companyName), JSON.stringify(messages));
}

function loadOpenState(jobId: string | null, companyName: string): boolean {
  if (typeof window === 'undefined') {
    return false;
  }

  return window.sessionStorage.getItem(buildOpenStateKey(jobId, companyName)) === 'open';
}

function saveOpenState(jobId: string | null, companyName: string, isOpen: boolean) {
  if (typeof window === 'undefined') {
    return;
  }

  window.sessionStorage.setItem(buildOpenStateKey(jobId, companyName), isOpen ? 'open' : 'closed');
}

function nextMessageId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

interface ReportCopilotProps {
  jobId: string | null;
  companyName: string;
}

export default function ReportCopilot({ jobId, companyName }: ReportCopilotProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ReportChatMessage[]>(() => [createWelcomeMessage(companyName)]);
  const [draft, setDraft] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const transcriptRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    setMessages(loadChatHistory(jobId, companyName));
    setIsOpen(loadOpenState(jobId, companyName));
  }, [jobId, companyName]);

  useEffect(() => {
    saveChatHistory(jobId, companyName, messages);
  }, [jobId, companyName, messages]);

  useEffect(() => {
    saveOpenState(jobId, companyName, isOpen);
  }, [jobId, companyName, isOpen]);

  useEffect(() => {
    const container = transcriptRef.current;
    if (!container) {
      return;
    }

    container.scrollTop = container.scrollHeight;
  }, [messages, isLoading, isOpen]);

  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
    }
  }, [isOpen]);

  const canSend = Boolean(jobId && draft.trim()) && !isLoading;
  const hasConversation = useMemo(
    () => messages.some((message) => message.role === 'user'),
    [messages],
  );
  const historyForApi = useMemo(
    () => messages.filter((message) => message.id !== 'welcome'),
    [messages],
  );

  const submitQuestion = async (
    question: string,
    options?: { restoreDraftOnError?: boolean },
  ) => {
    const normalizedQuestion = question.trim();
    if (!normalizedQuestion) {
      return;
    }

    if (!jobId) {
      setError('Chat is not ready for this report yet. Refresh the report once the latest analysis has finished loading.');
      return;
    }

    const userMessage: ReportChatMessage = {
      id: nextMessageId('user'),
      role: 'user',
      content: normalizedQuestion,
    };

    setMessages((current) => [...current, userMessage]);
    if (options?.restoreDraftOnError) {
      setDraft('');
    }
    setError(null);
    setIsLoading(true);
    setIsOpen(true);

    try {
      const response = await postReportChat({
        jobId,
        question: userMessage.content,
        history: historyForApi,
      });
      const answer = response.answer?.trim();
      if (!answer) {
        throw new Error('ESG Copilot returned an empty answer. Please try again.');
      }

      const assistantMessage: ReportChatMessage = {
        id: nextMessageId('assistant'),
        role: 'assistant',
        content: answer,
        citations: response.citations,
        answerSource: response.answerSource,
      };

      setMessages((current) => [...current, assistantMessage]);
    } catch (requestError) {
      if (options?.restoreDraftOnError) {
        setDraft(normalizedQuestion);
      }
      const message = requestError instanceof Error ? requestError.message : 'Unable to reach ESG Copilot right now.';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await submitQuestion(draft, { restoreDraftOnError: true });
  };

  const handleComposerKeyDown = async (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      if (draft.trim()) {
        await submitQuestion(draft, { restoreDraftOnError: true });
      }
    }
  };

  const jumpToSection = (sectionId?: string | null) => {
    if (!sectionId) {
      return;
    }

    if (typeof window !== 'undefined') {
      const targetTab = sectionId.startsWith('fraud') ? 'fraud' : 'esg';
      window.dispatchEvent(
        new CustomEvent('greenlens-report-tab-jump', {
          detail: {
            tab: targetTab,
            sectionId,
          },
        }),
      );
    }

    setIsOpen(false);
  };

  const toggleWidget = () => {
    setIsOpen((current) => !current);
    setError(null);
  };

  return (
    <div className="copilot-widget">
      {isOpen ? (
        <div id="greenlens-copilot-panel" className="copilot-card" role="dialog" aria-label="ESG Copilot">
          <div className="copilot-card-head">
            <div>
              <div className="copilot-eyebrow">ESG Copilot</div>
              <div className="copilot-title">Grounded Q&amp;A</div>
            </div>
            <button type="button" className="copilot-close" onClick={toggleWidget} aria-label="Close ESG Copilot">
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" width="14" height="14">
                <path d="M4 4l8 8M12 4l-8 8" />
              </svg>
            </button>
          </div>

          <p className="copilot-subtitle">
            Ask about this report, compliance gaps, emissions drivers, or matched funding. Answers stay grounded in the saved report and GreenLens knowledge base.
          </p>

          <div className="copilot-main">
            {!hasConversation ? (
              <div className="copilot-starters">
                <div className="copilot-starters-label">Starter questions</div>
                <div className="copilot-suggestions">
                  {SUGGESTED_QUESTIONS.map((question) => (
                    <button
                      key={question}
                      type="button"
                      className="copilot-suggestion"
                      onClick={() => submitQuestion(question)}
                      disabled={isLoading}
                    >
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}

            <div className="copilot-thread">
              <div ref={transcriptRef} className="copilot-transcript">
                {messages.map((message) => (
                  <div key={message.id} className={`copilot-message ${message.role === 'user' ? 'user' : 'assistant'}`}>
                    <div className="copilot-message-role">
                      {message.role === 'user' ? 'You' : 'ESG Copilot'}
                      {message.role === 'assistant' && message.answerSource === 'fallback' ? (
                        <span className="copilot-source-tag">Fallback</span>
                      ) : null}
                    </div>
                    <div className="copilot-bubble">{message.content}</div>

                    {message.citations && message.citations.length > 0 ? (
                      <div className="copilot-citations">
                        {message.citations.map((citation) => (
                          <button
                            key={`${message.id}-${citation.chunkId}`}
                            type="button"
                            className="copilot-citation"
                            onClick={() => jumpToSection(citation.sectionId)}
                          >
                            <div className="copilot-citation-label">{citation.sourceLabel}</div>
                            <div className="copilot-citation-title">{citation.title}</div>
                            <div className="copilot-citation-excerpt">{citation.excerpt}</div>
                          </button>
                        ))}
                      </div>
                    ) : null}
                  </div>
                ))}

                {isLoading ? (
                  <div className="copilot-message assistant">
                    <div className="copilot-message-role">ESG Copilot</div>
                    <div className="copilot-bubble copilot-bubble-loading">
                      <span className="copilot-dot" />
                      <span className="copilot-dot" />
                      <span className="copilot-dot" />
                    </div>
                  </div>
                ) : null}
              </div>
            </div>
          </div>

          {error ? <div className="copilot-error">{error}</div> : null}

          <form className="copilot-form" onSubmit={handleSubmit}>
            <textarea
              ref={inputRef}
              className="copilot-input"
              rows={2}
              placeholder="Ask a grounded question about this report..."
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={handleComposerKeyDown}
              disabled={isLoading}
            />
            <div className="copilot-form-actions">
              <div className="copilot-form-note">
                {jobId ? 'Enter to send. Shift + Enter for a new line.' : 'Loading report context before chat becomes available.'}
              </div>
              <button type="submit" className="btn-accent copilot-submit" disabled={!canSend}>
                Send
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.8" width="14" height="14">
                  <path d="M3 8h8M8 3l5 5-5 5" />
                </svg>
              </button>
            </div>
          </form>
        </div>
      ) : null}

      <button
        type="button"
        className={`copilot-launcher ${isOpen ? 'open' : ''}`}
        onClick={toggleWidget}
        aria-expanded={isOpen}
        aria-controls="greenlens-copilot-panel"
      >
        <span className="copilot-launcher-icon" aria-hidden="true">
          <span className="copilot-launcher-dot" />
          <span className="copilot-launcher-dot" />
          <span className="copilot-launcher-dot" />
        </span>
        <span className="copilot-launcher-text">{isOpen ? 'Close Copilot' : 'Ask ESG Copilot'}</span>
      </button>
    </div>
  );
}

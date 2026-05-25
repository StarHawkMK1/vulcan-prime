import { useEffect, useRef } from 'react';
import { openEventStream } from '../api';
import { nebTokens as t } from '../design';

export interface TriageReport {
  new_concepts: string[];
  extensions: string[];
  contradictions: string[];
  planned_pages: string[];
}

export interface LogEvent {
  type: 'text' | 'tool_call' | 'triage' | 'done' | 'error';
  content?: string;
  name?: string;
  args?: Record<string, unknown>;
  report?: TriageReport;
  summary?: string;
  message?: string;
}

interface Props {
  opId: string | null;
  onTriage?: (report: TriageReport) => void;
  onDone?: () => void;
}

const eventColor = (type: string): string => ({
  text:      t.text,
  tool_call: t.violet,
  triage:    t.warn,
  done:      t.cyan,
  error:     t.bad,
}[type] ?? t.textMuted);

function formatEvent(e: LogEvent): string {
  switch (e.type) {
    case 'text':      return e.content ?? '';
    case 'tool_call': return `[TOOL] ${e.name}(${JSON.stringify(e.args ?? {})})`;
    case 'triage':    return '[TRIAGE] Awaiting approval…';
    case 'done':      return `[DONE] ${e.summary ?? ''}`;
    case 'error':     return `[ERROR] ${e.message ?? 'unknown error'}`;
    default:          return JSON.stringify(e);
  }
}

export function LogStream({ opId, onTriage, onDone }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!opId) return;
    esRef.current?.close();
    const es = openEventStream(opId);
    esRef.current = es;

    es.onmessage = (ev: MessageEvent) => {
      const event: LogEvent = JSON.parse(ev.data as string);
      if (event.type === 'triage' && event.report) onTriage?.(event.report);
      if (event.type === 'done') { onDone?.(); es.close(); }
      if (event.type === 'error') { onDone?.(); es.close(); }

      if (containerRef.current) {
        const line = document.createElement('div');
        line.style.color = eventColor(event.type);
        line.style.fontFamily = t.mono;
        line.style.fontSize = '11px';
        line.style.lineHeight = '1.6';
        line.style.whiteSpace = 'pre-wrap';
        line.textContent = formatEvent(event);
        containerRef.current.appendChild(line);
        containerRef.current.scrollTop = containerRef.current.scrollHeight;
      }
    };
    return () => es.close();
  }, [opId]);

  return (
    <div ref={containerRef} style={{
      background: t.bgDeep, border: `1px solid ${t.border}`,
      padding: 12, height: 240, overflowY: 'auto',
      fontFamily: t.mono, fontSize: 11, lineHeight: 1.6,
    }} />
  );
}

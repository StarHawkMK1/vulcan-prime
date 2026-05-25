import React from 'react';
import { TriageReport } from './LogStream';
import { sendApproval } from '../api';
import { nebTokens as t, NebPanel, NebLabel, NebButton } from '../design';

interface Props { opId: string; report: TriageReport; onResolved: () => void }

export function TriagePanel({ opId, report, onResolved }: Props) {
  async function handle(approved: boolean) {
    try {
      await sendApproval(opId, approved);
      onResolved();
    } catch {
      console.error('sendApproval failed');
    }
  }

  const FIELD: React.CSSProperties = { fontSize: 9.5, fontFamily: t.mono, color: t.textFaint,
    letterSpacing: 1, textTransform: 'uppercase', marginBottom: 4 };
  const LIST: React.CSSProperties = { paddingLeft: 14, color: t.text, fontSize: 11, fontFamily: t.mono };

  return (
    <NebPanel glow style={{ marginTop: 10 }}>
      <NebLabel glow>Triage Report — approve before writing?</NebLabel>
      {report.new_concepts.length > 0 && (
        <div style={{ marginBottom: 8 }}>
          <div style={FIELD}>New concepts</div>
          <ul style={LIST}>{report.new_concepts.map((c) => <li key={c}>{c}</li>)}</ul>
        </div>
      )}
      {report.extensions.length > 0 && (
        <div style={{ marginBottom: 8 }}>
          <div style={FIELD}>Pages to update</div>
          <ul style={LIST}>{report.extensions.map((c) => <li key={c}>{c}</li>)}</ul>
        </div>
      )}
      {report.contradictions.length > 0 && (
        <div style={{ marginBottom: 8 }}>
          <div style={{ ...FIELD, color: t.bad }}>Contradictions</div>
          <ul style={{ ...LIST, color: t.bad }}>{report.contradictions.map((c) => <li key={c}>{c}</li>)}</ul>
        </div>
      )}
      {report.planned_pages.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <div style={FIELD}>Files to write</div>
          <ul style={{ ...LIST, color: t.cyanSoft }}>{report.planned_pages.map((p) => <li key={p}>{p}</li>)}</ul>
        </div>
      )}
      <div style={{ display: 'flex', gap: 8 }}>
        <NebButton primary onClick={() => handle(true)}>✓ Approve</NebButton>
        <NebButton onClick={() => handle(false)}>✗ Cancel</NebButton>
      </div>
    </NebPanel>
  );
}

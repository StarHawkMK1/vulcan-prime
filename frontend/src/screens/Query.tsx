import { useState } from 'react';
import type { CSSProperties } from 'react';
import { nebTokens as t, NebLabel, NebButton } from '../design';
import { startQuery } from '../api';
import { LogStream } from '../components/LogStream';
import { ProviderSelect } from '../components/ProviderSelect';

const TEXTAREA: CSSProperties = {
  background: t.bgGlass, border: `1px solid ${t.border}`, color: t.text,
  padding: '8px 10px', fontFamily: t.mono, fontSize: 11, width: '100%',
  resize: 'vertical', minHeight: 80,
};

export function Query() {
  const [provider, setProvider] = useState('anthropic');
  const [model, setModel] = useState('claude-opus-4-7');
  const [question, setQuestion] = useState('');
  const [fileBack, setFileBack] = useState(false);
  const [opId, setOpId] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  async function handleRun() {
    if (!question.trim() || running) return;
    setRunning(true);
    try {
      const id = await startQuery(question, provider, model, fileBack);
      setOpId(id);
    } catch { setRunning(false); }
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', height: 'calc(100vh - 60px)' }}>
      <div style={{ borderRight: `1px solid ${t.border}`, padding: 16, display: 'flex', flexDirection: 'column', gap: 12,
        background: 'rgba(2,5,13,0.4)' }}>
        <div>
          <label htmlFor="vp-question" style={{ fontSize: 9.5, fontWeight: 600, fontFamily: t.mono, color: t.textFaint,
            letterSpacing: 1.4, textTransform: 'uppercase', marginBottom: 5, display: 'block' }}>Question</label>
          <textarea id="vp-question" value={question} onChange={(e) => setQuestion(e.target.value)}
            placeholder="What is RAG and how does it differ from fine-tuning?"
            style={TEXTAREA} />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <input type="checkbox" id="fileback" checked={fileBack}
            onChange={(e) => setFileBack(e.target.checked)} />
          <label htmlFor="fileback" style={{ fontSize: 10.5, fontFamily: t.mono, color: t.textMuted, cursor: 'pointer' }}>
            File-back to vault
          </label>
        </div>
        <ProviderSelect provider={provider} model={model}
          onProviderChange={setProvider} onModelChange={setModel} />
        <NebButton primary onClick={handleRun} disabled={running || !question.trim()}
          style={{ width: '100%', marginTop: 8 }}>
          {running ? '⏳ Running…' : '▶ Run Query'}
        </NebButton>
      </div>
      <div style={{ padding: 22, display: 'flex', flexDirection: 'column', gap: 12, overflow: 'auto' }}>
        <NebLabel glow>Stream Output</NebLabel>
        <LogStream opId={opId} onDone={() => setRunning(false)} />
      </div>
    </div>
  );
}

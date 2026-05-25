import { useState } from 'react';
import { nebTokens as t, NebLabel, NebButton } from '../design';
import { startLint } from '../api';
import { LogStream } from '../components/LogStream';
import { ProviderSelect } from '../components/ProviderSelect';

export function Lint() {
  const [provider, setProvider] = useState('anthropic');
  const [model, setModel] = useState('claude-opus-4-7');
  const [opId, setOpId] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  async function handleRun() {
    if (running) return;
    setRunning(true);
    try {
      const id = await startLint(provider, model);
      setOpId(id);
    } catch { setRunning(false); }
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', height: 'calc(100vh - 60px)' }}>
      <div style={{ borderRight: `1px solid ${t.border}`, padding: 16, display: 'flex', flexDirection: 'column', gap: 12,
        background: 'rgba(2,5,13,0.4)' }}>
        <ProviderSelect provider={provider} model={model}
          onProviderChange={setProvider} onModelChange={setModel} />
        <NebButton primary onClick={handleRun} disabled={running}
          style={{ width: '100%', marginTop: 8 }}>
          {running ? '⏳ Scanning…' : '▶ Run Lint'}
        </NebButton>
        <div style={{ color: t.textFaint, fontSize: 9.5, fontFamily: t.mono, marginTop: 4 }}>
          Checks: broken links · orphan pages · stale claims
        </div>
      </div>
      <div style={{ padding: 22, display: 'flex', flexDirection: 'column', gap: 12, overflow: 'auto' }}>
        <NebLabel glow>Stream Output</NebLabel>
        <LogStream opId={opId} onDone={() => setRunning(false)} />
      </div>
    </div>
  );
}

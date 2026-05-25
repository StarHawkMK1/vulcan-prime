import { useState, useEffect } from 'react';
import type { CSSProperties } from 'react';
import { nebTokens as t, NebPanel, NebLabel, NebButton } from '../design';
import { startIngest, getVaultList } from '../api';
import { LogStream, TriageReport } from '../components/LogStream';
import { TriagePanel } from '../components/TriagePanel';
import { ProviderSelect } from '../components/ProviderSelect';

const SELECT: CSSProperties = {
  background: t.bgGlass, border: `1px solid ${t.border}`, color: t.textMuted,
  padding: '5px 8px', fontFamily: t.mono, fontSize: 11, width: '100%',
};

export function Ingest() {
  const [provider, setProvider] = useState('anthropic');
  const [model, setModel] = useState('claude-opus-4-7');
  const [sourcePath, setSourcePath] = useState('');
  const [sources, setSources] = useState<string[]>([]);
  const [opId, setOpId] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [triage, setTriage] = useState<{ opId: string; report: TriageReport } | null>(null);

  useEffect(() => {
    Promise.all([getVaultList('raw'), getVaultList('feed')])
      .then(([raw, feed]) => setSources([...raw, ...feed]))
      .catch(() => setSources([]));
  }, []);

  async function handleRun() {
    if (!sourcePath || running) return;
    setRunning(true); setTriage(null);
    try {
      const id = await startIngest(sourcePath, provider, model);
      setOpId(id);
    } catch { setRunning(false); }
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', height: 'calc(100vh - 60px)' }}>
      {/* Sidebar config */}
      <div style={{ borderRight: `1px solid ${t.border}`, padding: 16, display: 'flex', flexDirection: 'column', gap: 12,
        background: 'rgba(2,5,13,0.4)' }}>
        <div>
          <NebLabel>Source</NebLabel>
          <select value={sourcePath} onChange={(e) => setSourcePath(e.target.value)} style={SELECT}>
            <option value="">— select —</option>
            {sources.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <ProviderSelect provider={provider} model={model}
          onProviderChange={setProvider} onModelChange={setModel} />
        <NebButton primary onClick={handleRun} disabled={running || !sourcePath}
          style={{ width: '100%', marginTop: 8 }}>
          {running ? '⏳ Running…' : '▶ Run Ingest'}
        </NebButton>
        {running && (
          <div style={{ fontSize: 9.5, fontFamily: t.mono, color: t.textFaint, textAlign: 'center' }}>
            awaiting stream…
          </div>
        )}
      </div>

      {/* Stream output */}
      <div style={{ padding: 22, display: 'flex', flexDirection: 'column', gap: 12, overflow: 'auto' }}>
        <NebLabel glow>Stream Output</NebLabel>
        <LogStream opId={opId}
          onTriage={(report) => { if (opId) setTriage({ opId, report }); }}
          onDone={() => setRunning(false)} />
        {triage && (
          <TriagePanel opId={triage.opId} report={triage.report}
            onResolved={() => setTriage(null)} />
        )}
      </div>
    </div>
  );
}

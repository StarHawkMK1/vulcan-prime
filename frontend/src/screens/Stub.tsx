import { nebTokens as t, NebPanel, NebLabel } from '../design';

interface Props { label: string; phase: string }

export function Stub({ label, phase }: Props) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center',
      height: 'calc(100vh - 60px)', padding: 40 }}>
      <NebPanel glow style={{ maxWidth: 480, width: '100%', textAlign: 'center' }} padding={40}>
        <div style={{ fontSize: 48, marginBottom: 16, color: t.cyan, opacity: 0.5 }}>◈</div>
        <NebLabel glow>{phase}</NebLabel>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.text, marginBottom: 8 }}>{label}</div>
        <div style={{ fontSize: 13, color: t.textMuted, lineHeight: 1.7 }}>
          This feature is planned for {phase}. Phase 1 focuses on the core<br/>
          Knowledge operations: Ingest, Query, and Lint.
        </div>
        <div style={{ marginTop: 24, fontFamily: t.mono, fontSize: 10.5, color: t.textFaint }}>
          Navigate to Knowledge → Ingest to get started.
        </div>
      </NebPanel>
    </div>
  );
}

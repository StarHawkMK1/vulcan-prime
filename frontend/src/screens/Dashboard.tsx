import { useState, useEffect } from 'react';
import { nebTokens as t, NebPanel, NebLabel } from '../design';
import { getStatus } from '../api';
import type { StatusResponse } from '../api';

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  return `${Math.floor(mins / 60)}h ago`;
}

const OP_COLOR: Record<string, string> = {
  ingest: t.cyan, query: t.cyanSoft, lint: t.violet,
};

export function Dashboard() {
  const [status, setStatus] = useState<StatusResponse>({ tokens: 0, cost: 0, pages: 0, recent_ops: [] });

  useEffect(() => {
    getStatus().then(setStatus).catch(() => {});
    const id = setInterval(() => getStatus().then(setStatus).catch(() => {}), 10000);
    return () => clearInterval(id);
  }, []);

  return (
    <div style={{ padding: 26, display: 'flex', flexDirection: 'column', gap: 18 }}>
      {/* Greeting */}
      <div>
        <div style={{ fontSize: 11, fontFamily: t.mono, color: t.textFaint, letterSpacing: 1.5, textTransform: 'uppercase' }}>
          Vulcan Prime · local
        </div>
        <div style={{ fontSize: 28, fontWeight: 600, color: t.text, letterSpacing: -0.4, marginTop: 4 }}>
          Knowledge <span style={{ color: t.cyan, textShadow: `0 0 12px ${t.cyan}55` }}>Command Center</span>
        </div>
        <div style={{ fontSize: 13, color: t.textMuted, marginTop: 4 }}>
          {status.pages} wiki pages · {status.recent_ops.length} recent operations
        </div>
      </div>

      {/* KPI tiles */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14 }}>
        {[
          { l: 'Session Tokens', v: status.tokens.toLocaleString(), s: 'cumulative', c: t.cyan, glow: true },
          { l: 'Session Cost',   v: `$${status.cost.toFixed(4)}`,   s: 'estimated',  c: t.cyanSoft },
          { l: 'Wiki Pages',     v: String(status.pages),            s: 'in vault',   c: t.text },
          { l: 'Recent Ops',     v: String(status.recent_ops.length), s: 'last 20',   c: t.text },
        ].map((k) => (
          <NebPanel key={k.l} padding={14} glow={k.glow}>
            <NebLabel glow={k.glow}>{k.l}</NebLabel>
            <div style={{ fontSize: 26, fontWeight: 600, fontFamily: t.mono, color: k.c,
              letterSpacing: -0.4, textShadow: k.glow ? `0 0 14px ${t.cyan}55` : 'none' }}>{k.v}</div>
            <div style={{ fontSize: 10.5, color: t.textFaint, fontFamily: t.mono, marginTop: 3 }}>{k.s}</div>
          </NebPanel>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 14 }}>
        {/* Recent activity */}
        <NebPanel padding={0}>
          <div style={{ padding: '12px 16px', borderBottom: `1px solid ${t.border}`,
            display: 'flex', alignItems: 'center' }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: t.text }}>Recent activity</div>
            <div style={{ flex: 1 }} />
            <div style={{ fontSize: 10.5, fontFamily: t.mono, color: t.textFaint }}>last 20 ops</div>
          </div>
          {status.recent_ops.length === 0 ? (
            <div style={{ padding: '20px 16px', fontFamily: t.mono, fontSize: 11.5, color: t.textFaint }}>
              No operations yet. Run Ingest, Query, or Lint.
            </div>
          ) : (
            status.recent_ops.slice(0, 6).map((op, i) => (
              <div key={i} style={{ display: 'grid', gridTemplateColumns: '80px 70px 1fr',
                padding: '9px 16px', borderBottom: i < 5 ? `1px solid ${t.border}` : 'none',
                fontFamily: t.mono, fontSize: 11.5, alignItems: 'center' }}>
                <div style={{ color: t.textFaint }}>{timeAgo(op.ts)}</div>
                <div style={{ color: OP_COLOR[op.type] ?? t.text, letterSpacing: 0.4,
                  textTransform: 'uppercase', fontSize: 9.5 }}>{op.type}</div>
                <div style={{ color: t.textMuted, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {op.detail}
                </div>
              </div>
            ))
          )}
        </NebPanel>

        {/* Quick actions */}
        <NebPanel padding={16}>
          <NebLabel glow>Quick actions</NebLabel>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 4 }}>
            {[
              ['⬆', 'Ingest',  t.cyan,      'ingest'],
              ['🔍', 'Query',  t.cyanSoft,  'query'],
              ['🔧', 'Lint',   t.violet,    'lint'],
              ['✦', 'Vault',  t.textMuted, 'vault'],
            ].map(([ic, label, color]) => (
              <button key={label} type="button" style={{
                display: 'flex', alignItems: 'center', gap: 10, padding: '11px 12px',
                background: t.bgDeep, border: `1px solid ${t.border}`, color: t.text,
                fontSize: 12, fontFamily: t.font, textAlign: 'left', cursor: 'pointer' }}>
                <span style={{ width: 22, height: 22, display: 'flex', alignItems: 'center', justifyContent: 'center',
                  border: `1px solid ${t.borderGlow}`, color: color as string,
                  boxShadow: `inset 0 0 6px ${(color as string)}22`, fontSize: 13, fontFamily: t.mono }}>{ic}</span>
                {label}
              </button>
            ))}
          </div>
          <div style={{ marginTop: 16, padding: '12px 0', borderTop: `1px solid ${t.border}`,
            fontFamily: t.mono, fontSize: 10.5, color: t.textFaint }}>
            Use the sidebar to navigate to each operation.
          </div>
        </NebPanel>
      </div>
    </div>
  );
}

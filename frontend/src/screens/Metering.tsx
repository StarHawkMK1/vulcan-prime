import { useState, useEffect, useCallback, useRef } from 'react';
import { nebTokens as t, NebPanel, NebButton } from '../design';
import {
  getMeteringDashboard, refreshMetering, exportToVault,
  type MeteringDashboard, type ToolMetrics, type TrendEntry, type ChangelogEntry,
} from '../api';

// ── Helpers ───────────────────────────────────────────────────

function fmtTokens(n: number | null): string {
  if (n === null) return '—';
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${Math.round(n / 1_000)}k`;
  return String(n);
}

function fmtTime(sec: number | null): string {
  if (sec === null || sec <= 0) return '—';
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  return `${Math.floor(mins / 60)}h ago`;
}

function dayAbbr(dateStr: string, isToday: boolean): string {
  if (isToday) return 'Today';
  const d = new Date(dateStr + 'T12:00:00Z');
  return ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][d.getUTCDay()];
}

// ── Constants ─────────────────────────────────────────────────

const CHART_H = 56;
const COLORS = { claude_code: '#7af0ff', codex: '#9d7ad8', antigravity: '#00ff90' } as const;
const LEGEND = [
  { label: 'Claude Code', color: COLORS.claude_code + '88' },
  { label: 'Codex',       color: COLORS.codex + '88' },
  { label: 'Antigravity', color: COLORS.antigravity + '88' },
];
const TOOL_LIST = [
  { key: 'claude_code'  as const, name: 'Claude Code' },
  { key: 'codex'        as const, name: 'OpenAI Codex' },
  { key: 'antigravity'  as const, name: 'Google Antigravity' },
];
const EMPTY: MeteringDashboard = {
  scanned_at: new Date().toISOString(),
  tools: {
    claude_code: {
      status: 'offline',
      window_5h: { tokens: 0, limit: 0, resets_in_sec: null },
      weekly:    { tokens: 0, limit: 0, cost_usd: 0 },
      today:     { tokens: 0, cost_usd: 0, sessions: 0 },
    },
    codex: {
      status: 'offline',
      window_5h: { tokens: 0, limit: 0, resets_in_sec: null },
      weekly:    { tokens: 0, limit: 0, cost_usd: 0 },
      today:     { tokens: 0, cost_usd: 0, sessions: 0 },
    },
    antigravity: {
      status: 'offline',
      window_5h: { tokens: null, limit: 0, resets_in_sec: null },
      weekly:    { tokens: null, limit: 0, cost_usd: null },
      today:     { tokens: null, cost_usd: null, sessions: null },
    },
  },
  trend_7d: [],
  weekly_total: { tokens: 0, cost_usd: 0 },
  changelogs: [],
};

// ── Progress Bar ──────────────────────────────────────────────

function ProgressBar({ label, tokens, limit, rightLabel, warn }: {
  label: string;
  tokens: number | null;
  limit: number;
  rightLabel: string;
  warn?: boolean;
}) {
  const pct = limit > 0 && tokens !== null
    ? Math.min(100, (tokens / limit) * 100) : 0;
  const fill = warn
    ? 'linear-gradient(90deg, #f5c46a99, #ef546699)'
    : 'linear-gradient(90deg, #7af0ff77, #2f81f777)';

  return (
    <div style={{ marginBottom: 7 }}>
      <div style={{
        display: 'flex', justifyContent: 'space-between',
        fontFamily: t.mono, fontSize: 9.5, marginBottom: 3,
      }}>
        <span style={{ color: t.textFaint }}>{label}</span>
        <span style={{ color: warn ? t.warn : t.textMuted }}>{rightLabel}</span>
      </div>
      {limit > 0 && (
        <div style={{ height: 4, background: '#0d1a2a', borderRadius: 3, overflow: 'hidden' }}>
          <div style={{
            height: '100%', width: `${pct}%`, background: fill,
            borderRadius: 3, transition: 'width 0.5s ease',
          }} />
        </div>
      )}
    </div>
  );
}

// ── Status Badge ──────────────────────────────────────────────

function StatusBadge({ status, is5hHigh }: { status: 'live' | 'offline'; is5hHigh: boolean }) {
  if (status === 'offline') {
    return (
      <span style={{
        fontFamily: t.mono, fontSize: 8.5, fontWeight: 600, letterSpacing: 1,
        padding: '2px 7px', borderRadius: 3,
        background: 'rgba(74,92,114,0.18)', color: t.textFaint,
        border: '1px solid rgba(74,92,114,0.28)',
      }}>● OFFLINE</span>
    );
  }
  if (is5hHigh) {
    return (
      <span style={{
        fontFamily: t.mono, fontSize: 8.5, fontWeight: 600, letterSpacing: 1,
        padding: '2px 7px', borderRadius: 3,
        background: 'rgba(245,196,106,0.14)', color: t.warn,
        border: '1px solid rgba(245,196,106,0.32)',
      }}>⚠ 5H HIGH</span>
    );
  }
  return (
    <span style={{
      fontFamily: t.mono, fontSize: 8.5, fontWeight: 600, letterSpacing: 1,
      padding: '2px 7px', borderRadius: 3,
      background: 'rgba(122,240,255,0.10)', color: t.cyan,
      border: '1px solid rgba(122,240,255,0.28)',
    }}>● LIVE</span>
  );
}

// ── Tool Card ─────────────────────────────────────────────────

function ToolCard({ name, metrics, scannedAt }: {
  name: string;
  metrics: ToolMetrics;
  scannedAt: string;
}) {
  const { status, window_5h, weekly, today } = metrics;
  const offline = status === 'offline';
  const is5hHigh = !offline && window_5h.limit > 0 && window_5h.tokens !== null
    && window_5h.tokens / window_5h.limit >= 0.75;

  const win5hRight = offline ? '— / —'
    : window_5h.limit > 0
      ? `${fmtTokens(window_5h.tokens)} / ${fmtTokens(window_5h.limit)} tok · ${fmtTime(window_5h.resets_in_sec)} left`
      : `${fmtTokens(window_5h.tokens)} tok`;

  const weeklyRight = offline ? '—'
    : weekly.limit > 0
      ? `${fmtTokens(weekly.tokens)} / ${fmtTokens(weekly.limit)} tok · $${(weekly.cost_usd ?? 0).toFixed(2)}`
      : `${fmtTokens(weekly.tokens)} tok`;

  return (
    <NebPanel padding={12} style={{ opacity: offline ? 0.45 : 1, transition: 'opacity 0.3s' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
        <span style={{ fontFamily: t.mono, fontSize: 10.5, fontWeight: 600, color: t.text, letterSpacing: 0.3 }}>
          {name}
        </span>
        <StatusBadge status={status} is5hHigh={is5hHigh} />
      </div>

      <ProgressBar
        label="5H Window"
        tokens={window_5h.tokens}
        limit={window_5h.limit}
        rightLabel={win5hRight}
        warn={is5hHigh}
      />
      <ProgressBar
        label="Weekly Limit"
        tokens={weekly.tokens}
        limit={weekly.limit}
        rightLabel={weeklyRight}
      />

      <div style={{ height: 1, background: t.border, margin: '5px 0 7px' }} />

      <div style={{ display: 'flex', gap: 14, fontFamily: t.mono, fontSize: 9, color: t.textFaint, flexWrap: 'wrap' }}>
        {!offline ? (
          <>
            <span>Today: {fmtTokens(today.tokens)} tok · ${(today.cost_usd ?? 0).toFixed(2)}</span>
            <span>Sessions: {today.sessions ?? '—'}</span>
          </>
        ) : (
          metrics.last_seen && <span>Last seen: {metrics.last_seen.slice(0, 10)}</span>
        )}
        <span>Scanned: {timeAgo(scannedAt)}</span>
      </div>
    </NebPanel>
  );
}

// ── Trend Chart ───────────────────────────────────────────────

function TrendChart({ entries, weeklyTotal }: {
  entries: TrendEntry[];
  weeklyTotal: { tokens: number; cost_usd: number };
}) {
  const today = new Date().toISOString().slice(0, 10);
  const maxTotal = Math.max(1, ...entries.map(e => e.claude_code + e.codex + (e.antigravity ?? 0)));

  return (
    <NebPanel padding={12}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
        <span style={{
          fontFamily: t.mono, fontSize: 9.5, fontWeight: 700,
          color: t.textFaint, letterSpacing: 1.5, textTransform: 'uppercase',
        }}>7-Day Token Trend</span>
        <span style={{ fontFamily: t.mono, fontSize: 9, color: t.textMuted }}>
          Total this week: {fmtTokens(weeklyTotal.tokens)} · ${weeklyTotal.cost_usd.toFixed(2)}
        </span>
      </div>

      <div style={{ display: 'flex', gap: 4, height: CHART_H, alignItems: 'flex-end' }}>
        {entries.map((e) => {
          const isToday = e.date === today;
          const alpha = isToday ? 'cc' : '55';
          const total = e.claude_code + e.codex + (e.antigravity ?? 0);
          const totalH = Math.round((total / maxTotal) * CHART_H);
          const ccH = total > 0 ? Math.round((e.claude_code / total) * totalH) : 0;
          const cxH = total > 0 ? Math.round((e.codex / total) * totalH) : 0;
          const agH = Math.max(0, totalH - ccH - cxH);

          return (
            <div key={e.date} style={{
              flex: 1, display: 'flex', flexDirection: 'column',
              justifyContent: 'flex-end', height: '100%',
            }}>
              {total === 0 ? (
                <div style={{ height: 2, background: t.border, borderRadius: 2 }} />
              ) : (
                <>
                  {ccH > 0 && (
                    <div style={{
                      height: ccH,
                      background: `${COLORS.claude_code}${alpha}`,
                      borderRadius: cxH === 0 && agH === 0 ? '2px 2px 0 0' : undefined,
                    }} />
                  )}
                  {cxH > 0 && (
                    <div style={{ height: cxH, background: `${COLORS.codex}${alpha}` }} />
                  )}
                  {agH > 0 && (
                    <div style={{ height: agH, background: `${COLORS.antigravity}${alpha}` }} />
                  )}
                </>
              )}
            </div>
          );
        })}
      </div>

      <div style={{ display: 'flex', gap: 4, marginTop: 4 }}>
        {entries.map((e) => {
          const isToday = e.date === today;
          return (
            <div key={e.date} style={{
              flex: 1, textAlign: 'center', fontFamily: t.mono, fontSize: 7.5,
              color: isToday ? t.cyan : t.textFaint,
              fontWeight: isToday ? 700 : 400,
            }}>
              {dayAbbr(e.date, isToday)}
            </div>
          );
        })}
      </div>

      <div style={{ display: 'flex', gap: 12, marginTop: 8, fontFamily: t.mono, fontSize: 8.5, color: t.textFaint }}>
        {LEGEND.map(({ label, color }) => (
          <span key={label} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <span style={{ width: 8, height: 8, borderRadius: 2, background: color, display: 'inline-block' }} />
            {label}
          </span>
        ))}
      </div>
    </NebPanel>
  );
}

// ── Changelog Panel ───────────────────────────────────────

const CHANGELOG_COLORS: Record<string, string> = {
  claude_code: '#7af0ff',
  codex: '#9d7ad8',
  gemini_code: '#00ff90',
};

function ChangelogPanel({ entries }: { entries: ChangelogEntry[] }) {
  if (entries.length === 0) return null;
  return (
    <NebPanel padding={12}>
      <div style={{
        fontFamily: t.mono, fontSize: 9.5, fontWeight: 700,
        color: t.textFaint, letterSpacing: 1.5, textTransform: 'uppercase',
        marginBottom: 10,
      }}>
        Changelog Tracker
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {entries.map((e) => {
          const color = CHANGELOG_COLORS[e.key] ?? t.textMuted;
          const hasData = e.version !== null;
          return (
            <div
              key={e.key}
              onClick={() => e.url && window.open(e.url, '_blank')}
              style={{
                display: 'grid',
                gridTemplateColumns: '110px 70px 1fr 80px',
                alignItems: 'center',
                gap: 10,
                padding: '6px 0',
                borderBottom: `1px solid ${t.border}`,
                opacity: hasData ? 1 : 0.4,
                cursor: e.url ? 'pointer' : 'default',
              }}
            >
              {/* Tool name */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{
                  width: 6, height: 6, borderRadius: '50%',
                  background: color,
                  boxShadow: hasData ? `0 0 6px ${color}` : 'none',
                  flex: '0 0 auto',
                }} />
                <span style={{ fontFamily: t.mono, fontSize: 10, color: t.text }}>
                  {e.tool}
                </span>
              </div>
              {/* Version badge */}
              <span style={{
                fontFamily: t.mono, fontSize: 8.5, fontWeight: 600,
                padding: '2px 6px',
                background: hasData ? `${color}18` : 'transparent',
                border: `1px solid ${hasData ? color + '44' : t.border}`,
                color: hasData ? color : t.textFaint,
                letterSpacing: 0.5,
                whiteSpace: 'nowrap',
              }}>
                {e.version ?? '—'}
              </span>
              {/* Title */}
              <span style={{
                fontFamily: t.mono, fontSize: 9.5, color: t.textMuted,
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              }}>
                {e.title ?? '수집 불가'}
              </span>
              {/* Date */}
              <span style={{
                fontFamily: t.mono, fontSize: 9, color: t.textFaint,
                textAlign: 'right',
              }}>
                {e.date ?? '—'}
              </span>
            </div>
          );
        })}
      </div>
    </NebPanel>
  );
}

// ── Main ──────────────────────────────────────────────────────

export function Metering() {
  const [data, setData] = useState<MeteringDashboard>(EMPTY);
  const [refreshing, setRefreshing] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportMsg, setExportMsg] = useState<string | null>(null);
  const exportTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const load = useCallback(() => {
    getMeteringDashboard().then(setData).catch(() => {});
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, 30_000);
    return () => {
      clearInterval(id);
      if (exportTimer.current !== null) clearTimeout(exportTimer.current);
    };
  }, [load]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await refreshMetering();
      load();
    } finally {
      setRefreshing(false);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    setExportMsg(null);
    try {
      const r = await exportToVault();
      setExportMsg(`✓ ${r.path}`);
    } catch {
      setExportMsg('✗ Export failed');
    } finally {
      setExporting(false);
      if (exportTimer.current !== null) clearTimeout(exportTimer.current);
      exportTimer.current = setTimeout(() => setExportMsg(null), 4000);
    }
  };

  return (
    <div style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 14, maxWidth: 680 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{
          flex: 1, fontFamily: t.mono, fontSize: 11, fontWeight: 700,
          color: t.cyan, letterSpacing: 2, textTransform: 'uppercase',
          textShadow: `0 0 10px ${t.cyan}44`,
        }}>
          ◈ Metering
        </span>
        {exportMsg && (
          <span style={{ fontFamily: t.mono, fontSize: 9, color: exportMsg.startsWith('✓') ? t.cyan : t.bad }}>
            {exportMsg}
          </span>
        )}
        <NebButton onClick={handleExport} disabled={exporting} style={{ height: 28, fontSize: 9.5, padding: '0 12px' }}>
          {exporting ? '…' : 'Export to Vault'}
        </NebButton>
        <NebButton primary onClick={handleRefresh} disabled={refreshing} style={{ height: 28, fontSize: 9.5, padding: '0 12px' }}>
          {refreshing ? '…' : '↻ Refresh'}
        </NebButton>
      </div>

      {TOOL_LIST.map(({ key, name }) => (
        <ToolCard key={key} name={name} metrics={data.tools[key]} scannedAt={data.scanned_at} />
      ))}

      {data.trend_7d.length > 0 && (
        <TrendChart entries={data.trend_7d} weeklyTotal={data.weekly_total} />
      )}
      <ChangelogPanel entries={data.changelogs ?? []} />
    </div>
  );
}

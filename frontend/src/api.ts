const BASE = '/api';

export async function startIngest(sourcePath: string, provider: string, model: string): Promise<string> {
  const res = await fetch(`${BASE}/ingest`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source_path: sourcePath, provider, model }),
  });
  if (!res.ok) throw new Error(`ingest failed: ${res.status}`);
  return (await res.json()).op_id as string;
}

export async function startQuery(question: string, provider: string, model: string, fileBack: boolean): Promise<string> {
  const res = await fetch(`${BASE}/query`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, provider, model, file_back: fileBack }),
  });
  if (!res.ok) throw new Error(`query failed: ${res.status}`);
  return (await res.json()).op_id as string;
}

export async function startLint(provider: string, model: string): Promise<string> {
  const res = await fetch(`${BASE}/lint`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider, model }),
  });
  if (!res.ok) throw new Error(`lint failed: ${res.status}`);
  return (await res.json()).op_id as string;
}

export async function sendApproval(opId: string, approved: boolean): Promise<void> {
  const res = await fetch(`${BASE}/approve/${opId}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ approved }),
  });
  if (!res.ok) throw new Error(`approval failed: ${res.status}`);
}

export function openEventStream(opId: string): EventSource {
  return new EventSource(`${BASE}/stream/${opId}`);
}

export interface StatusResponse {
  tokens: number; cost: number; pages: number;
  recent_ops: { type: string; detail: string; ts: string }[];
}

export async function getStatus(): Promise<StatusResponse> {
  const res = await fetch(`${BASE}/status`);
  if (!res.ok) throw new Error(`status failed: ${res.status}`);
  return res.json();
}

export async function getVaultList(dir: string): Promise<string[]> {
  const res = await fetch(`${BASE}/vault/list?dir=${encodeURIComponent(dir)}`);
  if (!res.ok) throw new Error(`vault/list failed: ${res.status}`);
  return ((await res.json()).paths) as string[];
}

// ── Metering ──────────────────────────────────────────────

export interface WindowData {
  tokens: number | null;
  limit: number;
  resets_in_sec: number | null;
}

export interface WeeklyData {
  tokens: number | null;
  limit: number;
  cost_usd: number | null;
}

export interface TodayData {
  tokens: number | null;
  cost_usd: number | null;
  sessions: number | null;
}

export interface ToolMetrics {
  status: 'live' | 'offline';
  last_seen?: string | null;
  window_5h: WindowData;
  weekly: WeeklyData;
  today: TodayData;
}

export interface TrendEntry {
  date: string;
  claude_code: number;
  codex: number;
  antigravity: number;
  cost_usd: number;
}

export interface ChangelogEntry {
  tool: string;
  key: string;
  version: string | null;
  title: string | null;
  date: string | null;
  url: string | null;
}

export interface MeteringDashboard {
  scanned_at: string;
  tools: {
    claude_code: ToolMetrics;
    codex: ToolMetrics;
    antigravity: ToolMetrics;
  };
  trend_7d: TrendEntry[];
  weekly_total: { tokens: number; cost_usd: number };
  changelogs: ChangelogEntry[];
}

export async function getMeteringDashboard(): Promise<MeteringDashboard> {
  const res = await fetch(`${BASE}/metering/dashboard`);
  if (!res.ok) throw new Error(`metering/dashboard failed: ${res.status}`);
  return res.json();
}

export async function refreshMetering(): Promise<{ ok: boolean; scanned_at: string }> {
  const res = await fetch(`${BASE}/metering/refresh`, { method: 'POST' });
  if (!res.ok) throw new Error(`metering/refresh failed: ${res.status}`);
  return res.json();
}

export async function exportToVault(): Promise<{ ok: boolean; path: string }> {
  const res = await fetch(`${BASE}/metering/export`, { method: 'POST' });
  if (!res.ok) throw new Error(`metering/export failed: ${res.status}`);
  return res.json();
}

// ── Feed ──────────────────────────────────────────────────

export type FeedCategory = 'news' | 'ai-official';
export type FeedStatus = 'unread' | 'ingested' | 'dismissed';

export interface FeedItem {
  slug: string;           // e.g. "feed/2026-05-27-abc12345"
  title: string;
  url: string;
  source: string;
  category: FeedCategory;
  status: FeedStatus;
  fetched_at: string;     // ISO 8601
  summary: string;
}

export async function getFeedItems(): Promise<FeedItem[]> {
  const res = await fetch(`${BASE}/feed/items`);
  if (!res.ok) throw new Error(`feed/items failed: ${res.status}`);
  return ((await res.json()).items) as FeedItem[];
}

export async function refreshFeed(): Promise<{ ok: boolean; collected_at: string }> {
  const res = await fetch(`${BASE}/feed/refresh`, { method: 'POST' });
  if (!res.ok) throw new Error(`feed/refresh failed: ${res.status}`);
  return res.json();
}

export async function setFeedStatus(slug: string, status: FeedStatus): Promise<void> {
  const res = await fetch(`${BASE}/feed/status`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ slug, status }),
  });
  if (!res.ok) throw new Error(`feed/status failed: ${res.status}`);
}

export async function ingestFeedItems(
  slugs: string[],
  provider = 'anthropic',
  model = 'claude-sonnet-4-6',
): Promise<string[]> {
  const res = await fetch(`${BASE}/feed/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ slugs, provider, model }),
  });
  if (!res.ok) throw new Error(`feed/ingest failed: ${res.status}`);
  return ((await res.json()).op_ids) as string[];
}

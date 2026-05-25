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

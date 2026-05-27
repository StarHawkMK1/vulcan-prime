export interface NavItem { id: string; label: string; badge?: string }
export interface NavGroup { group: string; items: NavItem[] }

export const NAV: NavGroup[] = [
  { group: 'WORKSPACE', items: [
    { id: 'dashboard', label: 'Dashboard' },
  ]},
  { group: 'KNOWLEDGE', items: [
    { id: 'ingest', label: 'Ingest' },
    { id: 'query',  label: 'Query'  },
    { id: 'lint',   label: 'Lint'   },
    { id: 'vault',  label: 'Vault', badge: 'obsidian' },
    { id: 'tasks',  label: 'Tasks', badge: 'M4' },
  ]},
  { group: 'BUILD', items: [
    { id: 'playground', label: 'Playground',    badge: 'M2' },
    { id: 'prompts',    label: 'Prompt Library', badge: 'M2' },
    { id: 'skills',     label: 'Skills & Agents', badge: 'M2' },
  ]},
  { group: 'TEST', items: [
    { id: 'experiments', label: 'A/B Experiments', badge: 'M2' },
    { id: 'evals',       label: 'Evaluations',     badge: 'M2' },
  ]},
  { group: 'OPERATE', items: [
    { id: 'logs',      label: 'Logs & Traces', badge: 'M3' },
    { id: 'usage',     label: 'Usage & Cost',  badge: 'M3' },
    { id: 'providers', label: 'Providers',     badge: '3'  },
  ]},
  { group: 'DISCOVER', items: [
    { id: 'news', label: 'AI News' },
  ]},
];

export type ScreenId =
  | 'dashboard' | 'ingest' | 'query' | 'lint' | 'vault' | 'tasks'
  | 'playground' | 'prompts' | 'skills' | 'experiments' | 'evals'
  | 'logs' | 'usage' | 'providers' | 'news';

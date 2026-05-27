import React, { useState, useCallback } from 'react';
import './App.css';
import { AppShell } from './shell/AppShell';
import type { ScreenId } from './shell/nav';
import { Dashboard } from './screens/Dashboard';
import { Ingest } from './screens/Ingest';
import { Query } from './screens/Query';
import { Lint } from './screens/Lint';
import { Stub } from './screens/Stub';
import { Metering } from './screens/Metering';
import { Feed } from './screens/Feed';

const ROUTES: Record<ScreenId, {
  breadcrumb: string[]; status?: string; env?: string;
  component: (props: { onUnreadCount?: (n: number) => void }) => React.JSX.Element;
}> = {
  dashboard:   { breadcrumb: ['Workspace', 'Dashboard'], status: 'LIVE', env: 'local', component: () => <Dashboard /> },
  ingest:      { breadcrumb: ['Knowledge', 'Ingest'], env: 'local', component: () => <Ingest /> },
  query:       { breadcrumb: ['Knowledge', 'Query'], env: 'local', component: () => <Query /> },
  lint:        { breadcrumb: ['Knowledge', 'Lint'], env: 'local', component: () => <Lint /> },
  vault:       { breadcrumb: ['Knowledge', 'Vault'], status: 'SYNCED · obsidian', env: 'local', component: () => <Stub label="Vault" phase="M4" /> },
  tasks:       { breadcrumb: ['Knowledge', 'Tasks'], component: () => <Stub label="Tasks (Kanban)" phase="M4" /> },
  playground:  { breadcrumb: ['Build', 'Playground'], component: () => <Stub label="Playground" phase="M2" /> },
  prompts:     { breadcrumb: ['Build', 'Prompt Library'], component: () => <Stub label="Prompt Library" phase="M2" /> },
  skills:      { breadcrumb: ['Build', 'Skills & Agents'], component: () => <Stub label="Skills & Agents" phase="M2" /> },
  experiments: { breadcrumb: ['Test', 'A/B Experiments'], component: () => <Stub label="A/B Experiments" phase="M2" /> },
  evals:       { breadcrumb: ['Test', 'Evaluations'], component: () => <Stub label="Evaluations" phase="M2" /> },
  logs:        { breadcrumb: ['Operate', 'Logs & Traces'], component: () => <Stub label="Logs & Traces" phase="M3" /> },
  usage:       { breadcrumb: ['Operate', 'Usage & Cost'], status: 'LIVE', env: 'local', component: () => <Metering /> },
  providers:   { breadcrumb: ['Operate', 'Providers'], component: () => <Stub label="Providers" phase="M2" /> },
  news:        { breadcrumb: ['Discover', 'AI News'], status: 'LIVE', env: 'local',
                 component: ({ onUnreadCount }) => <Feed onUnreadCount={onUnreadCount} /> },
};

export default function App() {
  const [active, setActive] = useState<ScreenId>('dashboard');
  const [feedBadge, setFeedBadge] = useState(0);
  const route = ROUTES[active] ?? ROUTES.dashboard;

  const handleUnreadCount = useCallback((n: number) => setFeedBadge(n), []);

  return (
    <AppShell
      active={active}
      onNav={setActive}
      breadcrumb={route.breadcrumb}
      status={route.status}
      env={route.env}
      feedBadge={feedBadge}>
      {route.component({ onUnreadCount: handleUnreadCount })}
    </AppShell>
  );
}

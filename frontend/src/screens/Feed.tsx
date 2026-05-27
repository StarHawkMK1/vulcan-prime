import { useState, useEffect, useCallback } from 'react';
import { nebTokens as t, NebPanel, NebButton } from '../design';
import {
  getFeedItems, refreshFeed, setFeedStatus, ingestFeedItems,
  type FeedItem,
} from '../api';
import { FeedCard } from '../components/FeedCard';
import { LogStream } from '../components/LogStream';

type FilterCat = 'all' | 'news' | 'ai-official';

export function Feed({ onUnreadCount }: { onUnreadCount?: (n: number) => void }) {
  const [items, setItems]         = useState<FeedItem[]>([]);
  const [filter, setFilter]       = useState<FilterCat>('all');
  const [showDismissed, setShowDismissed] = useState(false);
  const [selected, setSelected]   = useState<Set<string>>(new Set());
  const [refreshing, setRefreshing] = useState(false);
  const [opIds, setOpIds]         = useState<string[]>([]);

  const load = useCallback(() => {
    getFeedItems().then((data) => {
      setItems(data);
      const unread = data.filter(i => i.status === 'unread').length;
      onUnreadCount?.(unread);
    }).catch(() => {});
  }, [onUnreadCount]);

  useEffect(() => {
    load();
    const id = setInterval(load, 30_000);
    return () => clearInterval(id);
  }, [load]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try { await refreshFeed(); load(); } finally { setRefreshing(false); }
  };

  const handleDismiss = async (slug: string) => {
    await setFeedStatus(slug, 'dismissed').catch(() => {});
    load();
  };

  const handleIngest = async () => {
    const slugs = [...selected];
    if (!slugs.length) return;
    const ids = await ingestFeedItems(slugs).catch(() => []);
    setOpIds(ids);
    setSelected(new Set());
    load();
  };

  const toggleSelect = (slug: string) => {
    setSelected(prev => {
      const next = new Set(prev);
      next.has(slug) ? next.delete(slug) : next.add(slug);
      return next;
    });
  };

  const visible = items.filter(i => {
    if (!showDismissed && i.status === 'dismissed') return false;
    if (filter !== 'all' && i.category !== filter) return false;
    return true;
  });

  const unreadCount = items.filter(i => i.status === 'unread').length;

  const CHIPS: { key: FilterCat; label: string }[] = [
    { key: 'all',         label: 'ALL'         },
    { key: 'news',        label: 'NEWS'        },
    { key: 'ai-official', label: 'AI OFFICIAL' },
  ];

  const chipStyle = (active: boolean): React.CSSProperties => ({
    fontFamily: t.mono, fontSize: 9.5, letterSpacing: 1,
    textTransform: 'uppercase', padding: '3px 10px',
    border: `1px solid ${active ? t.borderGlow : t.border}`,
    color: active ? t.cyan : t.textMuted,
    background: active ? 'rgba(122,240,255,0.12)' : t.bgDeep,
    cursor: 'pointer',
  });

  return (
    <div style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 14, maxWidth: 820 }}>
      {/* Header bar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{
          fontFamily: t.mono, fontSize: 11, fontWeight: 700,
          color: t.cyan, letterSpacing: 2, textTransform: 'uppercase',
          textShadow: `0 0 10px ${t.cyan}44`,
        }}>◈ Feed</span>
        <span style={{ fontFamily: t.mono, fontSize: 9.5, color: t.textFaint }}>
          {unreadCount} unread
        </span>
        <div style={{ flex: 1 }} />
        {unreadCount > 0 && (
          <button
            type="button"
            onClick={() => {
              const slugs = items.filter(i => i.status === 'unread').map(i => i.slug);
              setSelected(new Set(slugs));
            }}
            style={{ fontFamily: t.mono, fontSize: 9.5, color: t.textFaint, cursor: 'pointer',
              background: 'transparent', border: 'none' }}>
            select all unread
          </button>
        )}
        {selected.size > 0 && (
          <NebButton primary onClick={handleIngest}
            style={{ height: 28, fontSize: 9.5, padding: '0 14px' }}>
            {selected.size} selected → Ingest ↗
          </NebButton>
        )}
        <NebButton primary onClick={handleRefresh} disabled={refreshing}
          style={{ height: 28, fontSize: 9.5, padding: '0 12px' }}>
          {refreshing ? '…' : '↻ Refresh'}
        </NebButton>
      </div>

      {/* Filter chips */}
      <div style={{ display: 'flex', gap: 8 }}>
        {CHIPS.map(({ key, label }) => (
          <button key={key} type="button" style={chipStyle(filter === key)}
            onClick={() => setFilter(key)}>{label}</button>
        ))}
        <button type="button"
          style={{ ...chipStyle(showDismissed), marginLeft: 'auto' }}
          onClick={() => setShowDismissed(v => !v)}>
          {showDismissed ? 'hide dismissed' : 'show dismissed'}
        </button>
      </div>

      {/* Card list */}
      <NebPanel padding={0}>
        {visible.length === 0 ? (
          <div style={{ padding: '24px 18px', fontFamily: t.mono, fontSize: 11, color: t.textFaint }}>
            No items. Click ↻ Refresh to collect latest headlines.
          </div>
        ) : (
          visible.map(item => (
            <FeedCard
              key={item.slug}
              item={item}
              checked={selected.has(item.slug)}
              onCheck={() => toggleSelect(item.slug)}
              onDismiss={() => handleDismiss(item.slug)}
            />
          ))
        )}
      </NebPanel>

      {/* LogStream for active ingest */}
      {opIds.length > 0 && (
        <LogStream opId={opIds[0]} onDone={() => setOpIds([])} />
      )}
    </div>
  );
}

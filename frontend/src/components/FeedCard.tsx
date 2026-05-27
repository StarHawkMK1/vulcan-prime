import { nebTokens as t } from '../design';
import type { FeedItem } from '../api';

const STATUS_BORDER: Record<string, string> = {
  unread:    t.cyan,
  ingested:  '#00ff90',
  dismissed: t.border,
};
const CATEGORY_COLOR: Record<string, string> = {
  news:          t.warn,
  'ai-official': t.cyan,
};

function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const h = Math.floor(mins / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

export function FeedCard({ item, checked, onCheck, onDismiss }: {
  item: FeedItem;
  checked: boolean;
  onCheck: () => void;
  onDismiss: () => void;
}) {
  const borderColor = STATUS_BORDER[item.status] ?? t.border;
  const tagColor    = CATEGORY_COLOR[item.category] ?? t.textMuted;
  const domain      = (() => { try { return new URL(item.url).hostname; } catch { return ''; } })();

  return (
    <div style={{
      display: 'flex', alignItems: 'flex-start', gap: 10,
      padding: '10px 14px',
      borderLeft: `3px solid ${borderColor}`,
      boxShadow: item.status === 'unread' ? `inset 8px 0 16px -8px ${t.cyan}33` : 'none',
      borderBottom: `1px solid ${t.border}`,
      background: checked ? 'rgba(122,240,255,0.04)' : 'transparent',
    }}>
      {/* Custom checkbox */}
      <div
        onClick={onCheck}
        style={{
          width: 14, height: 14, marginTop: 2, flex: '0 0 auto',
          border: `1px solid ${checked ? t.cyan : t.border}`,
          background: checked ? `${t.cyan}33` : 'transparent',
          cursor: 'pointer',
        }}
      />
      {/* Source tag */}
      <span style={{
        fontFamily: t.mono, fontSize: 8.5, fontWeight: 600, letterSpacing: 0.8,
        padding: '2px 6px', border: `1px solid ${tagColor}44`,
        color: tagColor, background: `${tagColor}12`,
        flex: '0 0 auto', marginTop: 1,
      }}>
        {item.source.slice(0, 8).toUpperCase()}
      </span>
      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontSize: 13, color: t.text, fontFamily: t.font,
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        }}>
          <a href={item.url} target="_blank" rel="noopener noreferrer"
            style={{ color: 'inherit', textDecoration: 'none' }}>
            {item.title}
          </a>
        </div>
        <div style={{ fontSize: 10, fontFamily: t.mono, color: t.textFaint, marginTop: 2 }}>
          {domain}
        </div>
      </div>
      {/* Right side */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4, flex: '0 0 auto' }}>
        <span style={{ fontFamily: t.mono, fontSize: 9, color: t.textFaint }}>
          {timeAgo(item.fetched_at)}
        </span>
        <button
          type="button"
          onClick={onDismiss}
          style={{
            fontFamily: t.mono, fontSize: 9, color: t.textFaint,
            cursor: 'pointer', padding: '1px 5px',
            border: `1px solid ${t.border}`,
            background: 'transparent',
          }}>
          dismiss ×
        </button>
      </div>
    </div>
  );
}

import { useState } from 'react';
import type { ReactNode } from 'react';
import { nebTokens as t, NebulaBackdrop } from '../design';
import { NAV } from './nav';
import type { ScreenId } from './nav';
import { NavIcon } from './NavIcon';

interface Props {
  active: ScreenId;
  onNav: (id: ScreenId) => void;
  breadcrumb: string[];
  status?: string;
  env?: string;
  actions?: ReactNode;
  children: ReactNode;
}

export function AppShell({ active, onNav, breadcrumb, status, env, actions, children }: Props) {
  const [collapsed, setCollapsed] = useState(false);
  const sidebarW = collapsed ? 64 : 240;

  return (
    <div style={{
      position: 'relative', width: '100vw', height: '100vh', overflow: 'hidden',
      background: t.bg, color: t.text, fontFamily: t.font, display: 'flex',
    }}>
      <NebulaBackdrop seed={11} />

      {/* Sidebar */}
      <aside style={{
        position: 'relative', zIndex: 2, width: sidebarW, height: '100%',
        background: 'linear-gradient(180deg, rgba(2,5,13,0.92), rgba(4,8,20,0.85))',
        borderRight: `1px solid ${t.border}`, display: 'flex', flexDirection: 'column',
        transition: 'width .22s cubic-bezier(.4,.0,.2,1)', flex: '0 0 auto',
      }}>
        {/* Logo row */}
        <div style={{
          height: 60, padding: collapsed ? '0' : '0 16px',
          display: 'flex', alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'space-between',
          borderBottom: `1px solid ${t.border}`,
        }}>
          {!collapsed ? (
            <>
              <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
                <svg width="24" height="24" viewBox="0 0 22 22" fill="none">
                  <circle cx="11" cy="11" r="9" stroke={t.cyan} strokeWidth="1.2"/>
                  <circle cx="11" cy="11" r="3.2" fill={t.cyan}/>
                  <line x1="2" y1="11" x2="20" y2="11" stroke={t.cyan} strokeWidth="0.6" strokeOpacity="0.6"/>
                </svg>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, letterSpacing: 1.6, color: t.text }}>VULCAN</div>
                  <div style={{ fontSize: 9, fontFamily: t.mono, color: t.textFaint, letterSpacing: 0.8 }}>PRIME · v0.1</div>
                </div>
              </div>
              <button type="button" onClick={() => setCollapsed(true)} style={{
                width: 26, height: 26, background: 'transparent', border: `1px solid ${t.border}`,
                color: t.textMuted, cursor: 'pointer', fontFamily: t.mono, fontSize: 12,
              }}>«</button>
            </>
          ) : (
            <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
              <circle cx="11" cy="11" r="9" stroke={t.cyan} strokeWidth="1.2"/>
              <circle cx="11" cy="11" r="3.2" fill={t.cyan}/>
            </svg>
          )}
        </div>

        {/* Nav */}
        <nav style={{ flex: 1, overflowY: 'auto', overflowX: 'hidden', padding: '10px 0' }}>
          {NAV.map((g) => (
            <div key={g.group} style={{ marginBottom: 6 }}>
              {!collapsed && (
                <div style={{ fontSize: 9.5, fontWeight: 600, fontFamily: t.mono, letterSpacing: 1.3,
                  color: t.textFaint, padding: '10px 18px 5px' }}>{g.group}</div>
              )}
              {collapsed && <div style={{ height: 12 }} />}
              {g.items.map((it) => {
                const isActive = it.id === active;
                return (
                  <button key={it.id} type="button" onClick={() => onNav(it.id as ScreenId)}
                    title={collapsed ? it.label : undefined}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 11,
                      width: '100%', padding: collapsed ? '10px 0' : '8px 18px',
                      justifyContent: collapsed ? 'center' : 'flex-start',
                      background: isActive ? 'rgba(122,240,255,0.08)' : 'transparent',
                      border: 'none',
                      borderLeft: isActive ? `2px solid ${t.cyan}` : '2px solid transparent',
                      color: isActive ? t.text : t.textMuted,
                      fontSize: 12.5, fontFamily: t.font, fontWeight: isActive ? 500 : 400,
                      textAlign: 'left', cursor: 'pointer',
                      boxShadow: isActive ? `inset 8px 0 16px -8px ${t.cyan}55` : 'none',
                    }}>
                    <NavIcon id={it.id} color={isActive ? t.cyan : t.textMuted} />
                    {!collapsed && <span style={{ flex: 1 }}>{it.label}</span>}
                    {!collapsed && it.badge && (
                      <span style={{ fontSize: 9, fontFamily: t.mono, color: t.cyan,
                        padding: '1px 6px', border: `1px solid ${t.border}`, letterSpacing: 0.5 }}>{it.badge}</span>
                    )}
                  </button>
                );
              })}
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div style={{ borderTop: `1px solid ${t.border}`, padding: collapsed ? '10px 0' : '12px 16px',
          display: 'flex', alignItems: 'center', gap: 10, justifyContent: collapsed ? 'center' : 'flex-start',
          position: 'relative' }}>
          <div style={{ width: 28, height: 28, borderRadius: '50%',
            background: 'linear-gradient(135deg, #2f81f7, #7af0ff)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 11, fontWeight: 700, color: '#04101a', flex: '0 0 auto' }}>VP</div>
          {!collapsed && (
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 11.5, fontWeight: 500, color: t.text }}>vulcan-prime</div>
              <div style={{ fontSize: 9.5, fontFamily: t.mono, color: t.textFaint }}>
                <span style={{ display: 'inline-block', width: 5, height: 5, borderRadius: 3,
                  background: t.cyan, marginRight: 5, boxShadow: `0 0 4px ${t.cyan}` }} />
                all systems ok
              </div>
            </div>
          )}
          {collapsed && (
            <button type="button" onClick={() => setCollapsed(false)} style={{
              position: 'absolute', bottom: 50, right: -13, width: 26, height: 26,
              background: t.bgDeep, border: `1px solid ${t.borderGlow}`,
              color: t.cyan, cursor: 'pointer', fontFamily: t.mono, fontSize: 12,
              boxShadow: `0 0 10px ${t.cyan}44`,
            }}>»</button>
          )}
        </div>
      </aside>

      {/* Main */}
      <main style={{ position: 'relative', zIndex: 1, flex: 1, minWidth: 0, height: '100%',
        display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Header */}
        <div style={{ height: 60, display: 'flex', alignItems: 'center', padding: '0 26px', gap: 14,
          borderBottom: `1px solid ${t.border}`,
          background: 'linear-gradient(180deg, rgba(4,8,20,0.85), rgba(4,8,20,0.4))',
          backdropFilter: 'blur(6px)', flex: '0 0 auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontFamily: t.mono, fontSize: 12.5 }}>
            {breadcrumb.map((b, i, a) => (
              <span key={i} style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                {i > 0 && <span style={{ color: t.textFaint }}>/</span>}
                <span style={{ color: i === a.length - 1 ? t.cyan : t.textMuted,
                  fontWeight: i === a.length - 1 ? 500 : 400 }}>{b}</span>
              </span>
            ))}
          </div>
          <div style={{ flex: 1 }} />
          {status && (
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 7, padding: '4px 10px',
              border: `1px solid ${t.borderGlow}`, color: t.cyan, fontFamily: t.mono, fontSize: 10.5,
              letterSpacing: 1, textTransform: 'uppercase',
              boxShadow: `0 0 12px ${t.cyan}33, inset 0 0 12px ${t.cyan}1c` }}>
              <span style={{ width: 6, height: 6, borderRadius: 3, background: t.cyan,
                boxShadow: `0 0 8px ${t.cyan}` }} />{status}
            </div>
          )}
          {env && (
            <div style={{ fontFamily: t.mono, fontSize: 11, color: t.textMuted, padding: '4px 10px',
              border: `1px solid ${t.border}` }}>
              env: <span style={{ color: t.cyanSoft }}>{env}</span>
            </div>
          )}
          {actions && <div style={{ display: 'flex', gap: 8 }}>{actions}</div>}
        </div>
        <div style={{ flex: 1, minHeight: 0, overflow: 'auto' }}>{children}</div>
      </main>
    </div>
  );
}

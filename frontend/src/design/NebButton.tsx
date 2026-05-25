import type { ReactNode, CSSProperties } from 'react';
import { nebTokens as t } from './tokens';

interface Props {
  children: ReactNode;
  primary?: boolean;
  ghost?: boolean;
  onClick?: () => void;
  disabled?: boolean;
  style?: CSSProperties;
}

export function NebButton({ children, primary, ghost, onClick, disabled, style }: Props) {
  const base: CSSProperties = {
    height: 32, padding: '0 16px', fontSize: 11.5, fontWeight: primary ? 600 : 500,
    letterSpacing: 1.2, textTransform: 'uppercase', fontFamily: t.mono,
    cursor: disabled ? 'not-allowed' : 'pointer', opacity: disabled ? 0.45 : 1,
    display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 6,
    ...style,
  };
  if (primary) return (
    <button type="button" disabled={disabled} onClick={onClick} style={{
      ...base,
      background: 'linear-gradient(180deg, rgba(122,240,255,0.18), rgba(47,129,247,0.18))',
      color: t.cyan, border: `1px solid ${t.borderGlow}`,
      boxShadow: `0 0 16px ${t.cyan}33, inset 0 0 12px ${t.cyan}22`,
    }}>{children}</button>
  );
  return (
    <button type="button" disabled={disabled} onClick={onClick} style={{
      ...base, background: ghost ? 'transparent' : t.bgGlass,
      color: t.text, border: `1px solid ${t.border}`,
    }}>{children}</button>
  );
}

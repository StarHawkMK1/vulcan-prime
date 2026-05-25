import { ReactNode } from 'react';
import { nebTokens as t } from './tokens';

export function NebLabel({ children, glow }: { children: ReactNode; glow?: boolean }) {
  return (
    <div style={{
      fontSize: 9.5, fontWeight: 600, fontFamily: t.mono,
      color: glow ? t.cyan : t.textMuted,
      letterSpacing: 1.4, textTransform: 'uppercase', marginBottom: 7,
    }}>{children}</div>
  );
}

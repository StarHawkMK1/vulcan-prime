import { ReactNode, CSSProperties } from 'react';
import { nebTokens as t } from './tokens';
import { Corner } from './Corner';

interface Props { children: ReactNode; glow?: boolean; style?: CSSProperties; padding?: number }

export function NebPanel({ children, glow, style, padding = 16 }: Props) {
  return (
    <div style={{
      position: 'relative',
      background: glow ? t.bgGlassHi : t.bgGlass,
      border: `1px solid ${glow ? t.borderGlow : t.border}`,
      boxShadow: glow ? `0 0 24px ${t.cyan}22, inset 0 0 16px ${t.cyan}10` : 'none',
      backdropFilter: 'blur(8px)', padding, ...style,
    }}>
      {glow && (<><Corner x={-1} y={-1}/><Corner x={1} y={-1}/><Corner x={-1} y={1}/><Corner x={1} y={1}/></>)}
      {children}
    </div>
  );
}

import { nebTokens as t } from './tokens';

export function Corner({ x, y }: { x: -1 | 1; y: -1 | 1 }) {
  return (
    <div style={{
      position: 'absolute',
      [x < 0 ? 'left' : 'right']: -1, [y < 0 ? 'top' : 'bottom']: -1,
      width: 10, height: 10,
      borderLeft:   x < 0 ? `1.5px solid ${t.cyan}` : 'none',
      borderRight:  x > 0 ? `1.5px solid ${t.cyan}` : 'none',
      borderTop:    y < 0 ? `1.5px solid ${t.cyan}` : 'none',
      borderBottom: y > 0 ? `1.5px solid ${t.cyan}` : 'none',
      boxShadow: `0 0 8px ${t.cyan}`,
    }} />
  );
}

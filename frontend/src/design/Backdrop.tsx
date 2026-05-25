import { useMemo } from 'react';
import { nebTokens as t } from './tokens';

export function NebulaBackdrop({ seed = 1 }: { seed?: number }) {
  const stars = useMemo(() => {
    const out: { x: number; y: number; r: number; o: number }[] = [];
    let s = seed * 9301 + 49297;
    const rand = () => { s = (s * 9301 + 49297) % 233280; return s / 233280; };
    for (let i = 0; i < 220; i++)
      out.push({ x: rand() * 1440, y: rand() * 900, r: rand() * 1.1 + 0.2, o: rand() * 0.7 + 0.15 });
    return out;
  }, [seed]);

  return (
    <svg viewBox="0 0 1440 900" preserveAspectRatio="none"
      style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
      <defs>
        <radialGradient id={`neb-glow-${seed}`} cx="50%" cy="65%" r="55%">
          <stop offset="0%"   stopColor="#1a4a78" stopOpacity="0.55"/>
          <stop offset="55%"  stopColor="#0a1830" stopOpacity="0.15"/>
          <stop offset="100%" stopColor="#020410" stopOpacity="0"/>
        </radialGradient>
        <linearGradient id={`neb-arc-${seed}`} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%"   stopColor={t.cyan} stopOpacity="0"/>
          <stop offset="50%"  stopColor={t.cyan} stopOpacity="0.55"/>
          <stop offset="100%" stopColor={t.cyan} stopOpacity="0"/>
        </linearGradient>
        <filter id={`neb-blur-${seed}`}><feGaussianBlur stdDeviation="0.5"/></filter>
      </defs>
      <rect width="1440" height="900" fill={t.bgDeep}/>
      <rect width="1440" height="900" fill={`url(#neb-glow-${seed})`}/>
      {stars.map((s2, i) => <circle key={i} cx={s2.x} cy={s2.y} r={s2.r} fill="#aedcff" fillOpacity={s2.o}/>)}
      <line x1="0" y1="540" x2="1440" y2="540" stroke={`url(#neb-arc-${seed})`} strokeWidth="1.2"/>
      <line x1="0" y1="540" x2="1440" y2="540" stroke={`url(#neb-arc-${seed})`} strokeWidth="3" opacity="0.35" filter={`url(#neb-blur-${seed})`}/>
      <path d="M -200 980 Q 720 -120 1640 980" fill="none" stroke={t.cyan} strokeOpacity="0.18" strokeWidth="0.8"/>
      <path d="M -200 1100 Q 720 -200 1640 1100" fill="none" stroke={t.cyan} strokeOpacity="0.10" strokeWidth="0.6"/>
      <path d="M 1640 -80 Q 700 540 -200 1160" fill="none" stroke={t.cyan} strokeOpacity="0.13" strokeWidth="0.6"/>
      <ellipse cx="720" cy="540" rx="1200" ry="180" fill="none" stroke={t.cyan} strokeOpacity="0.08" strokeWidth="0.6"/>
    </svg>
  );
}

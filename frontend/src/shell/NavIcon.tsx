interface Props { id: string; color: string }

export function NavIcon({ id, color }: Props) {
  const p = {
    width: 16, height: 16, viewBox: '0 0 16 16', fill: 'none',
    stroke: color, strokeWidth: 1.3,
    strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const,
  };
  switch (id) {
    case 'dashboard':   return <svg {...p}><rect x="2" y="2" width="5" height="5"/><rect x="9" y="2" width="5" height="5"/><rect x="2" y="9" width="5" height="5"/><rect x="9" y="9" width="5" height="5"/></svg>;
    case 'ingest':      return <svg {...p}><path d="M8 2v8M4 7l4 4 4-4M3 13h10"/></svg>;
    case 'query':       return <svg {...p}><circle cx="6" cy="6" r="4"/><path d="M10 10l3 3"/></svg>;
    case 'lint':        return <svg {...p}><path d="M2 8l4 4 8-9"/></svg>;
    case 'vault':       return <svg {...p}><path d="M3 4l5-2 5 2v6c0 2.5-2.2 4-5 4s-5-1.5-5-4z"/><circle cx="8" cy="7" r="1.4"/></svg>;
    case 'tasks':       return <svg {...p}><rect x="2" y="3" width="3.5" height="10"/><rect x="6.3" y="3" width="3.5" height="6"/><rect x="10.5" y="3" width="3.5" height="8"/></svg>;
    case 'playground':  return <svg {...p}><path d="M2 4h12M2 8h12M2 12h8"/></svg>;
    case 'prompts':     return <svg {...p}><path d="M3 2h7l3 3v9H3z"/><path d="M10 2v3h3M5 8h6M5 11h4"/></svg>;
    case 'skills':      return <svg {...p}><circle cx="5" cy="5" r="2.2"/><circle cx="11" cy="5" r="2.2"/><circle cx="8" cy="11" r="2.2"/><path d="M5 7l3 2M11 7l-3 2"/></svg>;
    case 'experiments': return <svg {...p}><path d="M6 2v4l-3 7c-.3.7.2 1.5 1 1.5h8c.8 0 1.3-.8 1-1.5L10 6V2M4.5 2h7"/></svg>;
    case 'evals':       return <svg {...p}><path d="M2 8l4 4 8-9"/></svg>;
    case 'logs':        return <svg {...p}><path d="M3 3l1 11h8l1-11z"/><path d="M5 6h6M5 9h6M5 12h4"/></svg>;
    case 'usage':       return <svg {...p}><path d="M2 14h12"/><path d="M4 11V8M7 11V4M10 11V6M13 11V9"/></svg>;
    case 'providers':   return <svg {...p}><circle cx="8" cy="8" r="5.5"/><path d="M2.5 8h11M8 2.5C9.8 4 10.8 6 10.8 8S9.8 12 8 13.5C6.2 12 5.2 10 5.2 8S6.2 4 8 2.5z"/></svg>;
    case 'news':        return <svg {...p}><rect x="2" y="3" width="12" height="10"/><path d="M5 6h6M5 9h6M5 12h3"/></svg>;
    default:            return null;
  }
}

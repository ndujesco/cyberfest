import { SEV } from '../data';

export default function Badge({ sev }) {
  const s = SEV[sev] || SEV.low;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      background: s.bg, border: `1px solid ${s.bd}`, color: s.color,
      borderRadius: 5, padding: '3px 10px', fontSize: 11, fontWeight: 700,
      letterSpacing: .5, whiteSpace: 'nowrap',
    }}>
      {s.icon} {s.label}
    </span>
  );
}

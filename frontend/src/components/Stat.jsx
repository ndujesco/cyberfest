import { P } from '../data';

export default function Stat({ value, label, color, sub }) {
  return (
    <div style={{ background: P.card, border: `1px solid ${P.border}`, borderRadius: 12, padding: '18px 22px', flex: 1, minWidth: 110 }}>
      <div style={{ fontSize: 34, fontWeight: 900, color, lineHeight: 1 }}>{value}</div>
      <div style={{ color: P.muted, fontSize: 12, marginTop: 5, lineHeight: 1.3 }}>{label}</div>
      {sub && <div style={{ color: P.dim, fontSize: 11, marginTop: 3 }}>{sub}</div>}
    </div>
  );
}

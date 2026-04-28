import { P } from '../data';

export default function ScoreGauge({ score }) {
  const color = score >= 8 ? P.red : score >= 6 ? P.orange : P.yellow;
  return (
    <div style={{
      background: P.card, border: `1px solid ${P.border}`, borderRadius: 12,
      padding: '18px 22px', display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', minWidth: 130,
    }}>
      <div style={{ fontSize: 38, fontWeight: 900, color, lineHeight: 1 }}>{score}</div>
      <div style={{ color: P.muted, fontSize: 11, marginTop: 3, textAlign: 'center', letterSpacing: .5 }}>/ 10</div>
      <div style={{ width: '100%', height: 5, background: P.card2, borderRadius: 3, marginTop: 10, overflow: 'hidden' }}>
        <div style={{ width: `${score * 10}%`, height: '100%', background: color, borderRadius: 3, transition: 'width 1.2s ease' }} />
      </div>
      <div style={{ color, fontSize: 10, fontWeight: 700, marginTop: 6, letterSpacing: 1 }}>RISK SCORE</div>
    </div>
  );
}

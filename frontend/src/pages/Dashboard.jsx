import { P, TDATA } from '../data';
import ScoreGauge from '../components/ScoreGauge';
import Stat from '../components/Stat';
import FindingCard from '../components/FindingCard';
import AttackPath from '../components/AttackPath';

export default function Dashboard({ active, setActive, count, pathVis, exp, setExp }) {
  const d = TDATA[active];
  const shown = d.findings.slice(0, count);

  return (
    <div style={{ flex: 1, overflowY: 'auto', padding: '22px 28px' }}>
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        <ScoreGauge score={d.score} />
        <Stat value={d.stats.critical} label="Critical" color={P.red}    sub="Immediate action needed" />
        <Stat value={d.stats.high}     label="High"     color={P.orange}  sub="Fix within 24 hours" />
        <Stat value={d.stats.medium}   label="Medium"   color={P.yellow}  sub="Fix within 7 days" />
      </div>

      <div style={{
        background: P.card, border: `1px solid ${P.border}`, borderRadius: 8,
        padding: '9px 16px', marginBottom: 18,
        display: 'flex', alignItems: 'center', gap: 12, fontSize: 12, flexWrap: 'wrap',
      }}>
        <span style={{ color: P.green, fontWeight: 600 }}>✓ Scan complete</span>
        <span style={{ color: P.border }}>|</span>
        <span style={{ color: P.text, fontFamily: 'monospace' }}>{d.target}</span>
        <span style={{ color: P.border }}>|</span>
        <span style={{ color: P.dim }}>Completed in {d.time}</span>
      </div>

      {active === 'pathforge' && <AttackPath visible={pathVis} />}

      {shown.length > 0 && (
        <div>
          <div style={{ color: P.dim, fontSize: 10, fontWeight: 700, letterSpacing: 1.2, marginBottom: 10 }}>
            FINDINGS — {shown.length} of {d.findings.length}
          </div>
          {shown.map((f, i) => (
            <FindingCard
              key={f.id} f={f} delay={i * 60}
              expanded={exp === f.id}
              onToggle={() => setExp(p => p === f.id ? null : f.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

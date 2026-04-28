import { P, SEV } from '../data';
import Badge from './Badge';

export default function FindingCard({ f, delay = 0, expanded, onToggle }) {
  const s = SEV[f.sev] || SEV.low;
  return (
    <div
      className="fade-up"
      onClick={onToggle}
      style={{
        background: P.card, border: `1px solid ${P.border}`,
        borderLeft: `3px solid ${s.color}`, borderRadius: 8,
        marginBottom: 8, cursor: 'pointer',
        animationDelay: `${delay}ms`, opacity: 0,
        overflow: 'hidden', transition: 'border-color .2s',
      }}
    >
      <div style={{ padding: '14px 18px', display: 'flex', alignItems: 'flex-start', gap: 12 }}>
        <Badge sev={f.sev} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ color: P.text, fontWeight: 600, fontSize: 14, lineHeight: 1.4 }}>{f.title}</div>
          <div style={{ color: P.dim, fontSize: 11, marginTop: 4, fontFamily: 'monospace' }}>📍 {f.loc}</div>
        </div>
        <div style={{ color: P.dim, fontSize: 13, flexShrink: 0, marginTop: 1 }}>{expanded ? '▲' : '▼'}</div>
      </div>

      {expanded && (
        <div style={{ borderTop: `1px solid ${P.border}`, padding: '16px 18px', display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <div style={{ color: P.muted, fontSize: 10, fontWeight: 700, letterSpacing: 1, marginBottom: 6 }}>WHAT HAPPENED</div>
            <div style={{ color: P.text, fontSize: 13, lineHeight: 1.65 }}>{f.what}</div>
          </div>
          <div style={{ background: s.bg, border: `1px solid ${s.bd}`, borderRadius: 7, padding: '12px 14px' }}>
            <div style={{ color: s.color, fontSize: 10, fontWeight: 700, letterSpacing: 1, marginBottom: 6 }}>⚡ BUSINESS IMPACT</div>
            <div style={{ color: P.text, fontSize: 13, lineHeight: 1.65 }}>{f.impact}</div>
          </div>
          <details style={{ cursor: 'pointer' }}>
            <summary style={{ color: P.dim, fontSize: 12, userSelect: 'none', outline: 'none' }}>Technical detail ▸</summary>
            <div style={{
              marginTop: 8, fontFamily: 'monospace', fontSize: 11.5,
              color: '#94a3b8', background: '#070b13', padding: '10px 12px',
              borderRadius: 5, lineHeight: 1.7, wordBreak: 'break-word',
            }}>{f.tech}</div>
          </details>
          <div>
            <div style={{ color: P.green, fontSize: 10, fontWeight: 700, letterSpacing: 1, marginBottom: 6 }}>✅ HOW TO FIX</div>
            <div style={{ color: P.text, fontSize: 13, lineHeight: 1.65 }}>{f.fix}</div>
          </div>
        </div>
      )}
    </div>
  );
}

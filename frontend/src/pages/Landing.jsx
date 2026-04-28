import { P, CB, TOOLS } from '../data';

export default function Landing({ typed, ready }) {
  const full = CB.target;
  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: P.bg, padding: 40, gap: 0 }}>
      <div className="fade-up" style={{ textAlign: 'center', marginBottom: 52 }}>
        <div style={{ fontSize: 52, marginBottom: 16 }}>🔒</div>
        <div style={{ fontSize: 42, fontWeight: 900, letterSpacing: -1, color: P.text }}>Zer0day Saints</div>
        <div style={{ color: P.muted, fontSize: 17, marginTop: 10 }}>Hackathon Tool Clusters · Security Scanner Demo</div>
      </div>

      <div className="fade-up" style={{ width: '100%', maxWidth: 660, animationDelay: '120ms', opacity: 0 }}>
        <div style={{ color: P.muted, fontSize: 12, marginBottom: 8, letterSpacing: .3 }}>Repository or target URL</div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'stretch' }}>
          <div style={{
            flex: 1, background: P.card,
            border: `1.5px solid ${ready ? P.blue : P.border}`,
            borderRadius: 10, padding: '13px 16px',
            fontFamily: 'monospace', fontSize: 15, color: P.text,
            transition: 'border-color .4s, box-shadow .4s',
            boxShadow: ready ? `0 0 0 3px ${P.blue}18` : undefined,
            display: 'flex', alignItems: 'center', minHeight: 50,
          }}>
            <span>{typed}</span>
            {typed.length < full.length && (
              <span style={{
                display: 'inline-block', width: 2, height: '1.1em',
                background: P.blue, verticalAlign: 'text-bottom',
                marginLeft: 1, animation: 'blink .7s step-end infinite',
              }} />
            )}
          </div>
          <div style={{
            background: ready ? P.blue : '#1e293b',
            color: ready ? '#fff' : P.dim,
            borderRadius: 10, padding: '0 24px', fontWeight: 700, fontSize: 14,
            display: 'flex', alignItems: 'center',
            transition: 'background .4s, color .4s',
            animation: ready ? 'glow 2s ease-in-out infinite' : undefined,
            whiteSpace: 'nowrap',
          }}>
            ▶ Run Scan
          </div>
        </div>

        <div style={{ display: 'flex', gap: 10, marginTop: 18, flexWrap: 'wrap' }}>
          {TOOLS.map(t => (
            <div key={t.id} style={{
              background: P.card, border: `1px solid ${P.border}`,
              borderRadius: 20, padding: '6px 14px', fontSize: 12,
              color: P.muted, display: 'flex', alignItems: 'center', gap: 5,
            }}>
              {t.icon}<span style={{ fontWeight: 600 }}>{t.name}</span>
              <span style={{ color: P.dim }}>·</span>{t.sub}
            </div>
          ))}
        </div>
      </div>

      <div className="fade-up" style={{ display: 'flex', gap: 48, marginTop: 64, animationDelay: '240ms', opacity: 0 }}>
        {[['10', 'Security Tools'], ['3', 'Unified Workflows'], ['< 30s', 'Per Full Scan']].map(([v, l]) => (
          <div key={l} style={{ textAlign: 'center' }}>
            <div style={{ color: P.text, fontSize: 28, fontWeight: 900 }}>{v}</div>
            <div style={{ color: P.muted, fontSize: 12, marginTop: 4 }}>{l}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

import { useState, useEffect } from 'react';
import { P, TDATA } from '../data';

export default function Scanning({ tool, onDone }) {
  const d = TDATA[tool];
  const [prog, setprog] = useState(d.phases.map(() => 0));
  const [done, setDone] = useState(false);

  useEffect(() => {
    let cancel = false;
    (async () => {
      for (let i = 0; i < d.phases.length; i++) {
        if (cancel) return;
        const ms = d.phases[i].ms, t0 = Date.now();
        await new Promise(res => {
          const tick = () => {
            if (cancel) { res(); return; }
            const p = Math.min(1, (Date.now() - t0) / ms);
            setprog(prev => { const n = [...prev]; n[i] = p; return n; });
            if (p < 1) requestAnimationFrame(tick); else res();
          };
          requestAnimationFrame(tick);
        });
        if (!cancel) await new Promise(r => setTimeout(r, 280));
      }
      if (!cancel) { setDone(true); setTimeout(onDone, 700); }
    })();
    return () => { cancel = true; };
  }, []);

  return (
    <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', background: P.bg, padding: 40 }}>
      <div style={{ width: '100%', maxWidth: 520 }}>
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <div style={{ fontSize: 42, display: 'inline-block', animation: done ? undefined : 'spin 1.8s linear infinite' }}>
            {done ? '✅' : '⚙️'}
          </div>
          <div style={{ color: P.text, fontSize: 22, fontWeight: 700, marginTop: 14 }}>{done ? 'Scan complete' : 'Scanning…'}</div>
          <div style={{ color: P.muted, fontSize: 13, marginTop: 6, fontFamily: 'monospace' }}>{d.target}</div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {d.phases.map((ph, i) => {
            const p = prog[i], ok = p >= 1;
            return (
              <div key={ph.name} style={{
                background: P.card, border: `1px solid ${P.border}`,
                borderRadius: 10, padding: 18, transition: 'border-color .3s',
                borderColor: ok ? `${P.green}40` : P.border,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ fontSize: 20 }}>{ph.icon}</span>
                    <div>
                      <div style={{ color: P.text, fontWeight: 600, fontSize: 14 }}>{ph.name}</div>
                      <div style={{ color: P.muted, fontSize: 11, marginTop: 2 }}>{ph.label}</div>
                    </div>
                  </div>
                  <div style={{ color: ok ? P.green : P.muted, fontWeight: 600, fontSize: 12, minWidth: 42, textAlign: 'right' }}>
                    {ok ? '✓ Done' : `${Math.round(p * 100)}%`}
                  </div>
                </div>
                <div style={{ height: 5, background: P.card2, borderRadius: 3, overflow: 'hidden' }}>
                  <div style={{ width: `${p * 100}%`, height: '100%', background: ok ? P.green : P.blue, borderRadius: 3, transition: 'background .4s' }} />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

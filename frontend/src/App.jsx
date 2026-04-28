import { useState, useEffect, useRef, useCallback } from 'react';
import { P, CB, SA, PF, TOOLS, TDATA } from './data';
import Landing from './pages/Landing';
import Scanning from './pages/Scanning';
import Dashboard from './pages/Dashboard';
import Report from './components/Report';

export default function App() {
  const [view, setView] = useState('landing');
  const [spaces, setSpaces] = useState(0);
  const [typed, setTyped] = useState('');
  const [scanReady, setScanReady] = useState(false);
  const [active, setActive] = useState('chainbreak');
  const [count, setCount] = useState(0);
  const [exp, setExp] = useState(null);
  const [pathVis, setPathVis] = useState(0);
  const [report, setReport] = useState(false);
  const scanning = useRef(false);

  useEffect(() => {
    const full = CB.target;
    let i = 0, cancelled = false;
    const typeNext = () => {
      if (cancelled) return;
      if (i <= full.length) {
        setTyped(full.slice(0, i));
        const ch = full[i] || '';
        let delay = 38 + Math.random() * 72;
        if (ch === '/' || ch === ':' || ch === '.') delay += 55 + Math.random() * 90;
        if (Math.random() < 0.08) delay += 130 + Math.random() * 180;
        i++;
        setTimeout(typeNext, delay);
      } else {
        setTimeout(() => setScanReady(true), 400);
      }
    };
    setTimeout(typeNext, 300);
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    const h = (e) => {
      if (e.code !== 'Space') return;
      e.preventDefault();
      if (scanning.current) return;
      setSpaces(s => s + 1);
    };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, []);

  useEffect(() => {
    if (spaces === 0) return;
    if (view === 'landing') {
      setView('scanning');
      scanning.current = true;
    } else if (view === 'dashboard') {
      const dashSpace = spaces - 1;
      if (dashSpace === 1) {
        setCount(TDATA[active].findings.length);
      } else if (dashSpace === 2) {
        setActive('specterapi'); setCount(0); setExp(null);
        setTimeout(() => setCount(SA.findings.length), 200);
      } else if (dashSpace === 3) {
        setActive('pathforge'); setCount(0); setExp(null);
        let n = 0;
        const iv = setInterval(() => { n++; setPathVis(n); if (n >= PF.path.length + 1) clearInterval(iv); }, 520);
        setTimeout(() => setCount(PF.findings.length), 2600);
      } else if (dashSpace >= 4) {
        setReport(true);
      }
    }
  }, [spaces]);

  const onScanDone = useCallback(() => {
    scanning.current = false;
    setView('dashboard');
    setActive('chainbreak');
    setCount(2);
    setExp(null);
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: P.bg, color: P.text }}>
      {report && <Report onClose={() => setReport(false)} />}

      {view === 'landing' && <Landing typed={typed} ready={scanReady} />}
      {view === 'scanning' && <Scanning tool="chainbreak" onDone={onScanDone} />}

      {view === 'dashboard' && (
        <>
          <div style={{
            background: P.card, borderBottom: `1px solid ${P.border}`,
            padding: '0 24px', display: 'flex', alignItems: 'center',
            height: 55, gap: 0, flexShrink: 0,
          }}>
            <div style={{ fontWeight: 800, fontSize: 16, marginRight: 28, display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>🔒</span><span>Zer0day Saints</span>
            </div>
            {TOOLS.map(t => {
              const on = active === t.id;
              return (
                <button
                  key={t.id}
                  onClick={() => { setActive(t.id); setCount(TDATA[t.id].findings.length); setExp(null); }}
                  style={{
                    background: 'none', border: 'none',
                    borderBottom: `2px solid ${on ? P.blue : 'transparent'}`,
                    color: on ? P.blue : P.muted,
                    padding: '0 18px', height: 55, cursor: 'pointer',
                    fontSize: 13, fontWeight: on ? 700 : 400,
                    transition: 'all .2s', whiteSpace: 'nowrap',
                  }}
                >
                  {t.icon} {t.name}
                </button>
              );
            })}
            <div style={{ flex: 1 }} />
            <button
              onClick={() => setReport(true)}
              style={{ background: P.blue, color: '#fff', border: 'none', borderRadius: 8, padding: '8px 16px', fontWeight: 700, fontSize: 12, cursor: 'pointer' }}
            >
              📊 Full Report
            </button>
          </div>
          <Dashboard active={active} setActive={setActive} count={count} pathVis={pathVis} exp={exp} setExp={setExp} />
        </>
      )}
    </div>
  );
}

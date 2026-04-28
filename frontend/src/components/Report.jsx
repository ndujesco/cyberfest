import { useState } from 'react';
import { P, TOOLS } from '../data';
import { generatePDF } from '../utils/pdf';
import { buildReportJSON } from '../utils/report';

export default function Report({ onClose }) {
  const [copied, setCopied] = useState(false);
  const [exporting, setExporting] = useState(false);
  const rows = TOOLS.map(t => ({ ...t, ...t.stats }));
  const tot = rows.reduce((a, b) => ({ critical: a.critical + b.critical, high: a.high + b.high, medium: a.medium + b.medium }), { critical: 0, high: 0, medium: 0 });

  const handlePDF = () => {
    setExporting(true);
    setTimeout(() => { generatePDF(); setExporting(false); }, 50);
  };

  const handleCopy = () => {
    const json = JSON.stringify(buildReportJSON(), null, 2);
    navigator.clipboard.writeText(json).then(() => {
      setCopied(true); setTimeout(() => setCopied(false), 2200);
    }).catch(() => {
      const ta = document.createElement('textarea');
      ta.value = json; document.body.appendChild(ta); ta.select();
      document.execCommand('copy'); document.body.removeChild(ta);
      setCopied(true); setTimeout(() => setCopied(false), 2200);
    });
  };

  return (
    <div
      style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.75)', zIndex: 80, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="fade-up" style={{ background: P.card, border: `1px solid ${P.border}`, borderRadius: 16, padding: 36, maxWidth: 620, width: '100%', maxHeight: '82vh', overflowY: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 26 }}>
          <div>
            <div style={{ fontSize: 20, fontWeight: 800, color: P.text }}>Full Security Report</div>
            <div style={{ color: P.muted, fontSize: 12, marginTop: 4 }}>Generated 2026-04-28 · Zer0day Saints · 3 tools</div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: P.muted, cursor: 'pointer', fontSize: 20, lineHeight: 1 }}>✕</button>
        </div>

        <div style={{ display: 'flex', gap: 10, marginBottom: 26 }}>
          {[['critical', P.red, P.redBg, P.redBd], ['high', P.orange, P.orangeBg, P.orangeBd], ['medium', P.yellow, P.yellowBg, P.yellowBd]].map(([k, c, bg, bd]) => (
            <div key={k} style={{ flex: 1, background: bg, border: `1px solid ${bd}`, borderRadius: 10, padding: '16px', textAlign: 'center' }}>
              <div style={{ color: c, fontSize: 34, fontWeight: 900 }}>{tot[k]}</div>
              <div style={{ color: P.muted, fontSize: 12, marginTop: 3, textTransform: 'capitalize' }}>{k}</div>
            </div>
          ))}
        </div>

        {rows.map(t => {
          const s = t.score >= 8 ? P.red : P.orange;
          return (
            <div key={t.id} style={{ border: `1px solid ${P.border}`, borderRadius: 10, padding: '14px 18px', marginBottom: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ color: P.text, fontWeight: 600, fontSize: 14 }}>{t.icon} {t.name}</div>
                <div style={{ color: s, fontWeight: 800, fontSize: 16 }}>{t.score}<span style={{ color: P.muted, fontSize: 12 }}>/10</span></div>
              </div>
              <div style={{ color: P.dim, fontSize: 11, fontFamily: 'monospace', marginTop: 4 }}>{t.target}</div>
              <div style={{ display: 'flex', gap: 16, marginTop: 10, fontSize: 12 }}>
                <span style={{ color: P.red }}>🔴 {t.critical} Critical</span>
                <span style={{ color: P.orange }}>🟠 {t.high} High</span>
                <span style={{ color: P.yellow }}>🟡 {t.medium} Medium</span>
              </div>
            </div>
          );
        })}

        <div style={{ marginTop: 22, display: 'flex', gap: 10 }}>
          <button
            onClick={handlePDF}
            disabled={exporting}
            style={{
              flex: 1, background: exporting ? P.blueD : P.blue, color: '#fff',
              border: 'none', borderRadius: 8, padding: '12px', fontWeight: 700,
              fontSize: 13, cursor: exporting ? 'default' : 'pointer',
              transition: 'background .2s', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
            }}
          >
            {exporting
              ? <span style={{ display: 'inline-block', width: 14, height: 14, border: '2px solid #fff4', borderTopColor: '#fff', borderRadius: '50%', animation: 'spin .7s linear infinite' }} />
              : '⬇'}
            {exporting ? 'Generating…' : 'Export PDF'}
          </button>
          <button
            onClick={handleCopy}
            style={{
              flex: 1, background: copied ? P.greenBg : P.card2,
              color: copied ? P.green : P.text,
              border: `1px solid ${copied ? P.green : P.border}`,
              borderRadius: 8, padding: '12px', fontWeight: 600, fontSize: 13,
              cursor: 'pointer', transition: 'all .25s',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
            }}
          >
            {copied ? '✓ Copied!' : '📋 Copy JSON'}
          </button>
        </div>
      </div>
    </div>
  );
}

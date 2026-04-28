import React from 'react';
import { P, SEV, PF } from '../data';

export default function AttackPath({ visible }) {
  const steps = PF.path;
  return (
    <div style={{ background: P.card, border: `1px solid ${P.border}`, borderRadius: 12, padding: 22, marginBottom: 16 }}>
      <div style={{ color: P.muted, fontSize: 11, fontWeight: 700, letterSpacing: 1, marginBottom: 18 }}>
        🗺️ HOW AN ATTACKER REACHES YOUR PRODUCTION DATABASE — step by step
      </div>
      <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 4 }}>
        {steps.map((st, i) => {
          const s = SEV[st.sev];
          const show = visible > i;
          return (
            <React.Fragment key={i}>
              <div
                className={show ? 'fade-in' : ''}
                style={{
                  opacity: show ? 1 : 0,
                  background: P.card2,
                  border: `2px solid ${show ? s.color : P.border}`,
                  borderRadius: 10, padding: '14px 16px', textAlign: 'center',
                  minWidth: 138, transition: 'all .5s ease',
                  boxShadow: show ? `0 0 18px ${s.color}22` : undefined,
                }}
              >
                <div style={{ fontSize: 28 }}>{st.icon}</div>
                <div style={{ color: P.text, fontWeight: 600, fontSize: 12, marginTop: 6, lineHeight: 1.3 }}>{st.label}</div>
                <div style={{ color: P.muted, fontSize: 10, marginTop: 4, lineHeight: 1.4 }}>{st.desc}</div>
                {show && (
                  <div style={{
                    marginTop: 6, display: 'inline-block', background: s.bg,
                    color: s.color, borderRadius: 4, padding: '2px 7px',
                    fontSize: 9, fontWeight: 700, letterSpacing: .5,
                  }}>{s.label}</div>
                )}
              </div>
              {i < steps.length - 1 && (
                <div style={{ color: visible > i ? P.red : P.border, fontSize: 22, padding: '0 2px', transition: 'color .5s .2s', lineHeight: 1 }}>→</div>
              )}
            </React.Fragment>
          );
        })}
      </div>
      {visible >= steps.length && (
        <div className="fade-in" style={{
          marginTop: 16, background: P.redBg, border: `1px solid ${P.redBd}`,
          borderRadius: 8, padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 10,
        }}>
          <span style={{ fontSize: 22 }}>💥</span>
          <div>
            <div style={{ color: P.red, fontWeight: 700, fontSize: 13 }}>Attack complete</div>
            <div style={{ color: P.text, fontSize: 12, marginTop: 2 }}>
              4.2 million user records fully accessible — from nothing more than a file upload to a public S3 bucket
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

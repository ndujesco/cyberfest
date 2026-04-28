import { TOOLS } from '../data';

export function buildReportJSON() {
  const tots = TOOLS.reduce((a, t) => ({
    critical: a.critical + t.stats.critical,
    high: a.high + t.stats.high,
    medium: a.medium + t.stats.medium,
  }), { critical: 0, high: 0, medium: 0 });

  return {
    metadata: {
      generated: new Date().toISOString().split('T')[0],
      scanner: 'Zer0day Saints', version: '1.0.0',
      tools: TOOLS.length, totalFindings: TOOLS.reduce((a, t) => a + t.findings.length, 0),
    },
    summary: tots,
    tools: TOOLS.map(t => ({
      id: t.id, name: t.name, target: t.target, riskScore: t.score,
      scanTime: t.time, stats: t.stats,
      findings: t.findings.map(f => ({
        id: f.id, severity: f.sev, title: f.title, location: f.loc,
        description: f.what, businessImpact: f.impact, technical: f.tech, remediation: f.fix,
      })),
    })),
  };
}

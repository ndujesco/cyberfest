import { jsPDF } from 'jspdf';
import { TOOLS } from '../data';

export function generatePDF() {
  const doc = new jsPDF({ unit: 'mm', format: 'a4' });
  const W = doc.internal.pageSize.getWidth();
  let y = 0;
  const newPage = () => { doc.addPage(); y = 22; };
  const need = (h) => { if (y + h > 272) newPage(); };

  doc.setFillColor(11, 15, 26);
  doc.rect(0, 0, 210, 48, 'F');
  doc.setTextColor(59, 130, 246);
  doc.setFontSize(24); doc.setFont('helvetica', 'bold');
  doc.text('Zer0day Saints', 20, 22);
  doc.setTextColor(241, 245, 249);
  doc.setFontSize(11); doc.setFont('helvetica', 'normal');
  doc.text('Security Vulnerability Report', 20, 33);
  doc.setTextColor(100, 116, 139);
  doc.setFontSize(8.5);
  doc.text(`Generated ${new Date().toISOString().split('T')[0]}  ·  3 tools  ·  Confidential`, 20, 42);
  y = 62;

  doc.setTextColor(15, 23, 42); doc.setFontSize(14); doc.setFont('helvetica', 'bold');
  doc.text('Executive Summary', 20, y); y += 10;

  const tots = TOOLS.reduce((a, t) => ({ critical: a.critical + t.stats.critical, high: a.high + t.stats.high, medium: a.medium + t.stats.medium }), { critical: 0, high: 0, medium: 0 });
  [[tots.critical, 'CRITICAL', 239, 68, 68], [tots.high, 'HIGH', 249, 115, 22], [tots.medium, 'MEDIUM', 234, 179, 8]].forEach(([v, lbl, r, g, b], i) => {
    const bx = 20 + i * 62;
    doc.setFillColor(r, g, b); doc.roundedRect(bx, y, 56, 28, 3, 3, 'F');
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(24); doc.setFont('helvetica', 'bold');
    doc.text(String(v), bx + 28, y + 15, { align: 'center' });
    doc.setFontSize(7.5); doc.setFont('helvetica', 'bold');
    doc.text(lbl, bx + 28, y + 24, { align: 'center' });
  });
  y += 38;

  doc.setFontSize(9); doc.setFont('helvetica', 'bold'); doc.setTextColor(100, 116, 139);
  ['TOOL', 'TARGET / RISK SCORE', 'CRIT', 'HIGH', 'MED'].forEach((h, i) => {
    doc.text(h, [20, 55, 160, 172, 184][i], y);
  });
  y += 3; doc.setDrawColor(226, 232, 240); doc.line(20, y, 190, y); y += 5;
  TOOLS.forEach(t => {
    doc.setFont('helvetica', 'bold'); doc.setTextColor(15, 23, 42); doc.setFontSize(9);
    doc.text(t.name, 20, y);
    doc.setFont('helvetica', 'normal'); doc.setTextColor(100, 116, 139);
    doc.text(doc.splitTextToSize(t.target, 98)[0], 55, y);
    const sc = t.score;
    doc.setTextColor(sc >= 8 ? 239 : 249, sc >= 8 ? 68 : 115, sc >= 8 ? 68 : 22); doc.setFont('helvetica', 'bold');
    doc.text(`${sc}/10`, 156, y);
    doc.setTextColor(239, 68, 68); doc.text(String(t.stats.critical), 167, y, { align: 'center' });
    doc.setTextColor(249, 115, 22); doc.text(String(t.stats.high), 179, y, { align: 'center' });
    doc.setTextColor(234, 179, 8); doc.text(String(t.stats.medium), 191, y, { align: 'center' });
    y += 8;
  });
  y += 6; doc.setDrawColor(226, 232, 240); doc.line(20, y, 190, y); y += 12;

  const sevRGB = { critical: [239, 68, 68], high: [249, 115, 22], medium: [234, 179, 8], low: [34, 197, 94] };
  TOOLS.forEach(tool => {
    need(22);
    doc.setFillColor(241, 245, 249); doc.roundedRect(20, y - 4, 170, 13, 2, 2, 'F');
    doc.setTextColor(15, 23, 42); doc.setFontSize(12); doc.setFont('helvetica', 'bold');
    doc.text(`${tool.name}`, 24, y + 4);
    doc.setTextColor(100, 116, 139); doc.setFontSize(8); doc.setFont('helvetica', 'normal');
    doc.text(`Risk: ${tool.score}/10  ·  ${tool.time}  ·  ${tool.target}`, 84, y + 4);
    y += 18;

    tool.findings.forEach(f => {
      const [r, g, b] = sevRGB[f.sev] || [100, 116, 139];
      const titleLines = doc.splitTextToSize(f.title, 148);
      const whatLines = doc.splitTextToSize(f.what, 158);
      const impLines = doc.splitTextToSize(f.impact, 156);
      const fixLines = doc.splitTextToSize(f.fix, 152);
      const blockH = titleLines.length * 5 + whatLines.length * 4.5 + impLines.length * 4.5 + 8 + fixLines.length * 4.5 + 26;
      need(blockH);

      doc.setFillColor(r, g, b); doc.rect(20, y, 2, blockH - 6, 'F');
      doc.setFillColor(r, g, b); doc.roundedRect(25, y, 22, 6, 1, 1, 'F');
      doc.setTextColor(255, 255, 255); doc.setFontSize(6.5); doc.setFont('helvetica', 'bold');
      doc.text(f.sev.toUpperCase(), 36, y + 4, { align: 'center' });
      doc.setTextColor(15, 23, 42); doc.setFontSize(10.5); doc.setFont('helvetica', 'bold');
      doc.text(titleLines, 50, y + 4);
      y += titleLines.length * 5 + 3;
      doc.setTextColor(148, 163, 184); doc.setFontSize(7.5); doc.setFont('helvetica', 'italic');
      doc.text(`Location: ${f.loc}`, 27, y); y += 6;
      doc.setTextColor(51, 65, 85); doc.setFontSize(8.5); doc.setFont('helvetica', 'normal');
      doc.text(whatLines, 27, y); y += whatLines.length * 4.5 + 4;
      const ibH = impLines.length * 4.5 + 9;
      doc.setFillColor(r + (255 - r) * .9, g + (255 - g) * .9, b + (255 - b) * .9);
      doc.roundedRect(26, y - 2, 162, ibH, 1.5, 1.5, 'F');
      doc.setTextColor(r, g, b); doc.setFont('helvetica', 'bold'); doc.setFontSize(6.5);
      doc.text('BUSINESS IMPACT', 29, y + 3);
      doc.setFont('helvetica', 'normal'); doc.setFontSize(8.5); doc.setTextColor(30, 41, 59);
      doc.text(impLines, 29, y + 8); y += ibH + 4;
      doc.setTextColor(21, 128, 61); doc.setFont('helvetica', 'bold'); doc.setFontSize(7.5);
      doc.text('HOW TO FIX:', 27, y);
      doc.setFont('helvetica', 'normal'); doc.setTextColor(51, 65, 85); doc.setFontSize(8.5);
      doc.text(fixLines, 27, y + 5); y += fixLines.length * 4.5 + 12;
    });
    y += 4; doc.setDrawColor(226, 232, 240); doc.line(20, y, 190, y); y += 12;
  });

  const pages = doc.internal.getNumberOfPages();
  for (let i = 1; i <= pages; i++) {
    doc.setPage(i);
    doc.setFillColor(248, 250, 252); doc.rect(0, 285, 210, 15, 'F');
    doc.setTextColor(148, 163, 184); doc.setFontSize(7.5); doc.setFont('helvetica', 'normal');
    doc.text('Zer0day Saints · Confidential', 20, 292);
    doc.text(`Page ${i} of ${pages}`, W / 2, 292, { align: 'center' });
    doc.text(new Date().toISOString().split('T')[0], 190, 292, { align: 'right' });
  }
  doc.save('zer0day-saints-security-report.pdf');
}

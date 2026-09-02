// Invariant de pagination (décision Tony 03/09/2026) : une demi-page blanche est
// acceptable s'il n'y a rien après. Elle ne l'est pas si le contenu de la page
// suivante aurait tenu dans ce blanc.
//
// Mesuré sur le PDF réellement produit, pas sur un modèle : chaque page est
// rendue en niveaux de gris, on relève jusqu'où descend l'encre en ignorant la
// bande du pied de page répété. Faute si extent(page i+1) <= blanc(page i).
//
// Usage : node tests/remplissage-sections.js [--garder <dossier>]
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs'), os = require('os'), path = require('path');

const FILE = 'file://' + path.join(__dirname, '..', 'calculateur-pv-nc.html');
const PIED = 0.90;   // les 10 % du bas portent le pied répété : hors mesure
const ENCRE = 245, MIN_PIX = 3;

const CAS = [
  ['A', 0, 'factures seul',        ['factures']],
  ['A', 0, 'amortissement seul',   ['amort']],
  ['A', 0, 'amort + factures',     ['amort', 'factures']],
  ['A', 0, 'bilan + factures',     ['bilan', 'factures']],
  ['A', 0, 'ROI + amortissement',  ['groi', 'amort']],
  ['A', 0, 'tout',                 ['fpast','tranches','groi','amort','factures','bilan']],
  ['B', 1, 'amort + factures',     ['amort', 'factures']],
  ['B', 1, 'tout',                 ['tranches','pile','gfact','groi','bilanEn','amort','factures','bilan']],
];

// Jusqu'où descend l'encre sur la page, en % de la hauteur (pied exclu).
function extent(png) {
  const pgm = png.replace(/\.png$/, '.pgm');
  execFileSync('magick', [png, pgm]);
  const buf = fs.readFileSync(pgm);
  let pos = 2, f = [];
  const ws = () => { while (pos < buf.length) { const c = buf[pos];
    if (c === 0x23) { while (buf[pos] !== 0x0a) pos++; } else if (c <= 0x20) pos++; else break; } };
  while (f.length < 3) { ws(); const s = pos; while (buf[pos] > 0x20) pos++; f.push(parseInt(buf.toString('ascii', s, pos), 10)); }
  pos++;
  const [w, h] = f, hUtile = Math.floor(h * PIED);
  let derniere = 0;
  for (let y = 0; y < hUtile; y++) {
    let n = 0;
    for (let x = 0; x < w; x++) if (buf[pos + y * w + x] < ENCRE) { if (++n >= MIN_PIX) break; }
    if (n >= MIN_PIX) derniere = y;
  }
  return Math.round(derniere / hUtile * 100);
}

(async () => {
  const garder = process.argv.includes('--garder') ? process.argv[process.argv.indexOf('--garder') + 1] : null;
  const dir = garder || fs.mkdtempSync(path.join(os.tmpdir(), 'remplissage-'));
  fs.mkdirSync(dir, { recursive: true });
  const b = await chromium.launch();
  let ko = 0;
  for (const [sortie, tab, nom, ids] of CAS) {
    const p = await b.newPage({ viewport: { width: 1280, height: 1400 } });
    const err = [];
    p.on('pageerror', e => err.push(e.message));
    await p.addInitScript(() => { window.print = () => {}; });
    await p.goto(FILE, { waitUntil: 'networkidle' });
    // Plotly peut retarder l'exécution du script : attendre que l'API soit là.
    await p.waitForFunction(() => typeof showTab === 'function' && typeof pmPrint === 'function');
    await p.evaluate(i => showTab(i), tab);
    await p.waitForTimeout(400);
    const btn = await p.$('#tab' + tab + ' button.btn-calc');
    if (btn) { await btn.click(); await p.waitForTimeout(2200); }
    await p.evaluate(() => openPrintModal());
    await p.evaluate(x => { document.querySelectorAll('#pm-list input').forEach(i => { i.checked = x.includes(i.dataset.psecId); }); }, ids);
    await p.evaluate(() => pmPrint());
    await p.waitForTimeout(1200);
    const pdf = path.join(dir, (sortie + '-' + nom).replace(/[^a-zA-Z0-9]+/g, '-') + '.pdf');
    await p.pdf({ path: pdf, format: 'A4', printBackground: true });
    await p.close();

    execFileSync('pdftoppm', ['-r', '60', '-gray', '-png', pdf, pdf.replace(/\.pdf$/, '')]);
    const pages = fs.readdirSync(dir).filter(f => f.startsWith(path.basename(pdf, '.pdf') + '-') && f.endsWith('.png')).sort();
    const ext = pages.map(f => extent(path.join(dir, f)));
    const fautes = [];
    for (let i = 0; i < ext.length - 1; i++) {
      const blanc = 100 - ext[i];
      if (ext[i + 1] <= blanc) fautes.push(`page ${i + 1} : ${blanc} % de blanc, la page ${i + 2} (${ext[i + 1]} %) y tenait`);
    }
    if (fautes.length || err.length) { ko++;
      console.log(`✗ ${sortie} — ${nom}\n    remplissage : ${ext.map(e => e + '%').join(' ')}\n    ${fautes.join('\n    ')}${err.length ? '\n    ERREURS JS : ' + err.join(' | ') : ''}`);
    } else {
      console.log(`✓ ${sortie} — ${nom} : ${ext.map(e => e + '%').join(' ')}`);
    }
  }
  await b.close();
  if (!garder) fs.rmSync(dir, { recursive: true, force: true });
  console.log(ko ? `\n${ko} cas en échec` : '\nREMPLISSAGE OK ✅');
  process.exit(ko ? 1 : 0);
})();

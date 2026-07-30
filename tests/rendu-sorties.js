// Rend les trois sorties imprimables (A particulier, B ajout batterie, C entreprise).
const { chromium } = require('playwright');
const path = require('path');
const OUT = process.argv[2] || path.join(__dirname, '..', '_rendu');
require('fs').mkdirSync(OUT, { recursive: true });
const FILE = 'file://' + path.join(__dirname, '..', 'calculateur-pv-nc.html');
const CAS = [['A', 0], ['B', 1], ['B', 2], ['C', 3]];

(async () => {
  const b = await chromium.launch();
  let ko = 0;
  for (const [sortie, tab] of CAS) {
    const p = await b.newPage({ viewport: { width: 1280, height: 1400 }, deviceScaleFactor: 2 });
    const err = [];
    p.on('pageerror', e => err.push(e.message));
    await p.goto(FILE, { waitUntil: 'networkidle' });
    await p.evaluate(i => showTab(i), tab);
    await p.waitForTimeout(400);
    const btn = await p.$('#tab' + tab + ' button.btn-calc');
    if (btn) { await btn.click(); await p.waitForTimeout(2200); }
    await p.evaluate(s => { document.body.classList.add('print-' + s); preparePrint(true); }, sortie);
    await p.waitForTimeout(1000);
    await p.pdf({ path: path.join(OUT, 'sortie-' + sortie + '-t' + (tab+1) + '.pdf'), format: 'A4', printBackground: true });
    const ess = await p.evaluate(() => {
      const e = document.getElementById('essentiel-page');
      return e ? e.innerHTML.length : 0;
    });
    console.log('sortie ' + sortie + ' (onglet ' + (tab + 1) + ') : essentiel ' +
      (ess > 500 ? 'présent' : 'ABSENT') + (err.length ? ' — ERREURS: ' + err.join(' | ') : ''));
    if (err.length) ko++;
    await p.close();
  }
  await b.close();
  process.exit(ko ? 1 : 0);
})();

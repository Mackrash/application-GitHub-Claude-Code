// Rend la sortie A imprimable en PDF + PNG pour contrôle visuel.
// Usage : node tests/rendu-sortie-a.js [dossier-de-sortie]
const { chromium } = require('playwright');
const path = require('path');
const OUT = process.argv[2] || path.join(__dirname, '..', '_rendu');
require('fs').mkdirSync(OUT, { recursive: true });
const FILE = 'file://' + path.join(__dirname, '..', 'calculateur-pv-nc.html');

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 1400 }, deviceScaleFactor: 2 });
  const erreurs = [];
  p.on('pageerror', e => erreurs.push(e.message));
  await p.goto(FILE, { waitUntil: 'networkidle' });
  await p.click('button.btn-calc');
  await p.waitForTimeout(2500);
  await p.evaluate(() => { document.body.classList.add('print-A'); preparePrint(true); });
  await p.waitForTimeout(1500);
  await p.pdf({ path: path.join(OUT, 'sortie-A.pdf'), format: 'A4', printBackground: true });
  // Les pages de garde, essentiel et récap ne sont visibles qu'en média print :
  // sans cette émulation elles restent en display:none et la capture expire.
  await p.emulateMedia({ media: 'print' });
  await p.waitForTimeout(500);
  for (const id of ['cover-page', 'essentiel-page', 'last-page']) {
    const el = await p.$('#' + id);
    if (!el) { console.log('ABSENT : #' + id); continue; }
    const visible = await el.isVisible();
    if (!visible) { console.log('INVISIBLE : #' + id); continue; }
    await el.screenshot({ path: path.join(OUT, id + '.png'), timeout: 15000 });
  }
  await p.emulateMedia({ media: 'screen' });
  await b.close();
  if (erreurs.length) { console.log('ERREURS JS :'); erreurs.forEach(e => console.log(' - ' + e)); process.exit(1); }
  console.log('RENDU OK →', OUT);
})();

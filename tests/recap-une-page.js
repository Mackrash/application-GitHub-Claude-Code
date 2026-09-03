// Le récapitulatif du dossier DOIT tenir sur une seule page (exigence Tony,
// 03/09/2026). Il déborde sinon d'une poignée de millimètres, et le client
// reçoit une page supplémentaire ne portant que la fin d'une liste.
//
// Mesure la hauteur imprimée de #last-page et la compare à la hauteur utile
// d'une A4 : 297 mm moins les marges @page (12 mm en haut, 14 mm en bas).
const { chromium } = require('playwright');
const path = require('path');
const FILE = 'file://' + path.join(__dirname, '..', 'calculateur-pv-nc.html');
const UTILE = 297 - 12 - 14;   // 271 mm

const CAS = [
  ['A', 0, ['fpast', 'tranches', 'groi', 'amort', 'factures', 'bilan']],
  ['B', 1, ['tranches', 'pile', 'gfact', 'groi', 'bilanEn', 'amort', 'factures', 'bilan']],
  ['B', 2, ['tranches', 'pile', 'gfact', 'groi', 'bilanEn', 'amort', 'factures', 'bilan']],
];

let ko = 0;
(async () => {
  const b = await chromium.launch();
  for (const [sortie, tab, ids] of CAS) {
    const p = await b.newPage({ viewport: { width: 1280, height: 1400 } });
    await p.addInitScript(() => { window.print = () => {}; });
    await p.goto(FILE, { waitUntil: 'networkidle' });
    await p.waitForFunction(() => typeof pmPrint === 'function');
    await p.evaluate(i => showTab(i), tab);
    await p.waitForTimeout(400);
    const btn = await p.$('#tab' + tab + ' button.btn-calc');
    if (btn) { await btn.click(); await p.waitForTimeout(2200); }
    await p.evaluate(() => openPrintModal());
    await p.evaluate(x => { document.querySelectorAll('#pm-list input').forEach(i => { i.checked = x.includes(i.dataset.psecId); }); }, ids);
    await p.evaluate(() => pmPrint());
    await p.emulateMedia({ media: 'print' });
    await p.evaluate(() => window.dispatchEvent(new Event('beforeprint')));
    await p.waitForTimeout(1200);
    const r = await p.evaluate(() => {
      const e = document.getElementById('last-page');
      const t = (e.textContent || '').replace(/\s+/g, ' ');
      return {
        mm: e ? Math.round(e.getBoundingClientRect().height / (96 / 25.4)) : -1,
        titres: [...e.querySelectorAll('.lp-h2')].map(h => h.textContent.trim()),
        essentiel: /Puissance install/i.test(t) && /Investissement/i.test(t) && /Économie annuelle/i.test(t),
        // ces analyses ne sont pas le dossier de base : elles vivent dans le corps
        annexes: /tranche/i.test(t) || /batterie change/i.test(t) || /prochaines étapes/i.test(t),
        // les analyses déplacées restent imprimables, hors du récapitulatif
        tranchesAilleurs: !!document.querySelector('#annexes-page [data-psec="tranches"]'),
      };
    });
    await p.close();
    const dit = (nom, ok) => { if (!ok) ko++; console.log(`    ${ok ? '✓' : '✗'} ${nom}`); };
    console.log(`  sortie ${sortie} (onglet ${tab + 1}) — ${r.mm} mm`);
    dit(`tient sur une page (${r.mm} / ${UTILE} mm)`, r.mm > 0 && r.mm <= UTILE);
    dit('porte les informations essentielles du dossier', r.essentiel);
    dit('ne porte aucune analyse annexe', !r.annexes);
    dit('un seul titre : « Récapitulatif du dossier »',
        r.titres.length === 1 && /Récapitulatif du dossier/i.test(r.titres[0]));
    dit('le ROI par tranche reste imprimable, dans les annexes', r.tranchesAilleurs);
  }
  await b.close();
  console.log(ko ? '\nTEST FAIL ❌' : '\nTEST PASS ✅');
  process.exit(ko ? 1 : 0);
})();

// Sortie B : les deux blocs « énergie » (répartition et bilan mensuel) se
// suivent, l'argent d'abord. Avant, la répartition occupait seule une page à
// 32 % de remplissage, coincée devant les pages financières.
// Et son titre ne s'écrit qu'une fois : le bandeau orange des sections
// imprimées faisait doublon avec le titre dessiné dans le graphique.
const { chromium } = require('playwright');
const path = require('path');
const FILE = 'file://' + path.join(__dirname, '..', 'calculateur-pv-nc.html');

let ko = 0;
const check = (nom, cond, detail) => { if (!cond) ko++; console.log(`  ${cond ? '✓' : '✗'} ${nom}${!cond && detail ? '\n     ' + detail : ''}`); };

(async () => {
  const b = await chromium.launch();
  for (const [tab, r] of [[1, 'r2'], [2, 'r3']]) {
    console.log(`onglet ${tab + 1} (#${r})`);
    const p = await b.newPage({ viewport: { width: 1280, height: 1400 } });
    const err = [];
    p.on('pageerror', e => err.push(e.message));
    await p.addInitScript(() => { window.print = () => {}; });
    await p.goto(FILE, { waitUntil: 'networkidle' });
    await p.waitForFunction(() => typeof pmPrint === 'function');
    await p.evaluate(i => showTab(i), tab);
    await p.waitForTimeout(400);
    await p.click(`#tab${tab} button.btn-calc`);
    await p.waitForTimeout(2200);
    await p.evaluate(() => openPrintModal());
    await p.evaluate(() => { document.querySelectorAll('#pm-list input').forEach(i => i.checked = true); });
    await p.evaluate(() => pmPrint());
    await p.emulateMedia({ media: 'print' });
    // Les bandeaux de titre sont posés par window.onbeforeprint (setPrintLabels).
    // page.pdf() le déclenche, pas pmPrint() : sans cet événement, le test
    // inspecterait un DOM sans ses titres de section et ne verrait aucun doublon.
    await p.evaluate(() => window.dispatchEvent(new Event('beforeprint')));
    await p.waitForTimeout(1200);

    const res = await p.evaluate(id => {
      const racine = document.getElementById(id);
      const visible = el => getComputedStyle(el).display !== 'none';
      // ordre des sections optionnelles, telles qu'elles s'impriment
      const ordre = [...racine.querySelectorAll('[data-psec]')]
        .filter(visible).map(el => el.dataset.psec);
      // le titre de la répartition, partout où il apparaît en impression
      const titres = [];
      racine.querySelectorAll('.ps-donut .ps-label, .ps-donut text').forEach(el => {
        if (visible(el) && /RÉPARTITION ÉNERGÉTIQUE/i.test(el.textContent)) titres.push(el.tagName);
      });
      return { ordre, titres };
    }, r);

    const iPile = res.ordre.indexOf('pile'), iBilan = res.ordre.indexOf('bilan');
    check('la répartition précède immédiatement le bilan mensuel',
          iPile >= 0 && iBilan === iPile + 1, 'ordre imprimé : ' + res.ordre.join(' → '));
    check('les blocs financiers passent avant',
          iPile > res.ordre.indexOf('amort'), 'ordre imprimé : ' + res.ordre.join(' → '));
    check('le titre de la répartition ne s\'écrit qu\'une fois',
          res.titres.length === 1, 'trouvé ' + res.titres.length + ' fois (' + res.titres.join(', ') + ')');
    check('aucune erreur JS', err.length === 0, err.join(' | '));
    await p.close();
  }
  await b.close();
  console.log(ko ? '\nTEST FAIL ❌' : '\nTEST PASS ✅');
  process.exit(ko ? 1 : 0);
})();

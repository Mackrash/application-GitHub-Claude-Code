// Les valeurs pré-remplies doivent former un dossier plausible : c'est ce que
// voit un commercial qui ouvre l'onglet et clique CALCULER sans rien changer.
// L'onglet 2 proposait un devis de 1 200 000 XPF (prix d'une Maestro) avec une
// Élite 4,8 kWh sélectionnée : le retour sortait à 25 ans, et le tableau fiscal
// affichait « > 15 ans » sur ses cinq lignes.
const { chromium } = require('playwright');
const path = require('path');
const FILE = 'file://' + path.join(__dirname, '..', 'calculateur-pv-nc.html');

let ko = 0;
const dit = (nom, ok, detail) => { if (!ok) ko++; console.log(`  ${ok ? '✓' : '✗'} ${nom}${!ok && detail ? '\n     ' + detail : ''}`); };

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 1400 } });
  await p.goto(FILE, { waitUntil: 'networkidle' });
  await p.waitForFunction(() => typeof calcT2 === 'function');

  // les deux onglets à batterie partagent la même logique : même batterie par défaut
  const defs = await p.evaluate(() => ({
    t2: document.getElementById('t2_bat').value,
    t3: document.getElementById('t3_bat').value,
    devis2: document.getElementById('t2_devis').value,
  }));
  dit('onglets 2 et 3 : même batterie par défaut', defs.t2 === defs.t3,
      `t2 = ${defs.t2}, t3 = ${defs.t3}`);

  // et le dossier par défaut doit se rembourser dans l'horizon étudié
  for (const [tab, nom] of [[0, 'onglet 1 — installation complète'], [1, 'onglet 2 — ajout batterie']]) {
    const r = await p.evaluate(async i => {
      showTab(i);
      await new Promise(r => setTimeout(r, 300));
      document.querySelector('#tab' + i + ' button.btn-calc').click();
      await new Promise(r => setTimeout(r, 2000));
      return { pb: lastStudyData.pb, devis: lastStudyData.devis,
               eco: Math.round(lastStudyData.ecoAn), dpv: getS().dpv };
    }, tab);
    dit(`${nom} : remboursé dans l'horizon`, !!r.pb && r.pb <= r.dpv,
        `devis ${r.devis} F, économie ${r.eco} F/an → ${(r.devis / r.eco).toFixed(1)} ans`);
  }
  await b.close();
  console.log(ko ? '\nTEST FAIL ❌' : '\nTEST PASS ✅');
  process.exit(ko ? 1 : 0);
})();

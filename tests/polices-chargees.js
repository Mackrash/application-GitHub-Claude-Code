// Toute graisse utilisée dans les styles doit être réellement chargée : sinon le
// navigateur la synthétise (faux gras), et le rendu imprimé s'écarte de l'écran.
// Le document appelle du 800 (tuiles de la garde, barre de répartition, rapport
// T4) et du 900 (récapitulatif final).
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const SRC = path.join(__dirname, '..', 'calculateur-pv-nc.html');

let ko = 0;
const check = (nom, cond, detail) => { if (!cond) ko++; console.log(`  ${cond ? '✓' : '✗'} ${nom}${!cond && detail ? '\n     ' + detail : ''}`); };

(async () => {
  // Graisses réclamées par les feuilles de style du fichier
  const html = fs.readFileSync(SRC, 'utf8');
  const voulues = [...new Set([...html.matchAll(/font-weight:\s*(\d{3})/g)].map(m => m[1]))]
    .filter(w => +w >= 400).sort();

  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto('file://' + SRC, { waitUntil: 'networkidle' });
  await p.waitForTimeout(1800);
  const chargees = await p.evaluate(async () => {
    await document.fonts.ready;
    return [...new Set([...document.fonts].filter(f => /Nunito/.test(f.family)).map(f => String(f.weight)))].sort();
  });
  await b.close();

  console.log(`  graisses demandées par le CSS : ${voulues.join(', ')}`);
  console.log(`  graisses déclarées pour Nunito : ${chargees.join(', ')}`);
  const manquantes = voulues.filter(w => !chargees.includes(w));
  check('aucune graisse synthétisée', manquantes.length === 0,
        'manquantes : ' + manquantes.join(', ') + ' — à ajouter au lien Google Fonts du <head>');

  console.log(ko ? '\nTEST FAIL ❌' : '\nTEST PASS ✅');
  process.exit(ko ? 1 : 0);
})();

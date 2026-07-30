// Tests des fonctions pures de la sortie A (code réel extrait du HTML)
const fs = require('fs');
const path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'calculateur-pv-nc.html'), 'utf8');
const grab = (start, endMark) => {
  const a = html.indexOf(start);
  if (a < 0) throw new Error('segment introuvable : ' + start);
  const b = html.indexOf(endMark, a) + endMark.length;
  return html.slice(a, b);
};
const src = grab('function moisPayes(', '\n}') + '\n' + grab('function libelleSurplus(', '\n}');
const { moisPayes, libelleSurplus } = new Function(src + '\nreturn {moisPayes, libelleSurplus};')();

let ok = true;
const eq = (nom, obtenu, attendu) => {
  const bon = JSON.stringify(obtenu) === JSON.stringify(attendu);
  if (!bon) { ok = false; console.log(`  ✗ ${nom}\n     obtenu  : ${JSON.stringify(obtenu)}\n     attendu : ${JSON.stringify(attendu)}`); }
  else console.log(`  ✓ ${nom}`);
};

console.log('moisPayes');
// cas de référence : 276 144 → 62 788 XPF/an
const r = moisPayes(276144, 62788);
eq('entiers = 2', r.entiers, 2);
eq('offerts = 9', r.offerts, 9);
eq('part entre 0 et 1', r.part > 0.7 && r.part < 0.75, true);
// facture nulle après installation : rien à payer
eq('facture après nulle', moisPayes(276144, 0), { payes: 0, entiers: 0, part: 0, offerts: 12 });
// aucune économie : on paie les douze mois
eq('aucune économie', moisPayes(276144, 276144), { payes: 12, entiers: 12, part: 0, offerts: 0 });
// division par zéro : ne doit pas produire NaN
eq('facture avant nulle', moisPayes(0, 0), { payes: 0, entiers: 0, part: 0, offerts: 12 });

console.log('libelleSurplus');
eq('revente à 0', libelleSurplus(0).titre, 'Réserve de production');
eq('revente à 15', libelleSurplus(15).titre, 'Énergie revendue');
eq('revente à 21', libelleSurplus(21).titre, 'Énergie revendue');
eq('couleur verte', libelleSurplus(0).couleur, '#35A46B');

console.log(ok ? '\nTEST PASS ✅' : '\nTEST FAIL ❌');
process.exit(ok ? 0 : 1);

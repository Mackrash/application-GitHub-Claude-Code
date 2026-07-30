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

console.log('svgMaestro');
const fmt = n => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
const srcM = grab('function svgMaestro(', '\n}');
const { svgMaestro } = new Function('fmt',
  grab('function libelleSurplus(', '\n}') + '\n' + srcM + '\nreturn {svgMaestro};')(fmt);
const svg = svgMaestro({
  prodAn: 8692, directAutoAn: 2699, batAutoAn: 1800, surplusAn: 4193,
  consoAn: 4499, achatAn: 0, batLabel: 'OMEGA Maestro 14,3 kWh', tarifRevente: 0
});
eq('svg responsive', /width="100%"/.test(svg), true);
eq('aucune largeur fixe', /<svg[^>]*width="\d+"/.test(svg), false);
eq('les trois pourcentages', [/31%/, /21%/, /48%/].every(re => re.test(svg)), true);
eq('libellé réserve', /Réserve de production/i.test(svg), true);
eq('aucune réinjection', /éinjection/.test(svg), false);
eq('aucun gris clair', /#8A8C8F|#9A9CA0|#999|#aaa/i.test(svg), false);
// bascule du vocabulaire quand la revente est rémunérée
const svgVendu = svgMaestro({
  prodAn: 8692, directAutoAn: 2699, batAutoAn: 1800, surplusAn: 4193,
  consoAn: 4499, achatAn: 0, batLabel: 'OMEGA Maestro 14,3 kWh', tarifRevente: 21
});
eq('bascule en revendue', /Énergie revendue/i.test(svgVendu), true);
// somme des pourcentages = 100 quel que soit l'arrondi
const pct = [...svg.matchAll(/>(\d+)%</g)].map(m => +m[1]);
eq('somme des pourcentages = 100', pct.reduce((a, b) => a + b, 0), 100);
// géométrie : le dernier segment (« Consommée le jour ») ne doit pas déborder du cadre de la jauge
const cadre = svg.match(/<rect x="44" y="([\d.]+)" width="202" height="([\d.]+)" rx="7"/);
const basCadre = +cadre[1] + +cadre[2];
const segments = [...svg.matchAll(/<rect x="48" y="([\d.]+)" width="194" height="([\d.]+)"/g)];
const dernier = segments[segments.length - 1];
const basDernierSegment = +dernier[1] + +dernier[2];
eq('dernier segment ne déborde pas du cadre', basDernierSegment <= basCadre + 0.01, true);

console.log(ok ? '\nTEST PASS ✅' : '\nTEST FAIL ❌');
process.exit(ok ? 0 : 1);

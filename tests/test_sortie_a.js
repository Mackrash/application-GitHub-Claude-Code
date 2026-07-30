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
const uidSrc = grab('let _svgUidSeq=0;', "(_svgUidSeq++);}");
const srcM = grab('function svgMaestro(', '\n}');
const { svgMaestro } = new Function('fmt',
  uidSrc + '\n' + grab('function libelleSurplus(', '\n}') + '\n' + srcM + '\nreturn {svgMaestro};')(fmt);
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
// id de <linearGradient> namespacés : deux instances sur une même page ne
// doivent jamais partager le même id (sinon la seconde écrase la première).
const idsMaestro1 = [...svg.matchAll(/id="(mgAlu_[^"]+)"/g)].map(m => m[1]);
const idsMaestro2 = [...svgVendu.matchAll(/id="(mgAlu_[^"]+)"/g)].map(m => m[1]);
eq('ids mgAlu différents entre deux appels', idsMaestro1[0] !== idsMaestro2[0] && !!idsMaestro1[0], true);
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

console.log('svgDouzeMois');
const srcF = grab('function splinePath(', '\n}') + '\n' +
             grab('function svgDouzeMois(', '\n}') + '\n' +
             grab('function svgEcartMensuel(', '\n}');
const fmtT = n => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
const F = new Function('fmt', 'moisPayes',
  uidSrc + '\n' + srcF + '\nreturn {splinePath, svgDouzeMois, svgEcartMensuel};')(fmtT, moisPayes);
const d12 = F.svgDouzeMois(276144, 62788);
eq('responsive', /width="100%"/.test(d12), true);
eq('trois mois payés', /3 mois/.test(d12), true);
eq('neuf mois offerts', /9 mois/.test(d12), true);
eq('formulation prudente', /équivalent/.test(d12), true);
eq('jamais « ne payez que »', /ne payez que/.test(d12), false);
eq('douze pastilles', (d12.match(/<circle[^>]*r="25"/g) || []).length, 12);

// Cohérence pastilles / accolade sur un cas pile à la frontière de
// l'arrondi (2,5 mois) : entiers = 2 (Math.floor), mais le nombre annoncé
// doit être dérivé de entiers/part et non recalculé séparément, sinon
// l'accolade et les pastilles peuvent raconter des histoires différentes.
console.log('svgDouzeMois — cohérence pastilles/accolade (2,5 mois)');
const refPayes = moisPayes(2400, 500);
eq('cas de référence : payes = 2.5', refPayes.payes, 2.5);
eq('cas de référence : entiers = 2', refPayes.entiers, 2);
const d25 = F.svgDouzeMois(2400, 500);
eq('accolade annonce 3 mois (2 entiers + 1 arrondi)', /3 mois/.test(d25), true);
eq('accolade annonce 9 mois offerts', /9 mois/.test(d25), true);
eq('toujours douze pastilles', (d25.match(/<circle[^>]*r="25"/g) || []).length, 12);
eq('exactement deux pastilles pleines (entiers)', (d25.match(/<circle[^>]*fill="#F07020"/g) || []).length, 2);
eq('exactement une pastille partielle (dégradé)', (d25.match(/fill="url\(#dmPart_[^)]+\)"/g) || []).length, 1);
// id namespacés : deux appels de svgDouzeMois sur la même page ne doivent
// jamais produire le même id de <linearGradient> (sinon le second dégradé
// écrase le premier et la pastille partielle affiche la mauvaise fraction).
const idDm1 = (d12.match(/id="(dmPart_[^"]+)"/) || [])[1];
const idDm2 = (d25.match(/id="(dmPart_[^"]+)"/) || [])[1];
eq('ids dmPart différents entre deux appels', !!idDm1 && !!idDm2 && idDm1 !== idDm2, true);

console.log('svgEcartMensuel');
const sans = [23012,22180,23012,22600,23012,22900,23012,23012,22800,23012,22950,23100];
const avec = [5232,5100,5232,5180,5232,5210,5232,5232,5190,5232,5205,5240];
const ecart = F.svgEcartMensuel(sans, avec);
eq('responsive', /width="100%"/.test(ecart), true);
eq('pas de rouge hors charte', /#FF4B6E/i.test(ecart), false);
eq('pas de turquoise hors charte', /#00D4A0/i.test(ecart), false);
eq('accents présents', /photovoltaïque/.test(ecart), true);
eq('douze étiquettes d\'écart', (ecart.match(/−\d/g) || []).length >= 12, true);

console.log(ok ? '\nTEST PASS ✅' : '\nTEST FAIL ❌');
process.exit(ok ? 0 : 1);

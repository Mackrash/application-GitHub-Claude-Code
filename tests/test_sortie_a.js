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

console.log('svgReliefROI');
// Le brief fournissait `new Function('fmt', ...)` sans injecter uidSrc :
// svgReliefROI appelle svgUid(), qui aurait été indéfini dans ce scope
// et aurait fait planter le test avant la première assertion. Corrigé
// ici en réutilisant uidSrc, comme pour F plus haut.
const R = new Function('fmt',
  uidSrc + '\n' + grab('function splinePath(', '\n}') + '\n' +
  grab('function svgReliefROI(', '\n}') + '\nreturn {svgReliefROI};')(fmtT);
const cum = (() => { const a = []; let c = -1650000, e = 213355;
  for (let i = 0; i < 20; i++) { c += e; a.push(Math.round(c)); e *= 1.025; } return a; })();
const roi = R.svgReliefROI(cum, 8);
eq('responsive', /width="100%"/.test(roi), true);
eq('jalon investissement', /INVESTISSEMENT/.test(roi), true);
eq('jalon bascule', /An 8/.test(roi), true);
eq('jalon gain final', /GAIN FINAL/.test(roi), true);
eq('trois jalons seulement', (roi.match(/<circle[^>]*stroke-width="2\.6"/g) || []).length, 3);
eq('aucun gris clair', /#8A8C8F|#9A9CA0|#999|#aaa/i.test(roi), false);
eq('aucun NaN dans le tracé', /NaN/.test(roi), false);

// jamais remboursé : pas de jalon de bascule, pas de plantage
const jamais = R.svgReliefROI(cum.map(() => -100000), 0);
eq('jamais remboursé', /An 0/.test(jamais), false);
eq('jamais remboursé : deux jalons seulement (investissement + gain final)',
  (jamais.match(/<circle[^>]*stroke-width="2\.6"/g) || []).length, 2);
eq('jamais remboursé : pas de plantage', /width="100%"/.test(jamais), true);

// tableau de cumuls vide : chaîne vide, pas de plantage
eq('cumuls vide', R.svgReliefROI([], 0), '');
eq('cumuls null', R.svgReliefROI(null, 0), '');

// tableau à une seule valeur : le dénominateur d'échelle horizontale (n-1)
// vaudrait zéro — vérifie l'absence de NaN et l'absence de jalon dupliqué
const uneValeur = R.svgReliefROI([500000], 1);
eq('une seule valeur : pas de plantage', /width="100%"/.test(uneValeur), true);
eq('une seule valeur : aucun NaN', /NaN/.test(uneValeur), false);
eq('une seule valeur : un seul jalon "Gain final" (pas de doublon avec investissement)',
  (uneValeur.match(/GAIN FINAL/g) || []).length, 0);

// géométrie : la ligne de base doit être la ligne du zéro, pas le bord du
// cadre (H - PB = 216), et strictement à l'intérieur du cadre vertical
// (PT=34 .. PT+ih=216) puisque les cumuls couvrent négatif et positif.
const zMatch = roi.match(/<line x1="34" y1="([\d.]+)" x2="666" y2="\1" stroke="#333333"/);
eq('ligne de zéro présente et alignée x1/x2', !!zMatch, true);
const Z = zMatch ? +zMatch[1] : null;
eq('ligne de zéro strictement dans le cadre (ni bord haut ni bord bas)', Z > 34 && Z < 216, true);
// la valeur du premier point (négative, investissement) doit être sous le zéro
const premierY = roi.match(/<circle cx="34" cy="([\d.]+)" r="5"/);
eq('point investissement sous la ligne de zéro (valeur négative)', premierY ? +premierY[1] > Z : false, true);
// le libellé du premier jalon (INVESTISSEMENT) doit être positionné sous son
// point (y du texte > y du point), pour ne pas chevaucher le tracé
const labelInvest = roi.match(/<text x="34" y="([\d.]+)"[^>]*>INVESTISSEMENT</);
eq('libellé investissement sous son point', labelInvest && premierY ? +labelInvest[1] > +premierY[1] : false, true);
// point final (x=666, dernier point à droite) doit être au-dessus du zéro
// (gain final positif dans ce jeu de données)
const dernierY = roi.match(/<circle cx="666" cy="([\d.]+)" r="5"/);
eq('point final au-dessus de la ligne de zéro (gain positif)', dernierY ? +dernierY[1] < Z : false, true);

// bascule qui coïncide avec une extrémité : les deux jalons fixes
// (investissement, gain final) ne doivent jamais partager leurs coordonnées
// avec le jalon mobile de bascule — l'info de remboursement doit être
// fusionnée dans le jalon existant, pas perdue.
const coordsUniques = (svg) => {
  const cercles = [...svg.matchAll(/<circle cx="([\d.]+)" cy="([\d.]+)" r="5"/g)]
    .map(m => `${m[1]},${m[2]}`);
  return new Set(cercles).size === cercles.length;
};

console.log('svgReliefROI — bascule dès la première année (paybackAn = 1)');
const roiAn1 = R.svgReliefROI(cum, 1);
eq('aucune paire de jalons superposés', coordsUniques(roiAn1), true);
eq('deux cercles seulement (fusion avec investissement)',
  (roiAn1.match(/<circle[^>]*stroke-width="2\.6"/g) || []).length, 2);
eq('année de remboursement toujours lisible', /Remboursée en l'an 1/.test(roiAn1), true);
eq('pas de jalon « Remboursée » séparé', /<text[^>]*>REMBOURSÉE</.test(roiAn1), false);

console.log('svgReliefROI — bascule à la toute dernière année (paybackAn = n)');
const roiAnN = R.svgReliefROI(cum, cum.length);
eq('aucune paire de jalons superposés', coordsUniques(roiAnN), true);
eq('deux cercles seulement (fusion avec gain final)',
  (roiAnN.match(/<circle[^>]*stroke-width="2\.6"/g) || []).length, 2);
eq('année de remboursement toujours lisible', new RegExp(`Remboursée en l'an ${cum.length}`).test(roiAnN), true);
eq('pas de jalon « Remboursée » séparé', /<text[^>]*>REMBOURSÉE</.test(roiAnN), false);

// cas nominal (bascule au milieu, paybackAn=8 déjà testé plus haut) : pas de
// fusion, trois cercles distincts, aucune coordonnée partagée
eq('cas nominal : aucune paire de jalons superposés (non-régression)', coordsUniques(roi), true);

console.log(ok ? '\nTEST PASS ✅' : '\nTEST FAIL ❌');
process.exit(ok ? 0 : 1);

# Refonte de la sortie client A — Plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remplacer la sortie imprimée A (particulier) par une page « L'essentiel » en deux colonnes, sans redondance, avec la batterie OMEGA Maestro-G comme représentation de la répartition énergétique.

**Architecture:** La nouvelle sortie est un bloc **print-only** (`#essentiel-page`) construit en JavaScript au moment de `preparePrint()`, sur le modèle exact de `#cover-page` et `#last-page` déjà en place. L'affichage écran (thème sombre, graphes Plotly) n'est **pas modifié** : les nouveaux visuels sont dessinés en SVG pur pensé pour le fond blanc, et cohabiteraient mal avec le thème sombre. Ce choix garantit zéro régression à l'écran et un contrôle total du rendu papier.

**Tech Stack:** HTML/CSS/JS monofichier, SVG inline (aucune dépendance ajoutée), Plotly 2.27 conservé pour l'écran et les autres onglets, Playwright pour la vérification visuelle, Node pour les tests de fonctions pures.

## Global Constraints

- Fichier unique : `calculateur-pv-nc.html`. Aucune dépendance nouvelle.
- Langue **française**, accents et diacritiques obligatoires, jamais d'ASCII dégradé.
- Devise **XPF**, séparateur de milliers = espace (fonction `fmt()` existante).
- Palette autorisée, valeurs exactes : orange `#F07020`, ambre `#F5A623`, ambre foncé `#D98B0A`, vert `#35A46B`, vert foncé `#2E8F5C`, gris `#A8ACB1`, anthracite `#333333`, texte secondaire `#55585C`, filets `#D8DADC`, fond doux `#F6F7F8`.
- **Aucun texte en gris clair** : les textes secondaires sont en `#55585C`. Interdits : `#8A8C8F`, `#9A9CA0`, `#999`, `#aaa`.
- **Aucun histogramme, aucun donut**, quelle que soit la donnée.
- SVG toujours en `width="100%"` + `viewBox` — une largeur fixe déborde de la colonne à l'impression.
- Le mot **« Réinjection »** disparaît de la sortie A. Remplacé par « Réserve de production » (tarif de revente = 0) ou « Énergie revendue » (tarif > 0).
- Formulation obligatoire et non négociable : **« l'équivalent de N mois »**. Ne jamais écrire « vous ne payez que N mois ».
- Vérification syntaxe JS après **chaque** modification (commande en Task 0).
- Aucune modification du moteur de calcul : `calcT1`, `calcT2`, `calcT3`, `calcT4`, `factureMois`, `prodM`, `buildAmort` restent intacts.

---

## Task 0 : Garde-fous avant de commencer

**Files:**
- Lire : `calculateur-pv-nc.html`
- Lire : `docs/superpowers/specs/2026-07-30-refonte-sortie-client-design.md`

- [ ] **Step 1 : Vérifier que l'arbre est propre et à jour**

```bash
cd "/home/tony-linux/Documents/Synology/SynoIA/SOLAR/Calculateur SOLAIRE"
git status --short          # doit être vide
git rev-parse main origin/main   # doivent converger après fetch
```

- [ ] **Step 2 : Mémoriser la commande de vérification syntaxe**

À relancer après **chaque** modification du fichier. Un saut de ligne littéral dans un template string a déjà cassé la prod par le passé.

```bash
cd "/home/tony-linux/Documents/Synology/SynoIA/SOLAR/Calculateur SOLAIRE"
node -e "const fs=require('fs');const html=fs.readFileSync('calculateur-pv-nc.html','utf8');const m=html.match(/<script>([\s\S]*?)<\/script>/g);if(m){const js=m.map(s=>s.replace(/<\/?script>/g,'')).join('\n');fs.writeFileSync('_check.js',js);}" && node --check _check.js && echo "SYNTAXE OK" && rm -f _check.js
```

- [ ] **Step 3 : Créer le script de rendu Playwright de contrôle**

Fichier à créer : `tests/rendu-sortie-a.js`

```javascript
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
  for (const id of ['cover-page', 'essentiel-page', 'last-page']) {
    const el = await p.$('#' + id);
    if (el) await el.screenshot({ path: path.join(OUT, id + '.png') });
    else console.log('ABSENT : #' + id);
  }
  await b.close();
  if (erreurs.length) { console.log('ERREURS JS :'); erreurs.forEach(e => console.log(' - ' + e)); process.exit(1); }
  console.log('RENDU OK →', OUT);
})();
```

- [ ] **Step 4 : Installer Playwright localement si absent, puis lancer le rendu de référence**

```bash
cd "/home/tony-linux/Documents/Synology/SynoIA/SOLAR/Calculateur SOLAIRE"
node -e "require('playwright')" 2>/dev/null || npm i --no-save playwright@1.62.0
node tests/rendu-sortie-a.js _rendu-avant
```

Attendu : `ABSENT : #essentiel-page` (il n'existe pas encore) puis `RENDU OK`. Conserver `_rendu-avant/` pour comparer.

- [ ] **Step 5 : Ignorer les dossiers de rendu**

```bash
cd "/home/tony-linux/Documents/Synology/SynoIA/SOLAR/Calculateur SOLAIRE"
printf '\n# rendus de contrôle\n_rendu*/\n' >> .gitignore
git add .gitignore tests/rendu-sortie-a.js
git commit -m "test(sortie A): script de rendu Playwright pour contrôle visuel"
```

---

## Task 1 : Fonctions pures — durée payée et vocabulaire du surplus

**Files:**
- Modify: `calculateur-pv-nc.html` — insérer juste avant `// ===== IMPRESSION =====` (ligne ~1136)
- Test: `tests/test_sortie_a.js` (créer)

**Interfaces:**
- Consomme : rien.
- Produit :
  - `moisPayes(fSansAn, fAvecAn)` → `{payes:number, entiers:number, part:number, offerts:number}`
    `payes` = 12 × fAvecAn / fSansAn, non arrondi. `entiers` = partie entière. `part` = fraction du mois suivant (0 à 1). `offerts` = 12 − round(payes).
  - `libelleSurplus(tarifRevente)` → `{titre:string, sousTitre:string, couleur:string}`

- [ ] **Step 1 : Écrire le test qui échoue**

Fichier `tests/test_sortie_a.js` :

```javascript
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
```

- [ ] **Step 2 : Lancer le test pour vérifier qu'il échoue**

```bash
cd "/home/tony-linux/Documents/Synology/SynoIA/SOLAR/Calculateur SOLAIRE"
node tests/test_sortie_a.js
```

Attendu : `Error: segment introuvable : function moisPayes(`

- [ ] **Step 3 : Écrire l'implémentation minimale**

Insérer dans `calculateur-pv-nc.html`, juste **avant** la ligne `// ===== IMPRESSION =====` :

```javascript
// ===== SORTIE A — FONCTIONS PURES =====
// Traduit le rapport des factures en durée : « l'équivalent de N mois ».
// Ne jamais écrire « vous ne payez que N mois » — le client paie bien chaque mois.
function moisPayes(fSansAn,fAvecAn){
  if(!(fSansAn>0))return{payes:0,entiers:0,part:0,offerts:12};
  const payes=Math.max(0,Math.min(12,12*fAvecAn/fSansAn));
  const entiers=Math.floor(payes);
  return{payes,entiers,part:payes-entiers,offerts:12-Math.round(payes)};
}
// Le surplus n'a pas le même sens selon qu'il est vendu ou non.
// À 0 XPF/kWh les onduleurs brident : ces kWh ne sont jamais produits.
function libelleSurplus(tarifRevente){
  return (tarifRevente>0)
    ?{titre:'Énergie revendue',sousTitre:'injectée sur le réseau et rémunérée',couleur:'#35A46B'}
    :{titre:'Réserve de production',sousTitre:'vos panneaux savent produire ces kWh en plus — il faut du stockage ou de la consommation pour les capter',couleur:'#35A46B'};
}
```

- [ ] **Step 4 : Lancer le test et la vérification syntaxe**

```bash
cd "/home/tony-linux/Documents/Synology/SynoIA/SOLAR/Calculateur SOLAIRE"
node tests/test_sortie_a.js
node -e "const fs=require('fs');const html=fs.readFileSync('calculateur-pv-nc.html','utf8');const m=html.match(/<script>([\s\S]*?)<\/script>/g);if(m){const js=m.map(s=>s.replace(/<\/?script>/g,'')).join('\n');fs.writeFileSync('_check.js',js);}" && node --check _check.js && echo "SYNTAXE OK" && rm -f _check.js
```

Attendu : `TEST PASS ✅` puis `SYNTAXE OK`.

- [ ] **Step 5 : Commit**

```bash
cd "/home/tony-linux/Documents/Synology/SynoIA/SOLAR/Calculateur SOLAIRE"
git add calculateur-pv-nc.html tests/test_sortie_a.js
git commit -m "feat(sortie A): durée payée et vocabulaire conditionnel du surplus

moisPayes() traduit le rapport des factures en nombre de mois.
libelleSurplus() bascule entre « Réserve de production » (revente à 0,
les onduleurs brident) et « Énergie revendue » (tarif > 0)."
```

---

## Task 2 : La batterie Maestro-G en SVG

**Files:**
- Modify: `calculateur-pv-nc.html` — insérer après les fonctions de Task 1
- Test: `tests/test_sortie_a.js` (compléter)

**Interfaces:**
- Consomme : `libelleSurplus()` (Task 1).
- Produit : `svgMaestro(cfg)` → `string` (markup SVG complet).
  `cfg = {prodAn, directAutoAn, batAutoAn, surplusAn, consoAn, achatAn, batLabel, tarifRevente}`

- [ ] **Step 1 : Compléter le test**

Ajouter à la fin de `tests/test_sortie_a.js`, **avant** la ligne `console.log(ok ? ...)` :

```javascript
console.log('svgMaestro');
const srcM = grab('function svgMaestro(', '\n}');
const { svgMaestro } = new Function(
  grab('function libelleSurplus(', '\n}') + '\n' + srcM + '\nreturn {svgMaestro};')();
const svg = svgMaestro({
  prodAn: 8692, directAutoAn: 2699, batAutoAn: 1800, surplusAn: 4193,
  consoAn: 4499, achatAn: 0, batLabel: 'OMEGA Maestro 14,3 kWh', tarifRevente: 0
});
eq('svg responsive', /width="100%"/.test(svg), true);
eq('aucune largeur fixe', /<svg[^>]*width="\d/.test(svg), false);
eq('les trois pourcentages', [/31%/, /21%/, /48%/].every(re => re.test(svg)), true);
eq('libellé réserve', /Réserve de production/.test(svg), true);
eq('aucune réinjection', /éinjection/.test(svg), false);
eq('aucun gris clair', /#8A8C8F|#9A9CA0|#999|#aaa/i.test(svg), false);
// bascule du vocabulaire quand la revente est rémunérée
const svgVendu = svgMaestro({
  prodAn: 8692, directAutoAn: 2699, batAutoAn: 1800, surplusAn: 4193,
  consoAn: 4499, achatAn: 0, batLabel: 'OMEGA Maestro 14,3 kWh', tarifRevente: 21
});
eq('bascule en revendue', /Énergie revendue/.test(svgVendu), true);
// somme des pourcentages = 100 quel que soit l'arrondi
const pct = [...svg.matchAll(/>(\d+)%</g)].map(m => +m[1]);
eq('somme des pourcentages = 100', pct.reduce((a, b) => a + b, 0), 100);
```

- [ ] **Step 2 : Lancer le test pour vérifier qu'il échoue**

```bash
cd "/home/tony-linux/Documents/Synology/SynoIA/SOLAR/Calculateur SOLAIRE"
node tests/test_sortie_a.js
```

Attendu : `Error: segment introuvable : function svgMaestro(`

- [ ] **Step 3 : Écrire l'implémentation**

Insérer dans `calculateur-pv-nc.html` après les fonctions de Task 1 :

```javascript
// ===== SORTIE A — BATTERIE OMEGA MAESTRO-G =====
// Armoire verticale blanche aux proportions réelles (230 × 490).
// Les pourcentages seuls vivent dans l'armoire ; libellés et valeurs sont
// à l'extérieur, reliés au centre géométrique de leur segment.
// Le SVG porte armoire ET textes : séparer les deux casse l'alignement
// dès qu'on change l'échelle.
function svgMaestro(c){
  const tot=c.directAutoAn+c.batAutoAn+c.surplusAn;
  if(!(tot>0))return'';
  // arrondis répartis pour que la somme fasse exactement 100
  let pJ=Math.round(c.directAutoAn/tot*100),pN=Math.round(c.batAutoAn/tot*100);
  let pS=100-pJ-pN;
  const H=394,Y0=110;                       // zone utile de la jauge
  const hJ=H*c.directAutoAn/tot,hN=H*c.batAutoAn/tot,hS=H*c.surplusAn/tot;
  const ySur=Y0+2, yNui=ySur+hS+2, yJou=yNui+hN+2;
  const cSur=ySur+hS/2, cNui=yNui+hN/2, cJou=yJou+hJ/2;
  const sur=libelleSurplus(c.tarifRevente);
  const OR='#F07020',AM='#F5A623',AMF='#D98B0A',VE=sur.couleur,VEF='#2E8F5C',TX='#55585C',AN='#333333';
  const t=(x,y,s,w,f,txt,ls)=>`<text x="${x}" y="${y}" font-size="${s}" font-weight="${w}" fill="${f}"${ls?` letter-spacing="${ls}"`:''}>${txt}</text>`;
  const seg=(y,h,fill,pct)=>`<rect x="48" y="${y}" width="194" height="${h}" rx="4" fill="${fill}"/>`+
    (h>34?`<text x="145" y="${y+h/2+13}" text-anchor="middle" font-size="${Math.min(48,h*0.42)}" font-weight="700" fill="#fff">${pct}%</text>`:'');
  const ligne=(cy,col)=>`<line x1="284" y1="${cy}" x2="336" y2="${cy}" stroke="${col}" stroke-width="2"/>`;
  const bloc=(cy,col,colVal,titre,valeur,l1,l2)=>
    ligne(cy,col)+
    t(352,cy-24,15,700,col===VE?VEF:AN,titre.toUpperCase(),'.09em')+
    t(352,cy+16,36,700,colVal,valeur)+
    (l1?t(352,cy+44,13,400,TX,l1):'')+
    (l2?t(352,cy+64,13,400,TX,l2):'');
  // le sous-titre de la réserve est long : on le coupe en deux lignes
  const mots=sur.sousTitre.split(' ');const mi=Math.ceil(mots.length/2);
  const s1=mots.slice(0,mi).join(' '),s2=mots.slice(mi).join(' ');
  return `<svg width="100%" viewBox="0 0 790 570" role="img" aria-label="Répartition de votre énergie solaire">
    <defs>
      <linearGradient id="mgAlu" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0" stop-color="#EDEEEF"/><stop offset=".14" stop-color="#FFFFFF"/>
        <stop offset=".66" stop-color="#FBFBFC"/><stop offset="1" stop-color="#E4E5E7"/></linearGradient>
      <linearGradient id="mgFlanc" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0" stop-color="#DDDEE0"/><stop offset="1" stop-color="#C2C4C7"/></linearGradient>
      <linearGradient id="mgEcran" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#26262A"/><stop offset="1" stop-color="#141416"/></linearGradient>
    </defs>
    <path d="M260 34 L284 47 L284 507 L260 520 Z" fill="url(#mgFlanc)"/>
    <rect x="30" y="30" width="230" height="490" rx="13" fill="url(#mgAlu)" stroke="#A8AAAD" stroke-width="1.4"/>
    <rect x="112" y="52" width="80" height="42" rx="5" fill="url(#mgEcran)"/>
    <rect x="119" y="63" width="47" height="22" rx="2" fill="#2E6FC4" opacity=".85"/>
    <circle cx="178" cy="65" r="2.2" fill="#4C4C50"/><circle cx="178" cy="72" r="2.2" fill="#4C4C50"/>
    <circle cx="178" cy="79" r="2.2" fill="#4C4C50"/><circle cx="178" cy="86" r="2.2" fill="#4C4C50"/>
    <rect x="44" y="${Y0}" width="202" height="${H}" rx="7" fill="#F8F9FA" stroke="#B4B6B9"/>
    ${seg(ySur,hS,VE,pS)}${seg(yNui,hN,AM,pN)}${seg(yJou,hJ,OR,pJ)}
    <rect x="56" y="520" width="34" height="21" rx="5" fill="#2A2A2C"/>
    <rect x="200" y="520" width="34" height="21" rx="5" fill="#2A2A2C"/>
    ${bloc(cSur,VE,VE,sur.titre,fmt(Math.round(c.surplusAn))+' kWh',s1,s2)}
    ${bloc(cNui,AM,AMF,'Stockée pour la nuit',fmt(Math.round(c.batAutoAn))+' kWh','restituée le soir par votre '+c.batLabel,'')}
    ${bloc(cJou,OR,OR,'Consommée le jour',fmt(Math.round(c.directAutoAn))+' kWh','directement par votre maison, en journée','')}
  </svg>`;
}
```

- [ ] **Step 4 : Lancer le test et la vérification syntaxe**

```bash
cd "/home/tony-linux/Documents/Synology/SynoIA/SOLAR/Calculateur SOLAIRE"
node tests/test_sortie_a.js
node -e "const fs=require('fs');const html=fs.readFileSync('calculateur-pv-nc.html','utf8');const m=html.match(/<script>([\s\S]*?)<\/script>/g);if(m){const js=m.map(s=>s.replace(/<\/?script>/g,'')).join('\n');fs.writeFileSync('_check.js',js);}" && node --check _check.js && echo "SYNTAXE OK" && rm -f _check.js
```

Attendu : `TEST PASS ✅` puis `SYNTAXE OK`.

Note : le test injecte `fmt` via `new Function` — si `fmt is not defined` apparaît, ajouter dans le test avant l'appel :
`const fmt = n => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');` et le passer en paramètre de `new Function`.

- [ ] **Step 5 : Commit**

```bash
cd "/home/tony-linux/Documents/Synology/SynoIA/SOLAR/Calculateur SOLAIRE"
git add calculateur-pv-nc.html tests/test_sortie_a.js
git commit -m "feat(sortie A): batterie OMEGA Maestro-G en SVG

Armoire verticale blanche aux proportions réelles. Pourcentages dans
l'armoire, libellés et valeurs à l'extérieur reliés au centre de leur
segment. Armoire et textes dans un seul SVG : les séparer casse
l'alignement au changement d'échelle."
```

---

## Task 3 : Les deux représentations de la facture

**Files:**
- Modify: `calculateur-pv-nc.html` — insérer après `svgMaestro`
- Test: `tests/test_sortie_a.js` (compléter)

**Interfaces:**
- Consomme : `moisPayes()` (Task 1).
- Produit :
  - `svgDouzeMois(fSansAn, fAvecAn)` → `string`
  - `svgEcartMensuel(fSansM, fAvecM)` → `string`
  - `splinePath(points)` → `string` — utilitaire Catmull-Rom, réutilisé en Task 4.

- [ ] **Step 1 : Compléter le test**

Ajouter avant le `console.log(ok ? ...)` final :

```javascript
console.log('svgDouzeMois');
const srcF = grab('function splinePath(', '\n}') + '\n' +
             grab('function svgDouzeMois(', '\n}') + '\n' +
             grab('function svgEcartMensuel(', '\n}');
const fmtT = n => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
const F = new Function('fmt', 'moisPayes',
  srcF + '\nreturn {splinePath, svgDouzeMois, svgEcartMensuel};')(fmtT, moisPayes);
const d12 = F.svgDouzeMois(276144, 62788);
eq('responsive', /width="100%"/.test(d12), true);
eq('trois mois payés', /3 mois/.test(d12), true);
eq('neuf mois offerts', /9 mois/.test(d12), true);
eq('formulation prudente', /équivalent/.test(d12), true);
eq('jamais « ne payez que »', /ne payez que/.test(d12), false);
eq('douze pastilles', (d12.match(/<circle[^>]*r="25"/g) || []).length, 12);

console.log('svgEcartMensuel');
const sans = [23012,22180,23012,22600,23012,22900,23012,23012,22800,23012,22950,23100];
const avec = [5232,5100,5232,5180,5232,5210,5232,5232,5190,5232,5205,5240];
const ecart = F.svgEcartMensuel(sans, avec);
eq('responsive', /width="100%"/.test(ecart), true);
eq('pas de rouge hors charte', /#FF4B6E/i.test(ecart), false);
eq('pas de turquoise hors charte', /#00D4A0/i.test(ecart), false);
eq('accents présents', /photovoltaïque/.test(ecart), true);
eq('douze étiquettes d\'écart', (ecart.match(/−\d/g) || []).length >= 12, true);
```

- [ ] **Step 2 : Lancer le test pour vérifier qu'il échoue**

```bash
cd "/home/tony-linux/Documents/Synology/SynoIA/SOLAR/Calculateur SOLAIRE"
node tests/test_sortie_a.js
```

Attendu : `Error: segment introuvable : function splinePath(`

- [ ] **Step 3 : Écrire l'implémentation**

```javascript
// ===== SORTIE A — COURBES =====
// Catmull-Rom converti en Bézier cubique : une spline qui passe par tous
// les points, sans dépendance externe.
function splinePath(p){
  if(!p||p.length<2)return'';
  let d='M '+p[0][0]+' '+p[0][1]+' ';
  for(let i=0;i<p.length-1;i++){
    const a=p[i-1]||p[i],b=p[i],c=p[i+1],e=p[i+2]||p[i+1];
    d+=`C ${b[0]+(c[0]-a[0])/6} ${b[1]+(c[1]-a[1])/6}, ${c[0]-(e[0]-b[0])/6} ${c[1]-(e[1]-b[1])/6}, ${c[0]} ${c[1]} `;
  }
  return d;
}

// Forme par défaut : le rapport des factures exprimé en durée.
// Sur un profil de consommation régulier les douze mois sont quasi
// identiques — une courbe temporelle n'aurait rien à raconter.
function svgDouzeMois(fSansAn,fAvecAn){
  const M=['Jan','Fév','Mar','Avr','Mai','Jun','Jul','Aoû','Sep','Oct','Nov','Déc'];
  const m=moisPayes(fSansAn,fAvecAn);
  const nb=Math.round(m.payes),reste=12-nb;
  const OR='#F07020',TX='#55585C',LI='#D8DADC',AN='#333333';
  const W=780,H=250,r=25,gx=63,ox=(W-11*gx)/2,cy=104;
  let s=`<svg width="100%" viewBox="0 0 ${W} ${H}" role="img" aria-label="Équivalent en mois de facture">
    <defs><clipPath id="dmPart"><rect x="0" y="0" width="${m.part*2*r}" height="${2*r}"/></clipPath></defs>
    <text x="${W/2}" y="26" text-anchor="middle" font-size="10" letter-spacing=".2em" fill="${TX}">SUR VOS DOUZE MOIS D'ÉLECTRICITÉ</text>`;
  for(let i=0;i<12;i++){
    const cx=ox+i*gx;
    if(i<m.entiers){
      s+=`<circle cx="${cx}" cy="${cy}" r="${r}" fill="${OR}"/><text x="${cx}" y="${cy+4}" text-anchor="middle" font-size="11" font-weight="700" fill="#fff">${M[i]}</text>`;
    }else if(i===m.entiers&&m.part>0.02){
      s+=`<circle cx="${cx}" cy="${cy}" r="${r}" fill="#fff" stroke="${LI}" stroke-width="1.8"/>`+
         `<g transform="translate(${cx-r},${cy-r})" clip-path="url(#dmPart)"><circle cx="${r}" cy="${r}" r="${r}" fill="${OR}"/></g>`+
         `<text x="${cx}" y="${cy+4}" text-anchor="middle" font-size="11" font-weight="700" fill="${TX}">${M[i]}</text>`;
    }else{
      s+=`<circle cx="${cx}" cy="${cy}" r="${r}" fill="#fff" stroke="${LI}" stroke-width="1.8"/><text x="${cx}" y="${cy+4}" text-anchor="middle" font-size="11" fill="${TX}">${M[i]}</text>`;
    }
  }
  const y1=cy+r+14,y2=cy+r+24;
  if(nb>0){
    s+=`<path d="M ${ox-r} ${y1} L ${ox-r} ${y2} L ${ox+(nb-1)*gx+r} ${y2} L ${ox+(nb-1)*gx+r} ${y1}" fill="none" stroke="${OR}" stroke-width="1.8"/>`+
       `<text x="${ox+(nb-1)*gx/2}" y="${y2+34}" text-anchor="middle" font-size="26" font-weight="700" fill="${OR}">${nb} mois</text>`+
       `<text x="${ox+(nb-1)*gx/2}" y="${y2+52}" text-anchor="middle" font-size="10" letter-spacing=".12em" fill="${TX}">QUE VOUS PAYEZ ENCORE</text>`;
  }
  if(reste>0){
    s+=`<path d="M ${ox+nb*gx-r} ${y1} L ${ox+nb*gx-r} ${y2} L ${ox+11*gx+r} ${y2} L ${ox+11*gx+r} ${y1}" fill="none" stroke="${LI}" stroke-width="1.8"/>`+
       `<text x="${ox+(nb+11)*gx/2}" y="${y2+34}" text-anchor="middle" font-size="26" font-weight="700" fill="${AN}">${reste} mois</text>`+
       `<text x="${ox+(nb+11)*gx/2}" y="${y2+52}" text-anchor="middle" font-size="10" letter-spacing=".12em" fill="${TX}">OFFERTS PAR LE SOLEIL</text>`;
  }
  s+=`<text x="${W/2}" y="${H-6}" text-anchor="middle" font-size="10" fill="${TX}">votre facture avec l'installation représente l'équivalent de ${nb} mois de facture actuelle</text></svg>`;
  return s;
}

// Forme alternative : l'écart réel mois par mois. Pertinente sur les
// profils saisonniers (piscine, climatisation, résidence secondaire).
function svgEcartMensuel(fSansM,fAvecM){
  const M=['Jan','Fév','Mar','Avr','Mai','Jun','Jul','Aoû','Sep','Oct','Nov','Déc'];
  const OR='#F07020',GR='#A8ACB1',TX='#55585C',LI='#D8DADC',AN='#333333';
  const W=880,H=290,PL=54,PR=26,PT=18,PB=54;
  const iw=W-PL-PR,ih=H-PT-PB;
  const max=Math.max(...fSansM)*1.08||1;
  const X=i=>PL+(i/11)*iw,Y=v=>PT+ih-(v/max)*ih;
  const pS=fSansM.map((v,i)=>[X(i),Y(v)]),pA=fAvecM.map((v,i)=>[X(i),Y(v)]);
  const dia=(cx,cy,r,f)=>`<path d="M ${cx} ${cy-r} L ${cx+r} ${cy} L ${cx} ${cy+r} L ${cx-r} ${cy} Z" fill="${f}" stroke="#fff" stroke-width="1.3"/>`;
  let s=`<svg width="100%" viewBox="0 0 ${W} ${H}" role="img" aria-label="Écart de facture mois par mois">`;
  const pas=Math.pow(10,Math.floor(Math.log10(max)))/2;
  for(let g=0;g<=max;g+=pas){
    s+=`<line x1="${PL}" y1="${Y(g)}" x2="${W-PR}" y2="${Y(g)}" stroke="${LI}"/>`+
       `<text x="${PL-8}" y="${Y(g)+3.5}" text-anchor="end" font-size="9" fill="${TX}">${Math.round(g/1000)}k</text>`;
  }
  const rev=[...pA].reverse(),dr=splinePath(rev);
  s+=`<path d="${splinePath(pS)} L ${rev[0][0]} ${rev[0][1]} ${dr.slice(dr.indexOf('C'))} Z" fill="${OR}" opacity=".11"/>`;
  pS.forEach((p,i)=>{s+=`<line x1="${p[0]}" y1="${p[1]}" x2="${pA[i][0]}" y2="${pA[i][1]}" stroke="${OR}" stroke-width="3.4" opacity=".13"/>`;});
  s+=`<path d="${splinePath(pS)}" fill="none" stroke="${GR}" stroke-width="2.2" stroke-dasharray="6 4"/>`;
  pS.forEach(p=>{s+=dia(p[0],p[1],4.4,GR);});
  s+=`<path d="${splinePath(pA)}" fill="none" stroke="${OR}" stroke-width="2.6"/>`;
  pA.forEach((p,i)=>{
    const anc=i===0?'start':(i===11?'end':'middle');
    s+=`<circle cx="${p[0]}" cy="${p[1]}" r="4.2" fill="${OR}" stroke="#fff" stroke-width="1.3"/>`+
       `<text x="${p[0]}" y="${p[1]+17}" text-anchor="${anc}" font-size="8" font-weight="700" fill="${OR}">−${fmt(Math.round(fSansM[i]-fAvecM[i]))}</text>`;
  });
  M.forEach((m,i)=>{s+=`<text x="${X(i)}" y="${PT+ih+18}" text-anchor="middle" font-size="9" fill="${TX}">${m}</text>`;});
  s+=`<line x1="${PL}" y1="${PT+ih}" x2="${W-PR}" y2="${PT+ih}" stroke="${AN}" stroke-width="1.2"/>`;
  const ly=H-10;
  s+=dia(PL+5,ly-3.5,4.4,GR)+`<text x="${PL+16}" y="${ly}" font-size="9.5" fill="${TX}">Sans photovoltaïque</text>`+
     `<circle cx="${PL+150}" cy="${ly-3.5}" r="4.2" fill="${OR}"/><text x="${PL+161}" y="${ly}" font-size="9.5" fill="${TX}">Avec votre installation</text>`+
     `<rect x="${PL+300}" y="${ly-9}" width="14" height="9" fill="${OR}" opacity=".20"/><text x="${PL+319}" y="${ly}" font-size="9.5" fill="${TX}">Votre économie</text>`+
     `<text x="${W-PR}" y="${ly}" text-anchor="end" font-size="9.5" fill="${TX}">XPF par mois</text></svg>`;
  return s;
}
```

- [ ] **Step 4 : Lancer le test et la vérification syntaxe**

```bash
cd "/home/tony-linux/Documents/Synology/SynoIA/SOLAR/Calculateur SOLAIRE"
node tests/test_sortie_a.js
node -e "const fs=require('fs');const html=fs.readFileSync('calculateur-pv-nc.html','utf8');const m=html.match(/<script>([\s\S]*?)<\/script>/g);if(m){const js=m.map(s=>s.replace(/<\/?script>/g,'')).join('\n');fs.writeFileSync('_check.js',js);}" && node --check _check.js && echo "SYNTAXE OK" && rm -f _check.js
```

- [ ] **Step 5 : Commit**

```bash
cd "/home/tony-linux/Documents/Synology/SynoIA/SOLAR/Calculateur SOLAIRE"
git add calculateur-pv-nc.html tests/test_sortie_a.js
git commit -m "feat(sortie A): deux formes de la facture, douze mois et écart mensuel

Les douze pastilles par défaut : sur un profil régulier les mois sont
identiques, une courbe temporelle ne raconte rien. L'écart mois par mois
reste disponible pour les profils saisonniers, restylé dans la palette
validée (le rouge et le turquoise Plotly sont hors charte)."
```

---

## Task 4 : Le ROI en relief

**Files:**
- Modify: `calculateur-pv-nc.html` — insérer après `svgEcartMensuel`
- Test: `tests/test_sortie_a.js` (compléter)

**Interfaces:**
- Consomme : `splinePath()` (Task 3).
- Produit : `svgReliefROI(cumuls, paybackAn)` → `string`.
  `cumuls` = tableau des bilans cumulés année par année (index 0 = an 1). `paybackAn` = numéro d'année de bascule, ou `0` si jamais atteint.

- [ ] **Step 1 : Compléter le test**

```javascript
console.log('svgReliefROI');
const R = new Function('fmt', grab('function splinePath(', '\n}') + '\n' +
  grab('function svgReliefROI(', '\n}') + '\nreturn {svgReliefROI};')(fmtT);
const cum = (() => { const a = []; let c = -1650000, e = 213355;
  for (let i = 0; i < 20; i++) { c += e; a.push(Math.round(c)); e *= 1.025; } return a; })();
const roi = R.svgReliefROI(cum, 8);
eq('responsive', /width="100%"/.test(roi), true);
eq('jalon investissement', /INVESTISSEMENT/.test(roi), true);
eq('jalon bascule', /An 8/.test(roi), true);
eq('jalon gain final', /GAIN FINAL/.test(roi), true);
eq('trois jalons seulement', (roi.match(/<circle[^>]*stroke-width="2\.6"/g) || []).length, 3);
// jamais remboursé : pas de jalon de bascule, pas de plantage
const jamais = R.svgReliefROI(cum.map(() => -100000), 0);
eq('jamais remboursé', /An 0/.test(jamais), false);
```

- [ ] **Step 2 : Lancer le test pour vérifier qu'il échoue**

```bash
cd "/home/tony-linux/Documents/Synology/SynoIA/SOLAR/Calculateur SOLAIRE"
node tests/test_sortie_a.js
```

Attendu : `Error: segment introuvable : function svgReliefROI(`

- [ ] **Step 3 : Écrire l'implémentation**

```javascript
// ===== SORTIE A — RETOUR SUR INVESTISSEMENT =====
// La courbe cumulée devient un versant : creusé sous le zéro, rempli
// au-dessus. Trois jalons, aucune grille, aucun axe chiffré.
function svgReliefROI(cumuls,paybackAn){
  if(!cumuls||!cumuls.length)return'';
  const OR='#F07020',GR='#A8ACB1',TX='#55585C',AN='#333333';
  const n=cumuls.length;
  const W=700,H=260,PL=34,PR=34,PT=34,PB=44;
  const iw=W-PL-PR,ih=H-PT-PB;
  const mn=Math.min(...cumuls,0)*1.12,mx=Math.max(...cumuls,0)*1.12;
  const X=i=>PL+(i/(n-1))*iw,Y=v=>PT+ih-((v-mn)/((mx-mn)||1))*ih,Z=Y(0);
  const pts=cumuls.map((v,i)=>[X(i),Y(v)]);
  const aire=`${splinePath(pts)} L ${X(n-1)} ${Z} L ${X(0)} ${Z} Z`;
  let s=`<svg width="100%" viewBox="0 0 ${W} ${H}" role="img" aria-label="Retour sur investissement">
   <defs>
    <linearGradient id="roUp" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="${OR}" stop-opacity=".45"/><stop offset="1" stop-color="${OR}" stop-opacity=".04"/></linearGradient>
    <linearGradient id="roDw" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="${GR}" stop-opacity=".05"/><stop offset="1" stop-color="${GR}" stop-opacity=".34"/></linearGradient>
    <clipPath id="roCu"><rect x="0" y="0" width="${W}" height="${Z}"/></clipPath>
    <clipPath id="roCd"><rect x="0" y="${Z}" width="${W}" height="${H-Z}"/></clipPath>
   </defs>
   <path d="${aire}" fill="url(#roUp)" clip-path="url(#roCu)"/>
   <path d="${aire}" fill="url(#roDw)" clip-path="url(#roCd)"/>
   <line x1="${PL}" y1="${Z}" x2="${W-PR}" y2="${Z}" stroke="${AN}" stroke-width="1.2"/>
   <path d="${splinePath(pts)}" fill="none" stroke="${OR}" stroke-width="2.8"/>`;
  const jalons=[[0,'Investissement',fmt(Math.round(cumuls[0])),TX]];
  if(paybackAn>0&&paybackAn<=n)jalons.push([paybackAn-1,'Remboursée','An '+paybackAn,OR]);
  jalons.push([n-1,'Gain final',(cumuls[n-1]>=0?'+':'')+fmt(Math.round(cumuls[n-1])),OR]);
  jalons.forEach(([i,lab,val,col])=>{
    const px=X(i),py=Y(cumuls[i]);
    // le premier jalon est en bas de courbe : son libellé passe dessous,
    // sinon il chevauche le tracé
    const dessous=(i===0),ty=dessous?py+20:py-24;
    const anc=i===n-1?'end':(i===0?'start':'middle');
    s+=`<circle cx="${px}" cy="${py}" r="5" fill="#fff" stroke="${OR}" stroke-width="2.6"/>`+
       `<text x="${px}" y="${ty}" text-anchor="${anc}" font-size="8.5" letter-spacing=".13em" fill="${TX}">${lab.toUpperCase()}</text>`+
       `<text x="${px}" y="${ty+17}" text-anchor="${anc}" font-size="17" font-weight="700" fill="${col}">${val}</text>`;
  });
  s+=`<text x="${PL}" y="${H-10}" font-size="9" fill="${TX}">An 1</text>`+
     `<text x="${W-PR}" y="${H-10}" text-anchor="end" font-size="9" fill="${TX}">An ${n}</text></svg>`;
  return s;
}
```

- [ ] **Step 4 : Lancer le test et la vérification syntaxe**

```bash
cd "/home/tony-linux/Documents/Synology/SynoIA/SOLAR/Calculateur SOLAIRE"
node tests/test_sortie_a.js
node -e "const fs=require('fs');const html=fs.readFileSync('calculateur-pv-nc.html','utf8');const m=html.match(/<script>([\s\S]*?)<\/script>/g);if(m){const js=m.map(s=>s.replace(/<\/?script>/g,'')).join('\n');fs.writeFileSync('_check.js',js);}" && node --check _check.js && echo "SYNTAXE OK" && rm -f _check.js
```

- [ ] **Step 5 : Commit**

```bash
cd "/home/tony-linux/Documents/Synology/SynoIA/SOLAR/Calculateur SOLAIRE"
git add calculateur-pv-nc.html tests/test_sortie_a.js
git commit -m "feat(sortie A): retour sur investissement en relief

Versant creusé sous le zéro, rempli au-dessus. Trois jalons seulement.
Le libellé du premier jalon passe sous le point, sinon il chevauche la
courbe. Cas « jamais remboursé » couvert : le jalon de bascule est omis."
```

---

## Task 5 : La page « L'essentiel »

**Files:**
- Modify: `calculateur-pv-nc.html` — ajouter le conteneur après `<div id="cover-page" ...>` (ligne ~507)
- Modify: `calculateur-pv-nc.html` — CSS print, après la règle `#last-page` (ligne ~466)
- Modify: `calculateur-pv-nc.html` — `preparePrint()`, après la construction de `#cover-page` (ligne ~1270)

**Interfaces:**
- Consomme : `svgMaestro()`, `svgDouzeMois()`, `svgEcartMensuel()` (Tasks 2-3), `lastStudyData`, `fmt()`.
- Produit : `#essentiel-page` rempli, imprimé entre la garde et les pages optionnelles.

- [ ] **Step 1 : Ajouter le conteneur**

Juste après la ligne `<div id="cover-page" style="display:none;page-break-after:always"></div>` :

```html
<div id="essentiel-page" style="display:none"></div>
```

- [ ] **Step 2 : Ajouter les règles CSS d'impression**

Repérer la règle existante (ligne ~466) :

```css
  #last-page{display:block!important;break-before:page;margin:0;padding:0}
```

Ajouter **juste après** :

```css
  #essentiel-page{display:block!important;break-before:page;break-after:page;margin:0;padding:0}
  body.print-B #essentiel-page,body.print-C #essentiel-page{display:none!important}
```

Et à côté de la règle `#cover-page{display:none}` (ligne ~218), ajouter :

```css
#essentiel-page{display:none}
```

- [ ] **Step 3 : Construire la page dans `preparePrint()`**

Dans `preparePrint()`, insérer **après** la fermeture du template de `cover.innerHTML` (juste avant le commentaire `// ===== DERNIÈRE PAGE : RÉCAPITULATIF + ROI =====`) :

```javascript
  // ===== PAGE « L'ESSENTIEL » (sortie A) =====
  const ess=document.getElementById('essentiel-page');
  if(tab<=1&&lastStudyData.prodAn){
    const L=lastStudyData;
    const eco=L.fSansAn-L.fAvecAn;
    const baisse=L.fSansAn>0?Math.round((1-L.fAvecAn/L.fSansAn)*100):0;
    const largeurApres=L.fSansAn>0?Math.max(14,Math.round(L.fAvecAn/L.fSansAn*100)):0;
    const ratio=L.devis>0?(L.eco20/L.devis).toFixed(1).replace('.',','):'—';
    const couvert=L.consoAn>0?Math.round((L.consoAn-L.achatAn)/L.consoAn*100):0;
    const formeEcart=document.body.classList.contains('psoff-fmois');
    const svgFacture=formeEcart?svgEcartMensuel(L.fSansM,L.fAvecM):svgDouzeMois(L.fSansAn,L.fAvecAn);
    ess.innerHTML=`
    <style>
      #essentiel-page .es{font-family:'Nunito',sans-serif;color:#333;display:flex;min-height:25.6cm;
        -webkit-print-color-adjust:exact;print-color-adjust:exact}
      #essentiel-page .es-l{flex:1;padding:1.4cm 0.9cm 1cm 1.5cm;display:flex;flex-direction:column;justify-content:space-between}
      #essentiel-page .es-r{width:8cm;background:#F6F7F8;padding:1.4cm 1.1cm 1cm;display:flex;flex-direction:column;justify-content:space-between}
      #essentiel-page .es-k{font-size:9px;letter-spacing:.18em;text-transform:uppercase;color:#55585C}
      #essentiel-page .es-v{font-size:33px;font-weight:700;line-height:1.15;margin-top:1mm}
      #essentiel-page .es-v small{font-size:11px;font-weight:400;color:#55585C;letter-spacing:0}
      #essentiel-page .es-bar{height:11mm;border-radius:1.5mm;display:flex;align-items:center;
        padding:0 3.5mm;color:#fff;font-size:16px;font-weight:700;white-space:nowrap}
      #essentiel-page .es-flux{border-left:3px solid #F07020;padding-left:4.5mm;margin-bottom:8mm}
      #essentiel-page .es-flux:last-child{margin-bottom:0}
      #essentiel-page .es-etape{display:flex;align-items:baseline;gap:4mm}
      #essentiel-page .es-etape b{font-size:20px;color:#F07020;width:7mm}
      #essentiel-page .es-sep{height:1px;background:#D8DADC;margin:3mm 0}
    </style>
    <div class="es">
      <div class="es-l">
        <div>
          <div style="font-size:15px;font-weight:700;letter-spacing:.22em">SOLAR <span style="color:#F07020">CONCEPT</span></div>
          <div style="font-size:9px;color:#55585C;margin-top:1.5mm">${client||'—'}${adresse?' · '+adresse:''} · ${dateStr}</div>
        </div>
        <div>
          <div style="font-size:10px;letter-spacing:.22em;text-transform:uppercase;color:#55585C">Vous économisez</div>
          <div style="font-size:70px;font-weight:700;line-height:1;color:#F07020;letter-spacing:-.025em;margin-top:2mm">${fmt(Math.round(eco))}</div>
          <div style="font-size:19px;font-weight:700;color:#F07020;letter-spacing:.14em;margin-top:1mm">XPF PAR AN</div>
        </div>
        <div>
          <div class="es-k" style="margin-bottom:3mm">Votre facture d'électricité</div>
          <div style="display:flex;align-items:center;gap:3mm;margin-bottom:2.5mm">
            <span class="es-k" style="width:19mm;text-align:right;letter-spacing:.08em">Aujourd'hui</span>
            <div class="es-bar" style="flex:1;background:#A8ACB1">${fmt(Math.round(L.fSansAn))} XPF</div>
          </div>
          <div style="display:flex;align-items:center;gap:3mm">
            <span class="es-k" style="width:19mm;text-align:right;letter-spacing:.08em">Avec le PV</span>
            <div class="es-bar" style="width:${largeurApres}%;background:#F07020">${fmt(Math.round(L.fAvecAn))}</div>
            <span style="font-size:10.5px;color:#55585C">XPF/an — soit <b style="color:#333">−${baisse} %</b></span>
          </div>
        </div>
        <div style="display:flex;flex-direction:column;gap:8mm">
          <div><div class="es-k">Installation remboursée</div>
            <div class="es-v">${L.pb?'An '+L.pb:'> '+getS().dpv+' ans'} <small>${L.pb?'puis '+(getS().dpv-L.pb)+' ans de gain net':''}</small></div></div>
          <div><div class="es-k">Gains cumulés · ${getS().dpv} ans</div>
            <div class="es-v">${fmt(Math.round(L.eco20||0))} <small>XPF · ${ratio} × l'investissement</small></div></div>
          <div><div class="es-k">Autonomie énergétique</div>
            <div class="es-v">${couvert} % <small>${fmt(Math.round(L.achatAn))} kWh acheté au réseau</small></div></div>
        </div>
        <div>
          <div class="es-k" style="margin-bottom:3.5mm">Les prochaines étapes</div>
          <div class="es-etape"><b>1</b><span style="font-size:12px;font-weight:700">Validation de l'étude</span><span style="font-size:10px;color:#55585C;margin-left:auto">ensemble, aujourd'hui</span></div>
          <div class="es-sep"></div>
          <div class="es-etape"><b>2</b><span style="font-size:12px;font-weight:700">Visite technique</span><span style="font-size:10px;color:#55585C;margin-left:auto">sous 10 jours</span></div>
          <div class="es-sep"></div>
          <div class="es-etape"><b>3</b><span style="font-size:12px;font-weight:700">Pose et mise en service</span><span style="font-size:10px;color:#55585C;margin-left:auto">½ journée</span></div>
        </div>
        <div style="font-size:8px;color:#55585C">Solar Concept · ${commTel||'47 03 02'} · document estimatif non contractuel</div>
      </div>
      <div class="es-r">
        <div>
          <div class="es-k" style="letter-spacing:.2em">Où va votre énergie</div>
          <div style="font-size:12px;color:#55585C;margin-top:1.5mm"><b style="color:#F07020;font-size:15px">${fmt(Math.round(L.prodAn))} kWh</b> produits par an</div>
        </div>
        <div>${svgMaestro({prodAn:L.prodAn,directAutoAn:L.directAutoAn,batAutoAn:L.batAutoAn,
          surplusAn:L.reinjAn,consoAn:L.consoAn,achatAn:L.achatAn,
          batLabel:L.batLabel||'batterie',tarifRevente:L.rev||0})}</div>
        <div style="border-top:1px solid #C9CBCD;padding-top:4mm">
          <div style="display:flex;justify-content:space-between;font-size:10px;color:#55585C;margin-bottom:2.5mm"><span>Votre besoin annuel</span><b style="color:#333;font-size:13px">${fmt(Math.round(L.consoAn))} kWh</b></div>
          <div style="display:flex;justify-content:space-between;font-size:10px;color:#55585C;margin-bottom:2.5mm"><span>Couvert par le solaire</span><b style="color:#F07020;font-size:13px">${couvert} %</b></div>
          <div style="display:flex;justify-content:space-between;font-size:10px;color:#55585C"><span>Acheté au réseau</span><b style="color:#F07020;font-size:13px">${fmt(Math.round(L.achatAn))} kWh</b></div>
        </div>
      </div>
    </div>
    <div style="padding:0 1.5cm 0.6cm">${svgFacture}</div>`;
  }else{ess.innerHTML='';}
```

- [ ] **Step 4 : Alimenter `lastStudyData` avec les champs manquants**

Dans `calcT1()`, repérer l'affectation de `lastStudyData` (chercher `lastStudyData=`) et compléter l'objet avec les champs consommés ci-dessus. Ajouter **sans retirer** les champs existants :

```javascript
    prodAn,consoAn:consoM.reduce((a,b)=>a+b,0),
    directAutoAn,batAutoAn,reinjAn,achatAn,
    fSansM,fAvecM,rev,
    batLabel:batModel>0?('OMEGA '+({4800:'Élite',10650:'Prestige',14336:'Maestro'}[batModel]||'batterie')+' '+fmtD(batWh/1000)+' kWh'):'batterie',
    nbP,panWc,
```

Si `eco20` n'existe pas dans `lastStudyData`, l'ajouter à partir du tableau d'amortissement déjà calculé dans `calcT1` (chercher `eco15`) :

```javascript
    eco20:(function(){const am=buildAmort(devis,ecoAn,s.hau,s.deg,20,0,s.ded,0,0);return am.rows[am.rows.length-1].cumul;})(),
```

- [ ] **Step 5 : Vérifier syntaxe, rendre et regarder le résultat**

```bash
cd "/home/tony-linux/Documents/Synology/SynoIA/SOLAR/Calculateur SOLAIRE"
node -e "const fs=require('fs');const html=fs.readFileSync('calculateur-pv-nc.html','utf8');const m=html.match(/<script>([\s\S]*?)<\/script>/g);if(m){const js=m.map(s=>s.replace(/<\/?script>/g,'')).join('\n');fs.writeFileSync('_check.js',js);}" && node --check _check.js && echo "SYNTAXE OK" && rm -f _check.js
node tests/rendu-sortie-a.js _rendu-t5
```

Attendu : `RENDU OK`, aucune erreur JS, et `_rendu-t5/essentiel-page.png` généré.

**Contrôle visuel obligatoire** — ouvrir `_rendu-t5/essentiel-page.png` et vérifier point par point :
- aucun texte tronqué ni chevauchant ;
- les trois lignes de rappel de la Maestro pointent bien au centre de leur segment ;
- les deux colonnes remplissent toute la hauteur, aucun blanc résiduel en bas ;
- le mot « Réinjection » n'apparaît nulle part.

- [ ] **Step 6 : Commit**

```bash
cd "/home/tony-linux/Documents/Synology/SynoIA/SOLAR/Calculateur SOLAIRE"
git add calculateur-pv-nc.html
git commit -m "feat(sortie A): page « L'essentiel » en deux colonnes

Bloc print-only sur le modèle de #cover-page : l'affichage écran n'est pas
touché, les SVG sont pensés pour le fond blanc et cohabiteraient mal avec
le thème sombre. L'argent à gauche, l'énergie à droite sur aplat clair."
```

---

## Task 6 : Suppression des doublons et panneau d'impression

**Files:**
- Modify: `calculateur-pv-nc.html` — `PRINT_CFG` (ligne ~1037)
- Modify: `calculateur-pv-nc.html` — CSS `psoff-*` (ligne ~439)
- Modify: `calculateur-pv-nc.html` — `renderEnergyFiscalRecap()` (ligne ~1539)
- Modify: `calculateur-pv-nc.html` — bloc résultats de l'onglet 1 (lignes 556-588)

- [ ] **Step 1 : Nouvelle configuration du panneau d'impression**

Remplacer l'entrée `A:` de `PRINT_CFG` par :

```javascript
  A:[{id:'fmois',label:'Facture — l’écart mois par mois',def:0},
     {id:'tranches',label:'ROI par tranche fiscale',def:1},
     {id:'groi',label:'Graphique ROI 20 ans',def:0},
     {id:'amort',label:"Tableau d'amortissement",def:0},
     {id:'factures',label:'Estimation de vos factures',def:0},
     {id:'bilan',label:'Bilan énergétique mensuel',def:0}],
```

`pile` et `gfact` disparaissent : la répartition vit dans la Maestro, la facture est sur la page « L'essentiel ».

Note sur `fmois` : la case **cochée** sélectionne la forme « écart mois par mois ». La logique `psoff-` étant inversée (une case décochée ajoute la classe), le code de Task 5 lit `document.body.classList.contains('psoff-fmois')` — décoché ⇒ classe présente ⇒ forme par défaut « douze mois ». Cohérent.

- [ ] **Step 2 : Rendre `tranches` et `amort` mutuellement exclusifs**

Dans `pmSync()`, remplacer le corps par :

```javascript
function pmSync(){
  // « ROI par tranche fiscale » et « Tableau d'amortissement » affichent tous
  // deux la déduction et le payback par tranche : cocher l'un décoche l'autre.
  const dernier=event&&event.target?event.target.dataset.psecId:null;
  if(dernier==='amort'&&event.target.checked){
    const t=document.querySelector('#pm-list input[data-psec-id="tranches"]');if(t)t.checked=false;
  }
  if(dernier==='tranches'&&event.target.checked){
    const a=document.querySelector('#pm-list input[data-psec-id="amort"]');if(a)a.checked=false;
  }
  pmMarkPreset('');pmCount();
}
```

- [ ] **Step 3 : Supprimer les blocs devenus redondants**

Dans le bloc résultats de l'onglet 1 (lignes 556-588), **retirer** les nœuds suivants et leurs appels de rendu associés :

- `<div class="kpi-grid" id="k1_fin" ...>` — doublon du héros et des trois chiffres.
- `<div id="recap1"></div>` — doublon du récapitulatif de fin.
- `<div id="recap1_efy_bilan"></div>` — doublon de la Maestro.
- `<div class="ps ps-donut" data-psec="pile">…</div>` — remplacé par la Maestro.
- `<div id="k1_pb"></div>` — doublon de « Installation remboursée ».

Ces nœuds étant lus par `calcT1()`, retirer aussi les appels correspondants : `renderRecap('recap1',…)`, `kpi('k1_fin',…)`, `plotDonut('g1_donut',…)`, et l'écriture de `k1_pb`. Remplacer la clé `bilan` passée à `renderEnergyFiscalRecap` par `null` et court-circuiter l'écriture correspondante :

```javascript
  if(divId.bilan)document.getElementById(divId.bilan).innerHTML=`…`;
```

**Attention** : ne retirer que les nœuds de l'onglet 1. Les onglets 2, 3 et 4 utilisent les mêmes fonctions avec d'autres identifiants — les casser romprait les sorties B et C, hors périmètre.

- [ ] **Step 4 : Retirer la ligne « Total économie annuelle »**

Dans `renderEnergyFiscalRecap()`, la ligne totale est un doublon du chiffre héros pour la sortie A. La conditionner :

```javascript
  if(!cfg.sansTotal)r2+=`<tr class="efy-total"><td>Total économie annuelle (An 1)</td><td class="efy-v">${fmt(Math.round(ecoTotal))} XPF</td></tr>`;
```

et passer `sansTotal:true` depuis `calcT1()` uniquement.

- [ ] **Step 5 : Brancher le ROI en relief sur la section `groi`**

`svgReliefROI()` a été créée en Task 4 mais n'est encore appelée nulle part. La section cochable `groi` de l'onglet 1 affiche aujourd'hui un graphe Plotly sombre : le remplacer.

Dans `calcT1()`, repérer l'appel qui alimente `g1_roi` (chercher `g1_roi`) et le remplacer par :

```javascript
  // ROI en relief — SVG print-only, remplace le tracé Plotly sombre
  (function(){
    const am=buildAmort(devis,ecoAn,s.hau,s.deg,s.dpv,0,s.ded,0,0);
    const cumuls=am.rows.map(r=>r.cumul);
    document.getElementById('g1_roi').innerHTML=svgReliefROI(cumuls,am.pb||0);
  })();
```

Retirer le `style="height:270px"` du conteneur `#g1_roi` dans le HTML (ligne ~571) : le SVG gère sa propre hauteur via son `viewBox`.

**Attention** : `g1_roi` n'est utilisé que par l'onglet 1. Les conteneurs `g2_roi`, `g3_roi`, `g4_roi` des autres onglets ne doivent pas être touchés.

- [ ] **Step 6 : Aligner l'horizon sur 20 ans**

Dans la dernière page (`#last-page`), remplacer la carte « Économies cumulées sur 15 ans » par 20 ans, pour ne pas contredire la page « L'essentiel » :

```javascript
        <div class="lp-kpi green"><div class="lp-kpi-v">${fmt(Math.round(eco20||eco15))} F</div><div class="lp-kpi-l">Gains cumulés sur 20 ans</div></div>`;
```

et déstructurer `eco20` depuis `lastStudyData` en tête de `preparePrint()`.

- [ ] **Step 7 : Vérifier**

```bash
cd "/home/tony-linux/Documents/Synology/SynoIA/SOLAR/Calculateur SOLAIRE"
node -e "const fs=require('fs');const html=fs.readFileSync('calculateur-pv-nc.html','utf8');const m=html.match(/<script>([\s\S]*?)<\/script>/g);if(m){const js=m.map(s=>s.replace(/<\/?script>/g,'')).join('\n');fs.writeFileSync('_check.js',js);}" && node --check _check.js && echo "SYNTAXE OK" && rm -f _check.js
node tests/test_t1_monotonie.js
node tests/test_t2_monotonie.js
node tests/test_export_json.js
node tests/rendu-sortie-a.js _rendu-t6
```

Attendu : `SYNTAXE OK`, les trois tests existants passent (le moteur de calcul n'a pas bougé), `RENDU OK` sans erreur JS.

**Contrôle visuel** : ouvrir `_rendu-t6/sortie-A.pdf`. Vérifier qu'aucun chiffre n'apparaît deux fois dans le document, et que l'onglet 1 s'affiche toujours correctement à l'écran.

- [ ] **Step 8 : Commit**

```bash
cd "/home/tony-linux/Documents/Synology/SynoIA/SOLAR/Calculateur SOLAIRE"
git add calculateur-pv-nc.html
git commit -m "refactor(sortie A): suppression des doublons, panneau d'impression revu

Quatre blocs imprimés d'office supprimés (bilan énergétique annuel, cartes
KPI, récapitulatif installation, carte payback) : tous redits sur la page
« L'essentiel ». La pile quitte les cases à cocher, remplacée par la
Maestro. « ROI par tranche » et « Tableau d'amortissement » deviennent
exclusifs. Horizon aligné sur 20 ans partout."
```

---

## Task 7 : Récapitulatif installation sur la garde, investissement remonté

**Files:**
- Modify: `calculateur-pv-nc.html` — page de garde dans `preparePrint()` (lignes ~1249-1256)
- Modify: `calculateur-pv-nc.html` — dernière page (lignes ~1278-1285, 1353-1356)

- [ ] **Step 1 : Ajouter le récapitulatif sur la garde**

Le CSS `.cv-recap` / `.cv-kpi-grid` existe déjà mais n'est utilisé nulle part. Insérer le bloc **entre** `<div class="cv-bigtitle">…</div>` et `<div class="cv-logolayer">` :

```javascript
    <!-- RÉCAPITULATIF INSTALLATION — sans montant, décision Tony 30/07/2026 -->
    <div class="cv-recap">
      <div class="cv-recap-label">Votre installation</div>
      <div class="cv-kpi-grid">
        <div class="cv-kpi-card"><div class="cv-kpi-card-val">${kwcStr||'—'}</div><div class="cv-kpi-card-lbl">Puissance installée</div></div>
        <div class="cv-kpi-card"><div class="cv-kpi-card-val">${lastStudyData.nbP?lastStudyData.nbP+' × '+lastStudyData.panWc+' Wc':'—'}</div><div class="cv-kpi-card-lbl">Panneaux</div></div>
        <div class="cv-kpi-card"><div class="cv-kpi-card-val">${batModel>0?fmtD(batModel*batQty/1000)+' kWh':'—'}</div><div class="cv-kpi-card-lbl">${batModel>0?lastStudyData.batLabel||'Stockage':'Sans stockage'}</div></div>
        <div class="cv-kpi-card"><div class="cv-kpi-card-val">${lastStudyData.prodAn?fmt(Math.round(lastStudyData.prodAn))+' kWh':'—'}</div><div class="cv-kpi-card-lbl">Production estimée / an</div></div>
      </div>
    </div>
```

**Aucun montant sur la page de garde** — ni devis, ni économie. Cette contrainte est explicite et ne doit jamais être contournée.

- [ ] **Step 2 : Remonter l'investissement dans le récapitulatif final**

Dans `#last-page`, `recapCards` variante particulier (ligne ~1283), l'ordre doit devenir : investissement d'abord, retours ensuite.

```javascript
        <div class="lp-kpi"><div class="lp-kpi-v">${fmt(devis)} F</div><div class="lp-kpi-l">Investissement TTC</div></div>
        <div class="lp-kpi green"><div class="lp-kpi-v">${fmt(Math.round(ecoAn))} F</div><div class="lp-kpi-l">Économie annuelle estimée</div></div>
        <div class="lp-kpi green"><div class="lp-kpi-v">${fmt(Math.round(eco20||eco15))} F</div><div class="lp-kpi-l">Gains cumulés sur 20 ans</div></div>`;
```

- [ ] **Step 3 : Vérifier**

```bash
cd "/home/tony-linux/Documents/Synology/SynoIA/SOLAR/Calculateur SOLAIRE"
node -e "const fs=require('fs');const html=fs.readFileSync('calculateur-pv-nc.html','utf8');const m=html.match(/<script>([\s\S]*?)<\/script>/g);if(m){const js=m.map(s=>s.replace(/<\/?script>/g,'')).join('\n');fs.writeFileSync('_check.js',js);}" && node --check _check.js && echo "SYNTAXE OK" && rm -f _check.js
node tests/rendu-sortie-a.js _rendu-t7
```

**Contrôle visuel obligatoire** — ouvrir `_rendu-t7/cover-page.png` :
- le logo Solar Concept est présent en haut ;
- la photo de maison est présente ;
- le récapitulatif installation apparaît en quatre cartes ;
- **aucun montant en XPF** nulle part sur cette page.

Puis `_rendu-t7/last-page.png` : l'investissement précède l'économie et les gains.

- [ ] **Step 4 : Commit**

```bash
cd "/home/tony-linux/Documents/Synology/SynoIA/SOLAR/Calculateur SOLAIRE"
git add calculateur-pv-nc.html
git commit -m "feat(garde): récapitulatif installation sans montant, investissement remonté

La garde accueille les quatre caractéristiques techniques via le CSS
.cv-recap déjà présent mais inutilisé. Aucun montant n'y figure. Dans le
récapitulatif final, l'investissement passe avant les retours : ce que ça
coûte, puis ce que ça rapporte."
```

---

## Task 8 : Vérification complète et mise en production

**Files:**
- Aucune modification — vérification puis déploiement.

- [ ] **Step 1 : Batterie de tests complète**

```bash
cd "/home/tony-linux/Documents/Synology/SynoIA/SOLAR/Calculateur SOLAIRE"
node -e "const fs=require('fs');const html=fs.readFileSync('calculateur-pv-nc.html','utf8');const m=html.match(/<script>([\s\S]*?)<\/script>/g);if(m){const js=m.map(s=>s.replace(/<\/?script>/g,'')).join('\n');fs.writeFileSync('_check.js',js);}" && node --check _check.js && echo "SYNTAXE OK" && rm -f _check.js
node tests/test_sortie_a.js
node tests/test_t1_monotonie.js
node tests/test_t2_monotonie.js
node tests/test_export_json.js
node tests/rendu-sortie-a.js _rendu-final
```

Les cinq commandes doivent réussir. **Ne pas continuer si l'une échoue.**

- [ ] **Step 2 : Vérifier qu'aucune régression n'est visible à l'écran**

```bash
cd "/home/tony-linux/Documents/Synology/SynoIA/SOLAR/Calculateur SOLAIRE"
node -e "
const {chromium}=require('playwright');const path=require('path');
(async()=>{const b=await chromium.launch();
const p=await b.newPage({viewport:{width:1280,height:1400},deviceScaleFactor:2});
const err=[];p.on('pageerror',e=>err.push(e.message));
await p.goto('file://'+path.join(process.cwd(),'calculateur-pv-nc.html'),{waitUntil:'networkidle'});
for(const t of [0,1,2,3,4]){
  await p.evaluate(i=>showTab(i),t);
  await p.waitForTimeout(400);
  const btn=await p.\$('#tab'+t+' button.btn-calc');
  if(btn){await btn.click();await p.waitForTimeout(1800);}
  await p.screenshot({path:'_rendu-final/ecran-tab'+t+'.png',fullPage:true});
}
await b.close();
if(err.length){console.log('ERREURS JS :');err.forEach(e=>console.log(' - '+e));process.exit(1);}
console.log('ÉCRAN OK — 5 onglets sans erreur');})()"
```

Attendu : `ÉCRAN OK`. Ouvrir les cinq captures : les onglets 2, 3 et 4 doivent être **strictement identiques** à avant (hors périmètre).

- [ ] **Step 3 : Contrôle visuel final du PDF**

Ouvrir `_rendu-final/sortie-A.pdf` et vérifier :

| Point | Attendu |
|---|---|
| Page 1 | garde avec logo et photo, récap installation, **aucun montant** |
| Page 2 | « L'essentiel », deux colonnes pleines, aucun blanc résiduel |
| Maestro | trois segments, lignes de rappel au centre, textes lisibles |
| Vocabulaire | « Réserve de production », le mot « Réinjection » absent partout |
| Facture | douze pastilles, formulation « l'équivalent de N mois » |
| Dernière page | investissement avant les retours, horizon 20 ans |
| Doublons | aucun chiffre affiché deux fois |
| Couleurs | ni rouge `#FF4B6E`, ni turquoise `#00D4A0` |

- [ ] **Step 4 : Contrôler la taille du fichier**

```bash
cd "/home/tony-linux/Documents/Synology/SynoIA/SOLAR/Calculateur SOLAIRE"
ls -lh calculateur-pv-nc.html
```

Attendu : ~1,03 Mo, inchangé à quelques Ko près. Une envolée signalerait une image accidentellement embarquée.

- [ ] **Step 5 : Mettre à jour la documentation projet**

Dans `CLAUDE.md`, section « État du projet », ajouter sous les corrections appliquées :

```markdown
### Refonte sortie A — Juillet 2026
- Page « L'essentiel » (print-only, `#essentiel-page`) : deux colonnes, argent à gauche, énergie à droite
- Batterie OMEGA Maestro-G en SVG remplace la pile de répartition
- « Réinjection réseau » → « Réserve de production » (revente à 0) ou « Énergie revendue » (tarif > 0)
- Facture : douze pastilles par défaut, écart mensuel en alternative cochable
- ROI en relief, trois jalons
- Quatre blocs redondants supprimés, horizon aligné sur 20 ans
- Spec : `docs/superpowers/specs/2026-07-30-refonte-sortie-client-design.md`
```

- [ ] **Step 6 : Commit et mise en production**

```bash
cd "/home/tony-linux/Documents/Synology/SynoIA/SOLAR/Calculateur SOLAIRE"
git add CLAUDE.md
git commit -m "docs: refonte sortie A dans l'état du projet"
git push origin main
```

- [ ] **Step 7 : Forcer le redéploiement et vérifier la prod**

```bash
gh api --method POST repos/Mackrash/application-GitHub-Claude-Code/pages/builds
sleep 180
curl -sI https://mackrash.github.io/application-GitHub-Claude-Code/calculateur-pv-nc.html | head -5
```

Attendu : `HTTP/2 200`. Puis ouvrir l'URL avec Ctrl+F5 et refaire le contrôle visuel du Step 3 sur la version en ligne.

- [ ] **Step 8 : Nettoyer les rendus de contrôle**

```bash
cd "/home/tony-linux/Documents/Synology/SynoIA/SOLAR/Calculateur SOLAIRE"
rm -rf _rendu-avant _rendu-t5 _rendu-t6 _rendu-t7 _rendu-final
git status --short   # doit être vide
```

---

## Points de vigilance

**Ce qui casse facilement dans ce fichier :**

1. **Les template strings.** Un saut de ligne littéral dans un backtick a déjà cassé la prod (`err.stack.split`). D'où la vérification syntaxe après chaque modification.
2. **Les identifiants partagés.** `renderEnergyFiscalRecap`, `renderRecap`, `kpi` servent aux quatre onglets. Retirer un nœud DOM de l'onglet 1 sans conditionner l'appel provoque un `Cannot set properties of null`.
3. **La logique `psoff-` est inversée.** La classe est ajoutée quand la case est **décochée**. Se tromper de sens inverse tout le panneau.
4. **Les SVG à largeur fixe débordent.** Toujours `width="100%"` + `viewBox`.

**Ce qui n'est pas couvert par ce plan :**

- Les sorties **B** (ajout batterie, onglets 2-3) et **C** (entreprise, onglet 4) gardent leur rendu actuel. Deux styles cohabiteront tant qu'elles ne sont pas déclinées.
- L'**affichage écran** reste inchangé, thème sombre et graphes Plotly compris.
- Le **total du tableau mensuel** doit égaler les chiffres annuels affichés ailleurs. Le calculateur dérive les deux du même calcul, donc l'écart ne devrait pas exister — mais si un arrondi le fait apparaître au contrôle visuel, il faut le corriger avant la mise en production : une contradiction sur un document remis au client est inacceptable.

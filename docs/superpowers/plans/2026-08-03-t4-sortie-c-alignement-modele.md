# Refonte T4 / sortie C — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aligner l'onglet 4 (sortie C entreprise) du calculateur PV NC sur le modèle Excel
« Simulation financière Pro1.xlsx », ramener sa sortie papier à deux pages, et lui ajouter
une bascule HT/TTC, un régime fiscal et l'import d'un logo client et d'une photo de site.

**Architecture:** Le calculateur est un **fichier HTML monopage unique**
(`calculateur-pv-nc.html`, 1,1 Mo) contenant HTML, CSS et JS embarqués. Aucun build, aucune
dépendance npm à l'exécution. Toutes les modifications se font dans ce seul fichier ; la
vérification passe par le rendu réel via Playwright, jamais par des tests unitaires (il n'en
existe pas).

**Tech Stack:** HTML/CSS/JS vanilla · Plotly 2.27 (CDN) · Playwright (dev uniquement, pour
le rendu PDF de contrôle) · Node 22.

## Global Constraints

- **Langue française partout**, accents et diacritiques obligatoires. Devise **XPF**,
  séparateur de milliers = espace.
- **Charte Solar Concept** : orange `#F07020`, anthracite `#333333`, fond blanc. Pas de
  couleurs froides.
- **Ne jamais modifier les calculs des onglets 1, 2 et 3.** `prodM()` reste inchangée.
  Seule exception autorisée par Tony : la surface passe de 2,1 à 2,2 m²/panneau sur les
  quatre onglets.
- **La sortie C fait exactement deux pages** : garde + une page de contenu.
- **Le ROI et le rendement doivent être identiques en HT et en TTC.** Un écart est un bug.
- Après chaque tâche, la **vérification syntaxe JS** doit répondre `SYNTAXE OK` :
  ```bash
  node -e "const fs=require('fs');const html=fs.readFileSync('calculateur-pv-nc.html','utf8');const m=html.match(/<script>([\s\S]*?)<\/script>/g);if(m){const js=m.map(s=>s.replace(/<\/?script>/g,'')).join('\n');fs.writeFileSync('_check.js',js);}" && node --check _check.js && echo "SYNTAXE OK"
  ```
- **La configuration des onduleurs existe déjà** (`#t4_ond_type`, `t4_getOndList()`,
  lignes 745-767 et 2852-2886). **Ne pas la réécrire.**

## Fichiers touchés

| Fichier | Rôle |
|---|---|
| `calculateur-pv-nc.html` | tout le travail — seul fichier de production |
| `_maquettes/T4-sortie-C-1page.html` | maquette validée de la page de contenu — **référence visuelle, ne pas modifier** |
| `_maquettes/T4-garde-entreprise.html` | maquette validée de la garde — **référence visuelle, ne pas modifier** |
| `/tmp/.../shot.js`, `mesure.js` | scripts Playwright de contrôle (hors dépôt) |

## Jeu de test de référence — « dossier Excel »

Saisi dans T4, il doit reproduire **exactement** les valeurs du modèle Excel. C'est le test
qui valide l'alignement des calculs. Il est réutilisé par plusieurs tâches.

| Champ | Valeur |
|---|---|
| `#t4_kwc` | `18.9` |
| `#t4_wc` | `450` |
| `#t4_kva` | `19.8` |
| `#t4_primefix` | `964` |
| `#t4_redev` | `681` |
| `#t4_tc` | `9` |
| `#t4_tarif` | `29.62` |
| `#t4_auto` | `65` |
| `#t4_rev` | `0` |
| `#t4_bat` | `0` |
| `#t4_devis` | `2900000` |
| `#t4_is` | `30` |
| `#t4_amortd` | `10` |
| Consommation `m4_1` à `m4_12` | `2300` chacun (27 600 kWh/an) |

**Valeurs attendues :**

| Grandeur | Attendu |
|---|---|
| Production annuelle | 28 085 kWh |
| Surface | 92 m² |
| kWh sur 15 ans | 421 281 kWh |
| Prix de revient | 6,88 F/kWh |
| Économie / an | 579 207 F |
| Économies sur 15 ans | 8 688 109 F |
| Avantage amortissement / an | 87 000 F |
| Rendement | 22,97 % |
| Économies d'impôt | 870 000 F |
| Coût net | 2 030 000 F |
| **ROI** | **3,5 ans** |

---

### Task 1: Corriger la page de garde qui n'affiche pas les données de T4

**Files:**
- Modify: `calculateur-pv-nc.html:3116` (affectation de `lastStudyData` dans `calcT4`)

**Interfaces:**
- Consomme : les variables locales `nbP`, `panWc`, `prodAn` de `calcT4`, déjà définies aux
  lignes 2931 et alentours.
- Produit : `lastStudyData.nbP`, `lastStudyData.panWc`, `lastStudyData.prodAn`, lus par
  `preparePrint()` aux lignes 1589 et 1591.

**Contexte du bug.** La page de garde lit `lastStudyData.nbP`, `.panWc` et `.prodAn`.
`calcT4` range bien ces valeurs, mais dans `lastCalcDetails` (ligne 3118), **pas** dans
`lastStudyData` (ligne 3116). Les cartouches « Panneaux » et « Production estimée / an »
affichent donc « — ». `calcT1` ne souffre pas du problème : il stocke `prodAn` ligne 2488.

- [ ] **Step 1: Constater le défaut**

Ouvrir le calculateur, aller sur l'onglet 4, cliquer CALCULER, puis dans la console :

```js
console.log(lastStudyData.nbP, lastStudyData.panWc, lastStudyData.prodAn);
```

Attendu : `undefined undefined undefined` — c'est le bug.

- [ ] **Step 2: Ajouter les trois clés**

Ligne 3116, dans l'objet `lastStudyData={tab:4,...}`, insérer `nbP,panWc,prodAn,` juste
après `kwc,devis,` :

```js
lastStudyData={tab:4,kwc,devis,nbP,panWc,prodAn,ecoAn,ecoAn1:ecoAn,fSansAn:fSans,fAvecAn:fAvec,batModel,batQty,client:document.getElementById('t4_nom').value||'Entreprise',commercial:document.getElementById('t4_commercial').value||'',adresse:document.getElementById('t4_commune').value,rows:_proRows,pb:pbPro,pbMin:pbPro,pbMax:pbMax_t4,eco10:eco10_t4,eco15:eco15_t4,coutNetImpot,avantageTotal,tIS,dAmort};
```

- [ ] **Step 3: Vérifier**

Recharger, onglet 4, CALCULER, puis en console :

```js
console.log(lastStudyData.nbP, lastStudyData.panWc, lastStudyData.prodAn);
```

Attendu : trois nombres (ex. `42 450 26076`), plus aucun `undefined`.

- [ ] **Step 4: Vérifier la syntaxe JS**

Lancer la commande de contrôle des Global Constraints. Attendu : `SYNTAXE OK`.

- [ ] **Step 5: Commit**

```bash
git add calculateur-pv-nc.html
git commit -m "fix(t4): la page de garde reçoit les données de l'onglet 4"
```

---

### Task 2: Retirer la compensation carbone en arbres

**Files:**
- Modify: `calculateur-pv-nc.html:2965` (constante `arbres`)
- Modify: `calculateur-pv-nc.html:3032` (ligne du rapport)
- Modify: `calculateur-pv-nc.html:3035` (note de bas de bloc)

**Interfaces:**
- Consomme : rien.
- Produit : rien. Suppression pure.

**À conserver** : « Émissions CO₂ évitées — X tonnes » et la note « 1 kWh produit au fioul
= 600 g de CO₂ », toutes deux présentes dans le modèle Excel.

- [ ] **Step 1: Supprimer la constante**

Ligne 2965, supprimer entièrement :

```js
  const arbres=Math.round(prodAn*0.03); // 1 arbre absorbe ~20kg CO2/an
```

- [ ] **Step 2: Supprimer la ligne du rapport**

Ligne 3032, supprimer entièrement :

```js
        ${R({k:'Compensation carbone par an',v:`${fmt(arbres)} arbres`,g:true})}
```

- [ ] **Step 3: Raccourcir la note**

Ligne 3035, remplacer la fin de la note. Avant :

```
1 kWh produit au fioul = 600 g de CO₂ — 1 arbre absorbe ~20 kg CO₂/an
```

Après :

```
1 kWh produit au fioul = 600 g de CO₂
```

- [ ] **Step 4: Vérifier qu'il ne reste aucune trace**

```bash
grep -in "arbre" calculateur-pv-nc.html
```

Attendu : **aucune ligne retournée**.

- [ ] **Step 5: Vérifier la syntaxe JS**

Commande de contrôle. Attendu : `SYNTAXE OK`. (Ce contrôle attrape un `arbres` resté
référencé quelque part.)

- [ ] **Step 6: Commit**

```bash
git add calculateur-pv-nc.html
git commit -m "feat(t4): retire la compensation carbone en arbres du rapport"
```

---

### Task 3: Surface des panneaux à 2,2 m²

**Files:**
- Modify: `calculateur-pv-nc.html:2430` (calcT1)
- Modify: `calculateur-pv-nc.html:2562` (calcT2)
- Modify: `calculateur-pv-nc.html:2690` (calcT3)
- Modify: `calculateur-pv-nc.html:2932` (calcT4)

**Interfaces:**
- Consomme : `nbP` dans chaque fonction.
- Produit : `surf`, valeur d'affichage uniquement — **aucun calcul financier n'en dépend**.

Le modèle Excel calcule `ROUND(nb × 2,2)`. Les quatre onglets utilisent `nbP*2.1`. Décision
Tony : 2,2 partout.

- [ ] **Step 1: Remplacer les quatre occurrences**

```bash
sed -i 's/const surf=nbP\*2\.1;/const surf=nbP*2.2;/g' calculateur-pv-nc.html
```

- [ ] **Step 2: Vérifier**

```bash
grep -n "const surf=nbP\*" calculateur-pv-nc.html
```

Attendu : **quatre lignes**, toutes en `*2.2`, aucune en `*2.1`.

- [ ] **Step 3: Contrôler la valeur**

Onglet 4, saisir `#t4_kwc = 18.9` et `#t4_wc = 450`, CALCULER. La surface affichée doit
être **92 m²** (42 panneaux × 2,2 = 92,4, arrondi à 92).

- [ ] **Step 4: Vérifier la syntaxe JS**

Commande de contrôle. Attendu : `SYNTAXE OK`.

- [ ] **Step 5: Commit**

```bash
git add calculateur-pv-nc.html
git commit -m "fix: surface panneau à 2,2 m² conformément au modèle Excel"
```

---

### Task 4: Production de T4 alignée sur les coefficients Excel

**Files:**
- Modify: `calculateur-pv-nc.html:888` (zone des constantes, après `IDX`)
- Modify: `calculateur-pv-nc.html:2890-2930` (début de `calcT4`, où `prod` est calculé)

**Interfaces:**
- Produit : la constante globale `IDX_PRO`, et un tableau local `prod` de 12 valeurs dans
  `calcT4`. `prodAn` reste la somme de `prod`, consommée par tout le reste de `calcT4`.

**Contexte.** `prodM(kwc,en,pe)` calcule `kwc × en × (1−pe/100) × 365` puis répartit selon
`IDX`. Avec les réglages par défaut (4,2 kWh/kWc/j, 10 % de pertes) cela donne
1 379,7 kWh/kWc/an, contre **1 486** dans l'Excel — soit 7,2 % d'écart. Les courbes
mensuelles diffèrent aussi.

**Décision Tony : T4 uniquement.** `prodM()` n'est pas modifiée ; T1, T2 et T3 gardent leur
production actuelle.

- [ ] **Step 1: Ajouter la constante des coefficients Excel**

Juste après la ligne 888 (`const IDX=[...]`), insérer :

```js
// Coefficients mensuels kWh/kWc du modèle Excel « Simulation financière Pro1.xlsx »
// (feuille Simul Conso, colonne B : =F4*147, =F4*138, …). Somme = 1486 kWh/kWc/an.
// RÉSERVÉ À L'ONGLET 4 : décision Tony 03/08/2026, l'Excel fait foi pour la sortie
// entreprise. Les onglets 1 à 3 continuent d'utiliser prodM(). Ce n'est PAS un doublon
// de IDX — ne pas fusionner les deux.
const IDX_PRO=[147,138,132,102,99,90,93,108,133,144,148,152];
```

- [ ] **Step 2: Utiliser ces coefficients dans calcT4**

Dans `calcT4`, repérer l'appel à `prodM(...)` qui alimente `prod` (aux alentours de la
ligne 2905). Le remplacer par :

```js
  // Production selon le modèle Excel (voir IDX_PRO) — spécifique à l'onglet 4
  const prod=IDX_PRO.map(c=>kwc*c);
```

Laisser `prodAn` inchangé s'il vaut déjà `prod.reduce((a,b)=>a+b,0)` ; sinon l'écrire ainsi.

- [ ] **Step 3: Vérifier la production**

Onglet 4, `#t4_kwc = 18.9`, CALCULER. En console :

```js
console.log(Math.round(lastCalcDetails.prodAn));
```

Attendu : **28 085**. (18,9 × 1 486 = 28 085,4.)

- [ ] **Step 4: Vérifier la non-régression des autres onglets**

Onglet 1, `#t1_kwc = 18.9`, CALCULER, puis en console :

```js
console.log(Math.round(lastCalcDetails.prodAn));
```

Attendu : **26 076** — inchangé, preuve que `prodM()` n'a pas bougé.

- [ ] **Step 5: Vérifier la syntaxe JS**

Commande de contrôle. Attendu : `SYNTAXE OK`.

- [ ] **Step 6: Commit**

```bash
git add calculateur-pv-nc.html
git commit -m "feat(t4): production alignée sur les coefficients du modèle Excel"
```

---

### Task 5: ROI de la sortie C selon la formule Excel

**Files:**
- Modify: `calculateur-pv-nc.html` — bloc du rapport `r4_rapport`, ligne affichant le ROI
  (rechercher `pbPro` dans la zone 3006-3110)

**Interfaces:**
- Consomme : `rsi` (déjà calculé ligne 2980 : `coutNetImpot/ecoAn`) et `pbPro`.
- Produit : rien de nouveau.

**Contexte.** L'Excel calcule `ROI = coût net ÷ économie annuelle`. `calcT4` calcule bien
cette valeur dans `rsi` mais **affiche `pbPro`**, le payback dynamique (hausse tarifaire,
dégradation, remplacement batterie). Écart constaté : 6,4 ans contre 8 ans.

**Décision Tony : la sortie C imprime la formule Excel seule.** `pbPro` reste calculé et
utilisé ailleurs (`lastStudyData.pb`), il ne doit simplement plus alimenter le bandeau ROI
du rapport.

- [ ] **Step 1: Localiser l'affichage du ROI**

```bash
grep -n "pbPro" calculateur-pv-nc.html | sed -n '1,20p'
```

Repérer l'occurrence située **dans le template de `r4_rapport`** (entre les lignes 3006 et
3110), celle qui produit le bandeau « Retour sur investissement ».

- [ ] **Step 2: Remplacer par la formule Excel**

Dans ce bandeau uniquement, remplacer la valeur `pbPro` par `rsi`, arrondie à une décimale :

```js
${fmtD(rsi,1)} ans
```

Et le libellé devient : `Retour sur investissement après amortissement comptable`.

Ne toucher à **aucune** autre occurrence de `pbPro`.

- [ ] **Step 3: Vérifier avec le jeu de référence**

Saisir le **jeu de test de référence** (tableau en tête de plan). Le bandeau ROI doit
afficher **3,5 ans**.

Contrôle croisé en console :

```js
console.log(lastCalcDetails.coutNetImpot / lastCalcDetails.ecoAn);
```

Attendu : ≈ `3.50`.

- [ ] **Step 4: Vérifier la syntaxe JS**

Commande de contrôle. Attendu : `SYNTAXE OK`.

- [ ] **Step 5: Commit**

```bash
git add calculateur-pv-nc.html
git commit -m "feat(t4): ROI de la sortie C selon la formule du modèle Excel"
```

---

### Task 6: Bascules HT/TTC et régime fiscal

**Files:**
- Modify: `calculateur-pv-nc.html:780` (zone de saisie de T4, avant le bouton CALCULER)
- Modify: `calculateur-pv-nc.html:2890-3130` (`calcT4`)

**Interfaces:**
- Produit :
  - `#t4_mode` — `select`, valeurs `ht` (défaut) et `ttc`
  - `#t4_regime` — `select`, valeurs `is` (défaut) et `sansis`
  - dans `calcT4` : `const kTTC` (1 ou 1+tgc/100) et `const sansIS` (booléen)

**Règle centrale.** En mode TTC, **tous** les montants sont multipliés par `kTTC` :
investissement, tarif du kWh, prix de revient, économie annuelle, économies sur 15 ans,
avantage d'amortissement, économies d'impôt, coût net. Numérateur et dénominateur du ROI
subissant le même facteur, **le ROI et le rendement ne bougent pas**.

- [ ] **Step 1: Ajouter les deux sélecteurs**

Dans la grille `fgrid3` de T4 (ligne 784 et suivantes), ajouter :

```html
    <div class="fg"><label>Montants du document</label>
      <select id="t4_mode">
        <option value="ht" selected>HT — hors taxes</option>
        <option value="ttc">TTC — TGC incluse</option>
      </select>
    </div>
    <div class="fg"><label>Régime fiscal</label>
      <select id="t4_regime">
        <option value="is" selected>Société soumise à l'IS</option>
        <option value="sansis">Sans IS — association, SCI non assujettie</option>
      </select>
    </div>
```

- [ ] **Step 2: Lire les deux réglages dans calcT4**

Au début de `calcT4`, après la lecture des autres champs :

```js
  const modeTTC=document.getElementById('t4_mode').value==='ttc';
  const sansIS=document.getElementById('t4_regime').value==='sansis';
  const kTTC=modeTTC?(1+(parseFloat(document.getElementById('s_tgc').value)||0)/100):1;
```

- [ ] **Step 3: Neutraliser l'amortissement en régime sans IS**

Remplacer les lignes 2972-2975 par :

```js
  const amortAn=devis/dAmort;
  const avantageAn=sansIS?0:Math.round(amortAn*tIS/100);
  const avantageTotal=sansIS?0:avantageAn*dAmort;
  const coutNetImpot=devis-avantageTotal;
```

- [ ] **Step 4: Appliquer kTTC à l'affichage du rapport**

Dans le template `r4_rapport`, multiplier par `kTTC` **uniquement à l'affichage** les
grandeurs suivantes : `devis`, `tarif`, `prixRevkWh`, `ecoAn`, `eco15`, `avantageAn`,
`avantageTotal`, `coutNetImpot`.

Exemple pour l'investissement :

```js
${R({k:`Coût total de l'investissement ${modeTTC?'TTC':'HT'}`,v:`${fmt(Math.round(devis*kTTC))} F.CFP`,or:true})}
```

**Ne pas multiplier** `rsi` ni `rendement` : ce sont des ratios, ils sont invariants.

- [ ] **Step 5: Adapter les libellés en régime sans IS**

Dans le rapport :

- « Avantage annuel lié à l'amortissement comptable (10 ans) » → si `sansIS`,
  « Amortissement comptable : sans objet » et valeur `—`
- « Coût de l'installation net d'impôt » → si `sansIS`, « Coût réel supporté »
- Bandeau ROI → si `sansIS`, « Retour sur investissement » (sans « après amortissement »)

Ajouter en tête du bloc « Données économiques » la mention du mode :

```js
`Montants ${modeTTC?'TTC':'HT'} — ${sansIS?"structure non soumise à l'IS":"société soumise à l'IS"}`
```

- [ ] **Step 6: Vérifier l'invariance du ROI**

Avec le jeu de référence, mode **HT** : noter ROI et rendement (`3,5 ans`, `22,97 %`).
Basculer sur **TTC**, recalculer.

Attendu :
- ROI **3,5 ans** et rendement **22,97 %** — **inchangés**
- investissement `2 987 000 F` (2 900 000 × 1,03)
- économie `596 583 F` (579 207 × 1,03)

Un ROI qui bouge = bug, corriger avant de continuer.

- [ ] **Step 7: Vérifier le régime sans IS**

Mode HT, régime **sans IS**, jeu de référence. Attendu :
- avantage d'amortissement : `—`
- économies d'impôt : `—`
- coût réel supporté : **2 900 000 F** (= investissement)
- ROI : **5,0 ans** (2 900 000 ÷ 579 207)
- rendement : **19,97 %** (579 207 ÷ 2 900 000)

- [ ] **Step 8: Vérifier la syntaxe JS**

Commande de contrôle. Attendu : `SYNTAXE OK`.

- [ ] **Step 9: Commit**

```bash
git add calculateur-pv-nc.html
git commit -m "feat(t4): bascules HT/TTC et régime fiscal sur la sortie entreprise"
```

---

### Task 7: Import du logo client et de la photo du site

**Files:**
- Modify: `calculateur-pv-nc.html:780` (zone de saisie de T4)
- Modify: `calculateur-pv-nc.html:1092` (`buildStudyJSON`)
- Modify: `calculateur-pv-nc.html` (fonction de rechargement d'étude, à repérer par
  `t4_nom` dans la zone 1100-1160)

**Interfaces:**
- Produit :
  - `t4Images` — objet global `{logo:null, photo:null}`, chaînes base64 ou `null`
  - `t4LoadImage(input, cible, maxPx)` — lit, redimensionne, stocke, rafraîchit l'aperçu
- Consommé par : la Task 8 (page de contenu) et la Task 9 (page de garde).

**Pourquoi redimensionner.** Une photo de téléphone brute pèse plusieurs mégaoctets. Stockée
telle quelle, elle sature le quota `localStorage` (~5 Mo) et alourdit le JSON d'étude. Le
redimensionnement par canvas n'est pas optionnel.

- [ ] **Step 1: Ajouter les deux champs de fichier**

Dans la zone de saisie de T4 :

```html
    <div class="fg"><label>Logo du client (optionnel)</label>
      <input type="file" id="t4_logo_file" accept="image/*" onchange="t4LoadImage(this,'logo',400)">
      <div id="t4_logo_prev" style="margin-top:6px"></div>
    </div>
    <div class="fg"><label>Photo du site (optionnel)</label>
      <input type="file" id="t4_photo_file" accept="image/*" onchange="t4LoadImage(this,'photo',1400)">
      <div id="t4_photo_prev" style="margin-top:6px"></div>
    </div>
```

- [ ] **Step 2: Écrire le chargeur d'image**

Juste avant `function calcT4(){` (ligne 2890) :

```js
// ===== IMAGES DU DOSSIER (logo client, photo du site) =====
// Redimensionnées par canvas AVANT stockage : une photo brute de téléphone
// saturerait le quota localStorage et alourdirait le JSON d'étude.
let t4Images={logo:null,photo:null};

function t4LoadImage(input,cible,maxPx){
  const f=input.files&&input.files[0];
  if(!f)return;
  const rd=new FileReader();
  rd.onload=e=>{
    const img=new Image();
    img.onload=()=>{
      const ech=Math.min(1,maxPx/img.width);
      const c=document.createElement('canvas');
      c.width=Math.round(img.width*ech);
      c.height=Math.round(img.height*ech);
      c.getContext('2d').drawImage(img,0,0,c.width,c.height);
      t4Images[cible]=c.toDataURL('image/jpeg',0.85);
      t4RenderPreview(cible);
    };
    img.src=e.target.result;
  };
  rd.readAsDataURL(f);
}

function t4RenderPreview(cible){
  const d=document.getElementById('t4_'+cible+'_prev');
  if(!d)return;
  d.innerHTML=t4Images[cible]
    ? `<img src="${t4Images[cible]}" style="max-height:46px;max-width:150px;border-radius:4px">
       <button type="button" onclick="t4ClearImage('${cible}')" style="margin-left:8px;cursor:pointer">Retirer</button>`
    : '';
}

function t4ClearImage(cible){
  t4Images[cible]=null;
  const inp=document.getElementById('t4_'+cible+'_file');
  if(inp)inp.value='';
  t4RenderPreview(cible);
}
```

- [ ] **Step 3: Faire voyager les images avec l'étude**

Dans `buildStudyJSON()` (ligne 1092), ajouter au niveau racine de l'objet retourné :

```js
    images:{logo:t4Images.logo,photo:t4Images.photo},
```

Dans la fonction qui recharge une étude, après la restauration des champs texte :

```js
  if(d.images){
    t4Images.logo=d.images.logo||null;
    t4Images.photo=d.images.photo||null;
    t4RenderPreview('logo'); t4RenderPreview('photo');
  }
```

- [ ] **Step 4: Vérifier le redimensionnement**

Charger une photo de plus de 2 Mo comme photo du site, puis en console :

```js
console.log(Math.round(t4Images.photo.length/1024)+' Ko');
```

Attendu : **moins de 400 Ko**. L'aperçu doit s'afficher avec un bouton « Retirer ».

- [ ] **Step 5: Vérifier l'aller-retour JSON**

Exporter l'étude, recharger la page, réimporter le fichier. Les deux aperçus doivent
réapparaître.

- [ ] **Step 6: Vérifier la syntaxe JS**

Commande de contrôle. Attendu : `SYNTAXE OK`.

- [ ] **Step 7: Commit**

```bash
git add calculateur-pv-nc.html
git commit -m "feat(t4): import d'un logo client et d'une photo de site"
```

---

### Task 8: Page de contenu unique, conforme à la maquette

**Files:**
- Modify: `calculateur-pv-nc.html:3006-3110` (template de `r4_rapport`)
- Modify: `calculateur-pv-nc.html:438-460` (CSS d'impression du rapport entreprise)
- Modify: `calculateur-pv-nc.html:801-815` (structure des pages imprimées de T4)
- Reference: `_maquettes/T4-sortie-C-1page.html` — **la maquette fait foi pour le visuel**

**Interfaces:**
- Consomme : toutes les grandeurs de `calcT4`, `t4Images.logo` (Task 7), `ondList`.
- Produit : une page de contenu unique.

**Contrainte.** La maquette validée consomme **264 mm sur les 277 mm utiles**, soit 33 mm de
réserve. Reprendre ses dimensions plutôt que d'improviser.

- [ ] **Step 1: Retirer la page 3 du flux d'impression**

Lignes 801-815, la structure de T4 comporte `<div class="ps-page2">` contenant
`ps-table[data-psec=amort]` et `ps-charts`. Les sortir de l'impression en ajoutant sur ce
conteneur :

```html
<div class="ps-page2" style="display:none" data-screen-only="1">
```

puis, dans le CSS écran uniquement (hors `@media print`) :

```css
.ps-page2[data-screen-only]{display:block!important}
```

Ainsi le tableau d'amortissement et les graphiques **restent visibles à l'écran** mais ne
s'impriment plus.

- [ ] **Step 2: Reprendre la structure de la maquette**

Remplacer le template de `r4_rapport` par la structure de
`_maquettes/T4-sortie-C-1page.html`, dans cet ordre : en-tête (logo Solar Concept + logo
client si présent), bloc projet, bandeau « Caractéristiques du générateur », bandeau
« Rendement annuel », tableau mensuel en deux rangées de six mois, bandeau « Données
économiques » portant la mention du mode, bandeau ROI, NB, pied.

Reprendre les valeurs CSS de la maquette : lignes `padding:.62mm 4mm`, bandeaux
`padding:1.2mm 4mm`, tableau `padding:.9mm .5mm`, blocs `margin-bottom:1.8mm`, libellés
13 px, valeurs 14 px, ROI 31 px.

- [ ] **Step 3: Insérer le logo client s'il existe**

Dans le bloc projet :

```js
${t4Images.logo?`<img src="${t4Images.logo}" style="height:12mm;max-width:32mm;object-fit:contain;margin-right:4mm">`:''}
```

Sans logo, **aucun cadre vide** ne doit apparaître.

- [ ] **Step 4: Vérifier le nombre de pages**

```bash
NODE_PATH="$PWD/node_modules" node /tmp/.../shot.js /tmp/sortieC.pdf "$PWD/calculateur-pv-nc.html"
pdfinfo /tmp/sortieC.pdf | grep -i pages
```

Attendu : **2 pages** (garde + contenu).

- [ ] **Step 5: Vérifier le cas dense**

Régler `#t4_ond_type` sur `hybride_string` (deux lignes d'onduleurs) et charger un logo
client, puis réimprimer. Attendu : **toujours 2 pages**.

- [ ] **Step 6: Vérifier la syntaxe JS**

Commande de contrôle. Attendu : `SYNTAXE OK`.

- [ ] **Step 7: Commit**

```bash
git add calculateur-pv-nc.html
git commit -m "feat(t4): sortie C ramenée à une page de contenu conforme au modèle"
```

---

### Task 9: Page de garde entreprise

**Files:**
- Modify: `calculateur-pv-nc.html:1470-1600` (`preparePrint`, génération de `cover-page`)
- Reference: `_maquettes/T4-garde-entreprise.html` — **la maquette fait foi**

**Interfaces:**
- Consomme : `lastStudyData` (dont `nbP`, `panWc`, `prodAn` corrigés en Task 1), `rsi`,
  `t4Images.logo`, `t4Images.photo`.
- Produit : la garde de la sortie C.

**Contexte.** `preparePrint` dispose déjà d'un booléen `isPro=tab===4` (ligne 1471). Il
sert d'aiguillage : la garde entreprise est un template distinct, pas une variante de la
garde particulier — laquelle ne doit **pas** être modifiée.

- [ ] **Step 1: Aiguiller vers un template dédié**

Dans `preparePrint`, là où `cover.innerHTML` est affecté, encadrer par :

```js
  cover.innerHTML = isPro ? coverPro() : `…template particulier inchangé…`;
```

- [ ] **Step 2: Écrire coverPro()**

Reprendre `_maquettes/T4-garde-entreprise.html` : logos en vis-à-vis, filet orange 2 px,
titre « Étude photovoltaïque », bloc client à barre orange verticale, trois chiffres
séparés par des filets (puissance installée, production annuelle, retour sur
investissement), photo du site en bandeau de **66 mm**, pied à deux colonnes.

Les emplacements image sont conditionnels :

```js
${t4Images.logo?`<img src="${t4Images.logo}" style="max-height:16mm;max-width:45mm;object-fit:contain">`:''}
${t4Images.photo?`<div style="margin-top:11mm;height:66mm"><img src="${t4Images.photo}" style="width:100%;height:100%;object-fit:cover;border-radius:1.5mm"></div>`:''}
```

- [ ] **Step 3: Vérifier les quatre combinaisons**

Imprimer la sortie C avec : sans image · logo seul · photo seule · les deux.

Attendu à chaque fois : **2 pages**, aucun cadre vide, aucun débordement.

- [ ] **Step 4: Vérifier la non-régression de la garde particulier**

Onglet 1, CALCULER, imprimer. La garde doit être **strictement identique** à
`_rendu-final/SORTIE-A-particulier.pdf`.

- [ ] **Step 5: Vérifier la syntaxe JS**

Commande de contrôle. Attendu : `SYNTAXE OK`.

- [ ] **Step 6: Commit**

```bash
git add calculateur-pv-nc.html
git commit -m "feat(t4): page de garde entreprise au design corporate"
```

---

### Task 10: Recette complète et mise à jour de la documentation

**Files:**
- Modify: `CLAUDE.md` (section « État du projet »)
- Create: `docs/sessions/2026-08-03-refonte-t4-sortie-c.md`
- Regenerate: `_rendu-final/SORTIE-C-entreprise.pdf`

- [ ] **Step 1: Passer le test de référence Excel**

Saisir le jeu de test de référence complet. Vérifier **les onze valeurs** du tableau en tête
de plan. Toute divergence est bloquante.

- [ ] **Step 2: Vérifier la non-régression T1/T2/T3**

Régénérer les sorties A et B et les comparer à `_rendu-final/`. Seul écart admis :
la surface (2,1 → 2,2 m²/panneau).

- [ ] **Step 3: Régénérer la sortie C de référence**

```bash
node tests/rendu-sorties.js _rendu-final
```

- [ ] **Step 4: Mettre à jour le CLAUDE.md du projet**

Ajouter sous « État du projet » une section « Sortie C — août 2026 » consignant : les deux
pages, les coefficients `IDX_PRO` réservés à T4, le ROI en formule Excel, les bascules
HT/TTC et régime fiscal, l'import logo/photo. Mentionner que **la configuration des
onduleurs préexistait**.

- [ ] **Step 5: Écrire le compte rendu de session**

`docs/sessions/2026-08-03-refonte-t4-sortie-c.md` : décisions actées, écarts au modèle
Excel et leur résolution, ce qui a été écarté (graphiques, tableau d'amortissement à
l'impression, recherche web de logo).

- [ ] **Step 6: Commit et push**

```bash
git add -A
git commit -m "docs: refonte T4 sortie C — spec, plan et compte rendu"
git push origin main
```

---

## Points ouverts, hors périmètre

- **Horizon 20 ans / 25 ans** : le libellé « Retour sur investissement — 20 ans » et le
  tableau d'amortissement tronqué à 20 lignes en CSS print restent codés en dur, alors que
  les gains cumulés suivent `s.dpv` (25 ans). Concerne toutes les sorties — décision
  séparée.
- **Deux hybrides de modèles différents** : `t4_getOndList()` applique une quantité à un
  modèle unique. Aucun besoin exprimé à ce jour.
- **Arrondi du CO₂** : entier dans l'Excel, décimale dans T4 (17 contre 16,6 tonnes).
  Écart d'affichage laissé tel quel.

# Évolutions Calculateur PV NC — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Corriger la courbe de production saisonnière NC, ajouter un produit « panneaux dédiés recharge batterie » dans T2, un header client global (T1/T2/T3) et le commercial Anthony Debray.

**Architecture:** Fichier unique `calculateur-pv-nc.html` (HTML + JS + CSS inline, Plotly 2.27 CDN). Aucune dépendance de build. La logique de production passe par la fonction partagée `prodM(kwc, en, pe)` (appelée seulement par T1 et T4). T2 et T3 utilisent des données mensuelles réelles saisies. Le header client est mutualisé via 3 helpers JS lus par les blocs `lastStudyData`/`lastCalcDetails` de chaque onglet.

**Tech Stack:** HTML5, JavaScript vanilla, Plotly 2.27, Node.js (uniquement pour la vérif syntaxe et un test numérique de `prodM`).

## Global Constraints

- Langue **FR**, accents obligatoires. Devise **XPF**, séparateur de milliers = espace.
- Fichier cible unique : `calculateur-pv-nc.html`. Ne pas changer la dépendance Plotly 2.27.
- Charte Solar Concept : orange `#F07020`, anthracite `#333333`, fond blanc. Pas de couleurs froides.
- **Vérif syntaxe JS obligatoire après chaque modif** (commande ci-dessous).
- Email commercial validé : `anthony.debray@solarconcept.nc`. Téléphone : `76.30.52`.
- Indices de production (Jan→Déc) : `1.38 1.38 1.32 0.90 0.80 0.65 0.80 0.95 1.25 1.25 1.40 1.50`.
- Commits fréquents ; push différé (le push global se fera en fin de chantier sur demande).

**Commande de vérif syntaxe (réutilisée à chaque tâche, notée « VÉRIF SYNTAXE ») :**
```bash
node -e "const fs=require('fs');const html=fs.readFileSync('calculateur-pv-nc.html','utf8');const m=html.match(/<script>([\s\S]*?)<\/script>/g);if(m){const js=m.map(s=>s.replace(/<\/?script>/g,'')).join('\n');fs.writeFileSync('_check.js',js);}" && node --check _check.js && echo "SYNTAXE OK"
```

---

## File Structure

- **Modify uniquement** : `calculateur-pv-nc.html`
  - Constantes (`SF`→`IDX`) et `prodM` : ~ligne 763 et ~805.
  - Header HTML global : après le bloc `.header` / avant `.tabs` (~ligne 449).
  - Bloc client de T1 à supprimer : ~lignes 459-471.
  - Inputs T2 (lot dédié) : `fgrid3` ~lignes 532-541.
  - Boucle batterie T2 : ~lignes 1729-1742, recap T2 ~1754-1764.
  - Consommateurs client : `lastStudyData`/`lastCalcDetails` de T1 (1660/1680), T2 (1781/1790), T3 (~1914/1924) ; `saveStudy` (~2355).
  - Listes commerciaux : header global (nouveau) + `t4_commercial` (~636).
- **Test temporaire** : `scratchpad/test-prodM.js` (Node, supprimé en fin de Task 1).

---

## Task 1 : Nouvelle courbe de production saisonnière

**Files:**
- Modify: `calculateur-pv-nc.html` (constante `SF` ~763, fonction `prodM` ~805)
- Test: `/tmp/claude-1000/.../scratchpad/test-prodM.js` (chemin scratchpad complet de la session)

**Interfaces:**
- Produces: `prodM(kwc, en, pe)` retourne un tableau de 12 productions mensuelles (kWh) réparties selon `IDX`, total annuel = `kwc*en*(1-pe/100)*365`. Consommé par T1 (1586), T4 (2052) et le lot dédié de T2 (Task 4).

- [ ] **Step 1 : Écrire le test numérique (échoue d'abord)**

Créer `scratchpad/test-prodM.js` (utiliser le chemin scratchpad absolu de la session) :
```js
// Réplique de la future implémentation pour valider les valeurs attendues.
const IDX=[1.38,1.38,1.32,0.90,0.80,0.65,0.80,0.95,1.25,1.25,1.40,1.50];
const IDXSUM=IDX.reduce((a,b)=>a+b,0);
function prodM(kwc,en,pe){const f=1-pe/100;const annual=kwc*en*f*365;return IDX.map(ix=>annual*ix/IDXSUM);}

const p=prodM(1,4.2,10);
const annual=p.reduce((a,b)=>a+b,0);
let ok=true;
// 1) Total annuel attendu ≈ 1379 kWh/kWc (1*4.2*0.9*365)
if(Math.abs(annual-1379)>2){console.error('FAIL annuel',annual);ok=false;}
// 2) Juin (index 5) est le plus bas
const minMonth=p.indexOf(Math.min(...p));
if(minMonth!==5){console.error('FAIL min mois',minMonth);ok=false;}
// 3) Décembre (index 11) est le plus haut
const maxMonth=p.indexOf(Math.max(...p));
if(maxMonth!==11){console.error('FAIL max mois',maxMonth);ok=false;}
// 4) Jan == Fév (mêmes indices, plus de pondération jours)
if(Math.abs(p[0]-p[1])>0.001){console.error('FAIL jan!=fev',p[0],p[1]);ok=false;}
console.log(ok?'TEST OK':'TEST ECHEC');
process.exit(ok?0:1);
```

- [ ] **Step 2 : Lancer le test, vérifier qu'il PASSE (valide les valeurs cibles)**

Run: `node scratchpad/test-prodM.js`
Expected: `TEST OK` (ce test valide les valeurs de référence avant de toucher au HTML).

- [ ] **Step 3 : Remplacer la constante `SF` par `IDX` dans le HTML**

Remplacer (ligne ~763) :
```js
const SF=[1.15,1.08,1.05,0.92,0.82,0.75,0.78,0.85,0.95,1.05,1.12,1.18];
```
par :
```js
const IDX=[1.38,1.38,1.32,0.90,0.80,0.65,0.80,0.95,1.25,1.25,1.40,1.50];
const IDXSUM=IDX.reduce((a,b)=>a+b,0);
```

- [ ] **Step 4 : Réécrire `prodM` pour répartir selon `IDX` (sans pondération jours)**

Remplacer (ligne ~805) :
```js
function prodM(kwc,en,pe){
  const f=1-pe/100;
  return SF.map((sf,i)=>kwc*en*sf*f*DM[i]);
}
```
par :
```js
function prodM(kwc,en,pe){
  const f=1-pe/100;
  const annual=kwc*en*f*365;            // productible annuel piloté par les réglages
  return IDX.map(ix=>annual*ix/IDXSUM); // réparti selon la courbe métier NC
}
```

- [ ] **Step 5 : Vérifier qu'aucune autre référence à `SF` ne subsiste**

Run: `grep -nE "\bSF\b" calculateur-pv-nc.html`
Expected: aucune ligne de code JS résiduelle (uniquement, le cas échéant, des occurrences dans des chaînes base64 — ignorer celles > 200 caractères). Si une vraie référence subsiste, la migrer vers `IDX`.

- [ ] **Step 6 : VÉRIF SYNTAXE**

Run la commande VÉRIF SYNTAXE (cf. Global Constraints).
Expected: `SYNTAXE OK`

- [ ] **Step 7 : Nettoyer le test temporaire et committer**

```bash
rm -f scratchpad/test-prodM.js _check.js
git add calculateur-pv-nc.html
git commit -m "feat(prod): courbe de production saisonnière NC (indices métier, Juin 0.65)"
```

---

## Task 2 : Header client global (T1/T2/T3) + helpers + recâblage

**Files:**
- Modify: `calculateur-pv-nc.html` (header HTML ~449, bloc T1 ~459-471, helpers JS près de `// ===== UTILS =====` ~801, consommateurs 1660/1680/1781/1790/~1914/~1924/~2355, CSS print)

**Interfaces:**
- Produces:
  - Inputs DOM `hdr_nom`, `hdr_prenom`, `hdr_adresse`, `hdr_commercial`.
  - `clientName()` → `"Prénom Nom"` (trim).
  - `clientAdresse()` → string adresse.
  - `clientCommercial()` → string `"Prénom|tel|email"` (valeur de l'option sélectionnée).
- Consumes: néant (les commerciaux Anthony seront ajoutés en Task 3).

- [ ] **Step 1 : Insérer le bandeau header global avant `.tabs`**

Repérer (ligne ~447) :
```html
<div id="cover-page" style="display:none;page-break-after:always"></div>

<div class="tabs">
```
Insérer entre les deux le bandeau :
```html
<div id="cover-page" style="display:none;page-break-after:always"></div>

<div class="study-id no-print" style="display:flex;gap:10px;flex-wrap:wrap;align-items:flex-end;background:#fafafa;border:1px solid #eee;border-radius:8px;padding:10px 12px;margin-bottom:10px">
  <div class="fg" style="flex:1;min-width:140px"><label>Nom client</label><input type="text" id="hdr_nom" value="" placeholder="Ex: DUPONT"></div>
  <div class="fg" style="flex:1;min-width:140px"><label>Prénom</label><input type="text" id="hdr_prenom" value="" placeholder="Ex: Jean"></div>
  <div class="fg" style="flex:2;min-width:200px"><label>Adresse client</label><input type="text" id="hdr_adresse" value="" placeholder="Ex: 123 Rue de la Paix, 98800 Nouméa"></div>
  <div class="fg" style="flex:1;min-width:180px"><label>Commercial</label>
    <select id="hdr_commercial">
      <option value="">-- Sélectionner --</option>
      <option value="Geoffrey|91.85.76|geoffrey.dupont@solarconcept.nc">Geoffrey Dupont — 91.85.76</option>
      <option value="Tony|74.96.99|tony.iorio@solarconcept.nc">Tony Iorio — 74.96.99</option>
      <option value="Patrice|76.51.97|patrice.mussard@solarconcept.nc">Patrice Mussard — 76.51.97</option>
      <option value="Michel|80.93.01|michel.devine@solarconcept.nc">Michel Devine — 80.93.01</option>
    </select>
  </div>
</div>

<div class="tabs">
```

- [ ] **Step 2 : Supprimer le bloc client propre à T1 (devenu global)**

Repérer dans `<!-- TAB 1 -->` (lignes ~459-471) le `fgrid3` contenant `t1_client`, `t1_commercial`, `t1_adresse` :
```html
  <div class="fgrid3" style="margin-bottom:14px">
    <div class="fg"><label>Nom client</label><input type="text" id="t1_client" value="" placeholder="Ex: M. DUPONT"></div>
    <div class="fg"><label>Commercial</label>
      <select id="t1_commercial">
        <option value="">-- Sélectionner --</option>
        <option value="Geoffrey|91.85.76|geoffrey.dupont@solarconcept.nc">Geoffrey Dupont — 91.85.76</option>
        <option value="Tony|74.96.99|tony.iorio@solarconcept.nc">Tony Iorio — 74.96.99</option>
        <option value="Patrice|76.51.97|patrice.mussard@solarconcept.nc">Patrice Mussard — 76.51.97</option>
        <option value="Michel|80.93.01|michel.devine@solarconcept.nc">Michel Devine — 80.93.01</option>
      </select>
    </div>
    <div class="fg"><label>Adresse client</label><input type="text" id="t1_adresse" value="" placeholder="Ex: 123 Rue de la Paix, 98800 Nouméa"></div>
  </div>
```
Supprimer ce bloc entièrement (le `<p>` « Consommation mensuelle… » qui suit devient le premier élément de T1).

- [ ] **Step 3 : Ajouter les helpers client près de `// ===== UTILS =====`**

Repérer (ligne ~801-803) :
```js
// ===== UTILS =====
const fmt=n=>Math.round(n).toLocaleString('fr-FR');
```
Insérer juste après la ligne `const fmtD=...` (ligne ~803) :
```js
// ===== IDENTITÉ CLIENT (header global) =====
function clientName(){const n=(document.getElementById('hdr_nom')?.value||'').trim();const p=(document.getElementById('hdr_prenom')?.value||'').trim();return (p+' '+n).trim();}
function clientAdresse(){return document.getElementById('hdr_adresse')?.value||'';}
function clientCommercial(){return document.getElementById('hdr_commercial')?.value||'';}
```

- [ ] **Step 4 : Recâbler les lecteurs `t1_client` (replace_all)**

Remplacer **toutes** les occurrences de :
```js
document.getElementById('t1_client').value
```
par :
```js
clientName()
```
(occurrences attendues : lastStudyData T1/T2/T3 et lastCalcDetails T1/T2/T3 — lignes ~1660,1680,1781,1790,1914,1924).

- [ ] **Step 5 : Recâbler `t1_commercial` et `t1_adresse` (replace_all)**

Remplacer **toutes** les occurrences de :
```js
document.getElementById('t1_commercial').value
```
par :
```js
clientCommercial()
```
puis **toutes** les occurrences de :
```js
document.getElementById('t1_adresse').value
```
par :
```js
clientAdresse()
```

- [ ] **Step 6 : Corriger le nom de fichier dans `saveStudy` (~2355)**

Remplacer :
```js
    const clientEl=document.getElementById('t1_client')||document.getElementById('t4_nom');
    const clientRaw=(clientEl&&clientEl.value)||'Etude';
```
par :
```js
    const clientRaw=clientName()||document.getElementById('t4_nom')?.value||'Etude';
```

- [ ] **Step 7 : Vérifier qu'aucune référence aux anciens IDs ne subsiste**

Run: `grep -noE "t1_client|t1_adresse|t1_commercial" calculateur-pv-nc.html`
Expected: aucune occurrence (sinon corriger).

- [ ] **Step 8 : VÉRIF SYNTAXE + commit**

Run la commande VÉRIF SYNTAXE → `SYNTAXE OK`, puis :
```bash
rm -f _check.js
git add calculateur-pv-nc.html
git commit -m "feat(header): identité client globale (Nom/Prénom/Adresse/Commercial) sur T1/T2/T3"
```

---

## Task 3 : Ajouter le commercial Anthony Debray

**Files:**
- Modify: `calculateur-pv-nc.html` (select `hdr_commercial` créé en Task 2, et `t4_commercial` ~636)

**Interfaces:**
- Consumes: select `hdr_commercial` (Task 2). Aucune sortie nouvelle.

- [ ] **Step 1 : Ajouter Anthony au header global**

Dans le select `hdr_commercial`, après l'option `Michel Devine` :
```html
      <option value="Michel|80.93.01|michel.devine@solarconcept.nc">Michel Devine — 80.93.01</option>
      <option value="Anthony|76.30.52|anthony.debray@solarconcept.nc">Anthony Debray — 76.30.52</option>
```

- [ ] **Step 2 : Ajouter Anthony au commercial T4**

Dans le select `t4_commercial` (~636), après l'option `Michel Devine` :
```html
        <option value="Michel|80.93.01|michel.devine@solarconcept.nc">Michel Devine — 80.93.01</option>
        <option value="Anthony|76.30.52|anthony.debray@solarconcept.nc">Anthony Debray — 76.30.52</option>
```

- [ ] **Step 3 : Vérifier la présence (2 occurrences attendues)**

Run: `grep -noE "Anthony Debray — 76.30.52" calculateur-pv-nc.html`
Expected: 2 lignes.

- [ ] **Step 4 : VÉRIF SYNTAXE + commit**

Run VÉRIF SYNTAXE → `SYNTAXE OK`, puis :
```bash
rm -f _check.js
git add calculateur-pv-nc.html
git commit -m "feat(commercial): ajout Anthony Debray (76.30.52) dans header global et T4"
```

---

## Task 4 : Panneaux dédiés recharge batterie (T2)

**Files:**
- Modify: `calculateur-pv-nc.html` (inputs T2 ~532-541, `calcT2` boucle batterie ~1729-1742, recap T2 ~1754-1764)

**Interfaces:**
- Consumes: `prodM` (Task 1), `DM`, `s.en`, `s.pe`, `s.dod`.
- Produces (variables locales dans `calcT2`) : `kwcDedie`, `prodDedieM[]`, `prodDedieAn`, `lostDedieAn`. La décharge batterie `bDischM`/`bDischAn` intègre la contribution du lot dédié.

- [ ] **Step 1 : Ajouter les inputs du lot dédié dans T2**

Dans le `fgrid3` de T2 (~532-541), après la ligne `t2_rev` (`<div class="fg"><label>Tarif revente réseau…</select></div>`), ajouter :
```html
    <div class="fg"><label>Panneaux dédiés batterie — nombre</label><input type="number" id="t2_pan_bat_nb" value="0" min="0" max="100" step="1"></div>
    <div class="fg"><label>Panneaux dédiés batterie — puissance (Wc)</label><input type="number" id="t2_pan_bat_wc" value="450" min="100" max="800" step="10"></div>
```

- [ ] **Step 2 : Lire les inputs et calculer la production du lot dédié dans `calcT2`**

Repérer dans `calcT2` (~1715) :
```js
  const dod=s.dod/100;
```
Ajouter juste après :
```js
  const panBatNb=Math.max(0,parseInt(document.getElementById('t2_pan_bat_nb').value)||0);
  const panBatWc=Math.max(100,parseInt(document.getElementById('t2_pan_bat_wc').value)||450);
  const kwcDedie=panBatNb*panBatWc/1000;
  const prodDedieM=kwcDedie>0?prodM(kwcDedie,s.en,s.pe):new Array(12).fill(0);
```

- [ ] **Step 3 : Intégrer le lot dédié dans la boucle batterie**

Remplacer la boucle batterie (~1730-1738) :
```js
  const batCap=batWh/1000*dod; // kWh utile/jour (DoD appliqué)
  const bChargeM=[],bDischM=[],newReinjM=[],newAchatM=[];
  for(let i=0;i<12;i++){
    const maxMois=batCap*DM[i];           // capacité cyclable sur le mois
    const bC=Math.min(reinjM[i],maxMois); // charge depuis réinjection
    const bD=Math.min(bC,achatM[i]);      // décharge couvre achat nuit
    bChargeM.push(bC); bDischM.push(bD);
    newReinjM.push(reinjM[i]-bC);         // injection réseau résiduelle
    newAchatM.push(achatM[i]-bD);         // achat réseau réduit
  }
```
par :
```js
  const batCap=batWh/1000*dod; // kWh utile/jour (DoD appliqué)
  const bChargeM=[],bDischM=[],newReinjM=[],newAchatM=[],lostDedieM=[];
  for(let i=0;i<12;i++){
    const maxMois=batCap*DM[i];                  // capacité cyclable sur le mois
    const bC=Math.min(reinjM[i],maxMois);        // charge depuis réinjection PV principal
    const capRest=Math.max(0,maxMois-bC);        // capacité restante après PV principal
    const bCDedie=Math.min(prodDedieM[i],capRest); // le lot dédié complète la charge
    const lost=prodDedieM[i]-bCDedie;            // surplus dédié écrêté (perdu)
    const bTot=bC+bCDedie;                        // charge totale du mois
    const bD=Math.min(bTot,achatM[i]);           // décharge couvre achat nuit
    bChargeM.push(bTot); bDischM.push(bD);
    newReinjM.push(reinjM[i]-bC);                // injection réseau résiduelle (lot dédié ne réinjecte pas)
    newAchatM.push(achatM[i]-bD);                // achat réseau réduit
    lostDedieM.push(lost);
  }
  const lostDedieAn=lostDedieM.reduce((a,b)=>a+b,0);
  const prodDedieAn=prodDedieM.reduce((a,b)=>a+b,0);
```

- [ ] **Step 4 : Afficher le lot dédié dans le recap T2 (si présent)**

Repérer la fin du tableau `renderRecap('recap2', [...])` (~1763-1764) :
```js
    {k:'Économie batterie / an',v:`${fmt(ecoAn)} XPF`,g:true},
  ]);
```
Remplacer par :
```js
    {k:'Économie batterie / an',v:`${fmt(ecoAn)} XPF`,g:true},
    ...(kwcDedie>0?[
      {k:'Panneaux dédiés batterie',v:`${panBatNb} × ${panBatWc} Wc (${fmtD(kwcDedie)} kWc)`},
      {k:'Production dédiée / an',v:`${fmt(prodDedieAn)} kWh`},
      {k:'Dont écrêté (batterie pleine)',v:`${fmt(lostDedieAn)} kWh`,r:true},
    ]:[]),
  ]);
```

- [ ] **Step 5 : VÉRIF SYNTAXE**

Run VÉRIF SYNTAXE → `SYNTAXE OK`

- [ ] **Step 6 : Vérification manuelle navigateur**

Ouvrir `calculateur-pv-nc.html` dans le navigateur, onglet « 🔋 Batterie + données » :
1. Avec « Panneaux dédiés batterie — nombre » = 0 → résultat identique à avant (pas de lignes dédiées dans le recap).
2. Mettre nombre = 10, Wc = 450 → cliquer CALCULER. Vérifier : recap affiche « Panneaux dédiés batterie 10 × 450 Wc (4,5 kWc) », « Production dédiée / an », « Dont écrêté ». L'économie batterie / an augmente (ou reste égale si batterie déjà saturée par la réinjection). Aucune erreur console.

- [ ] **Step 7 : Commit**

```bash
rm -f _check.js
git add calculateur-pv-nc.html
git commit -m "feat(T2): panneaux dédiés recharge batterie (production calculée, surplus écrêté)"
```

---

## Vérification finale (après les 4 tâches)

- [ ] **VÉRIF SYNTAXE** globale → `SYNTAXE OK`.
- [ ] Ouvrir le fichier, tester chaque onglet (T1, T2, T3, T4) : un calcul complet sans erreur console.
- [ ] T1 & T4 : graphe de production mensuelle montre le creux d'hiver (Juin minimum).
- [ ] Header global : saisir Nom/Prénom/Adresse/Commercial → repris dans la page de garde (📄 Enregistrer en PDF) et dans l'export HTML/PDF pour T1, T2 et T3.
- [ ] T4 conserve ses propres champs PRO.
- [ ] Anthony Debray présent dans le header global et dans T4.
- [ ] Nettoyer `_check.js` (ignoré par git, mais le supprimer).
- [ ] Proposer le push (`git push origin main`) — **uniquement sur validation de Tony**.

## Notes de cohérence (self-review)

- **Couverture spec** : Chantier 1 → Task 1 ; Chantier 2 → Task 4 ; Chantier 3 → Task 3 ; Chantier 4 → Task 2. ✅
- **Écart assumé vs spec** : la spec disait « courbe sur T1/T2/T3/T4 ». En réalité `prodM` n'est appelé que par T1 et T4 ; T2/T3 utilisent les **données réelles saisies** (donc non concernées par la courbe — comportement correct, la donnée réelle prime). Le lot dédié de T2 (Task 4) utilise bien `prodM`, donc la même courbe. « Le soleil est le même pour tout le monde » reste respecté partout où la production est modélisée.
- **Cohérence des noms** : `clientName()` / `clientAdresse()` / `clientCommercial()` utilisés identiquement dans Tasks 2 et 4. `prodM` signature inchangée (`kwc, en, pe`).
- **DRY** : un seul header, trois helpers, aucun champ client dupliqué.
- **YAGNI** : pas de calcul de prix automatique du lot dédié (devis saisi à la main, conforme à la spec).

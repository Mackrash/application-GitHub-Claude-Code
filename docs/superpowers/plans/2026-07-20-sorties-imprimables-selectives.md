# Sorties imprimables sélectives — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Panneau d'impression avec 2 presets + cases à cocher, 3 sorties distinctes (A=T1, B=T2/T3, C=T4), dédoublonnage des données imprimées, export JSON pour FOLIO.

**Architecture:** Tout dans `calculateur-pv-nc.html`. Les sections imprimables reçoivent `data-psec="<nom>"` ; le modal pose des classes sur `<body>` (`print-A|B|C` + `psoff-<nom>` par section décochée) ; le CSS `@media print` masque via ces classes. Aucun déplacement de DOM. La sortie B ajoute un bloc synthèse batterie print-only généré par `renderBatSynth()`.

**Tech Stack:** HTML5, JS vanilla, CSS print, Plotly 2.27 (inchangé), Node.js (vérif syntaxe).

## Global Constraints

- Fichier cible unique : `calculateur-pv-nc.html`.
- Langue FR + accents. Devise XPF, milliers = espace (via `fmt`).
- Charte : orange `#F07020`, anthracite `#333`, vert gains `#008040`, rouge dépenses `#CC2244`.
- **Le moins de papier possible** : preset Synthèse = 3 pages max par sortie.
- **Écran inchangé** : toutes les modifs visuelles sont print-only (sauf le modal, qui est un overlay écran `no-print`).
- Réutiliser les designs print existants (KPI cards, recap-box, efy-fiscal, pile `plotPile`, bandeaux `.ps-label`).
- Vérif syntaxe obligatoire après chaque modif + **push après chaque commit** (`git push origin main`).

**Commande VÉRIF SYNTAXE :**
```bash
node -e "const fs=require('fs');const html=fs.readFileSync('calculateur-pv-nc.html','utf8');const m=html.match(/<script>([\s\S]*?)<\/script>/g);if(m){const js=m.map(s=>s.replace(/<\/?script>/g,'')).join('\n');fs.writeFileSync('_check.js',js);}" && node --check _check.js && echo "SYNTAXE OK" && rm -f _check.js
```

**Rappel structure (état actuel) :**
- Onglets : `#tab0`=T1, `#tab1`=T2, `#tab2`=T3, `#tab3`=T4, `#tab4`=Paramètres.
- Résultats : `#r1` (~l.498), `#r2` (~l.551), `#r3` (~l.601), `#r4` (~l.710), `#last-page` (~l.770).
- `preparePrint(noPrint=false)` (~l.945) construit `#cover-page` + `#last-page` puis `window.print()`.
- **Bug connu à corriger (Task 1)** : `preparePrint` destructure `tab` depuis `lastStudyData`, mais seuls les calculs T4 y mettent `tab:4` → le titre « Ajout d'un système de stockage » (T2/T3) ne s'affiche jamais.

---

## Task 1 : Fondations — tab actif fiable, tagging `data-psec`, CSS de filtrage

**Files:**
- Modify: `calculateur-pv-nc.html`

**Interfaces:**
- Produces : `tabActif()` → 1..4 (onglet actif, fallback `lastStudyData.tab`) ; `sortieActive()` → `'A'|'B'|'C'`. Attributs `data-psec` posés : `pile`, `gfact`, `groi`, `amort`, `factures`, `bilan`, `bilanEn`, `tranches`. Classes body consommées par le CSS : `print-A|print-B|print-C`, `psoff-<nom>`.

- [ ] **Step 1 : Helpers `tabActif()` / `sortieActive()` + fix du bug tab**

Insérer juste AVANT `function preparePrint(noPrint=false){` (~l.945) :
```js
// Onglet actif (1=T1..4=T4) — fallback sur le dernier calcul si Paramètres est ouvert
function tabActif(){
  const a=document.querySelector('.tab-content.active');
  const i=a?parseInt(a.id.replace('tab',''),10):-1;
  return (i>=0&&i<=3)?i+1:(lastStudyData.tab||1);
}
// Sortie d'impression : A = T1 (install PV), B = T2/T3 (stockage), C = T4 (pro)
function sortieActive(){const t=tabActif();return t===4?'C':(t>=2?'B':'A');}
```

Dans `preparePrint`, remplacer la ligne (~l.949) :
```js
  const {tab=1,kwc=6.3,devis=0,ecoAn=0,fSansAn=0,fAvecAn=0,batModel=0,batQty=1,client='',commercial='',adresse='',pb=0,pbMin=0,pbMax=0,eco10=0,eco15=0,coutNetImpot=0,avantageTotal=0,tIS=0,dAmort=0}=lastStudyData;
```
par :
```js
  const tab=tabActif();
  const {kwc=6.3,devis=0,ecoAn=0,fSansAn=0,fAvecAn=0,batModel=0,batQty=1,client='',commercial='',adresse='',pb=0,pbMin=0,pbMax=0,eco10=0,eco15=0,coutNetImpot=0,avantageTotal=0,tIS=0,dAmort=0}=lastStudyData;
```

Et compléter les 3 affectations `lastStudyData={...}` (pour l'export JSON, Task 6) :
- calcT1 (~l.1771) : `lastStudyData={kwc,` → `lastStudyData={tab:1,kwc,`
- calcT2 (~l.1906) : `lastStudyData={kwc,` → `lastStudyData={tab:2,kwc,`
- calcT3 (~l.2042) : `lastStudyData={kwc,` → `lastStudyData={tab:3,kwc,`
(T4 l.2375 a déjà `tab:4`.)

- [ ] **Step 2 : Tagger les sections de `#r1` (T1)**

Dans `#r1` (~l.498-530), poser les attributs :
```html
    <div class="ps ps-donut" data-psec="pile">
      <div id="g1_donut" style="height:340px"></div>
    </div>
```
```html
    <div class="ps ps-financial">
      <div data-psec="gfact"><div id="recap1_efy_eco"></div>
      <div id="g1_mois" style="height:310px;margin-top:12px"></div></div>
      <div data-psec="groi"><div class="st" style="margin-top:14px">Retour sur investissement — 20 ans</div>
      <div id="g1_roi" style="height:270px"></div>
      <div id="k1_pb"></div></div>
      <div id="recap1_efy_fiscal" style="margin-top:12px"></div>
    </div>
    <div class="ps ps-table" data-psec="amort">
      <div class="tw" id="tb1"></div>
    </div>
    <div class="ps ps-table" data-psec="factures">
      <span class="ps-label">Estimation de vos factures</span>
      <div class="st">Estimation de vos factures (moyenne mensuelle)</div>
      <div class="tw" id="t1_facture"></div>
    </div>
    <div class="ps ps-table" data-psec="bilan">
      <span class="ps-label">Bilan énergétique mensuel</span>
      <div class="st">Bilan énergétique mensuel</div>
      <div class="tw" id="t1_bilan"></div>
    </div>
```
(On enveloppe `gfact` et `groi` dans des `<div data-psec>` — pas de déplacement, juste des wrappers.)

- [ ] **Step 3 : Tagger `#r2` et `#r3` (T2/T3) — identique + `bilanEn`**

Mêmes attributs que Step 2 en remplaçant les ids (`g2_*`/`recap2_*`/`tb2`/`t2_*`, puis `g3_*`/`recap3_*`/`tb3`/`t3_*`). En plus, dans le `ps-recap` :
```html
      <div id="recap2_efy_bilan" data-psec="bilanEn"></div>
```
(et `recap3_efy_bilan` pareil). Ne PAS tagger `recap1_efy_bilan` (T1 le garde en synthèse).

- [ ] **Step 4 : Tagger `#r4` (T4)**

```html
    <div class="ps ps-table" data-psec="amort">
      <div class="st">Tableau d'amortissement professionnel</div>
      <div id="amort4_combined"></div>
    </div>
```
(Le bloc `.ps-charts` reste sans psec : toujours imprimé en sortie C.)

- [ ] **Step 5 : CSS print de filtrage + dédoublonnage fiscal**

Dans le bloc `@media print{` (juste avant `/* ── PAGE DE GARDE ── */`, ~l.406), ajouter :
```css
  /* ── FILTRAGE SECTIONS (modal impression) ── */
  body.psoff-pile [data-psec="pile"],
  body.psoff-gfact [data-psec="gfact"],
  body.psoff-groi [data-psec="groi"],
  body.psoff-amort [data-psec="amort"],
  body.psoff-factures [data-psec="factures"],
  body.psoff-bilan [data-psec="bilan"],
  body.psoff-bilanEn [data-psec="bilanEn"],
  body.psoff-tranches [data-psec="tranches"],
  body.print-C.psoff-recapfin #last-page{display:none!important}
  /* Dédoublonnage : le tableau fiscal de la page financière ne sort plus (vit en dernière page) */
  [id$="_efy_fiscal"]{display:none!important}
  /* Page financière entièrement décochée → pas de page blanche */
  body.psoff-gfact.psoff-groi .ps-financial{display:none!important}
  /* Le modal ne s'imprime jamais */
  #print-modal{display:none!important}
```

- [ ] **Step 6 : VÉRIF SYNTAXE + test manuel rapide**

Lancer la commande VÉRIF SYNTAXE → `SYNTAXE OK`.
Test manuel : ouvrir le fichier, calculer T2, aperçu d'impression → le titre de garde doit maintenant afficher « Ajout d'un système de stockage d'énergie » (bug tab corrigé) ; le tableau fiscal de la page financière ne doit plus apparaître.

- [ ] **Step 7 : Commit + push**

```bash
git add calculateur-pv-nc.html
git commit -m "feat(print): fondations sorties sélectives — tabActif() (fix titre T2/T3), data-psec, CSS filtrage, dédoublonnage fiscal"
git push origin main
```

---

## Task 2 : Modal d'impression (presets + cases + localStorage)

**Files:**
- Modify: `calculateur-pv-nc.html`

**Interfaces:**
- Consumes : `sortieActive()`, `preparePrint()` (Task 1).
- Produces : `openPrintModal()` (bouton), `PRINT_CFG` (config sections par sortie), classes body posées avant impression et nettoyées sur `afterprint`.

- [ ] **Step 1 : HTML du modal**

Juste avant `<div id="last-page" style="display:none"></div>` (~l.770) :
```html
<!-- MODAL IMPRESSION -->
<div id="print-modal" class="no-print" style="display:none">
  <div class="pm-box">
    <div class="pm-head">Impression de l'étude <span class="pm-x" onclick="pmClose()">✕</span></div>
    <div class="pm-body">
      <div class="pm-sec">Preset</div>
      <div class="pm-presets">
        <div class="pm-pre" id="pm-pre-synth" onclick="pmPreset('synth')"><b>Synthèse client</b><small>3 pages — l'essentiel</small></div>
        <div class="pm-pre" id="pm-pre-full" onclick="pmPreset('full')"><b>Dossier complet</b><small>Toutes les sections</small></div>
      </div>
      <div class="pm-sec">Contenu</div>
      <label class="pm-chk pm-locked"><input type="checkbox" checked disabled> Page de garde <small>toujours incluse</small></label>
      <label class="pm-chk pm-locked"><input type="checkbox" checked disabled> Page synthèse <small>toujours incluse</small></label>
      <div id="pm-list"></div>
    </div>
    <div class="pm-foot">
      <div class="pm-pages" id="pm-pages">📄 3 pages</div>
      <button class="pm-btn pm-json" onclick="exportStudyJSON()" title="Export FOLIO">⚙ JSON</button>
      <button class="pm-btn pm-cancel" onclick="pmClose()">Annuler</button>
      <button class="pm-btn pm-print" onclick="pmPrint()">🖨 Imprimer</button>
    </div>
  </div>
</div>
```
(Le bouton `⚙ JSON` appellera `exportStudyJSON()` — créée en Task 6 ; d'ici là, ajouter un stub `function exportStudyJSON(){alert('Export JSON — à venir')}` dans le Step 3, remplacé en Task 6.)

- [ ] **Step 2 : CSS écran du modal**

Dans le `<style>` principal (hors `@media print`, après les règles `.btn-print`, ~l.46) :
```css
#print-modal{position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:1000;display:flex;align-items:center;justify-content:center}
.pm-box{background:var(--d3,#fff);color:var(--tx,#333);border-radius:12px;width:400px;max-width:92vw;max-height:90vh;overflow:auto;box-shadow:0 20px 60px rgba(0,0,0,.5)}
.pm-head{background:#F07020;color:#fff;padding:13px 18px;font-weight:800;letter-spacing:.5px;display:flex;justify-content:space-between;border-radius:12px 12px 0 0}
.pm-x{cursor:pointer;opacity:.85}
.pm-body{padding:16px 18px}
.pm-sec{font-size:.68rem;font-weight:800;text-transform:uppercase;letter-spacing:1px;color:var(--tx2,#999);margin:12px 0 7px}
.pm-sec:first-child{margin-top:0}
.pm-presets{display:flex;gap:8px}
.pm-pre{flex:1;border:2px solid rgba(128,128,128,.35);border-radius:9px;padding:9px 11px;cursor:pointer;transition:.15s}
.pm-pre.on{border-color:#F07020;background:rgba(240,112,32,.08)}
.pm-pre b{display:block;font-size:.8rem}
.pm-pre.on b{color:#F07020}
.pm-pre small{font-size:.62rem;color:var(--tx2,#888)}
.pm-chk{display:flex;align-items:center;gap:9px;padding:6px 4px;font-size:.8rem;border-bottom:1px solid rgba(128,128,128,.15);cursor:pointer}
.pm-chk input{width:15px;height:15px;accent-color:#F07020}
.pm-locked{opacity:.5;cursor:default}
.pm-chk small{margin-left:auto;font-size:.6rem;color:var(--tx2,#aaa);font-style:italic}
.pm-foot{padding:12px 18px;display:flex;gap:8px;justify-content:flex-end;border-top:1px solid rgba(128,128,128,.2);align-items:center}
.pm-pages{font-size:.68rem;color:var(--tx2,#888);margin-right:auto}
.pm-btn{font-family:'Nunito',sans-serif;font-weight:700;padding:8px 16px;border-radius:8px;border:none;cursor:pointer;font-size:.78rem}
.pm-cancel{background:rgba(128,128,128,.18);color:var(--tx,#555)}
.pm-print{background:#F07020;color:#fff}
.pm-json{background:transparent;border:1px solid rgba(128,128,128,.4);color:var(--tx2,#888)}
```

- [ ] **Step 3 : JS du modal**

Insérer juste APRÈS la fonction `sortieActive()` (Task 1) :
```js
// ===== MODAL IMPRESSION — presets + cases par sortie =====
const PRINT_CFG={
  A:[{id:'pile',label:'Pile répartition énergétique',def:1},
     {id:'tranches',label:'ROI par tranche fiscale',def:1},
     {id:'gfact',label:'Graphique factures avant/après',def:0},
     {id:'groi',label:'Graphique ROI 20 ans',def:0},
     {id:'amort',label:"Tableau d'amortissement",def:0},
     {id:'factures',label:'Estimation de vos factures',def:0},
     {id:'bilan',label:'Bilan énergétique mensuel',def:0}],
  B:[{id:'tranches',label:'ROI par tranche fiscale',def:0},
     {id:'pile',label:'Pile répartition énergétique',def:0},
     {id:'gfact',label:'Graphique factures avant/après',def:0},
     {id:'groi',label:'Graphique ROI 20 ans',def:0},
     {id:'bilanEn',label:'Bilan énergétique annuel',def:0},
     {id:'amort',label:"Tableau d'amortissement",def:0},
     {id:'factures',label:'Estimation de vos factures',def:0},
     {id:'bilan',label:'Bilan énergétique mensuel',def:0}],
  C:[{id:'amort',label:"Tableau d'amortissement 15 ans",def:0},
     {id:'recapfin',label:'Récapitulatif final',def:0}]
};
let pmSortie='A';
function exportStudyJSON(){alert('Export JSON — à venir')} // stub, remplacé en Task 6
function openPrintModal(){
  pmSortie=sortieActive();
  const saved=JSON.parse(localStorage.getItem('printPrefs_'+pmSortie)||'null');
  const list=document.getElementById('pm-list');
  list.innerHTML=PRINT_CFG[pmSortie].map(s=>{
    const on=saved?!saved.off.includes(s.id):!!s.def;
    return `<label class="pm-chk"><input type="checkbox" data-psec-id="${s.id}" ${on?'checked':''} onchange="pmSync()"> ${s.label}</label>`;
  }).join('');
  pmMarkPreset(saved?saved.preset:'synth');
  pmCount();
  document.getElementById('print-modal').style.display='flex';
}
function pmMarkPreset(p){
  document.getElementById('pm-pre-synth').classList.toggle('on',p==='synth');
  document.getElementById('pm-pre-full').classList.toggle('on',p==='full');
}
function pmPreset(p){
  document.querySelectorAll('#pm-list input').forEach(i=>{
    const cfg=PRINT_CFG[pmSortie].find(s=>s.id===i.dataset.psecId);
    i.checked=p==='full'?true:!!cfg.def;
  });
  pmMarkPreset(p);pmCount();
}
function pmOff(){
  return [...document.querySelectorAll('#pm-list input')].filter(i=>!i.checked).map(i=>i.dataset.psecId);
}
function pmSync(){pmMarkPreset('');pmCount();}
function pmCount(){
  const off=pmOff();
  const on=id=>PRINT_CFG[pmSortie].some(x=>x.id===id)&&!off.includes(id);
  let p=pmSortie==='A'?2:3;
  if(pmSortie==='A'&&on('tranches'))p+=1;
  if(on('gfact')||on('groi'))p+=1;
  ['amort','factures','bilan','recapfin'].forEach(id=>{if(on(id))p+=1});
  document.getElementById('pm-pages').textContent='📄 ~'+p+' page'+(p>1?'s':'');
}
function pmClose(){document.getElementById('print-modal').style.display='none'}
function pmPrint(){
  const off=pmOff();
  const preset=document.getElementById('pm-pre-full').classList.contains('on')?'full':'synth';
  localStorage.setItem('printPrefs_'+pmSortie,JSON.stringify({preset,off}));
  const b=document.body;
  b.classList.add('print-'+pmSortie);
  off.forEach(id=>b.classList.add('psoff-'+id));
  const clean=()=>{b.className=b.className.split(' ').filter(c=>!c.startsWith('print-')&&!c.startsWith('psoff-')).join(' ');window.removeEventListener('afterprint',clean)};
  window.addEventListener('afterprint',clean);
  pmClose();
  preparePrint();
}
```

- [ ] **Step 4 : Brancher le bouton**

Ligne ~442, remplacer :
```html
    <button class="btn-print" onclick="preparePrint()">📄 Enregistrer en PDF</button>
```
par :
```html
    <button class="btn-print" onclick="openPrintModal()">📄 Enregistrer en PDF</button>
```

- [ ] **Step 5 : VÉRIF SYNTAXE + test manuel**

VÉRIF SYNTAXE → `SYNTAXE OK`.
Test : ouvrir, calculer T1 → clic « Enregistrer en PDF » → le modal s'ouvre, preset Synthèse actif, 7 cases listées, compteur « ~3 pages ». Cocher/décocher → compteur bouge, preset se dé-surligne. Imprimer → aperçu conforme aux cases. Rouvrir le modal → derniers choix restaurés.

- [ ] **Step 6 : Commit + push**

```bash
git add calculateur-pv-nc.html
git commit -m "feat(print): modal d'impression — presets Synthèse/Complet, cases par sortie, mémorisation localStorage"
git push origin main
```

---

## Task 3 : Sortie A — synthèse 3 pages, récap T1 compacté

**Files:**
- Modify: `calculateur-pv-nc.html`

**Interfaces:**
- Consumes : classes `psoff-*` (Task 1), modal (Task 2).
- Produces : récap T1 sans doublons financiers (les KPI `k1_fin` restent seuls porteurs).

- [ ] **Step 1 : Compacter le récap installation T1**

Dans `calcT1`, l'appel `renderRecap('recap1',[...])` (~l.1740) liste 11 entrées. Supprimer les 3 doublons financiers (déjà dans `k1_fin`) :
```js
    {k:'Facture annuelle AVANT PV',v:`${fmt(fSansAn)} XPF`,r:true},
    {k:'Facture annuelle APRÈS PV',v:`${fmt(fAvecAn)} XPF`,g:true},
    {k:'Économie annuelle (An 1)',v:`${fmt(ecoAn)} XPF`,g:true},
```
→ supprimer ces 3 lignes. Garder : puissance, panneaux, surface, production, taux autoconso, batterie, investissement TTC (+ payback éventuel s'il y est).

- [ ] **Step 2 : Sauts de page — synthèse tient sur la page 2**

Dans `@media print`, après la règle `.ps-donut [id$="_donut"]{...}` (~l.272), ajouter :
```css
  /* Sortie A synthèse : si la page financière est masquée, la dernière page suit directement */
  body.psoff-gfact.psoff-groi .ps-page2{break-after:auto}
```
(`#last-page` a déjà `break-before:page`, donc garde/synthèse/ROI-tranches = 3 pages.)

- [ ] **Step 3 : VÉRIF SYNTAXE + test manuel**

VÉRIF SYNTAXE → `SYNTAXE OK`.
Test : T1 calculé, preset Synthèse → aperçu = 3 pages exactement (garde / récap+KPI+pile / ROI tranches). Aucune page blanche. Preset Complet → toutes les sections, pas de doublon économie annuelle hors KPI.

- [ ] **Step 4 : Commit + push**

```bash
git add calculateur-pv-nc.html
git commit -m "feat(print A): synthèse 3 pages T1 — récap compacté (doublons financiers retirés), sauts de page ajustés"
git push origin main
```

---

## Task 4 : Sortie B — synthèse batterie (héros + avant/après) + dernière page adaptée

**Files:**
- Modify: `calculateur-pv-nc.html`

**Interfaces:**
- Consumes : variables de `calcT2`/`calcT3` (`ecoAn`, `fSansBat`, `fAvecBat`, `newAchatAn`, `newInjAn`/`newReinjAn`, `bDischAn`, `devis`, `batModel`, `batQty`, `BLBL`), `getS()`.
- Produces : `renderBatSynth(id,d)` — remplit `#synth2`/`#synth3` (print-only).

- [ ] **Step 1 : Conteneurs print-only dans r2/r3**

Dans `#r2` :
```html
    <div class="ps ps-recap">
      <div id="synth2" class="print-synth"></div>
      <div id="recap2"></div>
```
Dans `#r3` : idem avec `synth3` avant `recap3`.

- [ ] **Step 2 : CSS — visible uniquement en impression sortie B, doublons masqués**

Écran (style principal) :
```css
.print-synth{display:none}
```
Print (`@media print`, après le bloc filtrage Task 1) :
```css
  /* ── SORTIE B : synthèse batterie ── */
  body.print-B .print-synth{display:block!important}
  body.print-B #recap2,body.print-B #recap3,
  body.print-B #k2_fin,body.print-B #k3_fin{display:none!important}
  .bs-hero{background:#F0FBF6!important;border:2px solid #008040;border-radius:8px;padding:12pt;text-align:center;margin-bottom:10pt;break-inside:avoid}
  .bs-hero-v{font-family:'RAIDenmarkNeo',sans-serif;font-size:24pt;font-weight:700;color:#008040!important}
  .bs-hero-l{font-size:8pt;color:#555;text-transform:uppercase;letter-spacing:1pt;margin-top:4pt;font-weight:700}
  .bs-tbl td:first-child{text-align:left!important;color:#333!important}
```

- [ ] **Step 3 : Fonction `renderBatSynth`**

Insérer après `renderRecap` (~l.1313) :
```js
// ===== SORTIE B (print) — synthèse batterie : héros économie + avant/après =====
function renderBatSynth(id,d){
  const el=document.getElementById(id);if(!el)return;
  const r=(k,a,b,g)=>`<tr><td>${k}</td><td>${a}</td><td>${b}</td><td style="color:#008040;font-weight:800">${g}</td></tr>`;
  el.innerHTML=`
  <div class="bs-hero"><div class="bs-hero-v">${fmt(Math.round(d.ecoAn))} XPF / an</div>
  <div class="bs-hero-l">Économie annuelle générée par votre batterie</div></div>
  <table class="efy-fiscal bs-tbl"><thead><tr><th></th><th>Sans batterie</th><th>Avec batterie</th><th>Gain</th></tr></thead><tbody>
   ${r('Achat réseau',fmt(Math.round(d.achatAvant))+' kWh',fmt(Math.round(d.achatApres))+' kWh','− '+fmt(Math.round(d.achatAvant-d.achatApres))+' kWh')}
   ${r('Injection réseau',fmt(Math.round(d.injAvant))+' kWh',fmt(Math.round(d.injApres))+' kWh',fmt(Math.round(d.injAvant-d.injApres))+' kWh valorisés')}
   ${r('Facture électricité',fmt(Math.round(d.fAvant))+' XPF/an',fmt(Math.round(d.fApres))+' XPF/an','− '+fmt(Math.round(d.fAvant-d.fApres))+' XPF')}
  </tbody></table>
  <div class="recap-box" style="margin-top:10pt"><div class="recap-grid">
   <div class="recap-row"><span class="recap-key">Batterie</span><span class="recap-val hi">${d.batLbl}</span></div>
   <div class="recap-row"><span class="recap-key">Couverture via batterie</span><span class="recap-val g">${fmt(Math.round(d.couvKwh))} kWh/an</span></div>
   <div class="recap-row"><span class="recap-key">Investissement TTC</span><span class="recap-val hi">${fmt(Math.round(d.devis))} XPF</span></div>
   <div class="recap-row"><span class="recap-key">Durée de vie batterie</span><span class="recap-val">${d.dureeVie} ans</span></div>
  </div></div>`;
}
```

- [ ] **Step 4 : Appels dans calcT2 et calcT3**

Dans `calcT2`, juste après la ligne `const ecoMois=fSansM.map((f,i)=>f-fAvecM[i]);` (~l.1876) :
```js
  renderBatSynth('synth2',{ecoAn,achatAvant:achatM.reduce((a,b)=>a+b,0),achatApres:newAchatAn,
    injAvant:reinjM.reduce((a,b)=>a+b,0),injApres:newReinjAn,fAvant:fSansBat,fApres:fAvecBat,
    batLbl:`${BLBL[batModel]}${batQty>1?' × '+batQty:''}`,couvKwh:bDischAn,devis,dureeVie:s.db});
```
Dans `calcT3`, juste après sa ligne `const ecoMois=fSansM.map((f,i)=>f-fAvecM[i]);` (~l.1991) :
```js
  renderBatSynth('synth3',{ecoAn,achatAvant:achatM.reduce((a,b)=>a+b,0),achatApres:newAchatAn,
    injAvant:injM.reduce((a,b)=>a+b,0),injApres:newInjAn,fAvant:fSansBat,fApres:fAvecBat,
    batLbl:`${BLBL[batModel]}${batQty>1?' × '+batQty:''}`,couvKwh:bDischAn,devis,dureeVie:s.db});
```
(Vérifier avant d'insérer que les noms `newReinjAn`/`newInjAn`, `bDischAn`, `fSansBat`, `fAvecBat` existent bien dans chaque fonction : `grep -n "newReinjAn\|newInjAn\|bDischAn" calculateur-pv-nc.html`.)

- [ ] **Step 5 : Dernière page — ROI tranches en section + prochaines étapes (B)**

Dans `preparePrint`, le bloc `roiSection` (~l.1106-1113) : envelopper son contenu :
```js
    roiSection=`
      <div data-psec="tranches">
      <h2 class="lp-h2">Retour sur investissement selon votre tranche fiscale</h2>
      ...(contenu existant inchangé)...
      <div class="lp-note">...</div>
      </div>`;
```
Puis ajouter juste après la construction de `roiSection` :
```js
  const isB=tab===2||tab===3;
  const stepsSection=isB?`
      <h2 class="lp-h2" style="margin-top:0.8cm">Les prochaines étapes</h2>
      <table class="lp-roi"><tbody>
        <tr><td class="tr">1. Validation de l'étude</td><td>ensemble, aujourd'hui</td></tr>
        <tr><td class="tr">2. Visite technique</td><td>sous 10 jours</td></tr>
        <tr><td class="tr">3. Pose et mise en service</td><td>½ journée</td></tr>
      </tbody></table>`:'';
```
Et dans le template de `#last-page`, remplacer `${roiSection}` par `${roiSection}${stepsSection}`.

- [ ] **Step 6 : VÉRIF SYNTAXE + test manuel**

VÉRIF SYNTAXE → `SYNTAXE OK`.
Test : calculer T2 (et T3), preset Synthèse → 3 pages : garde stockage / héros économie + avant/après + infos batterie / récap dossier avec prochaines étapes SANS tableau tranches. Cocher « ROI par tranche » → le tableau réapparaît en dernière page. Écran : rien ne change (synth2/3 invisibles).

- [ ] **Step 7 : Commit + push**

```bash
git add calculateur-pv-nc.html
git commit -m "feat(print B): synthèse batterie — héros économie annuelle, tableau avant/après, prochaines étapes; ROI tranches optionnel"
git push origin main
```

---

## Task 5 : Sortie C — T4 : rapport + graphes, tableau 15 ans et récap final cochables

**Files:**
- Modify: `calculateur-pv-nc.html`

**Interfaces:**
- Consumes : psec `amort` sur le tableau pro (Task 1 Step 4), règle `body.print-C.psoff-recapfin #last-page` (Task 1 Step 5), config C du modal (Task 2).

- [ ] **Step 1 : Sauts de page C quand le tableau est décoché**

Dans `@media print`, après les règles `#r4` existantes (~l.377-382) :
```css
  /* Sortie C synthèse : tableau amort masqué → les graphes montent en page 3 */
  body.print-C.psoff-amort #r4 .ps-charts{break-before:auto}
```

- [ ] **Step 2 : VÉRIF SYNTAXE + test manuel**

VÉRIF SYNTAXE → `SYNTAXE OK`.
Test : calculer T4, preset Synthèse → 3 pages : garde pro / rapport entreprise / pile + avant-après. Ni tableau 15 ans, ni récap final. Preset Complet → 5 pages avec tableau et récap final. Modal sur T4 : 2 cases seulement.

- [ ] **Step 3 : Commit + push**

```bash
git add calculateur-pv-nc.html
git commit -m "feat(print C): sortie pro — rapport + graphes en synthèse, tableau 15 ans et récap final cochables"
git push origin main
```

---

## Task 6 : Export JSON FOLIO

**Files:**
- Modify: `calculateur-pv-nc.html`

**Interfaces:**
- Consumes : `lastStudyData` (avec `tab`, Task 1), `getS()`, `TRANCHES_NC`, `calcDeduction`, `buildAmort`, `sortieActive()`.
- Produces : `buildStudyJSON()` → objet étude ; `exportStudyJSON()` → télécharge `ETUDE <client> <JJ-MM-AAAA>.json` (remplace le stub de Task 2).

- [ ] **Step 1 : Remplacer le stub par l'implémentation**

Remplacer `function exportStudyJSON(){alert('Export JSON — à venir')}` par :
```js
// ===== EXPORT JSON — format stable consommé par FOLIO (agent NEXIA) =====
// {meta,client,commercial,installation,finances,tranchesFiscales,parametres}
function buildStudyJSON(){
  const s=getS(),d=lastStudyData,sortie=sortieActive();
  const tranches=(sortie==='C')?[]:TRANCHES_NC.filter(t=>t.taux>0).map(t=>{
    const ded=calcDeduction(d.devis,t.taux,s.ded);
    const am=buildAmort(d.devis,d.ecoAn1||d.ecoAn,s.hau,s.deg,s.dpv,t.taux,s.ded,0,0);
    return {tranche:t.label,taux:t.taux,deductionXPF:Math.round(ded.eco),
      coutNetXPF:Math.round(d.devis-ded.eco),paybackAn:am.pb||null};
  });
  return {
    meta:{version:1,date:new Date().toISOString(),sortie,onglet:d.tab||1,source:'calculateur-pv-nc'},
    client:{nom:d.client||'',adresse:d.adresse||''},
    commercial:d.commercial||'',
    installation:{kwc:d.kwc,batterieModeleWh:d.batModel||0,batterieQte:d.batQty||0},
    finances:{devisTTC:d.devis,factureAvantAnXPF:Math.round(d.fSansAn),
      factureApresAnXPF:Math.round(d.fAvecAn),economieAn1XPF:Math.round(d.ecoAn1||d.ecoAn),
      gains10ansXPF:Math.round(d.eco10||0),gains15ansXPF:Math.round(d.eco15||0),paybackAn:d.pb||null},
    tranchesFiscales:tranches,
    parametres:s
  };
}
function exportStudyJSON(){
  if(!lastStudyData.devis){alert('Calcule d’abord une étude (bouton CALCULER).');return}
  const blob=new Blob([JSON.stringify(buildStudyJSON(),null,2)],{type:'application/json'});
  const dd=new Date(),ds=String(dd.getDate()).padStart(2,'0')+'-'+String(dd.getMonth()+1).padStart(2,'0')+'-'+dd.getFullYear();
  const a=document.createElement('a');
  a.href=URL.createObjectURL(blob);
  a.download=('ETUDE '+(lastStudyData.client||'Client')+' '+ds+'.json').replace(/[\\/:*?"<>|]/g,'');
  a.click();URL.revokeObjectURL(a.href);
}
```
(Vérifier la signature réelle de `buildAmort` avant insertion : `grep -n "function buildAmort" calculateur-pv-nc.html` — adapter les 2 derniers arguments (remplacement batterie) si besoin ; 0,0 = pas de remplacement, simplification assumée v1.)

- [ ] **Step 2 : VÉRIF SYNTAXE + test manuel**

VÉRIF SYNTAXE → `SYNTAXE OK`.
Test : calculer T1 → modal → `⚙ JSON` → fichier `ETUDE <nom> <date>.json` téléchargé, contenu cohérent (devis, économies, 4 tranches). Sur T4 : `tranchesFiscales` vide. Sans calcul préalable : alerte, pas de fichier.

- [ ] **Step 3 : Commit + push**

```bash
git add calculateur-pv-nc.html
git commit -m "feat(export): buildStudyJSON + export fichier — préparation FOLIO (agent NEXIA)"
git push origin main
```

---

## Task 7 : Vérification finale de bout en bout

**Files:**
- Modify (si corrections) : `calculateur-pv-nc.html`

- [ ] **Step 1 : VÉRIF SYNTAXE globale** → `SYNTAXE OK`.

- [ ] **Step 2 : Grille de test manuel complète (avec Tony)**

| # | Scénario | Attendu |
|---|---|---|
| 1 | T1 → Synthèse | 3 pages : garde kWc / récap+KPI+pile / ROI tranches |
| 2 | T1 → Complet | + page financière, amort, factures, bilan — zéro doublon éco annuelle |
| 3 | T2 → Synthèse | 3 pages : garde stockage sans kWc / héros+avant-après / récap+étapes |
| 4 | T3 → Synthèse | idem T2 |
| 5 | T2 → + case ROI tranches | tableau tranches en dernière page |
| 6 | T4 → Synthèse | 3 pages : garde pro / rapport / pile+avant-après |
| 7 | T4 → Complet | + tableau 15 ans + récap final |
| 8 | Tous | pas de page blanche, pas de tableau fiscal page financière |
| 9 | Rechargement page | préférences modal conservées (localStorage) |
| 10 | Écran (sans imprimer) | strictement identique à avant (synth cachée, modal fermé) |
| 11 | Export JSON T1 et T4 | fichiers valides, tranches remplies/vides selon sortie |

- [ ] **Step 3 : Corrections éventuelles + commit final + push**

```bash
git add calculateur-pv-nc.html
git commit -m "fix(print): ajustements suite tests de bout en bout des 3 sorties"
git push origin main
```

---

## Self-Review (fait à l'écriture)

- **Couverture spec** : modal+presets+localStorage (T2), 3 sorties (T3/T4/T5), dédoublonnage (T1 Step 5 + T3 Step 1 + T4 Step 2), FOLIO (T6), moins de papier (3 pages vérifiées T7). ✅
- **Bug bonus corrigé** : titre garde T2/T3 jamais actif (`tab` absent de `lastStudyData`) — T1 Step 1. ✅
- **Cohérence des noms** : `tabActif`/`sortieActive`/`PRINT_CFG`/`pmPrint`/`renderBatSynth`/`buildStudyJSON` utilisés de façon uniforme entre tâches. ✅
- **Points de vigilance signalés dans les steps** : signatures `buildAmort`, noms `newReinjAn`/`newInjAn` (grep avant insertion).

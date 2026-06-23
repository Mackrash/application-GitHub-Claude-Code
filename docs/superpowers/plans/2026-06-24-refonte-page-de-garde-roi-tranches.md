# Refonte page de garde + ROI tranche par tranche — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refondre la page de garde PDF (photo sans texte, grand titre déplacé, couche logo+slogan, pied commercial, sans récap) et déplacer le récapitulatif en dernière page avec un ROI présenté tranche fiscale par tranche.

**Architecture:** Tout se passe dans `calculateur-pv-nc.html`. La page de garde est générée par `preparePrint()` dans `#cover-page` (template string avec son propre `<style>`). On édite ce template (Task 1) et on ajoute un nouveau conteneur `#last-page` rempli par `preparePrint`, affiché uniquement à l'impression en fin de document (Task 2). Le ROI par tranche réutilise les fonctions globales `calcDeduction` et `buildAmort` (déjà utilisées par `saveCalcs`).

**Tech Stack:** HTML5, JavaScript vanilla, CSS print (`@media print`), Plotly 2.27 (inchangé), Node.js (vérif syntaxe + encodage base64 du logo).

## Global Constraints

- Fichier cible unique : `calculateur-pv-nc.html`. Plotly 2.27 inchangé.
- Langue FR + accents. Devise XPF, milliers séparés par espace (via `fmt`).
- Charte : orange `#F07020`, anthracite `#333`, blanc. Pas de couleurs froides.
- Polices du PDF (déjà embarquées) : **RAIDenmarkNeo** (logo, valeurs ROI), **SingaporeSling** (grand titre étude), **Nunito** (noms, titres de section de la dernière page, valeurs des cartes récap, textes).
- Changement **impression/PDF uniquement** — ne pas toucher l'affichage écran.
- Montants du récap **sur une seule ligne** (`white-space:nowrap`).
- Portée : page de garde + dernière page s'appliquent à **tous les onglets** ; le **tableau ROI par tranche = particuliers (T1/T2/T3, non-pro)** uniquement ; **T4 (pro)** conserve ses cartes récap actuelles (devis, coût HT après déduction IS, ROI « An X », économie annuelle), **sans** tableau de tranches.
- Vérif syntaxe JS obligatoire après modif.

**Commande VÉRIF SYNTAXE :**
```bash
node -e "const fs=require('fs');const html=fs.readFileSync('calculateur-pv-nc.html','utf8');const m=html.match(/<script>([\s\S]*?)<\/script>/g);if(m){const js=m.map(s=>s.replace(/<\/?script>/g,'')).join('\n');fs.writeFileSync('_check.js',js);}" && node --check _check.js && echo "SYNTAXE OK"
```

---

## File Structure
- **Modify uniquement** : `calculateur-pv-nc.html`
  - Constantes JS (~775) : ajout `LOGO_GROS_B64`.
  - `preparePrint` cover `<style>` (~954-1003) : ajout classes `.cv-bigtitle*`, `.cv-logolayer*`.
  - `preparePrint` cover body (~1018-1083) : retrait overlay photo, remplacement bloc récap par grand titre + couche logo, pied commercial.
  - CSS écran (~193) et print (~406) : règles `#last-page`.
  - HTML body (~766) : conteneur `#last-page`.
  - `preparePrint` (~952 + fin) : construction du contenu de `#last-page` (récap + ROI tranches / variante pro).

---

## Task 1 : Refonte de la page de garde

**Files:**
- Modify: `calculateur-pv-nc.html`

**Interfaces:**
- Produces (global) : `const LOGO_GROS_B64` (base64 du logo+slogan), consommé par le template de la garde.
- Le bloc récapitulatif est **retiré** de la garde (il sera recréé en dernière page par la Task 2).

- [ ] **Step 1 : Générer et insérer la constante base64 du logo+slogan**

Générer la valeur base64 :
```bash
base64 -w0 "Graphique/Logo Orange Gros.png" | head -c 60; echo " ... (longueur: $(base64 -w0 'Graphique/Logo Orange Gros.png' | wc -c))"
```
Puis insérer une constante dans le script. Repérer la ligne :
```js
const BAT_REPL={4800:360000,10650:530000,14336:590000};
```
et ajouter juste après une ligne `const LOGO_GROS_B64="<BASE64>";` où `<BASE64>` est la sortie complète de `base64 -w0 "Graphique/Logo Orange Gros.png"`. Méthode fiable (évite le copier-coller manuel de la longue chaîne) :
```bash
B64=$(base64 -w0 "Graphique/Logo Orange Gros.png")
node -e '
const fs=require("fs");const b64=process.argv[1];
let h=fs.readFileSync("calculateur-pv-nc.html","utf8");
const anchor="const BAT_REPL={4800:360000,10650:530000,14336:590000};";
if(!h.includes(anchor)) throw new Error("ancre BAT_REPL introuvable");
if(h.includes("const LOGO_GROS_B64=")) throw new Error("LOGO_GROS_B64 deja present");
h=h.replace(anchor, anchor+"\nconst LOGO_GROS_B64=\""+b64+"\";");
fs.writeFileSync("calculateur-pv-nc.html",h);
console.log("Inserted LOGO_GROS_B64 ("+b64.length+" chars)");
' "$B64"
```
Attendu : `Inserted LOGO_GROS_B64 (… chars)`.

- [ ] **Step 2 : Retirer l'encart texte sur la photo**

Dans `preparePrint`, supprimer le bloc overlay. Remplacer :
```html
      <div class="cv-photo-overlay">
        <div class="cv-photo-frame">
          <div class="cv-photo-title">ÉTUDE PHOTOVOLTAÏQUE</div>
          <div class="cv-photo-sub">${typeEtude}${kwcStr?' — '+kwcStr:''}</div>
          <div class="cv-photo-badge">Nouvelle-Calédonie</div>
        </div>
      </div>
```
par (chaîne vide — rien). La `.cv-photo-wrap` ne contient alors plus que l'image.

- [ ] **Step 3 : Remplacer le bloc récapitulatif par le grand titre + la couche logo**

Remplacer tout le bloc récap (depuis `<!-- RÉCAPITULATIF DOSSIER -->` jusqu'à son `</div>` fermant, avant `<!-- MENTIONS LÉGALES -->`) :
```html
    <!-- RÉCAPITULATIF DOSSIER -->
    <div class="cv-recap">
      <div class="cv-recap-label">Récapitulatif du dossier</div>
      <div class="cv-kpi-grid">
        <div class="cv-kpi-card">
          <div class="cv-kpi-card-val">${fmt(devis)} F</div>
          <div class="cv-kpi-card-lbl">${isPro?'Total HT du devis':'Montant du devis TTC'}</div>
        </div>
        ${isPro?`<div class="cv-kpi-card">
          <div class="cv-kpi-card-val">${fmt(Math.round(coutNetImpot))} F</div>
          <div class="cv-kpi-card-lbl">Prix HT après déduction fiscale (IS ${tIS}% × ${dAmort} ans)</div>
        </div>`:''}
        <div class="cv-kpi-card green">
          <div class="cv-kpi-card-val">${isPro?(pb?'An '+pb:'> 25 ans'):((pbMin&&pbMax&&pbMin!==pbMax)?pbMin+' à '+pbMax+' ans':(pb?pb+' ans':'—'))}</div>
          <div class="cv-kpi-card-lbl">Retour sur investissement</div>
        </div>
        <div class="cv-kpi-card green">
          <div class="cv-kpi-card-val">${fmt(Math.round(ecoAn))} F</div>
          <div class="cv-kpi-card-lbl">Économie annuelle estimée</div>
        </div>
        ${!isPro?`<div class="cv-kpi-card green">
          <div class="cv-kpi-card-val">${fmt(Math.round(eco15))} F</div>
          <div class="cv-kpi-card-lbl">Économies cumulées sur 15 ans</div>
        </div>`:''}
      </div>
    </div>
```
par :
```html
    <!-- GRAND TITRE (déplacé sous Client/Commercial) -->
    <div class="cv-bigtitle">
      <div class="cv-bigtitle-t1">ÉTUDE PHOTOVOLTAÏQUE</div>
      <div class="cv-bigtitle-t2">${typeEtude}${kwcStr?' — '+kwcStr:''}</div>
      <div class="cv-bigtitle-t3">Nouvelle-Calédonie</div>
    </div>
    <!-- COUCHE LOGO + SLOGAN -->
    <div class="cv-logolayer"><img src="data:image/png;base64,${LOGO_GROS_B64}" alt="Solar Concept" onerror="this.outerHTML='<div class=cv-logolayer-txt>SOLAR CONCEPT</div>'"></div>
```

- [ ] **Step 4 : Pied de page → contact du commercial**

Remplacer, dans `.cv-foot` :
```html
      <div>Votre meilleure source d'énergie &nbsp;|&nbsp; ☎ 47 03 02</div>
```
par :
```html
      <div>${commName?commName+' &nbsp;|&nbsp; ':''}☎ ${commTel||'47 03 02'}${commEmail?' &nbsp;|&nbsp; '+commEmail:''}</div>
```

- [ ] **Step 5 : Ajouter les classes CSS du grand titre et de la couche logo**

Dans le `<style>` du template de la garde, juste avant la ligne `/* ── MENTIONS LÉGALES + PIED ── */`, insérer :
```css
    /* ── GRAND TITRE + COUCHE LOGO ── */
    .cv-bigtitle{padding:1.1cm 1.5cm;text-align:center;border-bottom:1px solid #eee}
    .cv-bigtitle-t1{font-family:'SingaporeSling',sans-serif;font-size:3.23rem;font-weight:400;color:#333;letter-spacing:1px;text-transform:uppercase;line-height:1.05}
    .cv-bigtitle-t2{font-family:'SingaporeSling',sans-serif;font-size:1.62rem;font-weight:400;color:#F07020;margin-top:0.3cm;letter-spacing:1px}
    .cv-bigtitle-t3{font-family:'Nunito',sans-serif;font-size:1rem;color:#777;margin-top:0.2cm;text-transform:uppercase;letter-spacing:3px}
    .cv-logolayer{flex:1;display:flex;align-items:center;justify-content:center;padding:0.8cm 1.5cm}
    .cv-logolayer img{max-width:11cm;max-height:5cm;width:auto;height:auto}
    .cv-logolayer-txt{font-family:'RAIDenmarkNeo',sans-serif;font-size:2.4rem;color:#F07020;letter-spacing:4px;text-transform:uppercase}
```

- [ ] **Step 6 : VÉRIF SYNTAXE + commit**

Run VÉRIF SYNTAXE → `SYNTAXE OK`, puis :
```bash
rm -f _check.js
git add calculateur-pv-nc.html
git commit -m "feat(garde): refonte page de garde (photo sans texte, grand titre, couche logo, pied commercial)"
```

---

## Task 2 : Dernière page — récapitulatif + ROI tranche par tranche

**Files:**
- Modify: `calculateur-pv-nc.html`

**Interfaces:**
- Consumes : `lastStudyData` (devis, ecoAn, eco15, batModel, batQty, commName/Tel/Email via destructuration existante de `preparePrint`, isPro, pb, coutNetImpot, tIS, dAmort, client), `getS()`, `calcDeduction(devis,taux,ded)→{eco}`, `buildAmort(devis,ecoAn,hau,deg,dpv,taux,ded,batRepl,batReplAn)→{pb}`, `TRANCHES_NC`, `BAT_REPL`, `fmt`, `dateStr`.
- Produces : conteneur DOM `#last-page` rempli à l'impression.

- [ ] **Step 1 : Conteneur `#last-page` dans le body**

Repérer la fin du contenu (après l'onglet Paramètres), la ligne :
```html
  <p style="color:var(--tx2);font-size:.72rem;margin-top:10px">Tarifs EEC 2024 — Nouméa, NC. Résultats estimatifs non contractuels.</p>
</div>
```
Insérer juste après ce `</div>` (qui ferme l'onglet Paramètres), sur une nouvelle ligne :
```html

<div id="last-page" style="display:none"></div>
```

- [ ] **Step 2 : Règle CSS écran (cacher #last-page)**

Repérer :
```css
#cover-page{display:none}
```
Remplacer par :
```css
#cover-page{display:none}
#last-page{display:none}
```

- [ ] **Step 3 : Règle CSS print (afficher #last-page en dernière page)**

Repérer, dans `@media print` :
```css
  /* ── PAGE DE GARDE ── */
  #cover-page{display:block!important;break-after:page;margin:0;padding:0}
```
Remplacer par :
```css
  /* ── PAGE DE GARDE ── */
  #cover-page{display:block!important;break-after:page;margin:0;padding:0}
  #last-page{display:block!important;break-before:page;margin:0;padding:0}
```

- [ ] **Step 4 : Construire le contenu de #last-page dans `preparePrint`**

Repérer la ligne (juste avant la fermeture du template de la garde et le bloc `if(!noPrint){`) :
```js
  </div>`;

  if(!noPrint){
```
Remplacer par (insère la construction de `#last-page` entre le template garde et le bloc print) :
```js
  </div>`;

  // ===== DERNIÈRE PAGE : RÉCAPITULATIF + ROI =====
  const s=getS();
  const batRepl=batModel>0?BAT_REPL[batModel]*batQty:0;
  const batReplAn=batModel>0?s.bat_repl:0;

  // Cartes récap (variante pro / particulier)
  const recapCards=isPro?`
        <div class="lp-kpi"><div class="lp-kpi-v">${fmt(devis)} F</div><div class="lp-kpi-l">Total HT du devis</div></div>
        <div class="lp-kpi"><div class="lp-kpi-v">${fmt(Math.round(coutNetImpot))} F</div><div class="lp-kpi-l">Prix HT après déduction fiscale (IS ${tIS}% × ${dAmort} ans)</div></div>
        <div class="lp-kpi green"><div class="lp-kpi-v">${pb?'An '+pb:'> '+s.dpv+' ans'}</div><div class="lp-kpi-l">Retour sur investissement</div></div>
        <div class="lp-kpi green"><div class="lp-kpi-v">${fmt(Math.round(ecoAn))} F</div><div class="lp-kpi-l">Économie annuelle estimée</div></div>`:`
        <div class="lp-kpi"><div class="lp-kpi-v">${fmt(devis)} F</div><div class="lp-kpi-l">Montant du devis TTC</div></div>
        <div class="lp-kpi green"><div class="lp-kpi-v">${fmt(Math.round(ecoAn))} F</div><div class="lp-kpi-l">Économie annuelle estimée</div></div>
        <div class="lp-kpi green"><div class="lp-kpi-v">${fmt(Math.round(eco15))} F</div><div class="lp-kpi-l">Économies cumulées sur 15 ans</div></div>`;

  // Section ROI : tranche par tranche (particuliers) — sinon rien (pro garde son ROI dans les cartes)
  let roiSection='';
  if(!isPro){
    const trRows=TRANCHES_NC.map(t=>{
      const ded=calcDeduction(devis,t.taux,s.ded);
      const amort=buildAmort(devis,ecoAn,s.hau,s.deg,s.dpv,t.taux,s.ded,batRepl,batReplAn);
      const coutNet=devis-ded.eco;
      const roi=amort.pb?amort.pb+' ans':'> '+s.dpv+' ans';
      return {label:t.label,eco:ded.eco,coutNet,roi};
    });
    const lastIdx=trRows.length-1;
    const body=trRows.map((r,i)=>`<tr${i===lastIdx?' class="best"':''}><td class="tr">${r.label}</td><td>${r.eco>0?fmt(Math.round(r.eco))+' F':'—'}</td><td>${fmt(Math.round(r.coutNet))} F</td><td class="roi">${r.roi}</td></tr>`).join('');
    roiSection=`
      <h2 class="lp-h2">Retour sur investissement selon votre tranche fiscale</h2>
      <table class="lp-roi">
        <thead><tr><th>Tranche d'imposition</th><th>Déduction fiscale</th><th>Coût net après déduction</th><th>Retour sur investissement</th></tr></thead>
        <tbody>${body}</tbody>
      </table>
      <div class="lp-note">Le retour sur investissement dépend de votre tranche marginale d'imposition : plus elle est élevée, plus la déduction fiscale réduit le coût net et accélère l'amortissement.</div>`;
  }

  document.getElementById('last-page').innerHTML=`
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap');
    .lp{font-family:'Nunito',sans-serif;color:#333;-webkit-print-color-adjust:exact;print-color-adjust:exact}
    .lp-head{display:flex;align-items:center;justify-content:space-between;padding:1.2cm 1.5cm 0.6cm;border-bottom:3px solid #F07020}
    .lp-head-logo{font-family:'RAIDenmarkNeo',sans-serif;font-size:1.6rem;font-weight:700;color:#F07020;letter-spacing:3px;text-transform:uppercase}
    .lp-head-logo span{color:#333}
    .lp-head-right{text-align:right;font-size:0.78rem;color:#666;line-height:1.6}
    .lp-head-right strong{color:#333}
    .lp-body{padding:1.1cm 1.5cm}
    .lp-h2{font-family:'Nunito',sans-serif;font-weight:800;font-size:1.4rem;color:#F07020;text-transform:uppercase;letter-spacing:1.5px;border-bottom:2px solid #F07020;padding-bottom:0.2cm;margin:0 0 0.6cm}
    .lp-kpis{display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.5cm;margin-bottom:1.1cm}
    .lp-kpi{background:#FFF8F4;border:1px solid rgba(240,112,32,0.30);border-left:5px solid #F07020;border-radius:7px;padding:0.6cm 0.5cm}
    .lp-kpi.green{background:#F0FBF6;border-left-color:#008040}
    .lp-kpi-v{font-family:'Nunito',sans-serif;font-size:1.55rem;font-weight:900;color:#F07020;line-height:1;white-space:nowrap}
    .lp-kpi.green .lp-kpi-v{color:#008040}
    .lp-kpi-l{font-size:0.72rem;color:#666;text-transform:uppercase;letter-spacing:0.5px;margin-top:0.3cm;font-weight:700}
    .lp-roi{width:100%;border-collapse:collapse;margin-top:0.2cm}
    .lp-roi th,.lp-roi td{padding:9px 11px;border-bottom:1px solid #ececec;text-align:right;font-size:1rem}
    .lp-roi th{background:#F07020;color:#fff;font-weight:800;text-transform:uppercase;font-size:0.78rem;letter-spacing:0.5px}
    .lp-roi th:first-child,.lp-roi td:first-child{text-align:left}
    .lp-roi td.tr{font-weight:800;color:#333}
    .lp-roi td.roi{font-family:'RAIDenmarkNeo',sans-serif;font-weight:700;color:#008040;font-size:1.15rem}
    .lp-roi tr.best td{background:#F0FBF6}
    .lp-note{font-size:0.8rem;color:#888;font-style:italic;margin-top:0.5cm}
    .lp-foot{background:#333;color:#fff;padding:0.35cm 1.5cm;display:flex;justify-content:space-between;align-items:center;font-size:0.7rem;-webkit-print-color-adjust:exact;print-color-adjust:exact;margin-top:auto}
    .lp-foot-brand{font-family:'RAIDenmarkNeo',sans-serif;font-size:1rem;font-weight:700;color:#F07020;letter-spacing:2px;text-transform:uppercase}
    #last-page .lp{min-height:29.7cm;display:flex;flex-direction:column}
  </style>
  <div class="lp">
    <div class="lp-head">
      <div class="lp-head-logo">SOLAR <span>CONCEPT</span></div>
      <div class="lp-head-right"><strong>RÉCAPITULATIF DU DOSSIER</strong><br>${client||'—'} — ${dateStr}</div>
    </div>
    <div class="lp-body">
      <h2 class="lp-h2">Récapitulatif du dossier</h2>
      <div class="lp-kpis">${recapCards}</div>
      ${roiSection}
    </div>
    <div class="lp-foot">
      <div class="lp-foot-brand">Solar Concept</div>
      <div>${commName?commName+' &nbsp;|&nbsp; ':''}☎ ${commTel||'47 03 02'}${commEmail?' &nbsp;|&nbsp; '+commEmail:''}</div>
      <div>${dateStr}</div>
    </div>
  </div>`;

  if(!noPrint){
```

- [ ] **Step 5 : VÉRIF SYNTAXE**

Run VÉRIF SYNTAXE → `SYNTAXE OK`. Puis `rm -f _check.js`.

- [ ] **Step 6 : Vérification manuelle navigateur (aperçu impression)**

Ouvrir `calculateur-pv-nc.html`, calculer sur **T1** puis « 📄 Enregistrer en PDF » → aperçu :
1. **Page 1** : photo sans texte, grand titre « ÉTUDE PHOTOVOLTAÏQUE » sous Client/Commercial, couche logo+slogan, pied = contact commercial, **pas de récap**.
2. **Dernière page** : « Récapitulatif du dossier » (3 cartes sur une ligne) + tableau « Retour sur investissement selon votre tranche fiscale » (5 tranches, 40 % surlignée).
3. Refaire sur **T4** : dernière page = cartes pro (devis, coût HT après déduction IS, ROI An X, économie annuelle), **sans** tableau de tranches.
4. T2/T3 : comme T1 (tableau de tranches). Pages intermédiaires (graphes/tableaux) inchangées.

- [ ] **Step 7 : Commit**

```bash
rm -f _check.js
git add calculateur-pv-nc.html
git commit -m "feat(rapport): récap + ROI tranche par tranche en dernière page (T1/T2/T3), variante pro T4"
```

---

## Self-Review

- **Spec coverage** :
  - Photo conservée sans encart texte → T1 Step 2. ✅
  - Grand titre déplacé sous Client/Commercial, gros, SingaporeSling −5 % → T1 Steps 3+5. ✅
  - Couche logo + slogan (image) → T1 Steps 1+3+5. ✅
  - Pied de page = contact commercial → T1 Step 4 (+ dernière page Step 4). ✅
  - Récap retiré de la garde → T1 Step 3. ✅
  - Récap déplacé en dernière page, montants Nunito 900 sur une ligne → T2 Step 4. ✅
  - ROI tranche par tranche (calcDeduction+buildAmort), 40 % surlignée → T2 Step 4. ✅
  - Polices : titre SingaporeSling, titres section + valeurs récap Nunito, logo/ROI RAIDenmarkNeo → T1 Step 5 + T2 Step 4. ✅
  - T4 : garde + dernière page oui, mais cartes pro sans tableau tranches → T2 Step 4 (branche `isPro`). ✅
- **Placeholder scan** : seule « valeur générée » = `LOGO_GROS_B64` (produit par commande au Step 1, pas un placeholder de code). Tout le reste est du code complet. ✅
- **Cohérence des noms** : `LOGO_GROS_B64`, `#last-page`, classes `.cv-bigtitle*`/`.cv-logolayer*` (garde) et `.lp*` (dernière page) distinctes ; `calcDeduction`/`buildAmort`/`TRANCHES_NC`/`BAT_REPL`/`getS`/`fmt`/`dateStr` existent déjà (utilisés par `saveCalcs`). `commName`/`commTel`/`commEmail`/`isPro`/`pb`/`coutNetImpot`/`tIS`/`dAmort`/`eco15`/`devis`/`ecoAn`/`batModel`/`batQty`/`client` sont déjà destructurés/définis en tête de `preparePrint`. ✅
- **YAGNI** : pas de nouveau calcul, réutilisation des fonctions fiscales existantes. ✅

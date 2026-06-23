# Apport panneaux dédiés à la charge batterie (T2) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Afficher proprement, en T2, ce que les panneaux dédiés apportent à la recharge batterie (carte technique titrée + ligne dédiée dans le bilan mensuel), sans écrêté ni impact financier.

**Architecture:** Modifications dans le fichier unique `calculateur-pv-nc.html` (HTML+JS+CSS inline). On enrichit la boucle batterie de `calcT2` pour exposer la charge mensuelle apportée par le lot dédié (`bCDedieM`) et ses agrégats, on remplace les 3 lignes texte actuelles du récap par une carte titrée rendue au-dessus du bilan, et on ajoute une ligne dédiée à la fonction partagée `renderBilanMensuel`.

**Tech Stack:** HTML5, JavaScript vanilla, Plotly 2.27 (inchangé), Node.js (vérif syntaxe).

## Global Constraints

- Fichier cible unique : `calculateur-pv-nc.html`. Plotly 2.27 inchangé.
- Langue FR + accents ; XPF ; séparateur de milliers = espace (via `fmt`/`fmtD`).
- Charte Solar Concept : orange `#F07020`, anthracite `#333333`, pas de couleurs froides.
- **Bi-thème** : l'appli est sombre à l'écran et claire à l'impression via des variables CSS (`--tx`, `--tx2`, `--or`, `--org`). Tout nouveau visuel DOIT utiliser ces variables (pas de couleur en dur qui casserait le PDF). Conséquence : la mise en valeur se fait en **orange `var(--or)`** (lisible écran + PDF), pas en jaune fixe.
- **T2 uniquement.** Partie technique uniquement. **Aucun** changement des visuels financiers (`g2_mois`, `g2_roi`, `tb2`, `t2_facture`, `k2_fin`). **Aucun** nouveau graphe, **aucune** modif du donut `g2_donut`. L'écrêté n'est plus affiché.
- `prodDedieAn` reste calculé et utilisé par `txAuto` (ligne ~1765) — **ne pas y toucher**.
- Fonctions partagées (`renderBilanMensuel`) : sans la nouvelle donnée, comportement strictement inchangé pour T1/T3.
- Vérif syntaxe JS obligatoire après modif. Commits fréquents ; push différé.

**Commande VÉRIF SYNTAXE :**
```bash
node -e "const fs=require('fs');const html=fs.readFileSync('calculateur-pv-nc.html','utf8');const m=html.match(/<script>([\s\S]*?)<\/script>/g);if(m){const js=m.map(s=>s.replace(/<\/?script>/g,'')).join('\n');fs.writeFileSync('_check.js',js);}" && node --check _check.js && echo "SYNTAXE OK"
```

---

## File Structure

- **Modify uniquement** : `calculateur-pv-nc.html`
  - `calcT2` boucle batterie (~1745-1761) : collecte `bCM`, `bCDedieM` + agrégats.
  - `calcT2` récap (~1786-1791) : suppression des 3 lignes dédiées (dont écrêté).
  - Nouvelle fonction `renderDedieCard` (près de `renderBilanMensuel`, ~903).
  - `renderBilanMensuel` (~872-903) : ligne optionnelle `dedieCharge`.
  - Bloc HTML du bilan T2 (~570-574) : conteneur `t2_dedie_card`.
  - `calcT2` appels de rendu (~1832) : `dedieCharge` + appel `renderDedieCard`.

---

## Task 1 : Apport batterie du lot dédié — données, carte et bilan

**Files:**
- Modify: `calculateur-pv-nc.html`

**Interfaces:**
- Produces (variables locales `calcT2`) : `bCM[]` (charge mensuelle PV principal), `bCDedieM[]` (charge mensuelle apportée par le lot dédié), `bCAn`, `bCDedieAn`, `partDedie`.
- Produces (global) : `renderDedieCard(containerId, data|null)` où `data = {nb, wc, kwc, bCDedieAn, part}`.
- Modifies : `renderBilanMensuel(containerId, rows)` accepte `rows.dedieCharge` (tableau 12 nombres, optionnel).

- [ ] **Step 1 : Collecter `bCM` et `bCDedieM` dans la boucle batterie**

Remplacer (≈ lignes 1745-1761) le bloc :
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
par :
```js
  const batCap=batWh/1000*dod; // kWh utile/jour (DoD appliqué)
  const bChargeM=[],bDischM=[],newReinjM=[],newAchatM=[],lostDedieM=[],bCM=[],bCDedieM=[];
  for(let i=0;i<12;i++){
    const maxMois=batCap*DM[i];                  // capacité cyclable sur le mois
    const bC=Math.min(reinjM[i],maxMois);        // charge depuis réinjection PV principal
    const capRest=Math.max(0,maxMois-bC);        // capacité restante après PV principal
    const bCDedie=Math.min(prodDedieM[i],capRest); // le lot dédié complète la charge
    const lost=prodDedieM[i]-bCDedie;            // surplus dédié écrêté (perdu, non affiché)
    const bTot=bC+bCDedie;                        // charge totale du mois
    const bD=Math.min(bTot,achatM[i]);           // décharge couvre achat nuit
    bChargeM.push(bTot); bDischM.push(bD);
    newReinjM.push(reinjM[i]-bC);                // injection réseau résiduelle (lot dédié ne réinjecte pas)
    newAchatM.push(achatM[i]-bD);                // achat réseau réduit
    lostDedieM.push(lost); bCM.push(bC); bCDedieM.push(bCDedie);
  }
  const lostDedieAn=lostDedieM.reduce((a,b)=>a+b,0);
  const prodDedieAn=prodDedieM.reduce((a,b)=>a+b,0);
  const bCAn=bCM.reduce((a,b)=>a+b,0);
  const bCDedieAn=bCDedieM.reduce((a,b)=>a+b,0);
  const partDedie=(bCAn+bCDedieAn)>0?bCDedieAn/(bCAn+bCDedieAn)*100:0;
```

- [ ] **Step 2 : Retirer les 3 lignes dédiées du récap (dont écrêté)**

Remplacer (≈ lignes 1786-1792) :
```js
    {k:'Économie batterie / an',v:`${fmt(ecoAn)} XPF`,g:true},
    ...(kwcDedie>0?[
      {k:'Panneaux dédiés batterie',v:`${panBatNb} × ${panBatWc} Wc (${fmtD(kwcDedie)} kWc)`},
      {k:'Production dédiée / an',v:`${fmt(prodDedieAn)} kWh`},
      {k:'Dont écrêté (batterie pleine)',v:`${fmt(lostDedieAn)} kWh`,r:true},
    ]:[]),
  ]);
```
par :
```js
    {k:'Économie batterie / an',v:`${fmt(ecoAn)} XPF`,g:true},
  ]);
```

- [ ] **Step 3 : Ajouter la fonction `renderDedieCard`**

Repérer la fin de `renderBilanMensuel` (la ligne `}` qui suit `el.innerHTML=...${tot+'</tbody></table>'}\`;`, ≈ ligne 903) et insérer juste après :
```js
function renderDedieCard(id,d){
  const el=document.getElementById(id);if(!el)return;
  if(!d||!(d.kwc>0)){el.innerHTML='';return;}
  const lbl='color:var(--tx2);font-size:.68rem;text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px';
  const val='font-size:1.05rem;font-weight:800';
  const u='font-size:.7rem;color:var(--tx2);font-weight:600';
  const cell='padding:12px 14px';
  el.innerHTML=`<div style="background:var(--ors);border:1px solid var(--org);border-radius:10px;overflow:hidden;max-width:580px;margin-bottom:8px">
    <div style="background:var(--or);color:#fff;font-weight:800;font-size:.82rem;letter-spacing:.5px;text-transform:uppercase;padding:8px 14px">☀️ Panneaux dédiés → recharge batterie</div>
    <div style="display:grid;grid-template-columns:repeat(3,1fr)">
      <div style="${cell};border-right:1px solid var(--org)"><div style="${lbl}">Lot installé</div><div style="${val};color:var(--tx)">${d.nb} × ${d.wc} Wc</div><div style="${u}">= ${fmtD(d.kwc)} kWc</div></div>
      <div style="${cell};border-right:1px solid var(--org)"><div style="${lbl}">Recharge batterie apportée</div><div style="${val};color:var(--or)">${fmt(d.bCDedieAn)}</div><div style="${u}">kWh/an</div></div>
      <div style="${cell}"><div style="${lbl}">Part de la recharge totale</div><div style="${val};color:var(--tx)">${fmtD(d.part,0)} %</div><div style="${u}">de la charge batterie</div></div>
    </div>
  </div>`;
}
```

- [ ] **Step 4 : Ajouter la ligne « rechargé par panneaux dédiés » à `renderBilanMensuel`**

Remplacer toute la fonction `renderBilanMensuel` (≈ lignes 872-903) :
```js
function renderBilanMensuel(containerId,rows){
  const el=document.getElementById(containerId);if(!el)return;
  const defs=[
    ['Énergie produite (kWh)','prod'],
    ['Besoins énergétiques (kWh)','besoins'],
    ['Autoconsommation (kWh)','autoconso'],
    ['Production injectée batterie (kWh)','batInj'],
    ['Surplus revendu (kWh)','surplus'],
    ['Consommation sur réseau (kWh)','reseau'],
  ];
  const half=start=>{
    let t=`<table class="bc" style="font-size:.72rem;margin-top:8px"><thead><tr><th>Poste</th>`;
    for(let i=start;i<start+6;i++)t+=`<th>${MO[i]}</th>`;
    t+=`</tr></thead><tbody>`;
    defs.forEach(([lbl,key])=>{
      const arr=rows[key];
      t+=`<tr><td>${lbl}</td>`;
      for(let i=start;i<start+6;i++)t+=`<td>${arr?fmt(arr[i]):'—'}</td>`;
      t+=`</tr>`;
    });
    return t+`</tbody></table>`;
  };
  const sum=arr=>arr?arr.reduce((a,b)=>a+b,0):null;
  const totals=[
    ['Production estimée','prod'],['Consommation totale','besoins'],
    ['Autoconsommation solaire','autoconso'],['Consommation batteries','batInj'],
    ['Surplus réinjecté','surplus'],['Consommation réseau','reseau'],
  ];
  let tot=`<table class="bc" style="margin-top:12px;max-width:460px"><tbody>`;
  totals.forEach(([lbl,key])=>{const v=sum(rows[key]);tot+=`<tr><td>${lbl}</td><td><strong>${v==null?'—':fmt(v)+' kWh/an'}</strong></td></tr>`;});
  el.innerHTML=`<div style="overflow-x:auto">${half(0)}${half(6)}</div>${tot+'</tbody></table>'}`;
}
```
par :
```js
function renderBilanMensuel(containerId,rows){
  const el=document.getElementById(containerId);if(!el)return;
  const defs=[
    ['Énergie produite (kWh)','prod'],
    ['Besoins énergétiques (kWh)','besoins'],
    ['Autoconsommation (kWh)','autoconso'],
    ['Production injectée batterie (kWh)','batInj'],
    ['Surplus revendu (kWh)','surplus'],
    ['Consommation sur réseau (kWh)','reseau'],
  ];
  if(rows.dedieCharge)defs.splice(4,0,['↳ rechargé par panneaux dédiés (kWh)','dedieCharge','dedie']);
  const cellStyle=cls=>cls==='dedie'?' style="color:var(--or);font-weight:700"':'';
  const half=start=>{
    let t=`<table class="bc" style="font-size:.72rem;margin-top:8px"><thead><tr><th>Poste</th>`;
    for(let i=start;i<start+6;i++)t+=`<th>${MO[i]}</th>`;
    t+=`</tr></thead><tbody>`;
    defs.forEach(([lbl,key,cls])=>{
      const arr=rows[key];
      t+=`<tr${cellStyle(cls)}><td>${lbl}</td>`;
      for(let i=start;i<start+6;i++)t+=`<td>${arr?fmt(arr[i]):'—'}</td>`;
      t+=`</tr>`;
    });
    return t+`</tbody></table>`;
  };
  const sum=arr=>arr?arr.reduce((a,b)=>a+b,0):null;
  const totals=[
    ['Production estimée','prod'],['Consommation totale','besoins'],
    ['Autoconsommation solaire','autoconso'],['Consommation batteries','batInj'],
    ['Surplus réinjecté','surplus'],['Consommation réseau','reseau'],
  ];
  if(rows.dedieCharge)totals.splice(4,0,['↳ rechargé par panneaux dédiés','dedieCharge','dedie']);
  let tot=`<table class="bc" style="margin-top:12px;max-width:460px"><tbody>`;
  totals.forEach(([lbl,key,cls])=>{const v=sum(rows[key]);tot+=`<tr${cellStyle(cls)}><td>${lbl}</td><td><strong>${v==null?'—':fmt(v)+' kWh/an'}</strong></td></tr>`;});
  el.innerHTML=`<div style="overflow-x:auto">${half(0)}${half(6)}</div>${tot+'</tbody></table>'}`;
}
```

- [ ] **Step 5 : Ajouter le conteneur de la carte dans le bloc HTML du bilan T2**

Remplacer (≈ lignes 570-574) :
```html
    <div class="ps ps-table">
      <span class="ps-label">Bilan énergétique mensuel</span>
      <div class="st">Bilan énergétique mensuel</div>
      <div class="tw" id="t2_bilan"></div>
    </div>
```
par :
```html
    <div class="ps ps-table">
      <div id="t2_dedie_card"></div>
      <span class="ps-label">Bilan énergétique mensuel</span>
      <div class="st">Bilan énergétique mensuel</div>
      <div class="tw" id="t2_bilan"></div>
    </div>
```

- [ ] **Step 6 : Câbler les rendus dans `calcT2`**

Repérer l'appel (≈ ligne 1832) :
```js
  renderBilanMensuel('t2_bilan',{prod:prodM2,besoins:consoM,autoconso:autoconsoDirecteM,batInj:bDischM,surplus:newReinjM,reseau:newAchatM});
```
le remplacer par :
```js
  renderBilanMensuel('t2_bilan',{prod:prodM2,besoins:consoM,autoconso:autoconsoDirecteM,batInj:bDischM,surplus:newReinjM,reseau:newAchatM,dedieCharge:kwcDedie>0?bCDedieM:undefined});
  renderDedieCard('t2_dedie_card',kwcDedie>0?{nb:panBatNb,wc:panBatWc,kwc:kwcDedie,bCDedieAn,part:partDedie}:null);
```

- [ ] **Step 7 : VÉRIF SYNTAXE**

Run la commande VÉRIF SYNTAXE (Global Constraints).
Expected: `SYNTAXE OK`. Puis `rm -f _check.js`.

- [ ] **Step 8 : Vérification manuelle navigateur**

Ouvrir `calculateur-pv-nc.html`, onglet « 🔋 Batterie + données » :
1. « Panneaux dédiés batterie — nombre » = 0 → CALCULER : aucune carte, le bilan n'a PAS de ligne « rechargé par panneaux dédiés », et plus aucune ligne « Production dédiée » / « écrêté » dans le récap. Résultat identique à avant.
2. nombre = 10, Wc = 450 → CALCULER : la **carte** « ☀️ Panneaux dédiés → recharge batterie » s'affiche au-dessus du bilan (Lot 10 × 450 = 4,5 kWc · Recharge batterie apportée en kWh/an · Part %). Le **bilan** affiche une ligne orange « ↳ rechargé par panneaux dédiés » (mensuel + total). Aucun « écrêté ». Aucune erreur console.
3. Cliquer « 📄 Enregistrer en PDF » → la carte et la ligne du bilan apparaissent (lisibles sur fond blanc).
4. Onglets T1 et T3 : leur bilan mensuel est inchangé (pas de ligne dédiée).

- [ ] **Step 9 : Commit**

```bash
rm -f _check.js
git add calculateur-pv-nc.html
git commit -m "feat(T2): carte + bilan de l'apport des panneaux dédiés à la charge batterie"
```

---

## Self-Review

- **Spec coverage** :
  - Carte titrée (Lot installé / Recharge batterie apportée / Part) → Steps 3, 5, 6. ✅
  - Bilan : ligne « ↳ rechargé par panneaux dédiés » sous batterie → Steps 4, 6. ✅
  - Données `bCDedieM`/`bCDedieAn`/`partDedie` → Step 1. ✅
  - Suppression des 3 lignes récap + écrêté → Step 2. ✅
  - Pas de nouveau graphe, pas de donut, pas de financier → aucune étape n'y touche. ✅
  - `prodDedieAn`/`txAuto` intacts → non modifiés. ✅
  - T1/T3 inchangés : `renderBilanMensuel` sans `dedieCharge` garde exactement l'ancien rendu (defs/totals non splicés, `cellStyle(undefined)` = ''). ✅
- **Placeholder scan** : aucune (tout le code est fourni). ✅
- **Cohérence des noms** : `bCDedieM`/`bCDedieAn`/`partDedie`/`renderDedieCard`/`dedieCharge`/`t2_dedie_card` cohérents entre Steps 1, 3, 4, 5, 6. La clé du bilan `dedieCharge` est lue via `rows[key]` (key=`'dedieCharge'`). ✅
- **Bi-thème** : carte et ligne bilan en `var(--or)`/`var(--ors)`/`var(--org)`/`var(--tx)` → lisibles écran + PDF. ✅
- **YAGNI** : pas de prix/gain XPF, pas de graphe supplémentaire. ✅

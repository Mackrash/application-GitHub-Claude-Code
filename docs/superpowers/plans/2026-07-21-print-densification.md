# Densification des sorties imprimables — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Supprimer les demi-pages vides des PDF : flux de blocs tassé (plus de saut de page forcé intra-contenu) + graphes qui s'agrandissent selon le nombre de sections cochées.

**Architecture:** Tout dans `calculateur-pv-nc.html`. Levier 1 = CSS (`@media print`) : on retire les `break-before/after:page` des blocs de contenu (garde et dernière page gardent les leurs). Levier 2 = JS dans les hooks `window.onbeforeprint`/`onafterprint` existants : on pilote la hauteur des graphes lignes/barres via `Plotly.relayout({height})` selon le nombre de graphes visibles ; pour que le JS prime, on retire les hauteurs CSS `!important` de ces graphes. Le donut/pile garde sa hauteur CSS fixe.

**Tech Stack:** HTML5, JS vanilla, CSS print, Plotly 2.27 (`responsive:true`), Node.js (vérif syntaxe + script de mesure de remplissage via pdftoppm).

## Global Constraints

- Fichier cible unique : `calculateur-pv-nc.html`. Langue FR + accents. Charte orange `#F07020`.
- **Calculs INTOUCHÉS** : `tests/test_t1_monotonie.js`, `tests/test_t2_monotonie.js`, `tests/test_export_json.js` doivent rester PASS.
- **Page de garde (`#cover-page`) et dernière page (`#last-page`) INTOUCHÉES** : leurs sauts de page (`break-after`/`break-before`) restent.
- Cible remplissage : aucune page de contenu (hors garde/dernière) < 70 % de pixels non-blancs.
- Branche `main` uniquement, push `git push origin main`. Jamais master, jamais rebase.
- **Fichier de 3,9 Mo avec une ligne base64 géante** : ne JAMAIS le lire en entier — grep/sed ciblés, Edit avec ancres uniques.
- Vérif syntaxe JS obligatoire après chaque modif.

**Commande VÉRIF SYNTAXE :**
```bash
node -e "const fs=require('fs');const html=fs.readFileSync('calculateur-pv-nc.html','utf8');const m=html.match(/<script>([\s\S]*?)<\/script>/g);if(m){const js=m.map(s=>s.replace(/<\/?script>/g,'')).join('\n');fs.writeFileSync('_check.js',js);}" && node --check _check.js && echo "SYNTAXE OK" && rm -f _check.js
```

**Rappel ancres (état actuel, vérifier par grep) :**
- Sauts forcés à retirer : `.ps-financial{break-before:page;break-after:page;...}` (~l.302), `.ps-table{break-before:page;...}` (~l.328), `.ps-page2{break-after:page;...}` (~l.285), overrides T4 `#r4 .ps-table{break-before:auto!important}` (~l.405) et `#r4 .ps-page2{break-after:auto!important}` (~l.409) deviennent inutiles.
- Hauteurs CSS `!important` à retirer (Levier 2) : `.ps-financial [id$="_mois"],.ps-financial [id$="_mois_eco"]{height:210px!important;...}` (~l.303), `.ps-financial [id$="_roi"]{height:195px!important}` (~l.305), `.ps-roi [id$="_roi"]{height:210px!important}` (~l.326). NE PAS toucher `.ps-donut [id$="_donut"]{height:260px!important}` (~l.296).
- Hooks : `window.onbeforeprint=function(){...}` (~l.2953), `window.onafterprint=function(){...}` (~l.2977).
- Hauteurs inline écran des graphes : `_donut` 340px, `_mois`/`_mois_eco` 310/340px, `_roi` 270px.

---

## File Structure
- **Modify** : `calculateur-pv-nc.html` (CSS print + hooks JS onbeforeprint/onafterprint).
- **Create** : `tests/mesure-remplissage.js` (outil de mesure du taux de remplissage d'un PDF).

---

## Task 1 : Outil de mesure du remplissage + baseline

**Files:**
- Create: `tests/mesure-remplissage.js`

**Interfaces:**
- Produces : `node tests/mesure-remplissage.js <PDF> [--seuil=70] [--skip=1,N]` → tableau par page (taux de pixels non-blancs %), exit 0 si toutes les pages de contenu ≥ seuil, exit 1 sinon.

- [ ] **Step 1 : Écrire le script de mesure**

Create `tests/mesure-remplissage.js` :
```js
// Mesure le taux de remplissage (pixels non-blancs) de chaque page d'un PDF.
// Rend chaque page en PGM (P5, niveaux de gris) via pdftoppm et compte les pixels sombres.
// Usage : node tests/mesure-remplissage.js <fichier.pdf> [--seuil=70] [--skip=1,5]
//   --seuil : % minimal de remplissage exigé sur une page de contenu (défaut 70)
//   --skip  : numéros de pages 1-indexés à ignorer (garde, dernière page)
const {execFileSync}=require('child_process');
const fs=require('fs'),os=require('os'),path=require('path');

const args=process.argv.slice(2);
const pdf=args.find(a=>!a.startsWith('--'));
if(!pdf||!fs.existsSync(pdf)){console.error('PDF introuvable. Usage: node tests/mesure-remplissage.js <fichier.pdf> [--seuil=70] [--skip=1,5]');process.exit(2);}
const seuil=parseFloat((args.find(a=>a.startsWith('--seuil='))||'--seuil=70').split('=')[1]);
const skip=new Set(((args.find(a=>a.startsWith('--skip='))||'--skip=').split('=')[1]||'').split(',').filter(Boolean).map(Number));

// Parse un PGM binaire P5 → {white, dark} en comptant les octets < 245 (encre).
function tauxPGM(buf){
  // En-tête ASCII : "P5" <ws> width <ws> height <ws> maxval <un seul ws> puis données.
  let pos=2,fields=[];
  function skipWs(){while(pos<buf.length){const c=buf[pos];if(c===0x23){while(pos<buf.length&&buf[pos]!==0x0a)pos++;} else if(c===0x20||c===0x09||c===0x0a||c===0x0d){pos++;} else break;}}
  while(fields.length<3){skipWs();let s=pos;while(pos<buf.length&&buf[pos]>0x20)pos++;fields.push(parseInt(buf.toString('ascii',s,pos),10));}
  pos++; // le seul whitespace après maxval
  let total=0,dark=0;
  for(let k=pos;k<buf.length;k++){total++;if(buf[k]<245)dark++;}
  return total?dark/total*100:0;
}

const dir=fs.mkdtempSync(path.join(os.tmpdir(),'remplissage-'));
try{
  const nb=parseInt(execFileSync('pdfinfo',[pdf]).toString().match(/Pages:\s+(\d+)/)[1],10);
  let allOK=true;
  console.log('Page | Remplissage | Verdict');
  for(let page=1;page<=nb;page++){
    const base=path.join(dir,'p'+page);
    execFileSync('pdftoppm',['-gray','-r','50','-f',String(page),'-l',String(page),pdf,base]);
    const pgm=fs.readdirSync(dir).map(f=>path.join(dir,f)).find(f=>f.startsWith(base)&&f.endsWith('.pgm'));
    const pct=Math.round(tauxPGM(fs.readFileSync(pgm))*10)/10;
    const ignored=skip.has(page);
    const ok=ignored||pct>=seuil;
    if(!ok)allOK=false;
    console.log(`${String(page).padStart(4)} | ${String(pct).padStart(9)}% | ${ignored?'(ignorée)':(ok?'OK':'❌ < '+seuil+'%')}`);
  }
  console.log(allOK?'\nREMPLISSAGE OK ✅':'\nREMPLISSAGE INSUFFISANT ❌');
  process.exit(allOK?0:1);
}finally{
  fs.rmSync(dir,{recursive:true,force:true});
}
```
Note : `pdftoppm -gray` produit un `.pgm` (P5). Si sur cette machine il produit un `.ppm` (P6, 3 octets/pixel), adapter `tauxPGM` pour lire 3 octets par pixel et moyenner — vérifier l'extension générée au Step 2.

- [ ] **Step 2 : Vérifier le script sur un PDF de référence (baseline « avant »)**

Run :
```bash
node tests/mesure-remplissage.js "/home/tony-linux/Documents/Synology/Syno Clients/CLIENTS/DOSSIER A TRAITER/SOUNOU Betty Batterie/SOUNOU Betty 21-07-2026.pdf" --skip=1,5
```
Expected : un tableau à 5 lignes ; les pages 3 et 4 doivent ressortir **< 70 %** (baseline du gaspillage). Si `pdftoppm -gray` sans `-png` ne produit pas de `.pgm`, adapter la génération (certaines versions produisent `.ppm` : lire alors 3 octets/pixel et moyenner). Le script doit tourner sans exception et afficher des pourcentages plausibles (garde ~30-50 %, page vide ~35 %).

- [ ] **Step 3 : Commit**

```bash
git add tests/mesure-remplissage.js
git commit -m "test(print): outil de mesure du taux de remplissage des pages PDF (baseline gaspillage)"
git push origin main
```

---

## Task 2 : Levier 1 — flux libre (suppression des sauts de page forcés)

**Files:**
- Modify: `calculateur-pv-nc.html`

**Interfaces:**
- Consumes : rien. Produces : blocs de contenu qui se tassent au fil des pages ; garde/dernière page inchangées.

- [ ] **Step 1 : Retirer les sauts forcés de `.ps-financial`**

Repérer par grep `.ps-financial{break-before:page`. Remplacer :
```css
  .ps-financial{break-before:page;break-after:page;break-inside:auto}
```
par :
```css
  .ps-financial{break-inside:auto}
```

- [ ] **Step 2 : Retirer le saut de `.ps-table`**

Remplacer :
```css
  .ps-table{break-before:page;break-inside:auto;margin-top:0}
```
par :
```css
  .ps-table{break-inside:auto;margin-top:0}
```

- [ ] **Step 3 : Retirer le saut de `.ps-page2`**

Remplacer :
```css
  .ps-page2{break-after:page;break-inside:auto}
```
par :
```css
  .ps-page2{break-inside:auto}
```
La règle `body.psoff-gfact.psoff-groi .ps-page2{break-after:auto}` (~l.299) devient sans effet mais inoffensive — la laisser.

- [ ] **Step 4 : Neutraliser les overrides T4 devenus inutiles**

Les règles `#r4 .ps-table{break-before:auto!important}` et `#r4 .ps-page2{break-after:auto!important}` et `body.print-C.psoff-amort #r4 .ps-charts{break-before:auto}` ne cassent rien mais visent des sauts désormais absents. Les LAISSER en place (aucun risque) — ne pas les supprimer pour limiter la surface de modif.

- [ ] **Step 5 : Filet anti-coupure sur les blocs qui pourraient se scinder**

Pour éviter qu'un graphe ou un tableau soit coupé en deux entre 2 pages, s'assurer que les conteneurs portent `break-inside:avoid`. Repérer la règle `.ps-financial [id$="_mois"]...` — ajouter une règle juste après le bloc `.ps-donut [id$="_donut"]{...}` (~l.296) :
```css
  /* Densification : blocs graphes/tableaux non coupés entre 2 pages */
  div[id^="g1_"],div[id^="g2_"],div[id^="g3_"],div[id^="g4_"]{break-inside:avoid!important}
  .tw{break-inside:avoid}
```
(`.row` et `.efy-box` ont déjà `break-inside:avoid`.)

- [ ] **Step 6 : VÉRIF SYNTAXE + test manuel léger**

VÉRIF SYNTAXE → `SYNTAXE OK` (ce sont des lignes CSS, mais on relance la vérif par principe).
Test manuel (aperçu navigateur) : imprimer T2 preset Complet → les blocs se tassent, plus de page à moitié vide entre financier / factures / bilan. Garde et dernière page toujours sur leurs pages dédiées.

- [ ] **Step 7 : Commit**

```bash
git add calculateur-pv-nc.html
git commit -m "feat(print): flux libre — suppression des sauts de page forcés, les blocs se tassent"
git push origin main
```

---

## Task 3 : Levier 2 — graphes élastiques (hauteur pilotée en JS)

**Files:**
- Modify: `calculateur-pv-nc.html`

**Interfaces:**
- Consumes : hooks `onbeforeprint`/`onafterprint`.
- Produces : à l'impression, les graphes lignes/barres (`_mois`, `_mois_eco`, `_roi`) prennent une hauteur fonction de leur nombre visible ; restaurés après impression.

- [ ] **Step 1 : Retirer les hauteurs CSS `!important` des graphes lignes/barres**

Ces `!important` battraient la hauteur inline posée par Plotly → il faut les retirer pour que le JS pilote. Repérer et remplacer.

Remplacer :
```css
  .ps-financial [id$="_mois"],.ps-financial [id$="_mois_eco"]{height:210px!important;margin-top:32pt!important}
```
par :
```css
  .ps-financial [id$="_mois"],.ps-financial [id$="_mois_eco"]{margin-top:32pt!important}
```
Remplacer :
```css
  .ps-financial [id$="_roi"]{height:195px!important}
```
par (supprimer la ligne entière, plus rien à styler ici) :
```css
```
Remplacer :
```css
  .ps-roi [id$="_roi"]{height:210px!important}
```
par (supprimer la ligne entière) :
```css
```
NE PAS toucher `.ps-donut [id$="_donut"]{height:260px!important;overflow:hidden!important}` (le donut/pile garde son ratio).

- [ ] **Step 2 : Ajouter le dimensionnement adaptatif dans `onbeforeprint`**

Repérer dans `window.onbeforeprint` la ligne `setPrintLabels();`. Juste AVANT elle, insérer :
```js
  // ── Densification : hauteur des graphes lignes/barres selon leur nombre visible ──
  var bigCharts=[].slice.call(document.querySelectorAll('[id$="_mois"],[id$="_mois_eco"],[id$="_roi"]'))
    .filter(function(el){return el.offsetParent!==null && el._fullLayout;});
  var hFill=bigCharts.length<=1?380:(bigCharts.length===2?300:240);
  bigCharts.forEach(function(el){
    if(!el.hasAttribute('data-h0'))el.setAttribute('data-h0',Math.round(el._fullLayout.height));
    try{Plotly.relayout(el,{height:hFill});}catch(e){}
  });
```

- [ ] **Step 3 : Restaurer les hauteurs dans `onafterprint`**

Repérer dans `window.onafterprint` la boucle de restauration des marges `_roi` (la dernière `document.querySelectorAll('[id$="_roi"]')`). Juste APRÈS cette boucle (avant le `};` de fin de fonction), insérer :
```js
  // Restaure les hauteurs d'origine des graphes densifiés
  document.querySelectorAll('[data-h0]').forEach(function(el){
    var h0=parseInt(el.getAttribute('data-h0'),10);
    if(h0&&el._fullLayout){try{Plotly.relayout(el,{height:h0});}catch(e){}}
    el.removeAttribute('data-h0');
  });
```

- [ ] **Step 4 : VÉRIF SYNTAXE + tests calculs**

```bash
# VÉRIF SYNTAXE (voir Global Constraints) → SYNTAXE OK
node tests/test_t1_monotonie.js | tail -1   # PASS
node tests/test_t2_monotonie.js | tail -1   # PASS
node tests/test_export_json.js | tail -1    # PASS
```

- [ ] **Step 5 : Test manuel + mesure**

Test navigateur : imprimer T1 preset Synthèse (peu de graphes → grands) puis T2 Complet (plusieurs graphes → plus compacts). Aucun graphe coupé, aucune demi-page vide. Vérifier qu'après fermeture du dialogue d'impression, l'affichage écran est **strictement identique** (hauteurs restaurées, pas de graphe géant à l'écran).

- [ ] **Step 6 : Commit**

```bash
git add calculateur-pv-nc.html
git commit -m "feat(print): graphes élastiques — hauteur adaptée au nombre de graphes visibles, restaurée après impression"
git push origin main
```

---

## Task 4 : Vérification finale de bout en bout

**Files:**
- Modify (si calibration) : `calculateur-pv-nc.html`

- [ ] **Step 1 : VÉRIF SYNTAXE + 3 tests calculs** → tous PASS/OK.

- [ ] **Step 2 : Mesure sur PDF réels (avec Tony)**

Tony imprime les 6 combinaisons (T1, T2/T3, T4 × Synthèse/Complet) et fournit les PDF. Pour chacun :
```bash
node tests/mesure-remplissage.js "<chemin PDF>" --skip=1,<derniere_page>
```
Cible : `REMPLISSAGE OK ✅` (aucune page de contenu < 70 %). Comparer au baseline « avant » de Task 1.

- [ ] **Step 3 : Calibration éventuelle de la table de hauteurs**

Si une page reste < 70 % ou si un graphe déborde : ajuster les valeurs `hFill` (Task 3 Step 2 : 380/300/240) et/ou re-tasser. Re-mesurer. Itérer jusqu'à la cible.

- [ ] **Step 4 : Commit final éventuel**

```bash
git add calculateur-pv-nc.html
git commit -m "fix(print): calibration hauteurs de graphes suite mesures de remplissage"
git push origin main
```

---

## Self-Review (fait à l'écriture)

- **Couverture spec** : Levier 1 (Task 2), Levier 2 (Task 3), vérif objective (Task 1 outil + Task 4 mesure). ✅
- **Interaction CSS !important vs Plotly inline** : identifiée (Task 3 Step 1 retire les !important sinon le JS ne prendrait pas). ✅
- **Restauration écran** : data-h0 stashé/restauré (Task 3 Step 3) car un `relayout({height})` persiste hors media print, contrairement aux anciennes règles CSS media-scoped. ✅
- **Garde/dernière page** : sauts conservés (Global Constraints + Task 2 ne les touche pas). ✅
- **Point de vigilance** : la génération PGM par pdftoppm (Task 1) peut varier selon la version — Step 2 prévoit le fallback PPM (3 octets/pixel).

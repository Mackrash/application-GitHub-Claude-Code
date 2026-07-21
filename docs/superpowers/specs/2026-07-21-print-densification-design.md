# Spec — Densification des sorties imprimables (zéro demi-page vide)

**Date** : 21/07/2026
**Fichier cible** : `calculateur-pv-nc.html`
**Contexte** : suite de la feature « sorties imprimables sélectives » (specs/plans du 20/07).

## Problème

Les PDF laissent trop de blanc. Mesuré sur l'étude Betty SOUNOU (T2, preset Complet, 5 pages) :
la page « impact financier » (1 graphe seul) est vide à ~65 %, l'estimation factures à ~55 %,
le récap dossier à ~40 %. Cause racine double :

1. **Sauts de page forcés** : chaque bloc print (`.ps-financial`, `.ps-table`, `.ps-page2`)
   porte `break-before:page`/`break-after:page` → il occupe **seul** sa page, d'où les
   demi-pages vides.
2. **Graphes à hauteur fixe** (210px, 195px…) : un graphe seul sur sa page ne grandit pas.

## Objectif (décision Tony 21/07/2026 — option « densifier au max »)

Le PDF le plus court possible, **aucune page < 70 % de remplissage utile**. Les graphes se
calent intelligemment selon les sections cochées et s'agrandissent quand il y a de la place.

## Approche — 2 leviers

### Levier 1 — Flux libre (CSS)
Remplacer les sauts de page forcés intra-contenu par un **flux tassé** :
- Retirer `break-before:page` / `break-after:page` de `.ps-financial`, `.ps-table`, `.ps-page2`
  (et l'override T4 `#r4 .ps-table` / `#r4 .ps-page2`).
- Conserver `break-inside:avoid` sur les blocs atomiques (kpi-grid, recap-box, efy-box, `.row`
  graphes, `.bs-hero`, lignes de tableau) pour qu'aucun bloc ne soit coupé en deux.
- **Conserver** les sauts de la page de garde (`#cover-page{break-after:page}`) et de la
  dernière page (`#last-page{break-before:page}`) : ces deux-là restent des pages dédiées.
Résultat : les blocs légers se tassent, le navigateur ne coupe une page que lorsqu'elle est pleine.

### Levier 2 — Graphes élastiques (JS, dans `onbeforeprint` existant)
Le hook `window.onbeforeprint` relayoute déjà les graphes Plotly (fond blanc, marges). On y
ajoute un passage de **dimensionnement adaptatif** :
- Recenser les graphes **visibles** (non masqués par `psoff-*`/`print-*`) via `offsetParent!==null`.
- Attribuer une hauteur par graphe selon le **nombre de graphes visibles** de la sortie
  (moins de graphes cochés → graphes plus grands) : table de correspondance simple
  (ex. 1 graphe → 360px, 2 → 300px, 3+ → 250px ; pile/donut gardent leur ratio).
- Appliquer via `Plotly.relayout(el,{height})` (déclenche le redimensionnement, Plotly est
  `responsive:true`). `onafterprint` restaure les hauteurs écran d'origine.
- Ce passage cohabite avec les relayouts marges déjà présents (même boucle ou à la suite).

Les hauteurs CSS print fixes (`[id$="_mois"]{height:210px!important}`…) deviennent des
**planchers** ; la valeur JS prime à l'impression.

## Vérification objective

Script `tests/mesure-remplissage.js` (Node, sans navigateur) : prend un PDF, le rend en PNG
via `pdftoppm`, calcule le **taux de pixels non-blancs par page**, et échoue si une page de
contenu (hors garde) est < seuil. Cible : **aucune page de contenu < 70 %**. Complété par le
test visuel de Tony sur les 3 sorties (T1/T2-T3/T4) × 2 presets.

## Hors périmètre

- Aucune modification des **calculs** (les tests batterie/export restent verts).
- Aucune modification de la **page de garde** ni de la **dernière page** (structure et sauts
  conservés).
- Pas de refonte du contenu des sorties (fait le 20/07) : uniquement pagination + tailles.

## Risques

- Un graphe trop agrandi pourrait déborder d'une page → le plancher CSS + `break-inside:avoid`
  et la mesure de remplissage bornent le risque ; on ajuste la table de hauteurs si besoin.
- L'ordre des relayouts dans `onbeforeprint` (marges vs height) : appliquer la height en
  dernier pour que Plotly recalcule les marges dans la bonne taille.

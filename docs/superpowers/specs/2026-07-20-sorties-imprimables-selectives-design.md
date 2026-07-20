# Spec — Sorties imprimables sélectives (3 sorties + panneau d'impression)

**Date** : 20/07/2026
**Fichier cible** : `calculateur-pv-nc.html` (monopage, Plotly 2.27)
**Maquette validée** : `_maquette-sorties-print.html` (gitignorée)

## Problème

La sortie imprimable actuelle est trop fouillie : ~7 pages par étude, avec de fortes
redondances (l'économie annuelle apparaît 5×, le ROI/payback 4×, le tableau fiscal de la
page 3 est un quasi-doublon du tableau ROI de la dernière page). Chaque feature ajoutée a
empilé son bloc sans retirer les anciens. Impossible de choisir ce qui sort.

## Objectifs

1. **Choisir ce qui s'imprime** : panneau au clic sur « 📄 Enregistrer en PDF » avec
   2 presets + cases à cocher fines (option C validée).
2. **3 sorties distinctes** selon l'onglet actif :
   - **Sortie A** — T1 (installation PV complète ± batterie)
   - **Sortie B** — T2 + T3 (ajout d'un système de stockage)
   - **Sortie C** — T4 (étude professionnelle)
3. **Dédoublonner** : chaque donnée n'apparaît qu'à un seul endroit par mode.
4. **Préparer FOLIO** (agent NEXIA) : export JSON structuré de l'étude, sans couplage.

## Principes de design (règle Tony 20/07/2026)

- **Le moins de papier possible** : preset Synthèse = 3 pages, jamais plus. Toute
  section qui ne tient pas fait de la place, pas une page de plus.
- **Réutiliser les designs existants** (KPI cards, recap-box, pile batterie, bandeaux
  orange, page de garde, dernière page) — pas de nouveau langage graphique.
- **Plus fun et plus lisible** : chiffres-clés plus gros (style « héros »), moins de
  lignes de tableau, plus d'air, icônes/émojis existants conservés, couleurs charte
  (orange #F07020 dominant, vert gains, rouge dépenses). Un client doit comprendre
  chaque page en 10 secondes.

## 1. Panneau d'impression (modal)

- Ouvert par le bouton « 📄 Enregistrer en PDF » (le comportement direct actuel disparaît).
- **2 presets** : « Synthèse client » (défaut) / « Dossier complet ».
- **Cases à cocher** par section, adaptées à la sortie (voir §2). Choisir un preset
  coche/décoche automatiquement ; l'utilisateur peut ensuite affiner à la main.
- Page de garde + page synthèse : **toujours incluses** (cases verrouillées).
- Compteur de pages estimé en pied de modal.
- Mémorisation `localStorage` **par sortie** (clés `printPrefs_A`, `printPrefs_B`,
  `printPrefs_C`) : au prochain clic, on retrouve ses dernières cases.
- Boutons : Annuler / 🖨 Imprimer → applique les classes de filtrage puis `preparePrint()`.

## 2. Composition des 3 sorties

### Sortie A — T1, preset Synthèse = 3 pages

| Page | Contenu |
|---|---|
| 1 | Page de garde actuelle (titre « Installation Photovoltaïque — X kWc ») |
| 2 | **Synthèse** : récap installation compacté + 4 KPI financiers (avant/après/éco/gains 20 ans) + **pile répartition énergétique** (`plotPile`, g1_donut) |
| 3 | ROI par tranche fiscale (l'actuelle dernière page `#last-page`) |

Cases optionnelles (preset Complet les coche toutes) :
graphe factures avant/après (g1_mois) · graphe ROI 20 ans (g1_roi) · tableau
d'amortissement (tb1) · estimation factures (t1_facture) · bilan mensuel (t1_bilan).

### Sortie B — T2/T3, preset Synthèse = 3 pages

| Page | Contenu |
|---|---|
| 1 | Page de garde (titre « Ajout d'un système de stockage d'énergie », sans kWc) |
| 2 | **Synthèse batterie** : **économie annuelle en héros** (gros bloc vert) + tableau avant/après batterie (achat réseau, injection, facture, autonomie) + infos batterie (modèle, kWh utiles, couverture, devis, garantie) |
| 3 | Récap dossier (KPI + prochaines étapes) |

- ☐ **ROI par tranche fiscale : décoché par défaut**, cochable.
- Autres cases : graphes (pile, factures), tableau amortissement, bilan mensuel.
- La pile (`plotPile`) reste disponible en option, pas dans le preset Synthèse.

### Sortie C — T4 Pro, preset Synthèse = 3 pages

| Page | Contenu |
|---|---|
| 1 | Page de garde pro (« Solution professionnelle — X kWc ») |
| 2 | Rapport entreprise (r4_rapport, déjà une synthèse) |
| 3 | **Graphes clés** : pile répartition énergétique (`g4_donut`/plotPile) + charges avant/après (`g4_mois_eco`) |

- ☐ **Tableau d'amortissement 15 ans : décoché par défaut**, cochable.
- ☐ Récap final (t4-recap) cochable.

## 3. Dédoublonnage (tous modes)

- **Supprimer le tableau fiscal de la page financière** (`recapX_efy_fiscal`) : la donnée
  ne vit plus que sur la page « ROI par tranche » (`#last-page`).
- **Économie annuelle** : uniquement dans les KPI de synthèse — retirée du récap
  installation et du bloc « Économies annuelles » quand ils font doublon sur le même mode.
- **Factures avant/après** : KPI en synthèse ; graphe mensuel et tableau = options.
- Le récap installation de la page 2 est **compacté** (6-7 lignes max, plus de doublon
  avec les KPI).

## 4. Mécanique technique

- Chaque section imprimable reçoit `data-psec="<nom>"` (recap, pile, financier, roi-graph,
  amort, factures, bilan, fiscal-tranche, rapport, charts-pro, recap-final).
- À l'impression, le JS pose des classes sur `<body>` : `print-A|B|C` + une classe
  `psec-off-<nom>` par section décochée. Le CSS `@media print` masque via ces classes.
- Aucun déplacement de DOM : on garde les wrappers `.ps` existants, on ajuste les
  sauts de page (`break-*`) par sortie.
- Le titre de la page de garde reste géré par `preparePrint()` (déjà correct depuis
  le commit 3d6a181).

## 5. Préparation FOLIO (agent NEXIA)

- Fonction `buildStudyJSON()` : retourne un objet
  `{meta:{date,type:'A|B|C'}, client:{...}, commercial:{...}, installation:{...},
  finances:{...}, mensuel:{...}, tranchesFiscales:[...]}` — les valeurs déjà calculées,
  pas de recalcul.
- Déclenchement : bouton discret « ⚙ Export JSON » dans le modal d'impression →
  télécharge `ETUDE <NOM Prénom> <JJ-MM-AAAA>.json`.
- Aucun couplage réseau : fichier local uniquement, format stable documenté en
  commentaire au-dessus de la fonction.

## 6. Hors périmètre

- Pas de préréglage Enercal (décision Tony 20/07/2026).
- Pas de refonte des calculs (vérifiés sains : piscine T1 = part dédiée de la conso
  saisie ; T2/T3 = formule EEC complète via `factureMois`).
- Pas d'appel réseau vers NEXIA/FOLIO.

## 7. Vérification

- `node --check` sur le JS extrait (commande CLAUDE.md) après chaque modif.
- Test manuel : pour chaque onglet (T1→T4), preset Synthèse puis Complet, aperçu
  d'impression → nombre de pages conforme, aucune section dupliquée, pas de page blanche.
- Les presets mémorisés survivent au rechargement (localStorage).

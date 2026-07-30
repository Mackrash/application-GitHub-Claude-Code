# Refonte de la sortie client — page « L'essentiel »

**Date** : 30 juillet 2026
**Périmètre** : sortie A (particulier, onglets 1 & 2), PDF imprimé prioritaire
**Statut** : design validé, prêt pour plan d'implémentation

---

## 1. Problème

La sortie A actuelle dit trois fois la même chose et se lit mal.

### Redondances constatées

| Information | Endroits où elle apparaît |
|---|---|
| Autoconso 2 699 / batterie 1 800 / réinjection 4 193 kWh | tableau *Bilan énergétique annuel* **+** pile SVG |
| Économie annuelle 213 355 XPF | carte KPI **+** ligne *Total économie annuelle* |
| Production 8 692 kWh | récap installation **+** bilan énergétique |
| 6,3 kWc | récap **+** « 14 × 450 Wc » (même grandeur) |
| Taux autoconso 51,8 % | récap **+** déductible de la pile |
| « Répartition énergétique » | bandeau de section **+** titre interne du graphe |

Les trois cartes *avant / après / économie* sont également redondantes : la troisième est la soustraction des deux premières.

### Défauts de rendu constatés (PDF sortie A, rendu Playwright)

- Page 2 : le pied de page recouvre la ligne *Total économie annuelle*.
- Page 3 : bandeau *Tableau d'amortissement* suivi de ~20 cm de blanc.
- Graphe factures : coupé à Août (Sep→Déc absents), titre rogné par le cadre.
- Graphe « ROI 20 ans » : l'axe s'arrête à 13 ans.
- Libellés KPI en capitales très espacées, cassant sur deux lignes.
- Quatre bandeaux orange pleine largeur : hiérarchie plate.
- Vert et turquoise omniprésents, hors charte Solar Concept.

### Erreur de vocabulaire

`Réinjection réseau (surplus)` affiche 4 193 kWh alors que le tarif de revente est à 0 XPF/kWh. Ces kWh ne sont pas réinjectés : les onduleurs brident, ils **ne sont jamais produits**. Le terme est faux.

---

## 2. Décisions

| Sujet | Décision |
|---|---|
| Périmètre | Sortie A d'abord ; B et C déclinées ensuite |
| Support prioritaire | PDF imprimé (l'écran suit) |
| Structure | Garde (inchangée) → **L'essentiel** (1 page) → options cochées → dernière page |
| Direction graphique | **P2 — éditorial deux colonnes** (P1 typographique conservée comme alternative) |
| Métaphore énergie | Armoire **OMEGA Maestro-G** verticale, proportions réelles (230 × 490) |
| Palette | **A** — orange `#F07020`, ambre `#F5A623`, vert `#35A46B`, gris `#A8ACB1` |
| Vocabulaire | **Réserve de production** (revente = 0) / **Énergie revendue** (revente > 0) |
| Modes | Un seul gabarit ; **seul le récap du bas change** entre installation complète et ajout de batterie |
| Montant du devis | **Absent** de la page de garde, **présent** dans le récap du bas |

---

## 3. La page « L'essentiel »

Format A4 portrait, deux colonnes pleine hauteur.

```
┌──────────────────────────────┬──────────────────┐
│ SOLAR CONCEPT                │ OÙ VA VOTRE      │
│ client · lieu · date         │ ÉNERGIE          │
│                              │ 8 692 kWh/an     │
│ VOUS ÉCONOMISEZ              │                  │
│ 213 355                      │   ┌────────┐     │
│ XPF PAR AN                   │   │  48 %  │     │
│                              │   ├────────┤     │
│ VOTRE FACTURE                │   │  21 %  │     │
│ ▓▓▓▓▓▓▓▓▓ 276 144 XPF        │   ├────────┤     │
│ ▓▓▓ 62 788  −77 %            │   │  31 %  │     │
│                              │   └────────┘     │
│ REMBOURSÉE      An 8         │                  │
│ GAINS 20 ANS    3 980 368    │ │ Réserve 4 193  │
│ AUTONOMIE       100 %        │ │ Nuit    1 800  │
│                              │ │ Jour    2 699  │
│ PROCHAINES ÉTAPES            │                  │
│ 1 Validation      aujourd'hui│ besoin 4 499 kWh │
│ 2 Visite technique  10 jours │ couvert   100 %  │
│ 3 Pose            ½ journée  │ réseau    0 kWh  │
│ ──────────────────────────── │                  │
│ VOTRE INSTALLATION           │                  │
│ 6,3 kWc      14 × 450 Wc     │                  │
│ 14,3 kWh     8 692 kWh/an    │                  │
│ INVESTISSEMENT  1 650 000 XPF│                  │
└──────────────────────────────┴──────────────────┘
   colonne blanche ~117 mm       colonne #F6F7F8
                                       80 mm
```

Les deux colonnes utilisent `justify-content: space-between` : le contenu se répartit sur toute la hauteur, aucun vide résiduel.

### Le bloc énergie (Maestro-G)

Un **SVG unique** contenant à la fois l'armoire et les textes. C'est une contrainte de correction, pas de style : quand la batterie était un SVG et les textes du HTML à côté, l'alignement se rompait au moindre changement d'échelle.

- Armoire : corps 230 × 490, `rx=13`, dégradé **blanc** (`#FFFFFF` → `#E4E5E7`), contour `#A8AAAD`, flanc droit en perspective, écran de contrôle noir décoratif, deux pieds noirs.
- **Aucune donnée dans l'écran LCD** : illisible à cette taille.
- **Aucun logo OMEGA** sur l'armoire.
- Jauge interne : trois segments dont la hauteur est proportionnelle aux kWh.
- **Seuls les pourcentages** sont dans l'armoire ; libellés, valeurs et explications sont à l'extérieur.
- Chaque texte est relié à son segment par une ligne de rappel partant du **centre géométrique** du segment.

Ordre des segments, de haut en bas : réserve (vert) → nuit (ambre) → jour (orange).

### Vocabulaire conditionnel

| Tarif de revente | Libellé | Sous-texte |
|---|---|---|
| 0 XPF/kWh | **Réserve de production** | « vos panneaux savent produire ces kWh en plus — il faut du stockage ou de la consommation pour les capter » |
| 15 ou 21 XPF/kWh | **Énergie revendue** | montant perçu en XPF |

### Récap du bas — deux variantes

**Installation complète** : Puissance · Panneaux · Stockage · Production estimée, puis Investissement.

**Ajout de batterie** : Installation existante · Batterie ajoutée · Gain apporté, puis Investissement.

Le montant n'apparaît **jamais** sur la page de garde.

### Position du récap : toujours en dernier

Le récap **ferme le document**, quels que soient les blocs optionnels cochés.

- Aucune option cochée → le document s'arrête à « L'essentiel », le récap est en bas de cette page.
- Options cochées → les graphes et tableaux s'insèrent **entre** « L'essentiel » et le récap, qui migre en dernière position.

Le récap n'est donc pas ancré à la page 2 : c'est le dernier bloc du flux d'impression. Combiné à la règle « aucun blanc réservé », il remonte naturellement dès qu'une option est décochée.

---

## 3 bis. Les graphiques

Onze pistes ont été maquettées (`_maquettes/graphes.html`, `_maquettes/factures.html`). Deux retenues.

### Facture — « vous n'en payez plus que trois »

Douze pastilles, une par mois. Le nombre de pastilles pleines vaut `12 × factureAprès / factureAvant`,
arrondi pour les accolades, avec la dernière partiellement remplie au prorata.

> Sur vos douze mois d'électricité : **3 mois** que vous payez encore, **9 mois** offerts par le soleil.

Pourquoi cette forme plutôt qu'une courbe : sur un profil de consommation régulier, les douze valeurs
mensuelles sont quasi identiques. Un graphe temporel n'a alors **rien à raconter** — six variantes de
courbes ont été essayées et rejetées pour cette raison. Cette représentation traduit un ratio en durée,
une grandeur que le client manipule tous les jours.

**Formulation obligatoire** : « l'équivalent de trois mois ». Le client paiera bien un peu chaque mois ;
écrire « vous ne payez que 3 mois » serait faux et attaquable.

Cas limites à couvrir : facture après = 0 → 0 pastille pleine ; économie faible → le message reste
honnête même s'il devient peu vendeur ; ne jamais forcer l'arrondi à la hausse.

### Facture — l'écart mois par mois (alternative au choix)

La représentation historique est **conservée** et retravaillée dans la palette validée : deux courbes
splines, la nappe d'économie entre elles, le montant repris sous chaque mois. Rouge `#FF4B6E` → gris
`#A8ACB1` (tirets + diamants), turquoise `#00D4A0` → orange `#F07020` (plein + cercles).

Les deux formes sont **exclusives** et se choisissent dans le panneau d'impression :

| Entrée cochable | Rendu | Par défaut |
|---|---|---|
| Facture — les douze mois | pastilles, ratio exprimé en durée | ✅ |
| Facture — l'écart mois par mois | courbes splines + nappe d'économie | — |

Cocher l'une décoche l'autre. La seconde devient pertinente dès que la consommation est saisonnière
(piscine, climatisation, résidence secondaire) : c'est précisément le cas où les douze pastilles
n'apportent rien de plus que le chiffre annuel.

### ROI — « le relief »

La courbe cumulée devient un versant : creusé sous le zéro (gris), rempli au-dessus (orange).
**Trois jalons seulement** — l'investissement de départ, l'année de bascule, le gain final.
Aucune grille, aucun axe chiffré. Le libellé du premier jalon se place **sous** le point, sinon il
chevauche la courbe.

### Bilan mensuel — optionnel

La piste « flux mensuel » (trois nappes empilées, `E1`) reste disponible pour remplacer le tableau
à treize colonnes, notamment pour les profils saisonniers marqués (piscine, climatisation).
Non retenue pour l'instant.

### Règles générales

- **Aucun histogramme, aucun donut**, quelle que soit la donnée.
- SVG en `width="100%"` avec `viewBox` : une largeur fixe déborde de la colonne à l'impression.
- Palette validée uniquement — pas de rouge ni de turquoise, contrairement aux graphes Plotly actuels
  (`#FF4B6E`, `#00D4A0`), tous deux hors charte.

---

## 4. Contraintes de rendu

- **Aucun gris clair pour le texte.** Les textes secondaires sont en anthracite atténué `#55585C`. Les filets passent de `#EDEEEF` à `#D8DADC`. Le gris clair disparaît à l'impression.
- **Aucune couleur froide** hors le vert de la réserve, explicitement demandé et assumé comme dérogation à la charte Solar Concept.
- **Aucun blanc réservé** : un bloc optionnel non coché ne laisse pas de place vide, les blocs suivants se tassent.
- Contraste suffisant pour une impression noir et blanc.

---

## 5. Suppression des doublons

### Blocs imprimés d'office à supprimer

| Bloc | Motif |
|---|---|
| *Bilan énergétique annuel* (6 lignes) | doublon total avec la Maestro |
| 4 cartes KPI (dépense avant / après / économie / gains) | doublon total avec le héros + les trois chiffres |
| *Récapitulatif installation* | doublon avec le récap du bas |
| Carte « An 8 » sous le graphe ROI | doublon avec « Installation remboursée » |

### Liste cochable

- **Retirer** `pile` (remplacée par la Maestro).
- `tranches` et `amort` deviennent **mutuellement exclusifs** : les deux affichent déduction fiscale et payback par tranche.
- Dans *Économies annuelles générées*, retirer la ligne **Total** (doublon du héros) ; conserver la décomposition autoconso / batterie.
- Conserver `gfact`, `groi`, `factures`, `bilan` : ils apportent la saisonnalité mensuelle et le détail justificatif.

### Incohérence à corriger

La dernière page annonce des **économies cumulées sur 15 ans**, la page « L'essentiel » des **gains sur 20 ans**. Aligner sur **20 ans**.

---

## 6. Hors périmètre

- Sorties B (ajout batterie) et C (entreprise) : déclinaisons ultérieures.
- Page de garde : inchangée.
- Direction P1 (typographique, zéro cadre) : conservée dans `_maquettes/purs.html` comme alternative, non implémentée.
- Moteur de calcul : intact, les calculs sont justes.

---

## 7. Maquettes de référence

Toutes dans `_maquettes/` :

| Fichier | Contenu |
|---|---|
| `purs.html` | **P1 et P2** — les deux directions, P2 est celle retenue |
| `maquette-maestro-g.html` | itérations M3 / M4 du bloc énergie |
| `palettes.html` | les trois palettes, A retenue |
| `page-essentiel.html` | version encadrée intermédiaire (historique) |
| `maquette-energie.html` | premières variantes V1 / V2 / V3 (historique) |

Rendus produits avec Playwright (Chromium headless), captures A4 à `deviceScaleFactor: 2`.

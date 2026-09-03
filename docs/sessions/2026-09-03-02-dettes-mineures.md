# 2026-09-03-02 — Dettes mineures du calculateur

## Objet

Séance courte, après la clôture de la précédente : solder les quatre dettes mineures que la fiche
`2026-09-03-icone-rapport-annote-et-pagination.md` laissait ouvertes.

## Fait

### Import d'image de la sortie C — l'échec ne se voit plus muet

`t4LoadImage()` n'avait ni `rd.onerror` ni `img.onerror`. Le test écrit avant la correction a
montré **pire que l'échec silencieux** : après un import réussi, choisir un fichier illisible
laissait l'image précédente en place. Le commercial croyait avoir changé le logo, et l'ancien
partait à l'impression.

Désormais : message « Fichier illisible : choisissez une image (PNG, JPG) » dans la zone d'aperçu,
image précédente purgée, `input.value` remis à zéro pour permettre de re-choisir le même fichier.
Couvert par `tests/import-image-t4.js` (fichier illisible, image valide, retour à un fichier
illisible après un import réussi).

### Graisses de police — le faux gras est parti

Le `<head>` ne chargeait Nunito qu'en 400, 600 et 700, alors que le document réclame du 500, du 800
(tuiles de la garde, barre de répartition, rapport T4) et du 900 (récapitulatif final). Le
navigateur les synthétisait. Les deux `@import` injectés dans les styles d'impression tentaient de
rattraper le coup, sans couvrir l'écran.

Le lien du `<head>` porte maintenant `400;500;600;700;800;900`, et les deux `@import` redondants
ont disparu. `tests/polices-chargees.js` compare les graisses réclamées par le CSS à celles
réellement déclarées — il échouera au prochain ajout d'une graisse non chargée.

### Code mort retiré

- **`svgMaestro()`** (4,9 ko) : plus aucun appelant depuis le passage à l'illustration de maison.
  Le bloc de `tests/test_sortie_a.js` qui la couvrait n'a pas été supprimé mais **transféré** sur
  `barreFluxHTML()` et `blocsFluxHTML()` : somme des pourcentages à 100, largeurs proportionnelles,
  ordre réserve → nuit → jour, part nulle sans segment fantôme, production nulle qui ne rend rien,
  bascule « Réserve de production » / « Énergie revendue ».
- **Quatre règles CSS** de troncature du tableau T4 (`#amort4_combined`, limite à 15 lignes), sans
  effet depuis que `#r4 .ps-page2` est masquée à l'impression.

## Décidé

- **Une couverture de test ne se supprime pas avec le code qu'elle couvrait.** Les invariants de
  `svgMaestro` valaient pour la répartition elle-même, pas pour son dessin : ils ont suivi la
  fonction qui l'a remplacée.
- **Les graisses de police se chargent dans le `<head>`, pas par `@import` dans un style injecté.**
  Un `@import` posé au moment de l'impression ne couvre jamais l'écran, et fait diverger les deux.

## Reste ouvert

- **La palette des trois flux** : ambre `#F5A623` et orange `#F07020` indissociables (ΔE 12,4 en
  vision normale pour un seuil de 15 ; 9,4 en deutéranopie). Mesuré, écarté par Tony, assumé.
- **Le `.ico` reste hors dépôt** (`*.ico` dans `.gitignore`) : l'exécutable ne se reconstruit pas
  ailleurs que sur la machine de Tony. Décision à prendre.
- **Pages creuses conformes mais peu flatteuses** : en sortie B tout coché, la page 3 tombe à 32 %
  de remplissage et rien ne pouvait y remonter. Densifier ces blocs reste possible.
- **Le partage du Mac de Jean-Claude reste annoncé** sur le réseau (`Kyocéra 2552 CI @ MacBook Pro
  de Jean-Claude`). Cliquer dessus un jour où ce Mac dort reproduit la panne d'impression du
  04/08. La solution est chez Jean-Claude : décocher « Partager cette imprimante ».

## Reprise

La suite de tests est le filet ; elle tourne en moins de trois minutes :

```
node tests/test_sortie_a.js          # fonctions pures de la sortie A
node tests/coherence-horizon.js      # l'horizon affiché suit dpv
node tests/polices-chargees.js       # aucune graisse synthétisée
node tests/import-image-t4.js        # import du logo et de la photo
node tests/remplissage-sections.js   # pagination, mesurée sur le PDF produit
node tests/rendu-garde-pro.js        # sortie C : 2 pages, référence Excel, HT/TTC
node tests/rendu-sorties.js <dir>    # les quatre sorties se rendent
```

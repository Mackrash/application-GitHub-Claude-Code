# 2026-09-03 — Icône, rapport annoté, pagination

## Objet

Trois chantiers dans la même séance : une nouvelle icône pour le calculateur, la reprise des
annotations manuscrites de Tony sur la sortie A (`a refaire.pdf`), et la chasse aux pages à moitié
vides du PDF.

## Fait

### Icône

- `icone-calculateur.svg` : soleil orange `#F07020` et panneau blanc sur tuile anthracite, tracé
  vectoriel. L'ancienne était un soleil texturé bruité, illisible en 16 px.
- Favicon du HTML : SVG en premier, PNG 64 en repli, `apple-touch-icon`. Au passage l'ancien
  base64 de 13,5 ko tombe à 0,9 ko.
- `solar_calc.ico` régénéré en sept tailles (16 → 256) pour l'exécutable PyInstaller.

### Sortie A — les huit corrections du rapport annoté

| Où | Correction |
|---|---|
| Garde | chiffres des tuiles en Nunito (RAIDenmarkNeo déformait le « 14 × 450 ») |
| Garde | logo répété en bas de page supprimé (doublon de l'en-tête et du pied) |
| L'essentiel | l'armoire batterie devient une **maison** |
| L'essentiel | « An 8 » → « 8 ans », partout |
| L'essentiel | horizon ramené à **15 ans**, un seul paramètre |
| L'essentiel | couverture plafonnée à **99 %** |
| L'essentiel | « Autonomie énergétique » → « Part des énergies renouvelables dans votre consommation » |
| L'essentiel | étapes en quatre temps, avec les démarches administratives (environ 8 semaines) |

### Pagination

- Reproduction objective avant toute correction : huit combinaisons d'options imprimées par la
  vraie route (modal + `pmPrint()`), profil d'encre relevé page par page.
- Cause trouvée : `#last-page` forçait toujours sa page. Avec une seule option cochée, le document
  sortait deux demi-pages consécutives (38 % puis 58 %). Corrigé en `break-before:auto` +
  `break-inside:avoid` : « factures seul » passe de 4 à 3 pages.
- Bug d'horizon trouvé par la même occasion : `syncRoiTitres()` n'était appelée qu'à l'impression.
  À l'écran, le titre annonçait « Retour sur investissement — 20 ans » au-dessus d'une courbe de
  15 ans. Le libellé du panneau d'impression était figé à « Graphique ROI 20 ans ».

### Tests

- `tests/remplissage-sections.js` (neuf) — mesure le PDF réellement produit, huit combinaisons.
- `tests/coherence-horizon.js` (neuf) — l'horizon affiché suit `dpv` : écran, panneau, changement
  à chaud.
- `tests/test_export_json.js` — **réparé**. Il échouait depuis l'ajout des images entreprise :
  `buildStudyJSON()` lit `t4Images`, que le harnais n'injectait pas. `ReferenceError` avant la
  première assertion.
- `tests/test_sortie_a.js` — assertions alignées sur « 8 ans ».
- Suite complète verte, `rendu-garde-pro` compris (référence Excel : 28 085 kWh, ROI 3,5 ans).

## Décidé

- **Le visuel de la sortie A montre une maison, jamais une batterie.** Et cette illustration se
  **génère**, elle ne se dessine pas à la main : quatre propositions SVG successives ont été
  refusées avant qu'on passe par la génération d'image. La règle est dans le `CLAUDE.md`.
- **Horizon d'étude : 15 ans**, commandé par un paramètre unique (`dpv`, champ renommé). L'ancienne
  dette « le document affiche deux horizons, 20 et 25 » est soldée.
- **Le taux de couverture ne dépasse jamais 99 %** à l'affichage.
- **Invariant de pagination** : une demi-page blanche est tolérable s'il n'y a rien après, jamais
  si le contenu suivant y tenait.
- **Un test de mise en page se mesure sur le PDF produit, pas sur un modèle.** La première version
  de `remplissage-sections.js` simulait l'empilement des blocs et validait à tort ; réécrite sur
  le rendu réel, elle a trouvé le vrai défaut.
- La palette des trois flux a été mesurée (validateur `dataviz`) : **l'ambre `#F5A623` et l'orange
  `#F07020` sont trop proches** (ΔE 12,4 en vision normale, seuil 15 ; 9,4 en deutéranopie).
  Le passage de la part « nuit » en anthracite a été proposé et **écarté** — Tony a retenu la barre
  de répartition avec les couleurs d'origine. Le défaut reste, connu.

## Reste ouvert

- **La palette des trois flux** : ambre et orange indissociables (mesuré). Non corrigé, assumé.
- **Le `.ico` reste hors dépôt** (`*.ico` dans `.gitignore`) : l'exécutable ne se rebuild pas
  ailleurs que sur la machine de Tony. Lever l'exclusion est une décision à prendre.
- **Pages creuses conformes mais peu flatteuses** : en sortie B tout coché, la page 3 tombe à 32 %
  de remplissage et rien ne pouvait y remonter. Densifier ces blocs reste possible.
- **Le partage du Mac de Jean-Claude reste annoncé** sur le réseau (`Kyocéra 2552 CI @ MacBook Pro
  de Jean-Claude`). Cliquer dessus un jour où ce Mac dort reproduit la panne d'impression du
  04/08. La solution est chez Jean-Claude : décocher « Partager cette imprimante ».

### Dettes mineures

- `t4LoadImage()` n'a ni `rd.onerror` ni `img.onerror` : échec silencieux si le fichier choisi
  n'est pas une image valide.
- Règles CSS mortes autour de `#amort4_combined` (limite « 15 ans ») depuis que `.ps-page2` est
  masqué à l'impression.
- Police Nunito déclarée dans le template T4 sans `@import` — repli police système.
- `svgMaestro()` n'est plus appelée nulle part (son mode plein largeur était déjà mort) : code
  conservé, à supprimer un jour.

## Reprise

Lire `CLAUDE.md` (sections « Sortie A — Septembre 2026 » et « Sortie C ») puis cette fiche.

Avant toute modification touchant la mise en page imprimée :
`node tests/remplissage-sections.js` puis `node tests/coherence-horizon.js`.
Avant toute modification touchant T4 : `node tests/rendu-garde-pro.js` — il contrôle d'un coup le
rendu, les deux pages, le test de référence Excel et la stabilité HT/TTC.

Si le visuel de la sortie A doit changer : régénérer l'illustration avec
`outils/nano.py` (voir `~/.claude/CLAUDE.md`), en partant d'une photo d'installation réelle.
**Ne pas la redessiner en SVG.**

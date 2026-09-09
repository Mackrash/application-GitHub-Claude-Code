# 2026-09-10-02 — Le dossier de stockage cesse de parler comme un dossier PV

## Objet

Séance courte, trois retouches de la sortie B (onglets 2 et 3) demandées à la volée par Tony
pendant qu'il relisait un dossier client. Toutes portent le même constat : les deux premières
pages d'un dossier batterie reprenaient des formulations écrites pour une installation
photovoltaïque neuve.

## Fait

### Titre de la page de garde

`typeEtude` distinguait trois cas (dont « Système hybride PV + Batterie »). Ramené à deux, sur
consigne :

| Onglet | Titre |
|---|---|
| T1 « Installation » | **Installation d'un système photovoltaïque** |
| T2 « Batterie + données » · T3 « Estimation batterie » | **Installation du système de stockage d'énergie** |

### « Installation remboursée » retiré sur T2 et T3

Sur un ajout batterie, le bloc de la page « L'essentiel » sortait `> 15 ans sur l'horizon étudié`.
Masqué sur T2/T3, conservé sur T1.

⚠️ Point de méthode : Tony a demandé « enlève le ROI de la page de garde ». **La garde ne contient
aucun ROI** — vérifié sur le rendu réel avant de toucher quoi que ce soit. Le bloc visé était sur
la page suivante. Une question a été posée, puis reformulée par Tony lui-même
(« ─ Installation remboursée, c'est ça qu'il faut enlever »). Rien n'a été supprimé au jugé.

### « Démarches administratives » retirée sur T2 et T3

Les « quatre temps » du 03/09 (validation · démarches ~8 semaines · visite technique · pose)
valent désormais pour T1 seul. T2/T3 en comptent trois.

Les étapes ne sont plus écrites en dur : elles sont **générées depuis une liste et se numérotent
seules**. En retirer une laissait sinon la suite 1, 3, 4.

### Tests

**Suite complète verte, 11 fichiers** — `coherence-horizon`, `recap-une-page`, `defauts-coherents`,
`sortie-b-energie`, `remplissage-sections`, `rendu-garde-pro`, `test_sortie_a`, `test_export_json`,
`test_t1_monotonie`, `test_t2_monotonie`, `polices-chargees`.

✅ **La dette de la fiche précédente est soldée** : les quatre tests non joués sur les commits du
matin passent, y compris ceux qui mesurent la mise en page imprimée.

## Décidé

- **Un dossier de stockage ne parle pas comme un dossier PV.** Titre, retour sur investissement et
  parcours administratif sont propres à chaque famille de dossier. Reporté dans le `CLAUDE.md`.
- **T1 avec batterie garde le titre « photovoltaïque ».** Le sélecteur `t1_bat` existe, donc le cas
  est réel ; la variante « Système hybride PV + Batterie » a été retirée sur consigne explicite, et
  le point a été signalé à Tony plutôt que tranché en silence.
- **Une liste d'étapes se génère, elle ne s'écrit pas en dur.** La numérotation doit survivre au
  retrait d'un élément.
- **Ne rien supprimer d'un document sur une désignation approximative.** « Le ROI de la page de
  garde » ne désignait pas ce que le code appelle la garde ; le rendu réel a servi d'arbitre avant
  toute modification.

## Reste ouvert

- ⚠️ **« Bilan cumulé · 15 ans — −749 183 XPF » reste affiché en gros sur T3.** Signalé deux fois à
  Tony, non traité : c'est le même argument que « Installation remboursée » à l'envers, et il est
  plus voyant que les deux blocs qu'on vient de retirer. À trancher.
- **Pas de test de non-régression** sur les trois règles de cette séance (titre, bloc remboursé,
  étapes) ni sur la surbrillance de cellule `td.pb` du matin.
- **La palette des trois flux** : ambre `#F5A623` et orange `#F07020` indissociables (ΔE 12,4 ;
  9,4 en deutéranopie). Non corrigé, assumé.
- **Le `.ico` reste hors dépôt** (`*.ico` dans `.gitignore`) : l'exécutable ne se rebuild que sur
  la machine de Tony. Lever l'exclusion est une décision à prendre.
- **Pages creuses conformes mais peu flatteuses** : en sortie B tout coché, la page 3 tombe à 32 %
  de remplissage et rien ne pouvait y remonter.
- **Le partage du Mac de Jean-Claude reste annoncé** sur le réseau (`Kyocéra 2552 CI @ MacBook Pro
  de Jean-Claude`). Cliquer dessus un jour où ce Mac dort reproduit la panne d'impression du
  04/08. La solution est chez Jean-Claude : décocher « Partager cette imprimante ».

### Dettes mineures

- `t4LoadImage()` n'a ni `rd.onerror` ni `img.onerror` : échec silencieux si le fichier choisi
  n'est pas une image valide.
- Règles CSS mortes autour de `#amort4_combined` (limite « 15 ans ») depuis que `.ps-page2` est
  masqué à l'impression.
- Police Nunito déclarée dans le template T4 sans `@import` — repli police système.
- `svgMaestro()` n'est plus appelée nulle part : code conservé, à supprimer un jour.
- `td.pos` du tableau d'amortissement : classe posée, aucun style associé.

## Reprise

Lire `CLAUDE.md`, section « Sorties B », entrée **« Un dossier de stockage ne parle pas comme un
dossier PV »** — elle porte les trois règles de cette séance.

Premier sujet à trancher : le **bilan cumulé négatif sur T3**.

Avant toute modification de la mise en page imprimée :
`node tests/remplissage-sections.js` puis `node tests/recap-une-page.js`.

Déployé sur GitHub Pages le 10/09 à 9h07 (NC), build `3f095ea`, page publique vérifiée identique
au local.

| Commit | Contenu |
|---|---|
| `9610dc9` | titre de garde, « Installation remboursée », démarches administratives |
| `3f095ea` | les trois règles dans le `CLAUDE.md` |

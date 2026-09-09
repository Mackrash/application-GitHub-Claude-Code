# 2026-09-10-01 — Gains cumulés, surbrillance d'amortissement, horizon fantôme

## Objet

Séance ouverte le 09/09 en fin d'après-midi (NC), close le 10/09 au matin. Trois corrections de
lisibilité sur la sortie A, dont une dont la cause n'était pas dans le dépôt.

## Fait

### Le ratio « × l'investissement » est supprimé

La page « L'essentiel » écrivait `Gains cumulés · 15 ans · 1 505 912 XPF · 0,9 × l'investissement`.
Le ratio valait `ecoDuree / devis`, soit le **gain net** rapporté à la mise. Sur les défauts de
l'onglet 1, le client encaisse 3 155 912 XPF pour 1 650 000 investis — il lui reste 1 505 912 en
poche — et la page lui annonçait « 0,9 × », qu'on lit spontanément « je ne récupère même pas ma
mise ». Sur l'onglet 2, « 0,3 × » cohabitait avec « installation remboursée en 12 ans ».

Trois options soumises à Tony (multiple récupéré 1,9 × · gain net explicité · suppression) :
**suppression retenue**. Le montant et la ligne « installation remboursée en 8 ans » suffisent.

⚠️ Le **calcul** était juste et n'a pas été touché : `ecoDuree` est le cumul net à l'horizon
(`−investissement + Σ bénéfices`), déduction fiscale volontairement exclue (prudent).

### Tableau d'amortissement — la surbrillance passe de la ligne à la cellule

`var isPaybackRow = trancheData.some(d => d.pb===y)` posait la classe `pos` sur la **ligne** dès
qu'une tranche quelconque atteignait son retour cette année-là. Les cinq tranches remboursent entre
5 et 8 ans : quatre lignes entièrement peintes sur cinq colonnes, sans dire **quelle** tranche était
concernée. Tony : « c'est pas clair ».

La marque est désormais sur la cellule (`td.pb`, styles écran et print, ★ dans la case). Contrôlé
par le rendu réel : 0 ligne peinte, 5 cellules marquées, chacune dans sa colonne à son année.

À noter : `td.pos` (cumul positif) n'a **jamais eu de style** — seul `tr.pos` en avait un. La
classe est posée mais invisible ; laissée en l'état.

### L'horizon fantôme — « Gains cumulés sur 30 ans »

Tony voyait 30 ans là où le code porte `value="15"`. **La cause n'était pas dans le dépôt** :
`loadSettings()` réécrit les champs Paramètres depuis le `localStorage` (`sc2_settings`) à chaque
ouverture. Un `dpv` sauvegardé à 30 avant l'arbitrage des 15 ans écrasait le champ, en silence, et
les trois libellés qui lisent `dpv` suivaient — jusqu'à la page de garde.

Correctif : `saveSettings()` ne stocke plus l'horizon, `loadSettings()` **ignore et purge** une
valeur déjà stockée (sans la purge le poste resterait contaminé). Reproduit avant/après :
`localStorage` forcé à 30 → champ à 15, page à « 15 ans », clé nettoyée.

Même motif que `pf`, déjà exclu du `localStorage` juste au-dessus pour la même raison.

## Décidé

- **Aucun ratio, aucun multiple de l'investissement dans le dossier client.** Le gain cumulé
  s'écrit en francs, point. Un ratio inférieur à 1 se lit comme une perte, quel que soit le
  libellé qui l'accompagne.
- **La surbrillance d'un tableau à colonnes multiples se pose sur la cellule, jamais sur la
  ligne.** Une ligne peinte pour une seule colonne concernée efface l'information au lieu de la
  montrer.
- **L'horizon d'étude est une règle produit, pas une préférence de poste** : il n'entre plus dans
  le `localStorage`. Reporté dans le `CLAUDE.md`.
- **Un écart entre l'écran de Tony et le code ne se tranche pas en relisant le code.** Il a dû le
  signaler deux fois avant que la couche `localStorage` soit cherchée. Consigné en mémoire
  (`ecart-ecran-code-chercher-etat-persistant`).

## Reste ouvert

⚠️ **Dette de cette séance — la suite de tests n'a pas été relancée avant le déploiement.**
L'exécution de `coherence-horizon.js`, `recap-une-page.js` et `defauts-coherents.js` a été
interrompue, et le push a suivi (urgence demandée). Les trois modifications ont été vérifiées
individuellement par rendu Playwright réel, mais **la suite complète n'a pas tourné sur ces
commits**. À faire en ouverture de la prochaine séance :
`node tests/coherence-horizon.js && node tests/recap-une-page.js && node tests/defauts-coherents.js`.

- **Pas de test de non-régression sur la surbrillance de cellule** (`td.pb`). Rien n'empêche un
  futur passage de remettre la classe sur la ligne.
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

**D'abord** : relancer la suite de tests (voir la dette ci-dessus) — elle n'a pas tourné sur les
commits de cette séance.

Puis, côté poste de Tony : la première ouverture du calculateur nettoie son `localStorage` de
l'horizon périmé. Vérifier une fois l'onglet Paramètres (Horizon d'étude = 15) avant de générer un
dossier client.

Déployé sur GitHub Pages le 10/09 à 8h27 (NC), build `2581286`.

| Commit | Contenu |
|---|---|
| `5b90b65` | ratio supprimé + surbrillance sur la cellule |
| `2581286` | l'horizon ne se mémorise plus |
| `f3c75b5` | la règle dans le `CLAUDE.md` |

# 2026-09-10-03 — Largeur des graphiques, pied de page, dossiers DRESCHER

## Objet

Séance ouverte le 10/09 en début d'après-midi (NC), close le 11/09 au matin. Trois corrections
d'impression et la production du dossier client DRESCHER en deux variantes de batterie.

Séance coûteuse en allers-retours, et la cause est côté agent : un bug réel signalé par Tony a été
écarté deux fois — d'abord en partant sur un autre sujet, ensuite en affirmant sans mesure qu'il
n'existait pas. Voir *Décidé*.

## Fait

### « Bilan cumulé » disparaît au profit de « Économies sur X ans »

La page « L'essentiel » et les deux récapitulatifs affichaient `ecoDuree`, le cumul **net** de
l'investissement, qui pouvait sortir négatif — sur le dossier DRESCHER : `−55 426 XPF` en gros
caractères sur la première page client. Ce chiffre était juste et illisible pour un client.

Arbitrage Tony, à la lettre : **« économies sur 15 ans, c'est 15 × l'économie annuelle »**. Les
trois emplacements affichent désormais `ecoAn × dpv`, un produit simple, toujours positif.

⚠️ Point de méthode : une première implémentation avait pris `eco15` (somme des bénéfices annuels
nets de fiscalité et de remplacement batterie) — plus « exact », mais pas ce qui était demandé.
Tony a dû reprendre : « fais exactement au mot près ce que je te dis ».

### T2/T3 — « Avec le PV » devient « Avec la batterie »

Sur la page « L'essentiel », la barre de facture d'un dossier de stockage annonçait « Avec le PV ».
Prolonge la règle du 10/09-02 : un dossier de stockage ne parle pas comme un dossier PV.

### Les graphiques Plotly prenaient 700 px au lieu de la largeur disponible

**Le bug que Tony signalait depuis le début de la séance.** Les graphiques sont tracés pendant que
`.results` est encore en `display:none` : Plotly mesure un conteneur de largeur nulle et retombe
sur son défaut de **700 px**, définitivement. Résultat : 700 px dans un conteneur de 952 (écran) ou
794 (impression), avec une bande morte à droite.

Correctif : `resizePlots()` après l'affichage des résultats sur les quatre onglets, largeur du
conteneur appliquée à l'impression, relâchée au retour. Il a fallu aussi aligner la hauteur du div
sur celle du tracé — fixer la largeur coupe l'`autosize`, la hauteur 380 px s'appliquait alors pour
de bon et rognait la légende dans un div de 310 px en `overflow:hidden`.

### Le correctif précédent cassait l'impression — quatre mois sur douze

Première version : la largeur était **mesurée** dans `beforeprint`. Or **Chrome déclenche
`beforeprint` AVANT d'appliquer la mise en page d'impression** : on relevait la largeur écran
(1331 px chez Tony) et on l'imposait à une page de 794. Le graphique débordait et n'affichait plus
que Jan→Avr.

Le test ne pouvait pas le voir : il forçait `emulateMedia({media:'print'})` **puis** dispatchait
`beforeprint` à la main, mesurant la page papier là où Chrome mesure encore l'écran. **Un test qui
validait un code cassé.**

Correctif : la largeur papier se **calcule** — `largeurPapierPx()`, sonde en millimètres (210 mm),
indépendante du média actif.

### La note fiscale chevauchait le pied de page

Le pied répété est en `position:fixed`, et en impression **son bloc conteneur est la zone de
contenu, pas la feuille** : il flotte 6 mm au-dessus du bas du texte, donc *dedans*. La note « Le
retour sur investissement dépend de votre tranche marginale… » tombait pile dessus — mesuré dans le
PDF : pied 776→785, note 777→797.

Réservation côté contenu : `padding-bottom` sur `.lp-note`. Une marge n'aurait rien fait, Chrome
tronque les marges en fin de fragment et les ignore pour la pagination — vérifié avant d'en changer.

### Nouveau test — `tests/largeur-graphiques.js`

Reproduit la **vraie séquence** : aucun média forcé, aucun événement simulé, `page.pdf()` seul.
Contrôle écran (1452/1452), impression (794), retour écran (1452/1452). **Vérifié en échec sur le
code fautif** — un test de non-régression qui ne casse pas sur le bug qu'il vise ne sert à rien.

### Dossier client DRESCHER (Bourail) — deux variantes

Déposés dans `Syno Clients/CLIENTS/DOSSIER A TRAITER/DRESCHER/`, datés du 10-09-2026 : deux PDF
(Prestige, Maestro) de 4 pages et un HTML (Maestro).

Relevés EEC repris de l'export du 09/09 : production 8 670 kWh, consommation 4 970, injection 5 515,
achat 1 910. Revente 15 XPF/kWh, abonnement 6,6 kVA, horizon 15 ans.

**La Prestige fait exactement le même travail que la Maestro sur ce dossier.** L'achat réseau n'est
que de 1 910 kWh/an : les 10,65 kWh de la Prestige l'absorbent en entier, les 3,7 kWh de plus de la
Maestro n'ont plus rien à stocker. Même économie (71 063 XPF/an), même couverture. Seul le prix
sépare les deux dossiers :

| | Devis | 0 % | 12 % | 25 % | 40 % |
|---|---|---|---|---|---|
| **Prestige** | 1 000 000 | **15 ans** | 13 ans | 11 ans | 9 ans |
| Maestro | 1 200 000 | > 15 ans | > 15 ans | 13 ans | 11 ans |

C'est l'illustration du plafond déjà consigné au `CLAUDE.md` (« Prestige et Maestro donnent la même
économie… c'est un argument de vente, pas un défaut »).

### Trois déploiements

`9c802f2` (libellés + économies), `61fe43b` (largeur), `c3e3320` (largeur papier calculée + test),
`0765265` (pied de page). Suite complète verte à chaque fois — 12 fichiers avec le nouveau test.

## Décidé

- **« Économies sur X ans » = économie annuelle × horizon.** Pas de cumul net, pas de chiffre
  négatif sur un document client. Reporté dans le `CLAUDE.md`.
- **Une largeur d'impression se calcule, elle ne se mesure pas.** `beforeprint` s'exécute avant la
  mise en page papier : toute mesure prise à ce moment est une mesure d'écran. Reporté.
- **Un test d'impression ne force ni le média ni l'événement.** Il appelle `page.pdf()` et laisse le
  navigateur suivre sa vraie séquence. Le test précédent, qui forçait les deux, a certifié un code
  cassé — c'est ce qui a laissé passer les « quatre mois sur douze » jusque chez Tony. Reporté.
- **Un test de non-régression se vérifie en échec sur le bug qu'il vise**, sinon il ne prouve rien.
- ⛔ **Ne jamais déclarer qu'un bug signalé n'existe pas sans l'avoir mesuré.** La largeur a été
  qualifiée d'« illusion d'une capture zoomée » sur une simple lecture d'image ; la mesure disait
  700 px contre 952. Tony avait raison depuis le début et a dû le répéter trois fois.
- **Répondre à la question posée.** Une capture d'écran jointe à une question sur la *largeur* a
  déclenché une analyse des *valeurs négatives* de la courbe. Consigné en mémoire
  (`feedback-rester-sur-la-question-posee`).

## Reste ouvert

- ⚠️ **Le tarif haute tranche diffère entre le poste de Tony et le calculateur** : `s_th` vaut
  **46,50** dans son `localStorage` contre **42,24** en dur dans le HTML. C'est ce tarif qui fait
  l'économie annuelle (71 063 contre 61 928 sur DRESCHER). À trancher : mettre le défaut à jour, ou
  acter que le poste fait foi. Tant que ce n'est pas tranché, **tout dossier régénéré sur une
  machine neuve sortira des chiffres inférieurs à ceux de Tony.**
- **Pas de test de non-régression** sur les trois règles du 10/09-02 (titre de garde, bloc
  remboursé, étapes numérotées) ni sur la surbrillance de cellule `td.pb`.
- **La palette des trois flux** : ambre `#F5A623` et orange `#F07020` indissociables (ΔE 12,4 ;
  9,4 en deutéranopie). Non corrigé, assumé.
- **Le `.ico` reste hors dépôt** (`*.ico` dans `.gitignore`) : l'exécutable ne se rebuild que sur la
  machine de Tony. Lever l'exclusion est une décision à prendre.
- **Pages creuses conformes mais peu flatteuses** : en sortie B tout coché, la page 3 tombe à 32 %
  de remplissage et rien ne pouvait y remonter.
- **Le partage du Mac de Jean-Claude reste annoncé** sur le réseau (`Kyocéra 2552 CI @ MacBook Pro
  de Jean-Claude`). Cliquer dessus un jour où ce Mac dort reproduit la panne d'impression du 04/08.
  La solution est chez Jean-Claude : décocher « Partager cette imprimante ».

### Dettes mineures

- `t4LoadImage()` n'a ni `rd.onerror` ni `img.onerror` : échec silencieux si le fichier choisi n'est
  pas une image valide.
- Règles CSS mortes autour de `#amort4_combined` (limite « 15 ans ») depuis que `.ps-page2` est
  masqué à l'impression.
- Police Nunito déclarée dans le template T4 sans `@import` — repli police système.
- `svgMaestro()` n'est plus appelée nulle part : code conservé, à supprimer un jour.
- `td.pos` du tableau d'amortissement : classe posée, aucun style associé.
- La réservation du pied de page est posée sur `.lp-note` seule. Tout autre bloc qui viendrait
  finir en bas de page retomberait dans la même bande.

## Reprise

**Premier sujet à trancher : le tarif haute tranche `s_th`** (46,50 ou 42,24) — il commande
l'économie annuelle de tous les dossiers.

Lire `CLAUDE.md`, section « Impression — les pièges vérifiés », qui porte les trois règles
techniques de cette séance.

Avant toute modification touchant les graphiques ou la mise en page imprimée :
`node tests/largeur-graphiques.js && node tests/remplissage-sections.js && node tests/recap-une-page.js`.

Déployé sur GitHub Pages le 10/09 (NC), dernier build `0765265`.

| Commit | Contenu |
|---|---|
| `9c802f2` | « Avec la batterie » sur T2/T3, « Économies sur X ans » |
| `61fe43b` | les graphiques prennent la largeur de leur conteneur |
| `c3e3320` | la largeur papier se calcule + `tests/largeur-graphiques.js` |
| `0765265` | la note fiscale ne chevauche plus le pied de page |

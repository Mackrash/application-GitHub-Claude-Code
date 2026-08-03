# 2026-08-03 — Refonte de l'onglet 4 et de la sortie C

## Objet

Aligner la sortie entreprise sur le modèle Excel maison, la ramener à deux pages, et lui
ajouter les réglages qui manquaient pour couvrir les structures sans IS.

Point de départ : Tony fournit `Simulation financière Pro1.xlsx` (modèle joint aux devis) et
pose la règle — **« l'Excel fait foi »**, à l'exception de la compensation carbone en arbres,
qui ne doit plus sortir.

## Décisions actées

| Sujet | Décision |
|---|---|
| Format | **Deux pages** exactement : garde + contenu. Graphiques et tableau d'amortissement retirés de l'impression, conservés à l'écran |
| Production | Coefficients Excel (`IDX_PRO`, somme 1486 kWh/kWc/an) — **onglet 4 uniquement**, T1/T2/T3 inchangés |
| ROI | Formule Excel `coût net ÷ économie`, à la place du payback dynamique |
| Surface | 2,2 m²/panneau sur les quatre onglets |
| Montants | Bascule HT (défaut) / TTC, avec invariance obligatoire du ROI et du rendement |
| Régime fiscal | Bascule IS (défaut) / sans IS, pour associations et SCI non assujetties |
| Images | Logo client et photo du site, **import de fichier uniquement** |
| Garde | Design corporate dédié, distinct de celui des particuliers |
| Arbres | Supprimés |

## Écarts trouvés entre le calculateur et l'Excel

La comparaison ligne à ligne a montré que **le bloc fiscal et financier était déjà conforme**
(autoconsommation, facture, économie, amortissement, coût net, rendement). Il a même été
vérifié algébriquement que l'économie de T4, calculée comme `fSans − fAvec`, égale exactement
la somme des gains de l'Excel.

Trois écarts réels :

1. **Production, −7,2 %** — l'Excel donne `kWc × 1486`, le calculateur `kWc × 4,2 × 0,9 × 365`
   soit 1 379,7. Les courbes mensuelles différaient aussi (creux d'hiver bien plus marqué).
2. **ROI** — l'Excel fait `coût net ÷ économie` ; le calculateur *calculait* cette valeur
   (`rsi`) mais **affichait** `pbPro`, un payback dynamique intégrant hausse tarifaire et
   dégradation. Sur un dossier réel : 6,4 ans contre 8 ans.
3. **Surface** — 2,2 m² dans l'Excel, 2,1 dans le calculateur.

Arbitrage de Tony : aligner sur l'Excel, mais **la production pour l'onglet 4 seulement**,
afin de ne pas déplacer les sorties des particuliers validées en juillet.

## Découvertes en cours de route

- **La configuration des onduleurs existait déjà** (`t4_getOndList()` : micro, hybride,
  string, hybride + string). Elle avait été manquée à la première analyse ; une tâche de
  développement inutile a été annulée après vérification.
- **La page de garde n'affichait pas les données de T4** : elle lit `lastStudyData.nbP`,
  `.panWc` et `.prodAn`, or `calcT4` rangeait ces valeurs dans `lastCalcDetails`. D'où les
  « — » sur les cartouches. Corrigé.
- **Il n'existe aucun import d'étude au format JSON.** Le plan s'appuyait dessus à tort : le
  vrai mécanisme de persistance est `saveStudy()`, qui régénère une copie complète du fichier
  HTML. Les images sont donc sérialisées dans une balise `#t4-images-data` du document.
- **La page « L'essentiel » (propre à la sortie A) se générait aussi pour l'onglet 4**, avec
  des valeurs `NaN`. Supprimée du périmètre de T4.

## Ce qui a été écarté

- **Les graphiques** (factures mensuelles, répartition énergétique) : c'est le prix de la page
  unique. Ils restent à l'écran.
- **Le tableau d'amortissement à l'impression**, pour la même raison. L'option correspondante
  a été retirée du panneau d'impression plutôt que de la laisser sans effet.
- **La recherche web d'un logo client** : le calculateur doit fonctionner hors ligne et est
  distribué en `.exe`. Import de fichier uniquement.
- **Un taux de pertes différencié par technologie d'onduleur** : le choix ne modifie que le
  libellé, aucun calcul.
- **L'incohérence 20 ans / 25 ans** (libellé et tableau codés en dur face au paramètre `s.dpv`)
  reste ouverte : elle concerne toutes les sorties, elle mérite sa propre décision.

## Vérification

Un jeu de test de référence a été construit à partir du modèle Excel, consommation comprise
(2 300 kWh × 12). Résultat mesuré sur le rendu réel :

| Grandeur | Excel | Obtenu |
|---|---|---|
| Production annuelle | 28 085 kWh | 28 085 |
| Surface | 92 m² | 92 |
| Consommation | 27 600 kWh | 27 600 |
| Économie / an | 579 207 F | 579 207 |
| Avantage amortissement | 87 000 F | 87 000 |
| Économies d'impôt | 870 000 F | 870 000 |
| Coût net | 2 030 000 F | 2 030 000 |
| Rendement | 22,97 % | 22,97 % |
| **ROI** | **3,50 ans** | **3,5 ans** |

Non-régression contrôlée par rendu PDF : sortie A à 6 pages, sorties B à 8 pages, **identiques
au pixel près** avant et après. Réserve verticale de la page de contenu : 23,1 mm en cas dense
(deux lignes d'onduleurs, logo client, nom de projet de 80 caractères).

## Un douzième écart, trouvé au rendu final seulement

L'analyse ligne à ligne avait conclu à trois écarts. Le **contrôle visuel du document imprimé**
en a révélé un quatrième que la comparaison des formules avait manqué : les **économies sur
15 ans**. Le calculateur sommait les bénéfices année par année en appliquant la dégradation des
panneaux (8 567 523 F) là où l'Excel fait simplement `économie annuelle × 15` (8 688 109 F).
Corrigé, l'Excel faisant foi.

Leçon : comparer les formules ne suffit pas. Il faut **regarder le document produit**, ligne à
ligne, contre le modèle.

## Erreurs de méthode de cette session

- **La configuration des onduleurs a été proposée au développement alors qu'elle existait
  déjà.** L'analyse initiale s'était appuyée sur des `grep` trop étroits et sur la lecture
  d'une seule ligne d'un objet qui s'étend sur plusieurs. Tony a validé une fonctionnalité
  inutile avant que la vérification ne l'annule. Le réflexe manquant : lister *tous* les
  identifiants d'un onglet (`grep -o 'id="t4_[a-z_]*"'`) avant de conclure à une absence.
- **Le plan s'appuyait sur un import d'étude au format JSON qui n'existe pas.** Le mécanisme
  réel est `saveStudy()`, qui régénère une copie du fichier HTML. Détecté au moment de
  dispatcher la tâche, corrigé dans la consigne — mais le plan aurait dû le vérifier.
- **Une fausse alerte sur les séparateurs de milliers** : lus comme absents sur un rendu à
  90 dpi, ils étaient bien présents (espace fine U+202F, peu visible à cette résolution).
  Vérifier dans le texte extrait du PDF, jamais à l'œil sur une image basse résolution.
- **La revue finale globale de la branche n'a pas été faite**, à la demande de Tony qui
  trouvait le protocole de revue disproportionné. Chaque tâche a été revue individuellement
  et le test de référence passe, mais aucune relecture d'ensemble n'a eu lieu.

## Déploiement

Branche `t4-sortie-c` (13 commits) fusionnée dans `main`, poussée, et GitHub Pages
redéployé. **Vérification faite sur la version publiée** — pas seulement sur le local : la
page en ligne a été retéléchargée et le rendu rejoué dessus, il donne bien 2 pages,
8 688 109 F d'économies sur 15 ans et 22,97 % de rendement.

## Reste ouvert

- **Horizon 20 ans / 25 ans** : libellé de section et tableau d'amortissement tronqué à
  20 lignes restent codés en dur face au paramètre `s.dpv`. Concerne toutes les sorties.
- **Taux d'autoconsommation** : le calculateur affiche le taux réellement atteint (63,9 %),
  l'Excel afficherait le paramètre saisi (65 %). Le calculateur est plus juste ; à trancher
  si la conformité stricte au modèle est voulue.
- **`t4LoadImage()` sans `onerror`** : échec silencieux si le fichier choisi n'est pas une
  image valide.
- **Règles CSS mortes** autour du tableau d'amortissement, devenues sans objet depuis le
  masquage de `.ps-page2` à l'impression.
- **Police Nunito** déclarée dans le template T4 sans `@import` : repli sur la police système.

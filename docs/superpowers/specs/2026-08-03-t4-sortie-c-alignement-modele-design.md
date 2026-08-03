# T4 / sortie C — alignement sur le modèle Excel, régime fiscal et HT-TTC

*Design validé avec Tony le 03/08/2026.*

## Contexte

L'onglet 4 (« Entreprise », sortie C) est le dernier onglet à ne pas avoir été repris
lors de la refonte des sorties client de juillet 2026 : les onglets 1 à 3 ont reçu la
page « L'essentiel », T4 a conservé son rendu d'origine.

Le document de référence est le modèle Excel maison
`Solar Concept/1.2 - MODELES De Documents/Modèles Etude à joindre au Devis/Simulation financière Pro1.xlsx`
(feuille « Simul globale »). **La sortie papier de T4 doit produire les informations de ce
modèle, à l'exception de la compensation carbone exprimée en arbres.**

### Ce qui est déjà conforme

Comparaison ligne à ligne du modèle et de la page 2 actuelle : **22 des 23 lignes du modèle
sont déjà produites** — caractéristiques du générateur (puissance crête, panneaux,
micro-onduleurs, puissance unitaire, surface), production annuelle, émissions CO₂,
décomposition mensuelle sur 12 mois, et l'intégralité du bloc économique (coût total,
kWh sur 15 ans, prix de revient, prix payé actuellement, économie annuelle, économies sur
15 ans, avantage lié à l'amortissement, rendement, économies d'impôt, coût net, ROI).

**Le récapitulatif n'est donc pas à refondre.** Ce design porte sur quatre corrections
ciblées et un ajout fonctionnel.

## Objectifs

1. Retirer la compensation carbone en arbres.
2. Offrir un choix **HT / TTC** sur l'ensemble du document, HT par défaut.
3. Offrir un choix de **régime fiscal**, pour couvrir les structures sans IS.
4. Réparer la page 3 (graphiques tronqués, tableau d'amortissement absent, page à moitié vide).
5. Réparer la page de garde, qui n'affiche pas les données de T4.

Hors périmètre : les onglets 1 à 3, les formules de calcul énergétique (`calcT4` amont),
la page « L'essentiel » (volontairement absente de T4).

## 1. Bandeau « Paramètres du document »

Un bandeau placé **en tête de l'onglet 4**, au-dessus du bouton CALCULER, portant deux
bascules segmentées pleine largeur. Exigence explicite de Tony : **pas une case à cocher
discrète dans un coin — un élément visuellement fort**, au même niveau de présence que le
bouton CALCULER.

### Bascule A — Montants

| Choix | Effet |
|---|---|
| **HT** (défaut) | Comportement actuel, aucun changement |
| **TTC** | Tous les montants monétaires multipliés par `(1 + s.tgc/100)` |

Le taux vient du champ **TGC (%)** qui existe déjà dans les paramètres généraux
(`#s_tgc`, 3 % par défaut). Aucun nouveau champ de saisie.

Champs impactés en mode TTC : coût total de l'investissement, prix du kWh payé
actuellement, prix de revient du kWh, économie annuelle, économies sur 15 ans, économies
d'impôt, coût net, ainsi que le graphe des factures mensuelles et le tableau
d'amortissement.

**Propriété à préserver — le ROI et le rendement ne doivent pas bouger entre HT et TTC.**
Numérateur et dénominateur étant affectés du même facteur, le ratio est invariant. C'est
la garantie de cohérence du document : tout HT ou tout TTC, jamais un mélange. Un écart
de ROI entre les deux modes est un bug.

### Bascule B — Régime fiscal

| Choix | Effet |
|---|---|
| **Soumise à l'IS** (défaut) | Comportement actuel : amortissement sur `dAmort` années au taux `tIS` |
| **Sans IS** (association, SCI non assujettie) | `avantageAn = 0`, `avantageTotal = 0`, `coutNetImpot = devis` |

En mode « Sans IS », trois libellés changent pour que le document reste lisible :

- « Avantage annuel lié à l'amortissement comptable » → valeur `0`, mention **« sans objet — structure non soumise à l'IS »**
- « Coût net après déduction fiscale » → **« Coût réel supporté »**
- « Retour sur investissement après amortissement comptable » → **« Retour sur investissement »**

Le rendement annuel devient `ecoAn / devis` (l'avantage fiscal disparaissant du numérateur).

Les deux bascules sont **indépendantes** : les quatre combinaisons sont valides. Une SARL
assujettie prend HT + IS ; une association prend TTC + sans IS.

### Rappel sur le document imprimé

Le mode retenu est rappelé sur la page 2, en tête du bloc « Données économiques » :
`Montants exprimés en HT` ou `Montants exprimés en TTC (TGC 3 %) — structure non soumise à l'IS`.
Une ligne discrète, mais présente : le lecteur du PDF n'a pas accès à l'écran de saisie.

## 2. Suppression de la compensation carbone en arbres

Trois retraits dans `calcT4` :

- la constante `arbres` (calcul `prodAn * 0.03`) ;
- la ligne de rapport « Compensation carbone par an — X arbres » ;
- le fragment « — 1 arbre absorbe ~20 kg CO₂/an » de la note de bas de bloc.

**Conservés**, car présents dans le modèle : « Émissions CO₂ évitées — X tonnes » et la
note « 1 kWh produit au fioul = 600 g de CO₂ ».

## 3. Format : deux pages, pas une de plus

**Contrainte dure posée par Tony le 03/08/2026 : la sortie C fait exactement deux pages —
une page de garde et une page de contenu.** La troisième page actuelle (graphiques) est
supprimée, pas réparée.

Cette contrainte commande tous les arbitrages de contenu : ce qui ne tient pas sur la page
unique ne sort pas. Le modèle Excel de référence tient lui-même sur une page ; c'est la
preuve que l'information essentielle y rentre.

### Ce qui est retenu sur la page de contenu

Dans l'ordre du modèle Excel :

1. **Caractéristiques du générateur** — puissance crête, nombre de panneaux, micro-onduleurs,
   puissance unitaire, surface.
2. **Rendement annuel** — production annuelle, autoconsommation estimée, émissions CO₂
   évitées, note « 1 kWh produit au fioul = 600 g de CO₂ ».
3. **Décomposition de la production mensuelle** — douze mois plus le total, en tableau
   compact sur une seule bande, comme le modèle.
4. **Données économiques** — coût total de l'investissement, production annuelle, kWh sur
   15 ans, prix de revient du kWh, prix payé actuellement, économie annuelle, économies sur
   15 ans, avantage lié à l'amortissement, économies d'impôt.
5. **Trois chiffres de conclusion**, mis en relief : rendement annuel estimé, coût net (ou
   coût réel), retour sur investissement.

### Ce qui est supprimé

- La page 3 entière : graphe des factures mensuelles, graphe de répartition énergétique.
- Le tableau d'amortissement année par année (`#amort4_combined`) **reste disponible à
  l'écran** — il demeure utile en rendez-vous — mais ne s'imprime pas.

Ces éléments sont retirés du flux d'impression uniquement. Aucun calcul n'est supprimé.

### Validation préalable par maquette

Conformément à la règle de travail : **une maquette HTML est soumise à Tony et validée
dans le navigateur avant toute modification du calculateur.** La densité d'une page A4
unique ne se juge pas sur une description. La maquette vit dans `_maquettes/` et porte des
données réalistes.

## 4. Alignement des calculs sur le modèle Excel

**Règle posée par Tony : l'Excel fait foi.** La comparaison ligne à ligne du modèle et de
`calcT4` a été menée ; elle donne trois écarts. Le reste est déjà conforme.

### Déjà conforme — à ne pas toucher

Autoconsommation `MIN(conso × taux ; prod)`, facture HT `(1+tc)×(conso×tarif + prime) + redevance`,
économie annuelle, kWh sur 15 ans, prix de revient, avantage d'amortissement `invest/10 × 30 %`,
économies d'impôt `invest × 30 %`, coût net, rendement `(éco + avantage)/invest`.

### Écart 1 — Production annuelle : −7,2 %

| | Formule | Sur 18,9 kWc |
|---|---|---|
| Excel | `kWc × 1486`, réparti sur les coefficients mensuels | 28 085 kWh |
| T4 actuel | `kWc × irradiance(4,2) × (1−pertes 10 %) × 365` | 26 076 kWh |

Les courbes mensuelles diffèrent également : le creux d'hiver de T4 est plus marqué
(juin à 4,79 % de l'année contre 6,06 % dans le modèle).

**Décision Tony : alignement sur l'Excel pour T4 uniquement.** T1, T2 et T3 conservent
`prodM()` inchangé — leurs sorties validées en juillet ne doivent pas bouger.

Implémentation : une constante dédiée porte les coefficients mensuels du modèle
`[147, 138, 132, 102, 99, 90, 93, 108, 133, 144, 148, 152]` et `calcT4` calcule sa
production par `kWc × coef[mois]`, sans passer par `prodM()`.

**Conséquence assumée : deux moteurs de production coexistent dans le fichier.** Le
commentaire de la constante doit dire explicitement qu'elle est réservée à T4 et pourquoi,
faute de quoi la prochaine session la prendra pour un doublon à supprimer.

### Écart 2 — ROI : formule différente

L'Excel calcule `ROI = coût net ÷ économie annuelle`. `calcT4` calcule bien cette valeur
(`rsi`) mais **imprime `pbPro`**, un payback dynamique intégrant hausse tarifaire,
dégradation et remplacement batterie. Sur un même dossier : 6,4 ans contre 8 ans.

**Décision Tony : la sortie C imprime la formule Excel seule.** Le bandeau ROI affiche
`rsi`. Le payback dynamique reste calculé et disponible à l'écran, mais ne s'imprime plus
sur la sortie C.

### Écart 3 — Surface des panneaux

Excel `ROUND(nb × 2,2)`, calculateur `nbP × 2,1`. **Décision Tony : 2,2 m² partout**, sur
les quatre onglets. Aucun calcul financier n'en dépend, l'impact se limite à l'affichage.

### Point mineur non retenu

Le CO₂ est arrondi à l'entier dans l'Excel, à la décimale dans T4 (17 contre 16,6 tonnes).
Écart d'affichage sans conséquence — laissé tel quel.

## 5. Page de garde — correction

**Cause identifiée.** La page de garde lit `lastStudyData.nbP`, `lastStudyData.panWc` et
`lastStudyData.prodAn`. Or l'affectation de `lastStudyData` en fin de `calcT4` ne contient
aucune de ces trois clés, contrairement à celle de `calcT1`. Les trois cartouches
« Panneaux » et « Production estimée / an » affichent donc « — » alors que la page 2
dispose des valeurs.

**Correctif.** Ajouter `nbP`, `panWc` et `prodAn` à l'objet `lastStudyData` construit par
`calcT4`. Les trois variables existent déjà dans la portée de la fonction ; aucun calcul
supplémentaire n'est nécessaire.

## 6. Logo client et photo du site

Aucun mécanisme d'import d'image n'existe aujourd'hui : la photo de la page de garde est
embarquée en base64 dans le fichier, et il n'y a ni `input type="file"` ni `FileReader`.

**Décision Tony : upload de fichier uniquement.** Pas de recherche web — le calculateur est
un fichier autonome, utilisé hors ligne et distribué aussi en `.exe` ; une recherche
d'image dépendrait d'une API, d'une clé et d'une connexion, et casserait en clientèle.

Deux emplacements distincts :

| Élément | Emplacement | Rôle |
|---|---|---|
| **Logo client** | page de garde (grand, face au logo Solar Concept) **et** page de contenu (petit, dans le bloc projet) | identifie le document aux couleurs du client sur ses deux pages |
| **Photo du site** | page de garde, à la place de la maison générique | remplace le visuel par le site réel du client |

Quand aucune image n'est fournie, le comportement actuel est conservé : photo générique sur
la garde, et aucun encart logo sur la page de contenu — pas de cadre vide dans le document
imprimé.

**Traitement technique.** L'image est lue par `FileReader`, **redimensionnée via un canvas**
avant stockage (logo : 400 px de large maximum ; photo : 1 400 px), puis convertie en JPEG
ou PNG base64. Le redimensionnement n'est pas optionnel : une photo de téléphone brute
dépasse plusieurs mégaoctets et ferait exploser aussi bien le quota `localStorage` (~5 Mo)
que le poids du JSON d'étude.

**Persistance : dans le JSON d'étude.** Les images voyagent avec le dossier exporté, si
bien qu'une étude rouverte des mois plus tard retrouve son logo. Elles ne sont pas
mémorisées dans `localStorage` : d'une étude à l'autre, le client change.

## 7. Page de garde entreprise — design propre à T4

**Décision Tony : la garde de la sortie C ne réutilise pas celle des particuliers.** Elle
adopte un traitement corporate, sobre, validé sur maquette le 03/08/2026
(`_maquettes/T4-garde-entreprise.html`).

Différences assumées avec la garde particulier (photo pleine largeur, cartouches colorés,
badges orange) :

- **Les deux logos en vis-à-vis** en tête — Solar Concept à gauche, client à droite : une
  relation entre deux entreprises.
- **L'orange en accent seulement** : un filet sous les logos, une barre verticale devant le
  nom du client. Aucun aplat de couleur.
- **Trois chiffres séparés par de simples filets** — puissance installée, production
  annuelle, retour sur investissement. Pas de blocs colorés.
- **Photo du site en bandeau de 66 mm**, en bas de page, et non en bannière plein cadre.
- Blanc largement dominant, hiérarchie portée par la typographie.

Quand le logo client ou la photo sont absents, **leurs emplacements disparaissent
entièrement** : aucun cadre vide ne subsiste sur le document imprimé.

Pied de page : identité Solar Concept à gauche, référence, date et mention « document
estimatif, non contractuel » à droite.

## 8. Configuration des onduleurs — DÉJÀ IMPLÉMENTÉE, rien à faire

Vérification faite le 03/08/2026 : **la fonctionnalité existe déjà et est complète.** Elle
avait été manquée lors de la première analyse ; aucun développement n'est nécessaire.

L'existant, à ne pas réécrire :

| Élément | Emplacement |
|---|---|
| Sélecteur de type (`micro`, `hybride`, `string`, `hybride_string`) | `#t4_ond_type`, ligne 745 |
| Blocs de saisie marque / puissance kW / quantité | lignes 754-767 |
| Bascule d'affichage des blocs | `t4_toggleOnd()`, ligne 2852 |
| Construction de la liste | `t4_getOndList()`, lignes 2866-2886 |
| Rendu dans le rapport | ligne 3031, `ondList.map(...)` |
| Stockage | `lastCalcDetails.ondList`, ligne 3126 |

Les quatre configurations demandées par Tony sont couvertes : micro-onduleurs (quantité
calculée automatiquement sur le nombre de panneaux), un hybride, deux hybrides (quantité),
et hybride + string.

**Seule limite connue, non traitée** : on ne peut pas décrire deux hybrides de modèles
différents, la quantité s'appliquant à un modèle unique. Aucun besoin exprimé ; à rouvrir
seulement si le cas se présente.

### Conséquence sur la contrainte d'une page

Le bloc « Caractéristiques » devient de hauteur variable. La maquette validée consomme
264 mm sur les 277 mm utiles : il reste **environ 33 mm de réserve**, soit la place de
quatre à cinq lignes d'onduleurs supplémentaires. Au-delà, le document déborderait — le
rendu doit donc être vérifié avec une configuration à trois entrées au minimum.

## Vérification

Le calculateur n'a pas de suite de tests unitaires : la vérification passe par le rendu
réel, conformément à la règle du CLAUDE.md (« tester par la vraie route »).

1. **Syntaxe JS** — la commande de contrôle du CLAUDE.md doit répondre `SYNTAXE OK`.
2. **Rendu papier** — `node tests/rendu-sorties.js <dossier>` (script existant, qui couvre
   déjà l'ensemble des sorties), puis examen des images produites. Contrôles : **exactement
   deux pages**, aucun débordement, aucune mention d'arbres, page de garde renseignée,
   toutes les lignes du modèle présentes sur la page de contenu.
3. **Invariance du ROI** — sur un même jeu de données, basculer HT → TTC et vérifier que
   le ROI et le rendement sont identiques, tandis que les montants sont multipliés par 1,03.

3 bis. **Conformité au modèle Excel** — saisir dans T4 les paramètres du modèle
   (42 panneaux de 450 W, tarif 29,62 F/kWh, prime 964 F/kVA sur 19,8 kVA, redevance 681 F,
   taxe communale 9 %, autoconsommation 65 %, investissement 2 900 000 F, IS 30 % sur
   10 ans) et vérifier que la sortie reproduit les valeurs du modèle :
   production 28 085 kWh, surface 92 m², kWh sur 15 ans 421 281, prix de revient
   6,88 F/kWh, économie 579 207 F, économies sur 15 ans 8 688 109 F, avantage 87 000 F,
   rendement 22,97 %, économies d'impôt 870 000 F, coût net 2 030 000 F, **ROI 3,5 ans**.
   C'est le test de référence : il valide l'alignement des trois écarts d'un coup.
4. **Régime sans IS** — vérifier que l'avantage fiscal tombe à zéro, que le coût réel égale
   l'investissement, que le ROI vaut `devis / ecoAn` et que les trois libellés ont changé.
5. **Non-régression** — les onglets 1, 2 et 3 doivent produire un rendu inchangé **hormis
   la surface** (2,1 → 2,2 m²/panneau, seul écart attendu) : leurs sorties de référence
   dans `_rendu-final/` servent de comparaison.
6. **Débordement** — rendre la sortie C avec **trois entrées d'onduleurs** et un logo
   client chargé, puis vérifier que le PDF fait toujours une seule page de contenu.
7. **Images** — vérifier qu'une photo de plusieurs mégaoctets est bien redimensionnée
   avant stockage, que l'étude exportée en JSON la conserve, et qu'une étude sans image
   s'imprime sans cadre vide.

## Points ouverts, hors périmètre

Un écart connu, consigné dans le CLAUDE.md et **non traité ici** : le libellé de section
« Retour sur investissement — 20 ans » et le tableau d'amortissement tronqué à 20 lignes
en CSS print restent codés en dur, alors que les gains cumulés suivent le paramètre
`s.dpv` (25 ans par défaut). Le même document peut donc afficher deux horizons. À trancher
séparément, car la décision concerne toutes les sorties, pas seulement T4.

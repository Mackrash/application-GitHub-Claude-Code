# Spec — Visualisation de l'apport des panneaux dédiés à la charge batterie (T2)

Date : 2026-06-23
Fichier cible : `calculateur-pv-nc.html`
Onglet : **T2 uniquement** (`tab1`, « 🔋 Batterie + données »)
Demande : Tony (Solar Concept)

## Contexte

Le produit « panneaux dédiés recharge batterie » a été ajouté en T2 (lot de panneaux EN PLUS
du PV principal, dont la production sert uniquement à charger la batterie — ni revente, ni
autoconso directe ; surplus écrêté). Aujourd'hui il n'apparaît que via 3 lignes de texte
ajoutées au récap (zone financière), incluant une ligne « écrêté ». C'est trop discret et mal
placé.

Précisions métier de Tony :
- **Ces panneaux ne produisent que pour remplir la batterie.** Ce qui compte = ce qu'ils
  **apportent à la charge batterie** (l'énergie réellement stockée), pas la production brute.
- L'**écrêté ne doit plus être affiché**.
- Intégration **dans la partie technique uniquement** (bilan énergétique), **pas dans les
  visuels financiers** (factures, ROI, amortissement, fiscal).

Maquette validée : `_maquette-dedie.html` (v3).

## Décisions

### 1. Carte technique titrée (remplace les 3 lignes actuelles du récap)
Supprimer les 3 lignes ajoutées au `renderRecap('recap2', …)` (panneaux dédiés / production
dédiée / écrêté). Les remplacer par une **carte titrée** affichée dans la zone technique,
**juste au-dessus du bilan énergétique mensuel** (`t2_bilan`), uniquement si `kwcDedie > 0` :

Titre : **« ☀️ Panneaux dédiés → recharge batterie »**

3 statistiques :
| Statistique | Valeur | Source |
|---|---|---|
| Lot installé | `{nb} × {Wc} Wc = {kWc} kWc` | `panBatNb`, `panBatWc`, `kwcDedie` |
| Recharge batterie apportée | `{X} kWh/an` | `bCDedieAn` (énergie stockée depuis le lot dédié) |
| Part de la recharge totale | `{Y} %` | `bCDedieAn / (bCAn + bCDedieAn) × 100` |

Charte : carte orange Solar Concept (dégradé orange léger, bord `--org`, bandeau titre orange,
valeur clé en jaune `#FFD700` comme la batterie). Classe imprimable (apparaît dans le PDF étude).

### 2. Bilan énergétique mensuel enrichi (`renderBilanMensuel`)
Ajouter une ligne, **sous « Consommation batteries »**, intitulée
**« ↳ rechargé par panneaux dédiés »** (en jaune), donnant `bCDedieM[i]` mois par mois, plus le
total annuel. La ligne n'apparaît que si la donnée est fournie.

C'est ce qui répond directement à « ce que les panneaux amènent à la charge batterie ».

### 3. Hors périmètre (inchangé)
- **Aucun nouveau graphe.** Pas de graphe à barres dédié, pas de modification du donut
  `g2_donut`.
- **Aucune** intégration dans les visuels financiers (`g2_mois`, `g2_roi`, `tb2`, `t2_facture`,
  KPI `k2_fin`, fiscal).
- L'écrêté n'est plus affiché nulle part.

## Détails d'implémentation

### Dans `calcT2` (boucle batterie)
La boucle calcule déjà `bC` (charge depuis la réinjection PV principal) et `bCDedie` (charge
depuis le lot dédié) par mois. Il faut :
- stocker `bCDedieM[i] = bCDedie` (nouveau tableau) ;
- sommer `bCDedieAn = Σ bCDedieM` et `bCAn = Σ bC` ;
- calculer `partDedie = (bCAn + bCDedieAn) > 0 ? bCDedieAn / (bCAn + bCDedieAn) * 100 : 0`.

`prodDedieAn` reste calculé (il sert au dénominateur de `txAuto`, hors périmètre de cette
spec — ne pas y toucher). `lostDedie`/`lostDedieAn` ne sont plus affichés (le calcul interne
peut rester, mais aucune sortie visible).

### Carte
- Conteneur HTML dédié (ex. `id="t2_dedie_card"`) ajouté dans la `ps-table` du bilan, **avant**
  le titre « Bilan énergétique mensuel ».
- Rendu via une fonction de rendu de carte (HTML string) appelée dans `calcT2` ; vide si
  `kwcDedie === 0`.
- Format des nombres : `fmt`/`fmtD` (locale FR, espace séparateur de milliers).

### `renderBilanMensuel(containerId, rows)`
- Accepter une clé optionnelle `rows.dedieCharge` (tableau 12 valeurs).
- Si présente : insérer une ligne « ↳ rechargé par panneaux dédiés » juste après la ligne
  « Production injectée batterie » / « Consommation batteries », dans les deux demi-tableaux
  semestriels **et** dans le tableau des totaux annuels, avec un style jaune.
- Fonction partagée par T1/T3 : sans `dedieCharge`, comportement strictement inchangé.
- Appel T2 (`renderBilanMensuel('t2_bilan', …)`) : ajouter `dedieCharge: bCDedieM`.

## Vérification
1. **Syntaxe JS** (obligatoire) :
   ```bash
   node -e "const fs=require('fs');const html=fs.readFileSync('calculateur-pv-nc.html','utf8');const m=html.match(/<script>([\s\S]*?)<\/script>/g);if(m){const js=m.map(s=>s.replace(/<\/?script>/g,'')).join('\n');fs.writeFileSync('_check.js',js);}" && node --check _check.js && echo "SYNTAXE OK"
   ```
2. **nb = 0** : aucune carte, aucune ligne dédiée dans le bilan ; T2 strictement identique à avant.
3. **nb = 10, 450 Wc** : carte affichée (Lot 10 × 450 = 4,5 kWc, Recharge batterie apportée en
   kWh/an, Part %) au-dessus du bilan ; ligne jaune « ↳ rechargé par panneaux dédiés » dans le
   bilan (mensuel + total). Aucun « écrêté » visible. Graphes financiers inchangés.
4. **T1 / T3** : bilan inchangé (pas de ligne dédiée), aucun effet de bord.
5. **PDF étude** : la carte et la ligne du bilan apparaissent à l'impression de T2.

## Hors périmètre
- Pas de calcul de prix ni de gain XPF du lot dédié.
- Pas de modification de la courbe de production, du header, ni des autres onglets.

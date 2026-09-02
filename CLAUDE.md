# CLAUDE.md — Calculateur PV NC (Solar Concept)

## 👁️ RÈGLE DURE — tout visuel s'OUVRE dans le navigateur

> **Tony, 25/08/2026 : « je suis fatigué de répéter ça ».**

1. **Tout travail de design passe par un mockup ouvert pour validation** — on montre, on ne décrit
   pas. Rien n'est appliqué avant que Tony ait vu la maquette.
2. **Tout fichier HTML ou PDF s'ouvre dès sa création** (`xdg-open`), et à chaque version corrigée,
   sans attendre qu'il le demande.

⛔ Une capture lue par l'agent ne remplace pas l'ouverture chez Tony. Énoncé complet : `AppIA/CLAUDE.md`.

## ⏰ Heures : toujours en heure de Nouvelle-Calédonie (UTC+11)

Logs, bases et API horodatent en **UTC** ; l'équipe vit en `Pacific/Noumea` = **UTC+11**.
**Toute heure présentée à Tony est convertie** — recopier un horodatage brut est une faute :
`01:30 UTC` = **12h30 à Nouméa**. Règle complète : `~/.claude/CLAUDE.md`.

Guide de travail pour ce dépôt. Projet **monopage HTML** : tout tient dans
`calculateur-pv-nc.html`.

## Emplacement — règle dure

**Décision Tony 03/08/2026** : le calculateur vit dans **un seul dossier**, `AppIA/CalcPV/`.
Il occupait auparavant `SOLAR/Calculateur SOLAIRE/`, doublé d'une copie périmée à la racine
`SOLAR/` — les deux ont disparu. **Ne jamais recréer de copie ailleurs dans le portfolio.**

La **source de vérité est la version en ligne** (GitHub Pages, URL ci-dessous). En cas de
doute sur l'état du fichier, c'est elle qui tranche, pas une copie locale.

Seule exception légitime : `AppIA/Intranet/SOLAR/intranet-front/public/calculateur-pv-nc.html`,
qui n'est pas une copie mais une **redirection** de 648 octets vers l'URL publique. Ne pas y
coller le vrai fichier.

## Repo GitHub

Le repo distant est : `https://github.com/Mackrash/application-GitHub-Claude-Code.git`
Branche de travail : `main` (directe, la branche `master` a été supprimée le 20/07/2026).
**Toujours pusher après chaque modification** : `git push origin main`

GitHub Pages déploie depuis `main` sur :
`https://mackrash.github.io/application-GitHub-Claude-Code/calculateur-pv-nc.html`

Après un push, forcer le redéploiement si nécessaire :
`gh api --method POST repos/Mackrash/application-GitHub-Claude-Code/pages/builds`
Puis attendre 2-3 min et Ctrl+F5.

## État du projet — Février 2026

**Calculateur PV NC — TERMINÉ ✅**

Fichier unique : `calculateur-pv-nc.html`
Dépendances : Plotly 2.27.0 (CDN)

### Corrections appliquées
- Fix erreur syntaxe JS critique (saut de ligne littéral dans err.stack.split)
- Fix mise en page print onglets 3 et 4
- Onglet 4 (Entreprise) print : P2=rapport, P3=ROI+tableau+graphiques
- Rapport entreprise tailles augmentées en print
- GitHub Pages reconfiguré sur branche `main`

### Refonte sortie A — Juillet 2026
- Page « L'essentiel » (print-only, `#essentiel-page`) : deux colonnes, argent à gauche, énergie à droite
- ~~Batterie OMEGA Maestro-G en SVG~~ — **caduc depuis le 03/09/2026** : c'est une maison, voir plus bas
- « Réinjection réseau » → « Réserve de production » (revente à 0) ou « Énergie revendue » (tarif > 0)
- Facture : douze pastilles par défaut, écart mensuel en alternative cochable via le marqueur `pson-fmois` posé par le panneau d'impression
- ROI en relief, trois jalons
- ~~Armoire batterie SVG, mode compact pour les colonnes étroites~~ — **caduc** (`svgMaestro()` n'est plus appelée)
- Quatre blocs redondants supprimés
- **Horizon d'étude : 15 ans, un seul paramètre.** Le champ `dpv` (onglet Paramètres) s'appelle
  désormais « Horizon d'étude » et vaut **15** par défaut. Il commande les gains cumulés, le
  graphe ROI, le tableau d'amortissement et le récapitulatif — plus aucun horizon codé en dur.
  ⚠️ Le titre du graphe et le libellé du panneau d'impression annonçaient 20 ans : le premier
  parce que `syncRoiTitres()` n'était appelée qu'à l'impression, le second parce que le texte
  était figé. Les deux suivent maintenant `dpv` — contrôle : `node tests/coherence-horizon.js`.
- Spec : `docs/superpowers/specs/2026-07-30-refonte-sortie-client-design.md`

### Sortie A — Septembre 2026

Reprise du rapport annoté par Tony (`a refaire.pdf`, 03/09/2026).

- **Le visuel « Où va votre énergie » montre une MAISON, jamais une batterie.** L'armoire OMEGA
  Maestro a été retirée : c'est la maison du client qui est le sujet. L'illustration est une
  **image générée** (Gemini via `outils/nano.py`, à partir de `Graphique/Maison Caledonienne
  claire.png`), détourée et embarquée en WebP dans `MAISON_B64` — 52 ko. La répartition passe
  dans `barreFluxHTML()`, une barre proportionnelle rangée dans le même ordre que les blocs
  chiffrés qui suivent.
  ⛔ **Ne pas redessiner ce visuel en SVG à la main** : quatre tentatives successives ont été
  refusées (« designs à 2 francs », « une maison dessinée par un enfant de 3 ans »). Une
  illustration de niveau produit se génère, elle ne se code pas.
- **Le taux de couverture est plafonné à 99 %** : on n'annonce jamais l'autonomie totale. Quand
  l'achat au réseau tombe à zéro, il s'écrit « achat au réseau quasi nul » et « < 1 kWh ».
- **« Autonomie énergétique » est devenue « Part des énergies renouvelables dans votre
  consommation »**, avec la note « \* Selon vos consommations actuelles ».
- **Le retour s'écrit « 8 ans », jamais « An 8 »** — partout, écran compris.
- **Prochaines étapes en quatre temps** : validation · **démarches administratives (environ
  8 semaines)** · visite technique · pose. Les délais « sous 10 jours » et « ½ journée » ont été
  retirés.
- Page de garde : chiffres des tuiles en Nunito (RAIDenmarkNeo déformait les glyphes), et le logo
  répété en bas de garde a disparu (doublon de l'en-tête et du pied).

#### Pagination — l'invariant

> **Décision Tony 03/09/2026 : une demi-page blanche est tolérable s'il n'y a rien après.
> Jamais si le contenu de la page suivante y tenait.**

`#last-page` ne force plus sa page (`break-before:auto` + `break-inside:avoid`) : le récapitulatif
final remonte quand la place le permet. Avec une seule option cochée, le document sortait deux
demi-pages consécutives (38 % puis 58 %).

Contrôle : **`node tests/remplissage-sections.js`** — il mesure le PDF réellement produit (pas un
modèle de pagination : la première version simulait l'empilement et validait à tort), sur huit
combinaisons d'options en sorties A et B.

### Sorties B — Juillet 2026
- Onglets 2 et 3 : deux premières pages identiques à la sortie A (garde + « L'essentiel »)
- Onglet 3 (ajout sur PV existant) : libellés adaptés — « injection constatée » et non production, pas de panneaux, bloc d'autoconsommation directe masqué car nul
- Le tableau avant/après batterie est remonté dans le récapitulatif final (« Ce que la batterie change ») : il occupait sinon une page à lui seul
- « Gains cumulés » devient « Bilan cumulé » quand le cumul reste négatif sur l'horizon
- Sortie B ramenée de 4 à 3 pages
- **Onglet 4 (sortie C) volontairement hors périmètre** : rendu d'origine conservé

### Sortie C (onglet 4, entreprise) — Août 2026

**L'Excel fait foi pour la sortie entreprise.** Document de référence :
`Solar Concept/1.2 - MODELES De Documents/Modèles Etude à joindre au Devis/Simulation financière Pro1.xlsx`.

- **Format figé : deux pages**, garde + une page de contenu. Les graphiques et le tableau
  d'amortissement restent visibles à l'écran mais **ne s'impriment plus** (`#r4 .ps-page2`
  masqué en `@media print`). L'entrée `amort` a été retirée de `PRINT_CFG.C` : elle serait
  restée sans effet.
- **Production : `IDX_PRO`**, coefficients mensuels du modèle Excel (somme 1486 kWh/kWc/an).
  ⚠️ **Réservée à l'onglet 4.** Les onglets 1 à 3 continuent d'utiliser `prodM()` — ce n'est
  pas un doublon, ne pas fusionner.
- **ROI : formule Excel** `coût net ÷ économie annuelle` (`rsi`), et non plus le payback
  dynamique `pbPro`, qui reste calculé et exposé mais ne s'imprime plus. Repli sur « — »
  quand le retour n'est pas atteignable.
- **Surface : 2,2 m²/panneau** sur les quatre onglets (l'Excel fait `ROUND(nb × 2,2)`).
- **Deux bascules** : montants `HT` (défaut) ou `TTC` (taux du champ `#s_tgc`), et régime
  `IS` (défaut) ou `sans IS`. En TTC, le facteur ne s'applique **qu'à l'affichage** :
  le ROI et le rendement doivent rester identiques entre HT et TTC — un écart est un bug.
- **Logo client et photo du site** : `t4Images`, import de fichier uniquement (jamais de
  recherche web — le calculateur tourne hors ligne). Redimensionnés par canvas avant
  stockage (400 px / 1400 px), sérialisés dans le HTML par `saveStudy()` via la balise
  `#t4-images-data`. Emplacement absent = rien d'affiché, aucun cadre vide.
- **Garde dédiée** : `coverPro()`, aiguillée par `isPro` dans `preparePrint()`. La garde des
  particuliers n'est jamais modifiée.
- **Plus de compensation carbone en arbres** (absente du modèle). Les tonnes de CO₂ restent.
- La **configuration des onduleurs préexistait** (`t4_getOndList()`) : micro, hybride,
  string, hybride + string.

#### Page de garde — refonte du 04/08/2026

Barre orange latérale pleine hauteur, bord à bord. Règles dures :

- **La garde doit tenir debout sans photo du site.** La photo est un bonus, jamais un
  prérequis de mise en page — c'est le défaut qui a motivé la refonte. **Pas de bloc de
  texte à sa place** (un bloc de synthèse chiffré a été construit puis retiré), et **pas de
  photo générique en repli** : elle montrerait une installation qui n'est pas celle du client.
- ⚠️ **`@page cover` (marge nulle) reste restreinte à `body.print-C`.** Les gardes des
  sorties A et B partagent le conteneur `#cover-page` et dépendent des marges `@page`
  globales — les leur retirer casse leur mise en page.
- **Hauteur de la garde en `100vh`, jamais en `mm`.** Une hauteur fixe dépassant la zone
  imprimable déclenche un shrink-to-fit qui réduit toute la page (91 % constatés).
- **Aucune mention ni visuel de batterie** sur cette garde.
- **Logos : émetteur à gauche** (Solar Concept, 27 mm), **destinataire à droite** (logo
  client importé, 28 mm max).
- Le pied de page répété (`body::after`) est masqué en sortie C : il traversait la barre, et
  la page de contenu porte déjà sa propre mention légale.
- Contrôle : `node tests/rendu-garde-pro.js` — rendu avec et sans photo, 2 pages, test de
  référence et stabilité HT/TTC en une commande.
- Spec : `docs/superpowers/specs/2026-08-04-garde-entreprise-barre-orange-design.md`.

⚠️ Piège d'outillage : **Playwright ignore les `@page` nommées sans `preferCSSPageSize: true`**.
Un test sans cette option rogne la barre alors que Chrome la rend correctement.

**Test de référence** — saisir dans T4 les paramètres du modèle (18,9 kWc, 42 × 450 Wc,
19,8 kVA, prime 964, redevance 681, taxe 9 %, tarif 29,62, autoconso 65 %, revente 0,
sans batterie, devis 2 900 000, IS 30 % sur 10 ans, conso 2 300 kWh × 12) doit redonner :
production 28 085 kWh, surface 92 m², économie 579 207 F, avantage 87 000 F, économies
d'impôt 870 000 F, coût net 2 030 000 F, rendement 22,97 %, **ROI 3,5 ans**.

### Comptes rendus de session
Chaque session de travail produit un compte rendu dans `docs/sessions/`, nommé
`AAAA-MM-JJ-sujet.md`. Il consigne les arbitrages et ce qui a été écarté, pas
seulement ce qui a été fait. Convention détaillée dans `docs/sessions/README.md`.

**Rituel v3** (04/08/2026) : quatre sections — *Fait · Décidé · Reste ouvert · Reprise* — et
**la dernière fiche porte l'état du projet**. Plus d'`ETAT.md` : au démarrage d'une session,
lire `ls docs/sessions/ | tail -1`, c'est tout.

### Règles de travail sur ce fichier
- **Ne jamais modifier les calculs** (`calcT1` à `calcT4`, `buildAmort`, `factureMois`, `prodM`) sans accord explicite. `lastStudyData` ne doit qu'exposer des valeurs déjà produites.
- **Tester par la vraie route** : cliquer le bouton, ouvrir le panneau, appeler `pmPrint()`. Ne jamais réécrire la logique dans le test.
- Script de contrôle : `node tests/rendu-sortie-a.js <dossier>` puis regarder les images produites.

### Vérification syntaxe JS (à faire après chaque modif)
```bash
node -e "const fs=require('fs');const html=fs.readFileSync('calculateur-pv-nc.html','utf8');const m=html.match(/<script>([\s\S]*?)<\/script>/g);if(m){const js=m.map(s=>s.replace(/<\/?script>/g,'')).join('\n');fs.writeFileSync('_check.js',js);}" && node --check _check.js && echo "SYNTAXE OK"
```

## Icône

Source unique : **`icone-calculateur.svg`** — soleil orange `#F07020` et panneau blanc sur tuile
anthracite `#333333`, lisible jusqu'à 16 px. Le favicon du HTML embarque le SVG (plus un PNG 64 en
repli et un `apple-touch-icon`) ; `solar_calc.ico` en dérive pour l'exécutable PyInstaller, en sept
tailles de 16 à 256. ⚠️ Le `.ico` est exclu du dépôt par la règle `*.ico` du `.gitignore` : il ne
vit que sur la machine de Tony.

## Skill disponible

Tape `/charte` pour charger et appliquer automatiquement la charte graphique Solar Concept.
Fichier : `.claude/commands/charte.md`

## Identité

**Solar Concept** — Pose et vente de panneaux solaires, Nouvelle-Calédonie.
Tél. : 47 03 02
Slogan : *"Votre meilleure source d'énergie"*

## Charte graphique

### Couleurs
| Rôle | Couleur | Code |
|---|---|---|
| Principale (orange) | Orange Solar Concept | `#F07020` |
| Secondaire (fond sombre) | Anthracite | `#333333` |
| Fond | Blanc | `#FFFFFF` |

### Typographie
- **Logo / Titres** : **Raidenmark Neo Bold** — géométrique, tout en MAJUSCULES
- Pas de serif, pas de couleurs froides (bleu, vert)

### Logos disponibles (`Graphique/`, copie de travail locale)

Le **canon** reste `../../SOLAR/Données/Graphique/`. La copie locale `Graphique/` porte en
plus quelques visuels propres au calculateur (`Facture Avant_apres.jpg`,
`Maison Caledonienne claire.png`). Elle est ignorée par git.

| Fichier | Usage |
|---|---|
| `LOGO SC ORANGE.png` | Texte orange sur fond blanc |
| `Logo Orange Gros.png` | Avec slogan, fond blanc |
| `LOGO sc rond.png` / `LOGO (2).png` | Icône ronde, fond anthracite |
| `Logo SC Gris.png` | Version neutre grise avec téléphone |
| `LOGO-230x230.png` | Format carré pour web/favicon |
| `RAIDenmarkNeo (1).ttf` | Police logo — embarquer en base64 si besoin HTML |
| `Diapositive1.PNG` | Visuel présentation Solar Concept |
| `MAison 1.png` / `MAison 2.jpg` | Photos installation solaire |

### Données batteries OMEGA Power (`../../SOLAR/Données/Données Batterie/`)
Fiches techniques des 3 modèles de batteries :
| Modèle | Fichiers |
|---|---|
| **Elite** | `elite donnees.jpg` + `elite photo.jpg` |
| **Prestige** | `Prestige donnees.jpg` + `prestige photo.jpg` |
| **Maestro** | `MAestro donnée.jpg` + `Maestro photo.jpg` |

Ces images contiennent les specs (capacité, puissance, DoD, garantie) utiles pour alimenter le calculateur.

### Règles d'utilisation
- Toujours utiliser l'orange `#F07020` comme couleur dominante
- Fond sombre = anthracite `#333333`, jamais noir pur
- Texte courant : anthracite `#333333` sur fond blanc
- Ne jamais déformer ou recolorer le logo

# CLAUDE.md — Solar Concept

This file provides guidance to Claude Code (claude.ai/code) when working in this repository.

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
- Batterie OMEGA Maestro-G en SVG remplace la pile de répartition
- « Réinjection réseau » → « Réserve de production » (revente à 0) ou « Énergie revendue » (tarif > 0)
- Facture : douze pastilles par défaut, écart mensuel en alternative cochable via le marqueur `pson-fmois` posé par le panneau d'impression
- ROI en relief, trois jalons
- Armoire batterie SVG : mode compact pour les colonnes étroites (onglets 2/3)
- Quatre blocs redondants supprimés
- ⚠️ Horizon des gains cumulés (page « L'essentiel », graphe ROI, récap final) aligné sur le paramètre `s.dpv` (25 ans par défaut) — mais le libellé de section « Retour sur investissement — 20 ans » et le tableau d'amortissement (tronqué à 20 lignes en CSS print, `table.at tbody tr:nth-child(23)`) restent codés en dur sur 20 ans. Le même document affiche donc deux horizons différents (20 ans / 25 ans) — connu, non corrigé, à trancher.
- Spec : `docs/superpowers/specs/2026-07-30-refonte-sortie-client-design.md`

### Sorties B — Juillet 2026
- Onglets 2 et 3 : deux premières pages identiques à la sortie A (garde + « L'essentiel »)
- Onglet 3 (ajout sur PV existant) : libellés adaptés — « injection constatée » et non production, pas de panneaux, bloc d'autoconsommation directe masqué car nul
- Le tableau avant/après batterie est remonté dans le récapitulatif final (« Ce que la batterie change ») : il occupait sinon une page à lui seul
- « Gains cumulés » devient « Bilan cumulé » quand le cumul reste négatif sur l'horizon
- Sortie B ramenée de 4 à 3 pages
- **Onglet 4 (sortie C) volontairement hors périmètre** : rendu d'origine conservé

### Comptes rendus de session
Chaque session de travail produit un compte rendu dans `docs/sessions/`, nommé
`AAAA-MM-JJ-sujet.md`. Il consigne les arbitrages et ce qui a été écarté, pas
seulement ce qui a été fait. Convention détaillée dans `docs/sessions/README.md`.

### Règles de travail sur ce fichier
- **Ne jamais modifier les calculs** (`calcT1` à `calcT4`, `buildAmort`, `factureMois`, `prodM`) sans accord explicite. `lastStudyData` ne doit qu'exposer des valeurs déjà produites.
- **Tester par la vraie route** : cliquer le bouton, ouvrir le panneau, appeler `pmPrint()`. Ne jamais réécrire la logique dans le test.
- Script de contrôle : `node tests/rendu-sortie-a.js <dossier>` puis regarder les images produites.

### Vérification syntaxe JS (à faire après chaque modif)
```bash
node -e "const fs=require('fs');const html=fs.readFileSync('calculateur-pv-nc.html','utf8');const m=html.match(/<script>([\s\S]*?)<\/script>/g);if(m){const js=m.map(s=>s.replace(/<\/?script>/g,'')).join('\n');fs.writeFileSync('_check.js',js);}" && node --check _check.js && echo "SYNTAXE OK"
```

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

### Logos disponibles (`Données/Graphique/`)
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

### Données batteries OMEGA Power (`Données/Données Batterie/`)
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

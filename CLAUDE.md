# CLAUDE.md — Solar Concept

This file provides guidance to Claude Code (claude.ai/code) when working in this repository.

## Repo GitHub

Le repo distant est : `https://github.com/Mackrash/application-GitHub-Claude-Code.git`
Branche locale : `master` → push sur `main` (remote).
**Toujours pusher après chaque modification** : `git push origin master:main`

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

### Règles d'utilisation
- Toujours utiliser l'orange `#F07020` comme couleur dominante
- Fond sombre = anthracite `#333333`, jamais noir pur
- Texte courant : anthracite `#333333` sur fond blanc
- Ne jamais déformer ou recolorer le logo

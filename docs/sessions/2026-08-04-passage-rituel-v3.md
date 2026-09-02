# 2026-08-04 — Passage au rituel de session v3

## Objet

Bascule du portfolio au **rituel de session v3** (décision Tony du 04/08/2026) : le fichier `ETAT.md`
est supprimé, **la dernière fiche de session porte l'état**. Cette fiche-ci reprend le contenu de
l'ancien `docs/sessions/ETAT.md` (dernière mise à jour 03/08/2026).

## Fait

- Contenu de `docs/sessions/ETAT.md` replié ici, dans la structure v3.
- `docs/sessions/ETAT.md` supprimé.

## Décidé

- **Rituel v3** : une seule fiche par session (*Fait* · *Décidé* · *Reste ouvert* · *Reprise*).
  La dernière fiche du dossier **est** l'état du projet. Règle : `AppIA/CLAUDE.md`.
  Ce dépôt garde sa convention de nommage propre : `AAAA-MM-JJ-sujet.md`, sans numéro de séance.

### Acquis antérieurs (repris de l'ancien ETAT)

**En production, à jour.** Les quatre sorties client sont refaites et déployées.

| Onglet | Sortie | État |
|---|---|---|
| T1 particulier | A | ✅ refondue 30/07/2026 |
| T2 ajout batterie | B | ✅ refondue 30/07/2026 |
| T3 batterie sur PV existant | B | ✅ refondue 30/07/2026 |
| T4 entreprise | C | ✅ **refondue 03/08/2026** — 2 pages, alignée sur le modèle Excel |

**Le dépôt a déménagé le 03/08/2026** : le projet vit maintenant dans `AppIA/CalcPV/` (il était en
`SOLAR/Calculateur SOLAIRE/`). La copie périmée à la racine `SOLAR/` a été supprimée.

**Source de vérité : la version en ligne.**
`https://mackrash.github.io/application-GitHub-Claude-Code/calculateur-pv-nc.html`

## Reste ouvert

**Rien ne bloque.** Branche fusionnée, poussée, déployée et vérifiée en production.

### À trancher

1. **Horizon 20 ans / 25 ans** — le libellé « Retour sur investissement — 20 ans » et le tableau
   d'amortissement tronqué à 20 lignes en CSS print sont codés en dur, alors que les gains cumulés
   suivent le paramètre `s.dpv` (25 ans par défaut). Un même document peut donc afficher deux
   horizons. **Concerne toutes les sorties** — c'est le point ouvert le plus ancien et le plus visible.
2. **Taux d'autoconsommation en sortie C** — le calculateur affiche le taux réellement atteint
   (63,9 % sur le dossier de référence), l'Excel afficherait le paramètre saisi (65 %). Le calculateur
   est plus juste ; faut-il coller au modèle malgré tout ?

### Dettes mineures

- `t4LoadImage()` n'a ni `rd.onerror` ni `img.onerror` : échec silencieux si le fichier choisi n'est
  pas une image valide.
- Règles CSS mortes autour de `#amort4_combined` (limite « 15 ans ») depuis que `.ps-page2` est masqué
  à l'impression.
- Police Nunito déclarée dans le template T4 sans `@import` — repli police système.
- La revue finale globale de la branche `t4-sortie-c` n'a pas été faite (protocole allégé à la demande
  de Tony). Chaque tâche a été revue séparément.

## Reprise

Si tu reprends le calculateur : lire `CLAUDE.md` (section « Sortie C — Août 2026 » pour les règles
dures) puis `docs/sessions/2026-08-03-refonte-t4-sortie-c.md` pour le détail des arbitrages.

**Avant toute modification des calculs**, rejouer le test de référence Excel décrit dans le
`CLAUDE.md` : il doit redonner production 28 085 kWh, économie 579 207 F, rendement 22,97 % et
**ROI 3,5 ans**. C'est le filet qui garantit l'alignement sur le modèle.

# Page de garde entreprise (sortie C) — barre orange latérale

**Date** : 4 août 2026
**Périmètre** : `coverPro()` dans `calculateur-pv-nc.html`. **Rien d'autre ne change.**
Les pages de contenu de la sortie C, les gardes des sorties A et B, et tous les
calculs restent intacts.

## Problème

La garde entreprise livrée en août 2026 tasse tout son contenu dans le tiers
supérieur de la page. Le bloc photo (`.tcv-photo`) est le seul élément qui
descend, or il n'existe que si le commercial a importé une photo du site — cas
minoritaire. Sans photo, la moitié basse de la page est un blanc.

Constats secondaires : les logos sont sous-dimensionnés (Solar Concept 14 mm,
client 16 mm sur une page A4), et le rendu est froid pour un document dont la
fonction est commerciale.

## Décisions

Arbitrages de Tony, 4 août 2026 :

1. **Barre orange latérale** — bande `#F07020` pleine hauteur sur le bord gauche,
   28 mm, portant le slogan à la verticale et le téléphone. C'est elle qui donne
   à la page son aplat de couleur.
2. **La page tient debout sans photo.** La photo du site est un bonus, pas un
   prérequis de mise en page.
3. **Bloc de synthèse chiffré** quand la photo manque : une phrase d'accroche et
   trois chiffres complémentaires. Il remplit le milieu et sert l'argumentaire.
4. **Aucune mention ni visuel de batterie.** La sortie C entreprise n'en comporte
   pas.
5. Logos agrandis : Solar Concept 27 mm, logo client 28 mm maximum.

Écarté en cours de route : un socle orange en pied de page (piste A) et une photo
Solar Concept générique en remplacement de la photo du site — cette dernière
montrerait une installation qui n'est pas celle du client.

## Mise en page

Structure en deux colonnes sur 297 mm de haut :

```
┌──────┬────────────────────────────────────┐
│      │  logo Solar Concept │ logo client  │
│ b a  │  ─────── filet orange ──────────   │
│ a r  │  ÉTUDE TECHNIQUE ET FINANCIÈRE     │
│ r a  │  Étude photovoltaïque              │
│ r n  │  sous-titre / réf. / date          │
│ e g  │  ▌ Établie pour — NOM CLIENT       │
│   e  │  ┌──────────────────────────────┐  │
│ s    │  │ photo du site  OU  synthèse  │  │  ← s'étire (flex:1)
│ l    │  └──────────────────────────────┘  │
│ o    │  ┌────────┬────────┬────────┐      │
│ g    │  │  kWc   │  kWh   │  ROI   │      │
│ a    │  └────────┴────────┴────────┘      │
│ n    │  commercial      mention légale    │
└──────┴────────────────────────────────────┘
```

Le bloc central porte `flex:1` : il absorbe l'espace disponible, ce qui supprime
le blanc par construction quelle que soit la longueur du texte ou la présence de
la photo. C'est le point qui règle le défaut d'origine — pas les marges.

## Données

Toutes déjà produites par `calcT4`. Aucun calcul n'est ajouté ni modifié,
conformément à la règle du `CLAUDE.md`.

| Élément | Source |
|---|---|
| Puissance installée | `lastStudyData.kwc` |
| Production annuelle | `lastStudyData.prodAn` |
| Retour sur investissement | `lastStudyData.rsi` (formule Excel), `—` si non atteignable |
| Économie annuelle | `lastStudyData.ecoAn` |
| Part autoconsommée | `lastCalcDetails.tauxAuto` |
| Surface de panneaux | `lastCalcDetails.surf` (`nbP × 2,2`) |

**Bascule HT/TTC** : les montants du bloc de synthèse portent le même facteur
`kTTC` que le reste de la sortie C — `modeTTC ? 1 + s_tgc/100 : 1`. Les grandeurs
physiques (kWc, kWh, m²) et le ROI n'en dépendent pas. Un ROI qui différerait
entre HT et TTC serait un bug.

**Repli** : si `lastCalcDetails` est absent ou d'un autre onglet, le bloc de
synthèse est omis plutôt que rempli de valeurs fausses. La page reste valide,
le bloc central se réduit.

## Vérification

1. Contrôle de syntaxe JS (commande du `CLAUDE.md`).
2. Rendu de la sortie C dans ses deux états — avec photo importée et sans — par la
   vraie route : onglet 4 → CALCULER → Enregistrer en PDF → Imprimer.
3. Le document reste à **deux pages** : la garde et la page de contenu.
4. Test de référence du `CLAUDE.md` (18,9 kWc) : production 28 085 kWh,
   surface 92 m², ROI 3,5 ans doivent s'afficher sur la garde.
5. Bascule HT → TTC : le ROI et la production restent identiques.

Maquettes validées : `_maquettes/T4-garde-A5-sans-photo.png` et
`_maquettes/T4-garde-A5-avec-photo.png`.

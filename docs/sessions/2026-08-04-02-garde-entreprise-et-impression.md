# 2026-08-04-02 — Garde entreprise refondue, et le mystère de l'impression

## Objet

Deux sujets sans rapport, arrivés dans cet ordre. Une impression de la sortie C qui ne sortait
pas — le calculateur était hors de cause — puis la refonte de la page de garde entreprise.

## Fait

### L'impression qui ne partait pas (cause : la configuration CUPS, pas le calculateur)

Symptôme : en onglet 4, la fenêtre d'impression s'ouvrait, un clic sur « Imprimer » ne produisait
rien. Les trois autres sorties fonctionnaient.

Le calculateur était innocent, et deux preuves l'établissaient avant toute modification : un PDF
correct de la sortie C avait été produit le jour même à 15h46 (`NEYMAR Jean 04-08-2026.pdf`,
2 pages, garde entreprise), et la reproduction headless du parcours T4 complet ne levait aucune
erreur JS.

**La vraie cause** : la file `Kyocera-TASKalfa-2552ci` était déclarée en `dnssd://`, et cette
annonce mDNS résolvait vers un partage hébergé par le **MacBook de Jean-Claude**, éteint à ce
moment-là (`Host is down` dans `/var/log/cups/error_log`). Les travaux partaient vers une machine
dormante et disparaissaient sans message. Aucun job n'avait atteint CUPS depuis le 23 juin 2026.

Derrière, deux fabricants de doublons tournaient : le `cups-browsed` du système **et** un second
embarqué dans un **snap CUPS installé à côté du CUPS système**, qui réinjectait ses découvertes
réseau dans la configuration via l'interface `cups-control`.

Configuration remise à plat :

| File | Adresse | |
|---|---|---|
| `Kyocera_TASKalfa_2552ci` | `ipps://192.168.88.201:443/ipp/print` | par défaut |
| `Kyocera_TASKalfa_MZ2501ci` | `ipps://192.168.88.200:443/ipp/print` | |
| `HP_LaserJet_Pro_4001_94D42B` | `ipps://192.168.88.139:443/ipp/print` | |

Les deux `cups-browsed` sont désactivés au démarrage, quatre files fantômes supprimées, et les
trois files restantes portent **exactement les noms que CUPS générerait lui-même** — c'est ce qui
l'empêche d'en recréer une à côté. Liste passée de 7 entrées à 4. Impression papier validée de
bout en bout : job n° 85 sorti à 16h01.

### Page de garde entreprise (sortie C)

Le contenu se tassait dans le tiers supérieur : seul le bloc photo descendait, or il n'existe que
si une photo du site a été importée — cas minoritaire. Sans photo, la moitié basse restait blanche.

- **Barre orange latérale** `#F07020` pleine hauteur (26 mm), portant le slogan à la verticale, le
  nom du commercial et le téléphone
- **Bord à bord** par une page nommée `@page cover`, **restreinte à `body.print-C`**
- Logos agrandis : Solar Concept 14 → 27 mm, client 16 → 28 mm
- Nom du client à **50 px**, au-dessus du titre (44 px) ; sur-titre 11,5 → 16 px ; téléphone 17 px
- Pied de page répété masqué sur la sortie C : il traversait la barre, et la page de contenu porte
  déjà sa propre mention légale

Commit `e0fe971`, poussé sur `main`, GitHub Pages redéployé.
Spec : `docs/superpowers/specs/2026-08-04-garde-entreprise-barre-orange-design.md`.
Test rejouable : `node tests/rendu-garde-pro.js` — deux états (avec et sans photo), contrôle des
2 pages, du test de référence et de la stabilité HT/TTC.

## Décidé

- **La garde entreprise doit tenir debout sans photo.** La photo du site est un bonus, jamais un
  prérequis de mise en page.
- **`@page cover` reste réservée à `body.print-C`.** Les gardes des sorties A et B partagent le
  conteneur `#cover-page` et dépendent des marges `@page` globales — les leur retirer les casse.
- **Aucune mention ni visuel de batterie** sur la garde entreprise.
- **Pas de bloc de texte à la place de la photo.** Un bloc de synthèse chiffré avait été construit
  puis retiré à la demande de Tony : sans photo, la page se contente des trois cartes en bas, le
  titre et le client descendant vers le centre.
- **Une photo Solar Concept générique en repli est écartée** : elle montrerait une installation qui
  n'est pas celle du client.
- **Logos : émetteur à gauche, destinataire à droite.** Solar Concept à gauche, logo du client
  importé à droite.

### Deux pièges de rendu, à ne pas re-diagnostiquer

- **Hauteur en `mm` sur la garde = shrink-to-fit.** Une hauteur fixe qui dépasse la zone imprimable
  fait réduire toute la page par Chrome (91 % constatés). Utiliser `100vh`.
- **Playwright ignore les `@page` nommées sans `preferCSSPageSize: true`.** Le test rognait la barre
  alors que Chrome la rendait correctement — un faux bug qui a failli être « corrigé ».

## Reste ouvert

**Rien ne bloque le calculateur.** Déployé et vérifié.

### À trancher

1. **Horizon 20 ans / 25 ans** — le libellé « Retour sur investissement — 20 ans » et le tableau
   d'amortissement tronqué à 20 lignes en CSS print sont codés en dur, alors que les gains cumulés
   suivent `s.dpv` (25 ans par défaut). Un même document peut afficher deux horizons.
   **Concerne toutes les sorties** — point ouvert le plus ancien et le plus visible.
2. **Taux d'autoconsommation en sortie C** — le calculateur affiche le taux réellement atteint
   (63,9 % sur le dossier de référence), l'Excel afficherait le paramètre saisi (65 %). Le
   calculateur est plus juste ; faut-il coller au modèle malgré tout ?

### Hors calculateur — poste de travail

3. **Toners de la 2552ci : magenta 5 %, jaune 8 %** (TK-8349M / TK-8349Y). L'orange `#F07020` de la
   nouvelle garde les consomme à pleines mains.
4. **Les trois imprimantes sont fixées sur des IP en dur.** Si le DHCP redistribue les adresses,
   l'impression recassera à l'identique. Une réservation dans le routeur mettrait ça à l'abri.
5. **Le partage du Mac de Jean-Claude reste annoncé** sur le réseau (`Kyocéra 2552 CI @ MacBook Pro
   de Jean-Claude`). Tony a choisi de le laisser. **C'est le piège** : cliquer dessus un jour où ce
   Mac dort reproduit exactement la panne du jour. La solution définitive est chez Jean-Claude —
   décocher « Partager cette imprimante ».

### Dettes mineures

- `t4LoadImage()` n'a ni `rd.onerror` ni `img.onerror` : échec silencieux si le fichier choisi n'est
  pas une image valide.
- Règles CSS mortes autour de `#amort4_combined` (limite « 15 ans ») depuis que `.ps-page2` est
  masqué à l'impression.
- Police Nunito déclarée dans le template T4 sans `@import` — repli police système.
- `CLAUDE.md`, la suppression d'`ETAT.md` et la fiche du rituel v3 restent **non commités** : ils
  précèdent cette session et n'ont pas été mêlés au commit de la garde.

## Reprise

Pour reprendre le calculateur : lire `CLAUDE.md` (section « Sortie C ») puis cette fiche.
Avant toute modification touchant T4, rejouer `node tests/rendu-garde-pro.js` — il contrôle d'un
coup le rendu, les 2 pages, le test de référence Excel (28 085 kWh, ROI 3,5 ans) et la stabilité
HT/TTC. C'est le filet le plus rapide du dépôt.

Si une impression échoue de nouveau en silence : commencer par `lpstat -o` et
`lpstat -W completed -o`. **Une file vide et aucun travail récent signifient que rien n'a atteint
CUPS** — le problème est alors dans le choix de la file, pas dans le calculateur.

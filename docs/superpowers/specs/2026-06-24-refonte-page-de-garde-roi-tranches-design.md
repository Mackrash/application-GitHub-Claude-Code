# Spec — Refonte page de garde + ROI tranche par tranche

Date : 2026-06-24
Fichier cible : `calculateur-pv-nc.html`
Zone : fonction `preparePrint()` (génération de la page de garde `#cover-page`, ~lignes 939-1098) + CSS print + nouveau conteneur de dernière page.
Demande : Tony (Solar Concept)
Maquette validée : `_maquette-garde.html` (générée par `scratchpad/gen-garde.js`).

## Contexte

La page de garde actuelle (générée dans `preparePrint`) contient, dans l'ordre :
en-tête logo, photo maison **avec un encart texte par-dessus** (« ÉTUDE PHOTOVOLTAÏQUE / type / NC »),
bloc Client + Commercial, **récapitulatif** (cartes KPI : devis, ROI, économies), mentions légales, pied de page.

Le ROI y est affiché en **fourchette** (`pbMin à pbMax ans`, ex. « 5 à 8 ans »).

Tony veut une page de garde plus « page de garde » (gros textes, logo réaffiché), le récapitulatif
déplacé en **dernière page**, et le ROI présenté **tranche fiscale par tranche** au lieu d'une fourchette.

## Décisions

### 1. Page de garde refondue (`#cover-page`)
Ordre et contenu :
1. **En-tête** : logo Solar Concept **seul** (image, inchangé) + bloc date/réf à droite.
2. **Photo maison** : conservée, **sans aucun encart texte par-dessus** (retirer `.cv-photo-overlay` et son contenu).
3. **Client | Commercial** : 2 colonnes (Nom client + adresse | Commercial nom + tél/mail), conservé.
4. **Grand titre déplacé ici** (sous Client/Commercial), centré, en gros :
   - Ligne 1 : « ÉTUDE PHOTOVOLTAÏQUE » (police **SingaporeSling**, ~3,23 rem — réduit de 5 % vs essai initial).
   - Ligne 2 : `{typeEtude} — {kWc}` (SingaporeSling, orange, ~1,62 rem).
   - Ligne 3 : « Nouvelle-Calédonie » (Nunito, gris, petites capitales espacées).
5. **Couche logo** (zone qui prend l'espace restant, centrée) : image **logo + slogan** (« Logo Orange Gros.png », le slogan est déjà dans l'image).
6. **Pied de page** : contact du **commercial** → `{commName} | Tél {commTel} | {commEmail}` (remplace le « Votre meilleure source d'énergie | ☎ 47 03 02 » générique). Si pas de commercial sélectionné, repli sur le contact générique.
7. **Plus de récapitulatif** sur la garde (déplacé, cf. §2).

### 2. Récapitulatif déplacé en dernière page
- Nouveau conteneur `#last-page` ajouté **après** le contenu des onglets, rendu **uniquement à l'impression**, sur sa **propre page en fin de document** (`break-before:page`).
- `preparePrint` le remplit (et le vide quand on quitte l'impression, comme `#cover-page`).
- Contenu :
  - En-tête léger (logo + « Récapitulatif du dossier — {client} — {date} »).
  - Titre de section **« Récapitulatif du dossier »** (police **Nunito**, gras, orange).
  - Cartes KPI (3 colonnes) : **Montant du devis**, **Économie annuelle estimée**, **Économies cumulées sur 15 ans**.
    - Valeurs en **Nunito 900**, taille ~1,55 rem, **sur une seule ligne** (`white-space:nowrap`), padding réduit pour tenir.
  - Section ROI (cf. §3).
  - Pied de page commercial (idem garde).

### 3. ROI tranche par tranche (remplace la fourchette)
- Sous le titre **« Retour sur investissement selon votre tranche fiscale »** (Nunito, gras, orange).
- **Tableau** (une ligne par tranche `TRANCHES_NC` : 0 %, 4 %, 12 %, 25 %, 40 %), colonnes :
  | Tranche d'imposition | Déduction fiscale | Coût net après déduction | Retour sur investissement |
- Calcul par tranche, réutilisant les fonctions globales existantes (comme `saveCalcs`) :
  ```
  ded   = calcDeduction(devis, taux, s.ded)        // → ded.eco
  amort = buildAmort(devis, ecoAn, s.hau, s.deg, s.dpv, taux, s.ded, batRepl, batReplAn)  // → amort.pb
  coutNet = devis - ded.eco
  ROI = amort.pb ans
  ```
  où `s = getS()`, `devis`/`ecoAn` viennent de `lastStudyData`, et
  `batRepl = batModel>0 ? BAT_REPL[batModel]*batQty : 0`, `batReplAn = batModel>0 ? s.bat_repl : 0`.
- La tranche la plus haute (40 %) est **surlignée** (fond vert clair) comme amortissement le plus rapide.
- Valeurs ROI en **RAIDenmarkNeo**, vert.

### 4. Polices (reprises du PDF, déjà embarquées)
- **RAIDenmarkNeo** : logo (en-tête + couche), valeurs ROI.
- **SingaporeSling** : grand titre « Étude Photovoltaïque » + sous-titre.
- **Nunito** : noms client/commercial, titres de section de la dernière page, **valeurs des cartes KPI du récap**, textes courants.

## Portée par onglet
- **Particuliers (T1/T2/T3, non-pro)** : tout ce qui précède s'applique, y compris le **tableau ROI par tranche** (la déduction fiscale NC concerne les particuliers).
- **Entreprise (T4, PRO/IS)** : page de garde refondue + récap déplacé en dernière page s'appliquent aussi.
  Mais le **ROI par tranche NC ne s'applique pas** (régime IS différent) → T4 **conserve son indicateur ROI actuel** (« An X » + coût HT après déduction fiscale) dans le récap de dernière page, pas le tableau de tranches.

## Vérification
1. **Syntaxe JS** (obligatoire) — commande habituelle, attendu `SYNTAXE OK`.
2. **Aperçu impression** de **chaque onglet** (T1, T2, T3, T4) via « 📄 Enregistrer en PDF » :
   - Page 1 = garde refondue (photo sans texte, grand titre sous Client/Commercial, couche logo + slogan, pied commercial, **pas de récap**).
   - Pages intermédiaires = résultats existants (graphes/tableaux), inchangées.
   - **Dernière page** = récapitulatif (3 KPI sur une ligne) + ROI par tranche (T1/T2/T3) ou ROI entreprise (T4).
3. Montants du récap **sur une seule ligne**, jamais coupés.
4. Polices correctes (titre en SingaporeSling, titres section + montants en Nunito, logo/ROI en RAIDenmarkNeo).
5. Nom du fichier PDF (`NOM Prénom JJ-MM-AAAA`) inchangé.

## Hors périmètre
- Pas de changement des graphes/tableaux des pages intermédiaires.
- Pas de nouveau calcul financier (réutilisation de `calcDeduction`/`buildAmort` existants).
- Pas de modification de l'affichage écran (seulement le rendu impression/PDF).

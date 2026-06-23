# Spec — Évolutions Calculateur PV NC (juin 2026)

Date : 2026-06-23
Fichier cible : `calculateur-pv-nc.html` (monopage, Plotly 2.27, ~2640 lignes)
Auteur demande : Tony (Solar Concept)

## Contexte

Le calculateur PV NC est une page HTML autonome avec 4 onglets :
- **T1** (`tab0`) — étude particulier basée sur la consommation mensuelle.
- **T2** (`tab1`) — étude batterie « données complètes » (factures EEC réelles).
- **T3** (`tab2`) — étude batterie avec achat/injection réseau réels.
- **T4** (`tab3`) — rapport entreprise / PRO.

La production solaire mensuelle est calculée par une fonction partagée `prodM(kwc, en, pe)`
(ligne ~805), qui s'appuie sur la constante saisonnière `SF` (ligne 763), le rendement de base
`en` (réglage `s_en`, défaut 4.2 kWh/kWc/j) et les pertes `pe` (réglage `s_pe`, défaut 10 %).

Quatre évolutions sont demandées. Elles sont indépendantes et peuvent être livrées ensemble.

---

## Chantier 1 — Nouvelle courbe de production saisonnière (tous onglets)

### Problème
La production des mois d'hiver austral (Mai/Juin/Juillet) est trop optimiste par rapport
au terrain. Solar Concept dispose de ses propres indices mensuels de référence.

### Décision
Remplacer le facteur de forme saisonnier par les indices métier (Janvier → Décembre) :

```
Jan  Fév  Mar  Avr  Mai  Jun  Jul  Aoû  Sep  Oct  Nov  Déc
1.38 1.38 1.32 0.90 0.80 0.65 0.80 0.95 1.25 1.25 1.40 1.50
```

(Juin ajusté de 0.60 → 0.65 sur demande.)

Ces indices sont des **coefficients mensuels** (et non journaliers) : Janvier = Février = 1.38
bien que les mois aient un nombre de jours différent. La production mensuelle ne doit donc
**plus être multipliée par le nombre de jours** `DM`.

### Implémentation
Remplacer `SF` par une constante `IDX`, et réécrire `prodM` pour répartir un productible
annuel — toujours piloté par les réglages `en` et `pe` — selon la forme `IDX` :

```js
const IDX=[1.38,1.38,1.32,0.90,0.80,0.65,0.80,0.95,1.25,1.25,1.40,1.50];
const IDXSUM=IDX.reduce((a,b)=>a+b,0); // 13.58

function prodM(kwc,en,pe){
  const f=1-pe/100;
  const annual=kwc*en*f*365;          // productible annuel piloté par les réglages
  return IDX.map(ix=>annual*ix/IDXSUM); // réparti selon la courbe métier
}
```

- `MO` (libellés mois) et `DM` (jours/mois) restent inchangés : `DM` sert encore au calcul
  de capacité batterie journalière (`batUtileJ*DM[i]`) — ne pas le supprimer.
- Les éventuelles autres références à `SF` dans le code doivent être migrées vers la nouvelle
  logique (audit `grep SF` lors de l'implémentation).

### Portée
La constante étant globale et `prodM` partagée, **T1, T2, T3 et T4** héritent automatiquement
de la nouvelle courbe (« le soleil est le même pour tout le monde »).

### Impact attendu
- Productible annuel ≈ 1 370 kWh/kWc/an (quasi inchangé vs ~1 345 actuel).
- Creux d'hiver nettement plus marqué (Juin ≈ −22 %), été/printemps légèrement relevés.

---

## Chantier 2 — Panneaux dédiés recharge batterie (T2 uniquement)

### Besoin
Nouveau produit : poser des panneaux **uniquement pour charger les batteries**, en plus du
système PV existant. Ces panneaux ne font **ni revente, ni autoconsommation directe**.

### Décision
- C'est un **lot supplémentaire** qui s'ajoute au PV existant de T2 (qui conserve son rôle
  autoconso + revente actuel).
- Le surplus du lot dédié, une fois la batterie pleine, est **écrêté (perdu)**.

### UI (dans T2, `tab1`)
Nouveau bloc optionnel, désactivé par défaut (nombre = 0) :
- `t2_pan_bat_nb` — Nombre de panneaux dédiés batterie (défaut 0).
- `t2_pan_bat_wc` — Puissance unitaire (Wc) (défaut 450).
- Puissance dédiée calculée : `kwcDedie = nb * wc / 1000`.

### Modèle de calcul (dans `calcT2`)
Production du lot dédié, même courbe : `prodDedieM = prodM(kwcDedie, s.en, s.pe)`.

Priorité de charge batterie, par mois `i` (capacité utile jour × jours = `cap`) :
1. Le PV principal charge la batterie en premier (logique existante) → `bChargeMain`.
2. Capacité restante : `capRest = cap - bChargeMain`.
3. Le lot dédié complète : `bChargeDedie = min(prodDedieM[i], capRest)`.
4. Écrêté (perdu) : `lostDedie = prodDedieM[i] - bChargeDedie`.

La décharge batterie totale (qui évite l'achat réseau le soir) augmente d'autant →
le gain économique du lot dédié est capté **automatiquement** par la chaîne de calcul
existante (pas de revente ni d'autoconso directe créditée pour ce lot).

### Affichage
- Le récap T2 affiche le lot dédié : nombre, kWc dédié.
- Afficher l'énergie écrêtée annuelle (`Σ lostDedie`) pour la transparence commerciale.
- Le montant du devis TTC (`t2_devis`) reste saisi manuellement par le commercial (il inclut
  déjà le coût des panneaux dédiés). Pas de calcul de prix automatique.

---

## Chantier 3 — Nouveau commercial

Ajouter Anthony Debray dans les listes déroulantes commerciales.

Format existant : `value="Prénom|téléphone|email"`.

```html
<option value="Anthony|76.30.52|anthony.debray@solarconcept.nc">Anthony Debray — 76.30.52</option>
```

- À ajouter dans la liste du **header global** (cf. chantier 4, qui récupère le commercial
  de T1) et dans `t4_commercial` (ligne ~636).
- Email validé : `anthony.debray@solarconcept.nc`.

---

## Chantier 4 — Header client global (T1/T2/T3) — T4 séparé

### Besoin
Saisir l'identité client une seule fois et la retrouver sur tous les onglets particuliers.

### Décision
- Ajouter un **bandeau global** au-dessus de la barre d'onglets, avec :
  **Nom**, **Prénom**, **Adresse**, **Commercial** (le commercial migre de T1 vers ce bandeau).
- Identifiants proposés : `hdr_nom`, `hdr_prenom`, `hdr_adresse`, `hdr_commercial`.
- Saisi une fois, repris dans les récaps et impressions de **T1, T2, T3**.
- **T4 reste totalement séparé** : il garde ses champs PRO existants
  (`t4_nom`, `t4_ref`, `t4_commune`, `t4_commercial`). Pas de Prénom côté PRO.

### Refactor
- Supprimer de T1 (`tab0`) les champs `t1_client`, `t1_adresse`, `t1_commercial`
  (lignes ~460-470) devenus globaux.
- Recâbler tous les consommateurs vers les nouveaux IDs `hdr_*`. Points repérés (à revérifier
  à l'implémentation) :
  - `t1_client` / `t1_adresse` / `t1_commercial` : lignes ~1660, 1680, 1781, 1790, 1915, 1925, 2355.
  - `lastStudyData.client` / `.adresse` / `.commercial` : lignes ~778, 2451, 2478.
- Ajouter le rendu de l'identité client dans les récaps/impressions de **T2 et T3**
  (qui n'affichent rien aujourd'hui).

---

## Vérification (après implémentation)

1. **Syntaxe JS** (obligatoire, cf. CLAUDE.md) :
   ```bash
   node -e "const fs=require('fs');const html=fs.readFileSync('calculateur-pv-nc.html','utf8');const m=html.match(/<script>([\s\S]*?)<\/script>/g);if(m){const js=m.map(s=>s.replace(/<\/?script>/g,'')).join('\n');fs.writeFileSync('_check.js',js);}" && node --check _check.js && echo "SYNTAXE OK"
   ```
2. **Production** : vérifier que `prodM(1, 4.2, 10)` redonne une répartition mensuelle conforme
   à `IDX` et un total annuel ≈ 1 370 kWh.
3. **T1/T2/T3/T4** : lancer un calcul sur chaque onglet, vérifier l'absence d'erreur console
   et la cohérence des graphiques de production mensuelle (creux d'hiver visible).
4. **Panneaux dédiés T2** : avec nb=0, résultat identique à l'actuel ; avec nb>0, décharge
   batterie accrue et énergie écrêtée affichée.
5. **Header global** : saisir Nom/Prénom/Adresse/Commercial, vérifier la reprise sur T1/T2/T3
   (écran + impression). T4 inchangé.
6. **Commercial** : Anthony Debray présent dans header global et T4.
7. **Impression** (print) de chaque onglet : pas de régression de mise en page.

## Hors périmètre
- Pas de calcul automatique du prix des panneaux dédiés (devis saisi à la main).
- Pas de revente/autoconso pour le lot dédié batterie.
- Pas de modification de la charte graphique ni des dépendances (Plotly 2.27 conservé).

# Comptes rendus de session

Un fichier par session de travail, nommé `AAAA-MM-JJ-sujet.md` — convention propre à ce dépôt
(pas de numéro de séance, contrairement au reste du portfolio).

**Rituel v3** (04/08/2026) : un fichier **figé**, jamais modifié après coup, et **le dernier porte
l'état du projet**. Il n'y a plus ni `ETAT.md` ni tableau récapitulatif ici : ils recopiaient ce que
les fiches disaient déjà. Pour savoir où on en est, lire la dernière : `ls docs/sessions/ | tail -1`.

## À quoi ça sert

Retrouver, des mois plus tard, **pourquoi** une décision a été prise — pas seulement
ce qui a été fait. Le code dit le quoi, git dit le quand, ces fichiers disent le
pourquoi et ce qui a été écarté en chemin.

## Structure — quatre sections

```markdown
# AAAA-MM-JJ — sujet

## Fait           ce qui a été réalisé, découvert, déployé
## Décidé         les arbitrages actés (durables → aussi dans le CLAUDE.md)
## Reste ouvert   ⚠️ l'état : ce qui bloque, ce qui traîne, ce qui est à trancher
## Reprise        par où repartir à la prochaine séance
```

⚠️ **« Reste ouvert » se recopie d'une fiche à l'autre, expurgé de ce qui est fait.** C'est ce qui
permet à la dernière fiche de tenir lieu d'état courant.

## Ce qu'un compte rendu doit contenir

- la demande de départ, dans les mots du client ;
- le diagnostic, chiffré quand c'est possible ;
- les décisions et surtout **les arbitrages** — ce qui a été essayé puis rejeté, et
  la raison ;
- les dérogations assumées aux règles du projet (charte, périmètre) ;
- les défauts trouvés en route, y compris ceux qui préexistaient ;
- les erreurs de méthode, sans les arrondir ;
- ce qui reste ouvert à la fin.

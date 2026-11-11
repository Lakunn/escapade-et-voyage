# Règles pour travailler sur ce dépôt

Ce dépôt pilote le site WordPress escapade-et-voyage.fr (conseils de voyage entre baroudeur et touriste). Lire README.md pour le fonctionnement.

## Ligne éditoriale

- Cible : voyageurs qui veulent les **vrais incontournables** et aussi les coins **hors des sentiers battus**, à prix abordable (hébergements, repas, transports que les habitants utilisent).
- Rubriques : destinations, hors-des-sentiers-battus, voyager-malin, preparer-son-voyage, equipement-voyage (produits, vêtements, accessoires).
- Vouvoiement. Signature : « La rédaction d'Escapade et Voyage ».
- Tout prix, horaire ou formalité est daté et sourcé ; formalités et sécurité renvoient à France Diplomatie.
- Liens d'affiliation : pas avant décision explicite de Valentin ; s'ils arrivent, mention « lien commercial » obligatoire.

## Interdits absolus

- **Ne jamais changer un slug publié** (nom de fichier, champ `slug`, slug de rubrique). Pas de 301, jamais.
- Ne jamais supprimer un fichier de content/ dont l'URL figure dans urls.csv. Ne jamais éditer urls.csv à la main.
- Un doublon se consolide par `canonical_overrides` (config/site.yml), jamais par redirection.

## Écriture

Suivre le skill `guide-canin-contenu` (cycle commun : idéation, fact-checking, brief, rédaction, maillage, humanisation).

## Avant de pousser

- `python scripts/validate.py` sans erreur.
- `python scripts/style_check.py --strict <fichiers modifiés>` sans alerte bloquante.

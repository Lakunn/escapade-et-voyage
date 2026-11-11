---
name: "guide-canin-contenu"
description: "Créer ou réécrire un contenu pour guide-canin.fr ou valentinrouault.com : idéation, fact-checking, brief, rédaction au format du dépôt git, maillage interne, médias, puis humanisation (tirets longs, voix passive, formules d'IA)."
---

# Création de contenu : guide-canin.fr et valentinrouault.com

Ces lignes directrices s'appliquent aux deux sites de l'utilisateur, chacun piloté par un dépôt git où chaque contenu est un fichier Markdown publié automatiquement :

| Site | Dépôt | Sujet |
|---|---|---|
| guide-canin.fr | `Lakunn/guide-canin` | Guide pratique sur les chiens |
| valentinrouault.com | `Lakunn/valentinrouault-media` | Média SEO / GEO |

Commencer par identifier le site concerné, puis lire la section « Spécificités par site » en fin de document : signature, sources de référence et règles d'URL diffèrent.

Le cycle d'un contenu compte six étapes, **dans l'ordre**. Ne pas sauter une étape, ne pas rédiger avant d'avoir validé le brief.

Règles communes aux deux sites : aucune expérience personnelle inventée, aucune monétisation (pas d'affiliation, pas de recommandation payée, pas d'appel commercial), et **aucun slug, aucune rubrique d'un contenu existant ne change** (zéro redirection 301).

## Étape 1 : idéation

Objectif : choisir un sujet qui répond à une vraie demande et qui n'existe pas déjà sur le site.

1. **Sources de sujets** : questions des « Autres questions posées » de Google, requêtes de la Search Console si l'utilisateur les fournit, rubriques peu fournies du site, questions récurrentes sur les forums canins, saisonnalité (chaleur l'été, chenilles processionnaires au printemps, pétards au Nouvel An).
2. **Vérifier l'existant** : chercher dans `content/posts/*.md` (titres, slugs, mots-clés) et dans `urls.csv`. Si un article couvre déjà la même intention, proposer de le **mettre à jour** plutôt que d'en créer un nouveau (cannibalisation).
3. **Livrer une liste** de 5 à 10 idées sous forme de tableau : sujet, requête principale, intention (info, comparaison, urgence, pratique), rubrique existante (slug de `config/site.yml`), angle distinctif, priorité. Les sujets de santé urgente (intoxication, coup de chaleur) passent en priorité haute.

Demander à l'utilisateur de choisir avant de continuer.

## Étape 2 : fact-checking

Objectif : rassembler les faits **avant** d'écrire, chacun avec sa source. Faire les recherches web nécessaires, une par point de fait important.

Hiérarchie des sources pour guide-canin.fr (pour valentinrouault.com, voir les spécificités par site), de la plus fiable à la moins fiable :

1. **Organismes vétérinaires et sanitaires** : WSAVA, AAHA, ANSES, Ordre national des vétérinaires, centres antipoison vétérinaires (CNITV Lyon, CAPAE-Ouest), écoles vétérinaires (ENVA, VetAgro Sup, Oniris, ENVT).
2. **Publications scientifiques** : articles évalués par des pairs (PubMed), avec année.
3. **Textes officiels** pour le droit : Légifrance, service-public.fr, ministère de l'Agriculture (identification, chiens catégorisés, voyages, vaccins obligatoires).
4. **Références reconnues** : ASPCA (aliments toxiques), Société Centrale Canine et FCI (standards de races), Merck Veterinary Manual.

À éviter comme source : blogs, sites marchands, forums, contenus générés, articles sans auteur ni date.

Produire un **tableau de faits** : affirmation, source (nom + URL), date de la source, niveau de certitude. Toute affirmation sans source fiable est retirée ou formulée comme une opinion clairement signalée.

Règles santé (guide-canin.fr), non négociables :
- **jamais de dose de médicament**, humain ou vétérinaire ; renvoyer au vétérinaire ;
- jamais de « dose acceptable » pour un toxique ; en cas d'ingestion : vétérinaire ou centre antipoison immédiatement ;
- chaque article santé contient un encadré « Quand consulter en urgence » ;
- les remèdes naturels ne sont présentés que si une source sérieuse les documente, avec leurs limites.

## Étape 3 : brief

Avant de rédiger, écrire le brief et le faire valider :

```
Sujet / requête principale :
Intention de recherche :
Lecteur visé et sa situation :
Ce que la première page de Google propose déjà (formats, angles) :
Notre angle distinctif :
Plan (H2 / H3) avec la réponse attendue sous chaque titre :
Faits sourcés à utiliser (renvoi au tableau de l'étape 2) :
Outil du site à intégrer, s'il y en a un (guide-canin : ration, âge, quiz race, budget, aliments) :
Liens internes sortants prévus (3 à 6, URL existantes uniquement) :
Pages existantes à modifier pour ajouter un lien vers ce contenu (2 à 4) :
Médias prévus (images, schéma, vidéo YouTube) et leur rôle :
Questions de la FAQ :
Rubrique (slug) :
```

## Étape 4 : rédaction

Format du fichier `content/posts/<slug>.md` :

```markdown
---
title: "Titre (H1), explicite, sans point d'exclamation"
slug: slug-court-sans-mots-vides
status: draft
date: AAAA-MM-JJT09:00:00
origin: new
categories: [slug-rubrique]
dek: "Chapô de 1 à 2 phrases qui répond à la question."
seo_title: "30 à 65 caractères"
meta_description: "110 à 160 caractères"
essentiel:
  - "3 à 4 points clés, chacun autoportant."
sources:
  - "Nom de la source, titre, année : URL"
---
```

Règles :
- **réécriture d'un article existant** : garder `slug`, `wp_id`, `date`, `url` et **les rubriques à l'identique** (sur guide-canin.fr la rubrique fait partie de l'URL), passer `origin: rewrite` ;
- **vouvoiement** partout ;
- réponse directe dans la première phrase sous chaque H2 ;
- un paragraphe = une idée, 2 à 4 phrases ;
- listes pour les étapes, tableaux pour les comparaisons ;
- les outils s'insèrent avec leur shortcode, sur une ligne seule : `[gc_ration]`, `[gc_age]`, `[gc_race]`, `[gc_budget]`, `[gc_aliments]` ;
- une section `## Sources` en fin d'article, liste des sources citées avec liens ;
- FAQ éventuelle dans `<section class="faq" markdown="1">` avec des H3 ;
- images : texte alternatif descriptif obligatoire.

## Étape 5 : maillage interne et médias

### Maillage interne

1. **Liens sortants** : 3 à 6 liens vers des contenus existants du même site, placés dans le texte là où le lecteur en a besoin (pas en liste à la fin). Ancres descriptives, jamais « cliquez ici », jamais la même ancre vers deux pages différentes.
2. **Liens entrants** : identifier 2 à 4 contenus existants qui parlent du sujet (recherche dans `content/`), et y ajouter un lien contextuel vers le nouveau contenu. Ces fichiers sont modifiés dans le même commit.
3. **Pages piliers** : chaque contenu est relié au guide de référence de sa rubrique, et le guide pointe vers lui.
4. **Vérification** : tous les liens sont relatifs et pointent vers des URL qui existent (`urls.csv` ou fichiers de `content/`). Lancer `python scripts/validate.py`, qui signale les liens internes cassés.

### Médias

- **Images** : photos de l'utilisateur ou images sous licence libre vérifiée, avec attribution, déposées dans `content/media/` et insérées en Markdown `![texte alternatif descriptif](media/nom-explicite.webp)`. La synchro les téléverse dans WordPress. WebP ou JPG, 1600 px de large au maximum, nom de fichier en français avec tirets. Jamais d'image trouvée sur le web sans licence vérifiée, ni de photo d'une personne réelle.
- **Schémas et infographies** : quand une explication gagne à être visualisée (étapes, comparaison, chiffres), créer un schéma SVG simple dans `content/media/`, avec un texte alternatif qui en reprend l'information.
- **Vidéos YouTube** : seulement si une vidéo apporte un vrai plus (geste de soin, exercice d'éducation, démonstration) et vient d'une source fiable (vétérinaire, école, institution, chaîne reconnue). Coller l'URL seule sur sa ligne : le thème affiche un lecteur léger qui ne charge YouTube qu'au clic. Ajouter une phrase qui résume ce que montre la vidéo.
- **Image de couverture** : champs `cover: media/…` et `cover_alt:` dans l'en-tête.

## Étape 6 : humanisation

Relire le texte entier pour supprimer les tics d'écriture des IA, puis lancer le contrôle :

```bash
python scripts/style_check.py content/posts/<slug>.md
```

Corriger **toutes** les alertes ✗ (bloquantes) et traiter les alertes · une par une :

- **tirets cadratins et demi-cadratins** comme ponctuation (« les chiens — nos amis — ») : remplacer par une virgule, des parenthèses, deux-points ou une nouvelle phrase ;
- **voix passive** (« le chien est nourri par ») : remettre un sujet qui agit (« vous nourrissez le chien ») ; garder le passif seulement quand l'agent est inconnu ou sans intérêt ;
- **formules creuses** : « il est important de noter », « dans un monde où », « n'hésitez pas à », « véritable allié », « incontournable », « en conclusion »… : supprimer ou dire la chose directement ;
- **énumérations systématiques en trois** et structures parallèles à répétition : varier ;
- **gras** : au plus un ou deux passages par section, pour ce qui doit vraiment ressortir ;
- **rythme** : alterner phrases courtes et longues ; couper toute phrase de plus de 30 mots ;
- **questions rhétoriques** enchaînées : les remplacer par des affirmations ;
- **adverbes en -ment** : en supprimer la moitié ;
- **emojis** : aucun ;
- **conclusion qui résume** : supprimer ; finir sur une action concrète ou la FAQ ;
- **typographie française** : espace avant `; : ! ?`, guillemets « », pas de majuscule après deux-points ;
- **registre** : un seul, le vouvoiement, sur les deux sites.

Relancer `style_check.py` jusqu'à zéro alerte bloquante, puis lire le texte à voix haute mentalement : si une phrase ne serait pas dite par un humain qui connaît bien les chiens, la réécrire.

## Livraison

1. `python scripts/validate.py` sans erreur.
2. `python scripts/style_check.py --strict content/posts/<slug>.md` sans alerte bloquante.
3. Passer `status: publish` seulement si l'utilisateur a validé le texte.
4. Commit avec un message qui nomme le contenu, puis push sur `main` (déploiement automatique).
5. Donner à l'utilisateur : l'URL finale, le tableau des sources, les liens internes ajoutés (sortants et entrants), et les alertes de style restantes jugées acceptables.

## Spécificités par site

### guide-canin.fr

- **Signature** : « La rédaction de Guide Canin ». Aucun auteur individuel, aucune anecdote personnelle (« mon chien », « j'ai testé »).
- **Ton** : chaleureux et rassurant, sans infantiliser.
- **Sources** : hiérarchie vétérinaire de l'étape 2, règles santé non négociables, section `## Sources` en fin d'article.
- **URL** : elles contiennent la rubrique (`/sante/premiers-secours/slug/`). Un article existant ne change **jamais** de rubrique.
- **Outils** : intégrer l'outil pertinent par son shortcode (`[gc_ration]`, `[gc_age]`, `[gc_race]`, `[gc_budget]`, `[gc_aliments]`) et faire un lien vers sa page dans `/outils/`.

### valentinrouault.com

- **Signature** : Valentin Rouault. La première personne est permise pour **ses** retours d'expérience réels, fournis par lui ; ne jamais en inventer.
- **Ton** : éditorial de média ; aucune offre de prestation, aucun appel à prendre rendez-vous.
- **Sources** : documentation officielle (Google Search Central, Bing Webmaster, éditeurs d'IA), études identifiables avec auteur et année (Ahrefs, Semrush, SparkToro…), annonces datées. Toute affirmation datable est datée.
- **URL** : `/slug/` à la racine ; rubriques `blog` (GEO & IA), `seo`, `contenu-seo`, `actus-seo` et rubriques historiques. Pas d'outils interactifs.
- **Doublons** : ils se consolident par `canonical_overrides` dans `config/site.yml`, jamais par redirection.
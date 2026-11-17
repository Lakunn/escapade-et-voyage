---
name: escapade-contenu
description: "Créer ou réécrire un contenu pour escapade-et-voyage.fr : idée, données SERP et UGC réseaux sociaux par mot-clé (gain d'information), fact-checking des prix et formalités, brief SEO sémantique, rédaction très humanisée, maillage, contrôle algoproof. À utiliser pour tout article de voyage, itinéraire, guide de destination, conseil budget ou équipement."
---

# Contenu escapade-et-voyage.fr

Site de conseils de voyage « on & off the road » : les **vrais incontournables** et les coins **hors des sentiers battus**, à prix abordable. Lire d'abord `CLAUDE.md` (ligne éditoriale, interdits) et la grille commune [`algoproof.md`](algoproof.md) : ce skill l'applique au voyage.

Cycle en sept étapes, **dans l'ordre**. On ne rédige pas avant que Valentin ait validé le brief.

## 1. Idée et vérification de l'existant

1. Sources d'idées : suggestions et « Autres questions » Google, UGC (étape 2), saisonnalité (vacances scolaires, ponts, saison sèche d'une destination), outils du site à alimenter (budget, trajet voiture, décalage horaire, bagages, partage des dépenses).
2. Chercher dans `content/` et `urls.csv` un contenu qui couvre la même intention : si oui, **mettre à jour** plutôt que créer.
3. Livrer 5 à 10 idées en tableau : sujet, requête principale, intention, rubrique (`destinations`, `hors-des-sentiers-battus`, `voyager-malin`, `preparer-son-voyage`, `equipement-voyage`), gain d'information envisagé, priorité. Un sujet sans gain d'information possible est écarté.

Attendre le choix de Valentin.

## 2. Données : SERP + UGC par mot-clé

Lancer la collecte de l'outil (réutilise ses collecteurs ; ~0,002 $ la SERP, le reste gratuit) depuis le dépôt `marketing-intelligence` :

```bash
cd ../marketing-intelligence
.venv/Scripts/python.exe -m scripts.ugc_collect "road trip islande" --videos 8 --comments 40 --transcripts 2 --out ../escapade-et-voyage/.ugc
```

Le dossier `.ugc/` est hors git. Le relevé contient : top 10 Google avec extraits, blocs, Autres questions, recherches associées, AI Overview et ses sources ; suggestions « comment / combien / quel / avis / erreur… » ; vidéos YouTube qui se classent, avec leurs commentaires les plus aimés et la transcription des premières ; épingles Pinterest et sites les plus épinglés.

Reddit : le flux public renvoie 403 depuis novembre 2026. Compléter par une recherche web `site:reddit.com <sujet>` (r/VoyageFrance, r/travel, r/solotravel, subreddit du pays) et par les forums de voyageurs (forum du Routard, forums Tripadvisor), lus à la main. Pour une destination, relancer aussi la collecte en anglais (`--lang en --country US`) : les voyageurs anglophones documentent souvent mieux les coins peu connus.

Exploiter le relevé ainsi :

| Ce qu'on cherche dans l'UGC | Ce que ça devient dans l'article |
|---|---|
| Problèmes cités plusieurs fois (« la route F35 fermée en juin », « le bus n'existe plus ») | Encadré « Ce qui surprend sur place », pièges datés |
| Prix réels donnés par les voyageurs | Fourchette de prix datée, croisée avec une source officielle ou le site du prestataire |
| Lieux cités en dehors des listes habituelles | Section hors des sentiers battus (à vérifier : existe, accessible, pas privé) |
| Regrets (« si j'avais su ») | Erreurs à éviter, ordre d'itinéraire, durée minimale |
| Questions sans réponse claire dans les commentaires | H2 ou FAQ |
| Mots des voyageurs (« van aménagé », « 4x4 obligatoire ? ») | Vocabulaire des intertitres et des ancres |

Règles UGC : jamais de pseudonyme ni de citation nominative d'un internaute ; un témoignage n'est pas une source, c'est une piste à vérifier ; on écrit « des voyageurs signalent… » seulement si plusieurs le disent, avec la date du relevé.

## 3. Fact-checking

Tableau de faits avant d'écrire : affirmation, source (nom + URL), date, certitude. Hiérarchie :

1. **Officiel** : France Diplomatie « Conseils aux voyageurs » (sécurité, formalités : toujours renvoyer vers la fiche pays), sites des ambassades et des services d'immigration (visas, ETA, ESTA, ETIAS), Institut Pasteur et OMS (vaccins), service-public.fr (passeport, permis international).
2. **Opérateurs** : sites des compagnies de transport, parcs nationaux, offices de tourisme nationaux et régionaux (horaires, prix d'entrée, fermetures saisonnières, routes).
3. **Données** : Banque mondiale (niveau des prix, déjà dans le calculateur), instituts statistiques, météo officielle du pays.
4. **UGC et blogs** : uniquement pour repérer ce qu'il faut vérifier.

Tout prix, horaire, formalité ou règle est **daté** (« en novembre 2026 ») et sourcé. Un prix relevé sur place par Valentin peut alimenter le calculateur : front matter `budget: {pays: IS, petit: 70, moyen: 140, gros: 300}` (euros par adulte et par jour).

## 4. Brief

Suivre `algoproof.md` § 2, puis remplir :

```
Requête principale / intention / requêtes secondaires :
Lecteur visé (durée, budget, saison, avec qui il part) :
SERP : formats du top 10, blocs, ce que dit l'AI Overview et qui elle cite :
Entités attendues (lieux, routes, transports, prestataires, saisons, formalités) :
Sous-questions retenues (SERP, suggestions, UGC) → H2/H3 :
Ce que le top 10 dit déjà (à ne pas répéter longuement) :
GAIN D'INFORMATION (au moins un, nommé) :
Avis tranché de la rédaction (ce qu'on recommande, ce qu'on déconseille) :
Incontournables retenus / coins hors des sentiers battus retenus (vérifiés) :
Prix et formalités à dater (renvoi au tableau de faits) :
Outil du site à intégrer : [ev_budget] [ev_trajet] [ev_decalage] [ev_bagages] [ev_depenses] :
Plan H2/H3 avec la réponse attendue sous chaque titre :
Liens internes sortants (3 à 6) / pages à modifier pour lier ce contenu (2 à 4) :
Médias (photos de Valentin, carte, schéma d'itinéraire) :
seo_title / meta_description proposés :
```

Gains d'information typiques au voyage : itinéraire jour par jour avec temps de route réels ; budget poste par poste daté ; comparaison chiffrée (location de voiture contre bus, haute contre basse saison) ; tableau « quel mois pour quoi » ; liste des pièges remontés par l'UGC et vérifiés ; adresses et transports utilisés par les habitants.

## 5. Rédaction très humanisée

Format `content/posts/<slug>.md`, front matter : `title`, `slug`, `status: draft`, `date`, `origin: new`, `categories`, `dek`, `seo_title` (30 à 65 car.), `meta_description` (110 à 160 car.), `essentiel` (3 à 4 points), `sources`, `cover` et `cover_alt` si photo, `budget` si relevé sur place.

Voix d'Escapade et Voyage :

- **Vouvoiement**, signature collective. Le « nous » de la rédaction est permis pour un avis (« nous déconseillons… »), jamais pour une expérience inventée. Une expérience vécue n'apparaît que si Valentin l'a fournie.
- **Concret avant tout** : noms de lieux, routes, lignes de bus, horaires, prix, durées. Un paragraphe sans un seul détail vérifiable est à réécrire.
- **Un avis par section** : ce qui vaut le détour, ce qui ne le vaut pas, à quelle heure y aller, ce qu'on peut sauter. Le lecteur vient chercher un tri, pas un catalogue.
- **Incontournables honnêtes** : dire quand un lieu célèbre mérite la foule et comment l'éviter (heure, entrée secondaire, saison), et quand il ne la mérite pas.
- **Hors des sentiers battus vérifié** : accessibilité, saison, coût, et respect des lieux (propriété privée, zones fragiles, pas de spot que les habitants demandent de taire).
- **Prix des habitants** : à côté de l'option touristique, l'alternative locale chiffrée (cantine, bus régional, guesthouse).
- Réponse dans la première phrase sous chaque H2 ; une section se lit seule (les IA citent des passages).
- Tableaux pour les comparaisons et les budgets, liste numérotée pour l'itinéraire, prose pour le raisonnement.
- Phrases de longueurs variées ; des phrases courtes pour les conseils, plus longues pour expliquer un choix.

Interdits propres au voyage (en plus de `style_check.py`) : « joyau », « écrin », « niché au cœur de », « trésor caché », « à couper le souffle », « vue imprenable », « véritable paradis », « havre de paix », « dépaysement garanti », « mélange unique de tradition et de modernité », « pour tous les goûts », « que vous soyez aventurier ou… », introductions « Vous rêvez de… / Imaginez… / Envie d'évasion ? », conclusions « Bon voyage ! » qui résument l'article.

Test du nom propre (`algoproof.md` § 3.3) : remplacez « Islande » par « Norvège ». Si un paragraphe reste vrai, il est vide.

## 6. Maillage et médias

- 3 à 6 liens internes contextuels, 2 à 4 liens entrants ajoutés dans des contenus existants (même commit), lien vers la page de la rubrique et vers l'outil concerné dans `/outils/`.
- Formalités et sécurité : lien vers la fiche pays de France Diplomatie, avec la date de consultation.
- Photos : celles de Valentin en priorité, ou sous licence libre vérifiée avec attribution, dans `content/media/` (WebP, 1600 px max, nom en français), texte alternatif qui décrit le lieu. Jamais d'image sans licence, ni de visage identifiable sans accord.
- Schéma d'itinéraire ou carte simple en SVG quand le parcours compte.

## 7. Contrôle et livraison

1. Contrôle final de `algoproof.md` § 4, point par point.
2. `python scripts/style_check.py --strict content/posts/<slug>.md` : zéro alerte bloquante ; traiter les alertes « vocabulaire IA », « transitions » et « moule ».
3. `python scripts/validate.py` sans erreur.
4. `status: publish` (ou `future` avec une date) seulement après validation du texte par Valentin. Le push sur `main` publie : le demander avant.
5. Rendre : URL, tableau des sources, gain d'information retenu, liens ajoutés, alertes de style restantes.

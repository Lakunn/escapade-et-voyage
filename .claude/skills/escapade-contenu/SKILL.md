---
name: escapade-contenu
description: "Créer ou réécrire un contenu pour escapade-et-voyage.fr : idée, données SERP et UGC réseaux sociaux par mot-clé (gain d'information), fact-checking des prix et formalités, brief SEO sémantique, rédaction très humanisée, maillage, contrôle algoproof. À utiliser pour tout article de voyage, itinéraire, guide de destination, conseil budget ou équipement."
---

# Contenu escapade-et-voyage.fr

Site de conseils de voyage « on & off the road » : les **vrais incontournables** et les coins **hors des sentiers battus**, à prix abordable. Lire d'abord `CLAUDE.md` (ligne éditoriale, interdits) et la grille commune [`algoproof.md`](algoproof.md) : ce skill l'applique au voyage.

Cycle en huit étapes, **dans l'ordre**, précédé de la carte des mots-clés. Valentin ne veut pas être sollicité à chaque étape : on choisit les sujets d'après la carte, on rédige, on contrôle, et on lui présente le lot terminé avant le push (le push publie).

## 0. Carte des mots-clés, veille et volumes (commun aux 4 sites)

- **Sujets de fond** : `config/keywords.yml` (calendrier lisible dans `keywords/calendrier.md`), régénéré le 1er du mois par le workflow « Carte des mots-clés » (`scripts/keyword_map.py`, identique dans les 4 dépôts ; graines, rubriques et exclusions dans `config/keyword_seeds.yml`). Prendre le prochain sujet du calendrier ; `statut: existe_peut_etre` = un article existant couvre peut-être déjà le sujet : vérifier et **mettre à jour** plutôt que créer.
- **Volumes** : la carte prend, dans l'ordre, `config/volumes.yml` (relevés Keyword Surfer), DataForSEO, Bing, sinon l'indice Google Suggest (« à relever »). Pour relever : `python scripts/keyword_map.py --a-relever` donne la liste ; dans le Chrome de Valentin, recherche google.fr de chaque requête, lecture du tableau « Keyword ideas » de Surfer ; **au plus ~30 recherches d'affilée** (au-delà Google affiche un CAPTCHA, qu'on ne résout jamais) ; consigner la formulation la plus recherchée et ses variantes dans `config/volumes.yml`, puis relancer le script (gratuit grâce au cache).
- **Actualité** : `veille/AAAA-MM-JJ.md` et `veille/plan.md` (workflow de veille, `scripts/veille.py` identique dans les 4 dépôts, flux dans `config/veille.yml`). Une règle, un prix ou une formalité qui change : mise à jour datée de l'article concerné avant tout nouvel article.
- Renseigner `keyword` (requête principale de la carte) et `keywords_secondaires` dans le front matter de chaque nouvel article : la carte suivante le marque alors `programme` ou `publie`.
- Récapitulatif chaque lundi par e-mail (n8n, `growww-site/deploy/n8n/`).
- Spécifique à escapade : graines larges (« voyage », « week end », « quand partir », « voyage en famille »…), second niveau par destination, regroupement des « où partir en <mois> », sujets saisonniers placés 3 à 10 semaines avant leur mois, **2 articles par semaine** (ralenti le 18/11/2026 : on ne publie que si l'article apporte du vécu crédité, § 2 bis). **Destinations prioritaires** marquées ★ dans le calendrier (`focus` dans `config/keyword_seeds.yml` : Japon, La Réunion, Écosse) : on les couvre à fond (saison, budget, itinéraire, hors des sentiers battus, en famille) et chaque nouvel article d'une destination prioritaire lie les autres articles de la même destination. Biais d'adresse IP de Google Suggest en local (villes bretonnes exclues) ; dans GitHub Actions les suggestions viennent de serveurs hors de France avec `gl=fr`.

## 1. Choix du sujet et vérification de l'existant

1. Prendre le prochain sujet du `calendrier` de `config/keywords.yml` (ou un sujet d'actualité de `veille/AAAA-MM-JJ.md` quand il rend un article faux ou ouvre un vrai besoin).
2. Chercher dans `content/` et `urls.csv` un contenu qui couvre la même intention : si oui, **mettre à jour** plutôt que créer. `validate.py` bloque deux articles sur la même requête.
3. Vérifier qu'aucun autre site de Valentin ne vise la même requête (animaux : guidecanin.fr) ; sinon, angle voyage strict et lien vers l'autre site.
4. Un sujet sans gain d'information possible est sauté et marqué dans le compte rendu.

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

Règles UGC : un témoignage n'est pas une source pour un prix, un horaire ou une formalité, c'est une piste à vérifier (§ 3). En revanche, c'est la source du **vécu**, et il est alors cité nommément (§ 2 bis).

## 2 bis. Le vécu : témoignages des réseaux sociaux, crédités

Escapade n'invente aucune expérience et la rédaction n'a pas tout parcouru : le vécu vient des voyageurs qui l'ont publié, **cités avec le nom du compte ou de la personne et un lien vers la publication**. C'est le gain d'information que le top 10 n'a pas, et c'est honnête envers le lecteur et l'auteur.

Où chercher (par destination, en français puis en anglais) : commentaires YouTube du relevé (auteur et lien direct `&lc=` fournis par `ugc_collect`), vidéos et descriptions YouTube, TikTok et Instagram (recherche du lieu ou du hashtag dans le Chrome de Valentin), Reddit (`site:reddit.com`), blogs de voyageurs, forums (Routard, Tripadvisor), avis Google Maps d'un lieu précis.

Ce qu'on retient : un détail qu'on ne trouve qu'en y étant allé (temps réel d'une randonnée, bus qui ne passe plus, prix payé, foule à telle heure, erreur commise, coin trouvé par hasard), **daté**. Pas les avis vagues (« magnifique, à faire absolument »).

Comment on cite :

- Formule : « Le 12 mars 2026, @compte (TikTok) raconte avoir mis 4 h 30 pour… » ou « Sur r/JapanTravel, u/pseudo signale en octobre 2025 que… », avec **le lien vers la publication** sur le nom du compte. Nom de chaîne, de compte, ou nom de la personne si elle publie sous son nom (créateur, blogueur) ; jamais de nom réel deviné derrière un pseudonyme.
- Citation **courte** (une phrase, moins de 25 mots) entre guillemets, traduite si elle est en anglais (« traduit par nos soins ») ; le reste en paraphrase. Jamais de texte ou de transcription recopié en bloc.
- Comptes publics uniquement, publications publiques. Rien qui expose une personne (enfants identifiables, adresse, données de santé, propos dont l'auteur pourrait pâtir) : dans ce cas, paraphrase sans nom.
- Une vidéo YouTube peut être intégrée (URL seule sur sa ligne). Une photo ou une vidéo TikTok/Instagram ne se télécharge jamais : lien seulement, sauf accord écrit de l'auteur.
- Un témoignage illustre, il ne prouve pas : un prix ou une règle cités par un voyageur sont recoupés (§ 3) et la différence signalée (« en 2024 ; le tarif officiel est passé à… en 2026 »).
- Viser **3 à 6 témoignages crédités** par article, de sources différentes, dont au moins un qui nuance ou contredit l'avis majoritaire.
- Front matter `temoignages` : liste `{auteur, plateforme, url, date}` pour pouvoir les revérifier à la mise à jour (un lien mort se remplace ou se retire).

Un article sans aucun témoignage crédité ni donnée propre ne se publie pas : on choisit un autre sujet du calendrier.

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
Témoignages crédités retenus (auteur, plateforme, lien, date, ce qu'ils apportent) :
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

Format `content/posts/<slug>.md`, front matter : `title`, `slug`, `status: draft`, `date`, `origin: new`, `categories`, `keyword` (requête principale de la carte), `keywords_secondaires` (requêtes du groupe), `dek`, `seo_title` (30 à 65 car.), `meta_description` (110 à 160 car.), `essentiel` (3 à 4 points), `sources`, `temoignages` (§ 2 bis), `cover` et `cover_alt` si photo, `budget` si relevé sur place.

Voix d'Escapade et Voyage :

- **Vouvoiement**, signature collective. Le « nous » de la rédaction est permis pour un avis (« nous déconseillons… »), jamais pour une expérience inventée. Une expérience vécue n'apparaît que si Valentin l'a fournie ou si elle est citée d'un voyageur nommé, avec lien (§ 2 bis).
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
4. `status: future` avec la date du calendrier. Le push sur `main` publie : présenter le lot à Valentin et pousser après son accord.
5. Rendre : URL, requête et score de la carte, tableau des sources, gain d'information retenu, liens ajoutés, alertes de style restantes.
6. Relancer `scripts/keyword_map.py` : le sujet passe en `programme` dans la carte.

## 8. Suivi après publication

- **J+7** : URL indexée ? (Search Console, inspection d'URL ; sinon IndexNow est déjà parti au déploiement).
- **J+30** : requêtes réelles et position. Une requête en position 8 à 30 absente du texte → H2 ou FAQ à ajouter ; une requête qui relève d'une autre intention → idée pour la carte.
- **J+90** : rien en top 30 → réécrire selon le top 10 du moment, ou fusionner avec un article proche par `canonical_overrides`.
- Chaque lundi, lire `veille/AAAA-MM-JJ.md` (workflow « 7 · Veille ») : une formalité, une taxe ou une règle qui change → mise à jour datée de l'article concerné avant tout nouvel article.

# Grille « algoproof » : contenu qui résiste aux mises à jour de Google et que les IA citent

Fichier commun aux skills de contenu des sites de Valentin (escapade-et-voyage.fr, guidecanin.fr, valentinrouault.com, growww.app). Il dit **ce que les études établissent**, **ce qu'il faut mettre dans un brief**, et **ce qui trahit un texte écrit par une IA**. Mis à jour le 17/11/2026 ; à relire quand une étude ou une mise à jour majeure change la donne.

Principe : Google ne sanctionne pas l'outil, il sanctionne l'absence d'effort, d'originalité et de valeur ajoutée. Mais les textes IA « bruts » ont statistiquement moins d'impressions et sont moins indexés. Un contenu algoproof est donc un contenu **qu'aucune IA n'aurait pu écrire seule**, parce qu'il contient de la matière qu'elle n'a pas.

## 1. Ce que disent les sources (et avec quel niveau de preuve)

| Source | Ce qu'elle établit | Niveau de preuve |
|---|---|---|
| Google, « Creating helpful, reliable, people-first content » (Search Central) | Questions Who / How / Why : qui a écrit, comment (dire quand l'automatisation a servi), pourquoi (pour aider, pas pour ranker). Contenu original, analyse au-delà de l'évident, expérience de première main. | Officiel |
| Consignes des Quality Raters, mise à jour de janvier 2025 (section 4.6.6 et suivantes) | Note « Lowest » quand tout ou presque du contenu principal est copié, paraphrasé, généré automatiquement ou par IA **avec peu ou pas d'effort, d'originalité ni de valeur ajoutée**. L'usage de l'IA seul ne détermine pas la note. Le contenu produit à grande échelle sans valeur est « Lowest », qu'il vienne d'humains ou d'IA. | Officiel (sert à évaluer et entraîner, pas une règle de classement directe) |
| Politiques anti-spam de Google (mars 2024) | « Scaled content abuse » : beaucoup de pages produites pour manipuler le classement, quel que soit l'outil. « Site reputation abuse », domaines expirés. | Officiel |
| Fuite de la documentation « Content Warehouse » (mai 2024) | Attributs nommés `contentEffort` (estimation par LLM de l'effort humain d'une page), `OriginalContentScore`, `siteFocusScore` et `siteRadius` (cohérence thématique du site et écart d'une page à ce thème), NavBoost (clics satisfaisants, `lastLongestClicks`), décrit aussi sous serment au procès antitrust américain. | Interprétations de tiers, non confirmées par Google |
| Brevet Google « Contextual estimation of link information gain » (US11354342B2) | Score de ce qu'un document apporte **en plus** des documents déjà vus par l'utilisateur. Contexte surtout assistants et réponses IA. | Brevet (rien ne prouve son usage en classement organique) |
| Ahrefs, juillet 2025 (600 000 pages, 100 000 mots-clés) | Corrélation quasi nulle (0,011) entre part d'IA et position ; 86,5 % des pages du top contiennent un peu d'IA ; les n°1 en contiennent légèrement moins. | Corrélation, détecteur maison |
| Ahrefs, 27 juillet 2026 (« Google Doesn't Punish AI Content; It Punishes Bad Content », 331 000 pages) | Pages très marquées IA : **2 à 3 fois moins d'impressions**, indexation estimée 40 % contre 49 % pour les moins marquées, un peu plus fréquentes en bas du top 10. | Corrélation, détecteur maison |
| Aggarwal et al., « GEO: Generative Engine Optimization », KDD 2024 (Princeton, IIT Delhi, Allen AI) | Ajouter des **citations de sources, des citations textuelles et des statistiques** augmente la visibilité dans les réponses génératives (jusqu'à +40 %, +37 % mesuré sur Perplexity) ; l'efficacité dépend du domaine. Le bourrage de mots-clés n'aide pas. | Étude évaluée par des pairs |
| Études de citations IA 2025-2026 (Ahrefs, BrightEdge, Seer Interactive, AirOps) | Le recouvrement entre top 10 Google et sources des AI Overviews baisse (76 % mi-2025, 38 % début 2026 selon Ahrefs) ; les pages avec listes **et** tableaux sont un peu plus citées par ChatGPT ; les contenus datés de l'année en cours progressent, les vieilles listes sont purgées. | Études d'éditeurs, méthodes variables |
| Kobak et al., « Delving into ChatGPT usage in academic writing through excess vocabulary » (2024, 14 M de résumés PubMed) | Les LLM laissent une empreinte lexicale mesurable : « delves » ×28, « showcasing », « underscores »… Au moins 10 % des résumés de 2024 passés par un LLM. | Étude scientifique |
| Wikipédia, « Signs of AI writing » (WikiProject AI Cleanup) | Catalogue des marques d'écriture IA (importance gonflée, vocabulaire, gras, formules). Les détecteurs automatiques sont jugés peu fiables : c'est la lecture humaine qui compte. | Guide collaboratif |

Ce qu'on en tire, en une phrase par point :
1. **L'effort doit se voir** : données propres, terrain, tests, sources primaires, médias originaux.
2. **Le gain d'information est le critère n°1** : chaque article contient au moins un élément absent du top 10 actuel.
3. **La cohérence thématique du site compte** : pas d'article hors ligne éditoriale pour « prendre du trafic ».
4. **Le clic satisfaisant compte** : répondre vite, tenir la promesse du titre, ne pas faire rebondir.
5. **Pour être cité par les IA** : faits sourcés, chiffres datés, citations exactes, passages autoportants.
6. **Pas d'échelle sans valeur** : jamais de série de pages quasi identiques, jamais de rythme qui sent l'usine.

## 2. Critères du brief (SEO sémantique)

Le brief se construit sur des **données relevées**, pas sur l'intuition. Pour chaque article :

### 2.1 Intention et SERP
- Requête principale, intention dominante (savoir, comparer, faire, acheter, urgence) et intentions secondaires.
- Ce que montre la SERP : formats du top 10 (guide, liste, comparatif, fiche, vidéo), blocs présents (AI Overview, Autres questions, vidéos, pack local, images). L'outil de l'agence le donne : SERP reconstituée de la Fiche mot-clé, ou outil gratuit « Ce que Google affiche » sur growww.app.
- Le format retenu suit l'intention : on ne répond pas par un guide de 3 000 mots à une question qui appelle un tableau.

### 2.2 Couverture sémantique (entités et sous-sujets)
- **Entités attendues** : lieux, marques, races, organismes, concepts, chiffres que tous les bons résultats mentionnent. Les lister depuis le top 10, les questions Google, les suggestions, les recherches associées.
- **Sous-questions** : chaque question réelle (suggestions « comment / pourquoi / combien », Autres questions posées, UGC) devient un H2 ou H3 si elle relève de l'intention, sinon elle part dans un autre article ou dans la FAQ.
- **Vocabulaire du lecteur** : reprendre les mots des internautes (UGC), pas seulement ceux des experts. C'est ce qui fait matcher les requêtes longues.
- Pas de densité de mot-clé : la requête apparaît naturellement dans le titre, le H1, l'introduction et un ou deux intertitres. Les variantes viennent d'elles-mêmes si le sujet est couvert.

### 2.3 Gain d'information (obligatoire)
Lister ce que le top 10 dit déjà, puis écrire **au moins un** apport qu'il n'a pas, et le nommer dans le brief :
- donnée propre (calcul, relevé de prix daté, comparaison chiffrée, extraction d'étude) ;
- terrain ou expérience réelle (fournie par Valentin ou documentée par une source nommée) ;
- synthèse de retours d'internautes (UGC) : problèmes récurrents, erreurs, astuces que personne n'écrit ;
- vérification : une idée reçue confrontée à une source primaire ou une étude ;
- outil ou schéma original (calculateur du site, carte, tableau de décision).

Un sujet sans gain d'information possible **ne s'écrit pas** : le noter « à surveiller » ou mettre à jour un article existant.

### 2.4 Structure pensée pour Google et les IA
- **Réponse d'abord** : le chapô et la première phrase sous chaque H2 répondent, sans préambule. Les détails viennent après.
- **Passages autoportants** : chaque section se comprend seule (les IA citent des passages, pas des pages). Reprendre le sujet dans la phrase plutôt qu'un pronom renvoyant à la section précédente.
- **Intertitres = questions ou promesses concrètes** formulées comme le lecteur les taperait.
- **Tableaux** pour toute comparaison, **listes numérotées** pour toute procédure. Pas de liste pour ce qui est un raisonnement.
- **Chiffres datés et sourcés** dans le texte (« 14 € la nuit en dortoir en octobre 2026, relevé sur… »), citations textuelles courtes d'experts ou de documents officiels.
- Date de mise à jour visible et vraie ; une mise à jour réelle change le fond, pas seulement la date.

### 2.5 Confiance (E-E-A-T)
- Signature conforme au site, page auteur ou page « à propos » à jour.
- Sources primaires en fin d'article ; sujets YMYL (santé, argent, sécurité, droit) : sources officielles ou scientifiques uniquement.
- Aucune expérience, aucun test, aucun client, aucune citation inventés. Ce qu'on n'a pas vérifié ne s'écrit pas comme un fait.
- Médias originaux de préférence (photos de Valentin, captures, schémas faits pour l'article).

### 2.6 Snippets et clic
- `seo_title` : la requête au début, une promesse précise, 30 à 65 caractères ; pas de « guide complet » ni d'année si le contenu n'est pas tenu à jour.
- `meta_description` : la réponse ou l'apport distinctif, 110 à 160 caractères.
- Le titre tient sa promesse dès l'écran d'arrivée (NavBoost : un clic qui revient vite à Google est un mauvais clic).

### 2.7 Maillage et cohérence du site
- 3 à 6 liens sortants contextuels vers des pages existantes, 2 à 4 liens entrants ajoutés, lien avec la page pilier de la rubrique.
- Vérifier la cannibalisation (même intention qu'une page existante : mettre à jour plutôt que créer).

## 3. Ce qui trahit l'IA (à traquer à la relecture)

Les détecteurs sont peu fiables ; ce qui compte, c'est qu'un lecteur et un évaluateur ne puissent pas « sentir » la machine. Les marques ci-dessous viennent des études lexicales (Kobak 2024), du guide de Wikipédia et de l'observation des textes générés en français.

### 3.1 Lexique
- **Formules creuses** (bloquées par `style_check.py`) : « dans un monde où », « il est important de noter », « n'hésitez pas à », « véritable allié », « incontournable », « en conclusion », « plongeons », « que vous soyez… ou… », « à l'ère de », « pierre angulaire », « en constante évolution »…
- **Verbes et noms passe-partout** : « offrir » (« la ville offre une vue… »), « permettre de », « souligner », « témoigner de », « favoriser », « garantir », « explorer », « découvrir », « expérience », « univers », « richesse », « authentique ». Un ou deux passent, une avalanche signe le texte.
- **Superlatifs et clichés** (voyage surtout) : « joyau », « écrin », « niché au cœur de », « trésor caché », « à couper le souffle », « vue imprenable », « véritable paradis », « havre de paix », « expérience inoubliable », « mélange unique de tradition et de modernité ».
- **Calques de l'anglais** : « adresser un problème », « faire du sens », « dans le cadre de », « au final », « en termes de ».

### 3.2 Structure
- Introduction qui reformule la question, ou qui commence par « Vous rêvez de… », « Imaginez… », « Envie de… », « Bienvenue… ».
- Conclusion qui résume l'article, titres « Introduction » ou « Conclusion ».
- Tous les H2 sur le même moule (« Nom : explication »), toutes les sections de même longueur, toutes les listes de 5 à 7 puces de même longueur.
- Énumérations systématiques en trois, triplets d'adjectifs.
- Faux équilibre : « d'un côté… de l'autre », « avantages et inconvénients » quand le sujet appelle une recommandation.
- Gras partout, emojis, tirets longs en guise de ponctuation.
- Annonces de plan : « Dans cet article, nous allons voir… », « Voici tout ce qu'il faut savoir ».

### 3.3 Fond (la marque la plus forte, et celle que les algorithmes mesurent)
- **Généralités vraies partout** : rien qui ne pourrait s'appliquer à une autre ville, une autre race, un autre outil. Test : remplacer le nom propre ; si le paragraphe tient encore, il est vide.
- **Aucun détail vérifiable** : pas de prix, de date, de nom de lieu précis, de chiffre, de source, de cas.
- **Prudence uniforme** : tout est « généralement », « peut varier », « il est conseillé de consulter un professionnel » sans dire quand et pourquoi.
- **Aucun avis** : un humain qui connaît le sujet tranche (« ne réservez pas là », « ce harnais blesse les épaules des chiens qui tirent fort »).
- **Pas d'erreurs fréquentes ni de pièges** : ce que seuls les gens qui ont vécu la situation savent (c'est exactement ce que l'UGC apporte).

### 3.4 Rythme
- Phrases de longueur uniforme (contrôlé par `style_check.py`), paragraphes tous de 3 phrases.
- Transitions mécaniques en tête de paragraphe : « De plus », « En outre », « Par ailleurs », « Ainsi », « Enfin ».
- Questions rhétoriques enchaînées.

### 3.5 Au niveau du site
- Rythme de publication industriel ou irrégulier par rafales ; dizaines d'articles sur le même gabarit.
- Pages quasi identiques qui ne changent qu'un nom de ville ou de race.
- Dates de mise à jour changées sans changement de fond.
- Pas d'auteur, pas de page à propos, pas de médias originaux.

## 4. Contrôle final (bloquant avant `status: publish`)

1. Le gain d'information du brief est présent et identifiable dans le texte.
2. Chaque chiffre, prix, date ou règle a une source datée ; les sujets YMYL n'ont que des sources officielles ou scientifiques.
3. Le test du nom propre passe : aucun paragraphe ne survit au remplacement du sujet par un autre.
4. Au moins un avis tranché, un piège ou une erreur fréquente par section importante.
5. La réponse est dans la première phrase sous chaque H2 et dans le chapô.
6. Aucune expérience, citation, test ou client inventé.
7. `python scripts/style_check.py --strict <fichier>` : zéro alerte bloquante ; alertes « vocabulaire IA » traitées une par une.
8. Relecture à voix haute : chaque phrase pourrait être dite par quelqu'un qui connaît vraiment le sujet.
9. Titre et méta tiennent leur promesse ; liens internes vérifiés (`python scripts/validate.py`).
10. L'article a sa place dans la ligne éditoriale et ne cannibalise aucune page existante.

## Sources de cette grille

- Google Search Central, « Creating helpful, reliable, people-first content » : https://developers.google.com/search/docs/fundamentals/creating-helpful-content
- Google, Search Quality Rater Guidelines (janvier 2025) : https://guidelines.raterhub.com/searchqualityevaluatorguidelines.pdf ; synthèse Search Engine Land : https://searchengineland.com/google-quality-raters-content-ai-generated-lowest-quality-454161
- Google, politiques anti-spam : https://developers.google.com/search/docs/essentials/spam-policies
- Fuite Content Warehouse, synthèse Search Engine Land (mai 2024) : https://searchengineland.com/google-search-document-leak-ranking-442617 ; analyse de `contentEffort` (Hobo) : https://www.hobo-web.co.uk/the-contenteffort-attribute-the-helpful-content-system-and-e-e-a-t-is-gemini-behind-the-hcu/
- Brevet « information gain », lecture critique Search Engine Journal : https://www.searchenginejournal.com/googles-information-gain-patent-for-ranking-web-pages/524464/
- Ahrefs, 600 000 pages (2025) : https://ahrefs.com/blog/ai-generated-content-does-not-hurt-your-google-rankings/
- Ahrefs, 331 000 pages (27/07/2026) : https://ahrefs.com/blog/google-doesnt-punish-ai-content/
- Aggarwal et al., GEO, KDD 2024 : https://arxiv.org/abs/2311.09735
- Kobak et al., excess vocabulary (2024) : https://arxiv.org/abs/2406.07016
- Wikipédia, Signs of AI writing : https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing
- Statistiques de citations IA (AirOps, octobre 2026) : https://www.airops.com/blog/ai-search-statistics

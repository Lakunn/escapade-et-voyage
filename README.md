# escapade-et-voyage.fr — média SEO & GEO piloté par git

Le site WordPress est entièrement piloté depuis ce dépôt : le thème, la configuration, chaque page et chaque article. On modifie un fichier, on pousse sur `main`, GitHub Actions déploie.

**Règle d'or : zéro 301.** Toutes les URL qui existent aujourd'hui doivent répondre 200 après la refonte, à la même adresse. Le pipeline le garantit à trois niveaux :

| Garde-fou | Où | Effet |
|---|---|---|
| Référentiel `urls.csv` | généré par l'import | liste de toutes les URL actuelles en 200 (articles, pages, rubriques, auteur, pagination, sitemap) |
| `validate.py` | à chaque push / PR | échoue si un article ou une page du référentiel n'a plus de fichier avec le même slug |
| `wp_sync.py` | au déploiement | s'arrête avant toute écriture si un slug existant devait changer ; ne supprime jamais rien |
| Lancement progressif | au déploiement | les contenus pas encore réécrits (`origin: import`) ne sont jamais renvoyés vers WordPress : ils restent en ligne tels quels |
| `check_urls.py` | après déploiement + chaque lundi | échoue si une URL du référentiel redirige, renvoie une erreur ou a une canonical différente |

## Verrous avant mise en production

- un texte contenant « À COMPLÉTER ».

Dans les deux cas, la simulation le signale et la production refuse de démarrer.

## Doublons : consolidation sans redirection

Deux URL qui se concurrencent ne sont pas redirigées : la moins bonne reste en ligne (200), sa balise canonical pointe vers l'autre, et elle sort du sitemap et du llms.txt. À déclarer dans `config/site.yml` :

```yaml
canonical_overrides:
  google-penalise-constenu-ia: /google-penalise-contenu-ia/
```

## Structure

```
config/site.yml        marque, rubriques (slugs figés), menus, auteur, newsletter
content/pages/*.md     pages  (nom du fichier = slug = URL)
content/posts/*.md     articles
content/media/         images à téléverser (champ cover)
theme/escapade/        thème WordPress sur mesure (sans builder, sans jQuery)
scripts/               import, validation, synchro, contrôle des URL
urls.csv               référentiel des URL à préserver (généré, ne pas éditer à la main)
```

## Écrire un article

Créer `content/posts/mon-slug.md` :

```markdown
---
title: "Titre affiché (H1)"
slug: mon-slug
status: publish            # ou draft
date: 2026-11-15T09:00:00
categories: [blog]         # slugs de config/site.yml
dek: "Chapô de 1 à 2 phrases (sert aussi d'extrait)."
seo_title: "Balise title, 30 à 65 caractères"
meta_description: "110 à 160 caractères."
essentiel:                 # bloc « L'essentiel » en tête d'article (repris dans le schema)
  - "Point clé 1, **gras** autorisé."
  - "Point clé 2."
cover: media/mon-image.jpg # optionnel
cover_alt: "Texte alternatif"
---

Texte en Markdown. Les H2 / H3 génèrent le sommaire automatiquement.

<section class="faq" markdown="1">

## Questions fréquentes

### Une question ?

La réponse (balisée FAQPage automatiquement).

</section>
```

Champs propres aux contenus importés : `origin: import` (pas encore réécrit), `wp_id` (identifiant WordPress, sert de verrou contre un changement de slug). Une fois un article réécrit, passer `origin: rewrite` : l'import ne l'écrasera plus jamais.

## Mise en route (une seule fois)

### 1. Sauvegarde complète du site

Fichiers + base de données (sauvegardes hPanel Hostinger, ou extension type UpdraftPlus). C'est le seul retour arrière possible : **ne pas sauter cette étape**.

### 2. Accès WordPress pour l'API

Dans WordPress : *Utilisateurs > Profil > Mots de passe d'application*, créer « github-actions ». Le site doit être en HTTPS.

Sur certains hébergements mutualisés, l'en-tête `Authorization` est parfois supprimé par Apache. Si la synchro renvoie une erreur 401, ajouter en haut du `.htaccess` :

```apache
SetEnvIf Authorization "(.*)" HTTP_AUTHORIZATION=$1
```

### 3. Secrets et variables GitHub

*Settings > Secrets and variables > Actions*

| Type | Nom | Valeur |
|---|---|---|
| Variable | `WP_URL` | `https://escapade-et-voyage.fr` |
| Secret | `WP_USER` | identifiant WordPress |
| Secret | `WP_APP_PASSWORD` | mot de passe d'application |
| Variable | `FTP_PROTOCOL` | `sftp` |
| Variable | `FTP_PORT` | `65002` (port SFTP Hostinger, visible dans hPanel > Avancé > Accès SSH) |
| Secret | `FTP_HOST` | IP ou hôte SSH indiqué dans hPanel |
| Secret | `FTP_USER` / `FTP_PASSWORD` | identifiants SSH/SFTP Hostinger |
| Variable | `FTP_THEME_DIR` | ex. `domains/escapade-et-voyage.fr/public_html/wp-content/themes/guide-canin` |
| Variable | `DEPLOY_ENABLED` | laisser **vide** jusqu'au lancement, puis `true` |

Créer aussi un environnement `production` (*Settings > Environments*) : on peut y exiger une validation manuelle avant chaque déploiement.

### 4. Import du site actuel

*Actions > « 1 · Import du site actuel » > Run workflow.* Le workflow écrit `urls.csv` et un fichier Markdown par article / page encore non réécrit, puis commite. Vérifier dans les logs la liste des URL déjà redirigées ou en erreur (signalées, non retenues).

### 5. Simulation

*Actions > « 2 · Déploiement » > Run workflow > simulation.* La sortie liste tout ce qui serait créé, mis à jour, renommé. Rien n'est écrit.

### 6. Lancement

1. Passer la variable `DEPLOY_ENABLED` à `true`.
2. Lancer « 2 · Déploiement » en mode **production** : le thème est envoyé par FTP/SFTP.
3. Dans WordPress, *Apparence > Thèmes* : activer **VR Média** (un clic, une seule fois ; l'API ne permet pas d'activer un thème). Désactiver ensuite le builder Divi s'il est installé comme extension.
4. Relancer « 2 · Déploiement » en **production** avec `force` coché : tous les contenus sont réécrits avec les champs SEO du thème.
5. Le contrôle final doit afficher `N/N OK`. Sinon, les URL en cause sont listées dans le résumé du workflow.
6. Vider le cache (extension de cache ou CDN), puis soumettre le sitemap `/wp-sitemap.xml` dans la Search Console.

Ensuite, chaque push sur `main` déploie automatiquement.

## Développement local

```bash
pip install -r requirements.txt
python scripts/validate.py                      # contrôles hors ligne + génère site.json
WP_URL=… WP_USER=… WP_APP_PASSWORD=… python scripts/wp_sync.py   # simulation
python scripts/check_urls.py --base https://escapade-et-voyage.fr
```

## Ce que fait le thème

- Accueil magazine (à la une, manifeste, rubriques, newsletter), page des articles `/blog-seo/` paginée, rubriques, auteur, recherche, 404.
- Article : rubrique, chapô, signature datée (« Mis à jour le » si modifié), bloc « L'essentiel », sommaire automatique, bio auteur, articles liés.
- SEO intégré (désactivé automatiquement si Yoast, Rank Math, AIOSEO ou SEOPress est actif) : title, meta description, canonical, robots (noindex sur recherche et 404), Open Graph.
- JSON-LD : WebSite, Person, BlogPosting / WebPage / CollectionPage, BreadcrumbList, FAQPage.
- `/llms.txt` généré dynamiquement.
- Mode sombre automatique, aucune police externe, aucun jQuery, aucun CSS de blocs.

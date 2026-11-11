"""Contrôles hors ligne (à chaque push / PR), avant tout déploiement.

- génère theme/vr-media/site.json depuis config/site.yml ;
- vérifie le front matter de chaque contenu ;
- vérifie que chaque article / page du référentiel urls.csv existe toujours dans le dépôt
  avec le MÊME slug (sinon l'URL disparaîtrait) ;
- signale titres et meta descriptions hors des longueurs recommandées.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT, URLS_FILE, all_docs, die, doc_path, load_config, warn  # noqa: E402

REQUIRED = ["title", "slug"]


def build_site_json(cfg: dict) -> None:
    keys = ["brand", "home", "author", "categories", "nav", "footer_nav", "footer", "newsletter", "default_share_image",
            "per_page", "analytics", "publisher_type", "urgence", "urgence_categories"]
    out = {k: cfg.get(k) for k in keys}
    if out["author"] and out["author"].get("links") is None:
        out["author"]["links"] = []
    theme_dirs = [p for p in (ROOT / "theme").iterdir() if p.is_dir()]
    if len(theme_dirs) != 1:
        die("theme/ doit contenir exactement un dossier de thème")
    dest = theme_dirs[0] / "site.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"site.json généré ({dest.stat().st_size} octets)")


def check_pagination(cfg: dict, docs: list) -> int:
    """Chaque URL paginée du référentiel (…/page/N/) doit exister avec les réglages per_page actuels."""
    import math
    import re

    if not URLS_FILE.exists():
        return 0
    posts = [d for d in docs if d.kind == "post" and d.meta.get("status", "publish") == "publish"]
    per = cfg.get("per_page", {})
    errors = 0
    with URLS_FILE.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            m = re.search(r"^https?://[^/]+/(?:(.*)/)?page/(\d+)/$", row["url"])
            if not m:
                continue
            archive, n = (m.group(1) or ""), int(m.group(2))
            last = archive.split("/")[-1]
            cat_slugs = {c["slug"]: c for c in cfg.get("categories", [])}
            if archive.startswith("author/"):
                count, size = len(posts), per.get("author", 5)
            elif archive == (cfg.get("posts_page_slug") or "\0"):
                count, size = len(posts), per.get("blog", 9)
            elif archive.startswith("category/") or (cfg.get("category_in_url") and last in cat_slugs):
                # une rubrique parente affiche aussi les articles de ses sous-rubriques
                family = {last} | {s for s, c in cat_slugs.items() if c.get("parent") == last}
                count = sum(1 for d in posts if family & set(d.meta.get("categories") or []))
                size = per.get("archive", 6)
            else:
                count, size = len(posts), per.get("blog", 9)
            if math.ceil(count / size) < n:
                print(f"✗ /{archive}/page/{n}/ disparaîtrait : {count} articles à {size} par page = {math.ceil(count / size)} page(s)")
                errors += 1
    return errors


def check_links(cfg: dict, docs: list) -> int:
    """Liens internes relatifs des contenus réécrits ou nouveaux : la cible doit exister."""
    import re

    known = {doc_path(d, cfg) for d in docs}
    known |= {"/" + str(urlsplit(d.meta["url"]).path).strip("/") + "/" for d in docs if d.meta.get("url")}
    if URLS_FILE.exists():
        with URLS_FILE.open(encoding="utf-8") as f:
            known |= {"/" + urlsplit(r["url"]).path.strip("/") + "/" for r in csv.DictReader(f)}
    for c in cfg.get("categories", []):
        known.add(f"/category/{c['slug']}/")
        parent = c.get("parent")
        known.add(f"/{parent}/{c['slug']}/" if parent else f"/{c['slug']}/")
    known |= {"//", "/llms.txt/"}
    errors = 0
    for d in docs:
        if d.meta.get("origin") == "import":
            continue
        for target in re.findall(r"\]\((/[^)\s#?]*)", d.body):
            if target.startswith(("/wp-content/", "/media/")):
                continue
            path = "/" + target.strip("/") + "/"
            if path not in known:
                print(f"✗ {d.path.name} : lien interne vers {target} introuvable")
                errors += 1
    return errors


def main() -> None:
    cfg = load_config()
    build_site_json(cfg)
    errors = 0
    docs = all_docs()
    cat_slugs = {c["slug"] for c in cfg.get("categories", [])}
    slugs = {d.slug for d in docs}

    for d in docs:
        for k in REQUIRED:
            if not d.meta.get(k):
                print(f"✗ {d.path.relative_to(ROOT)} : champ « {k} » manquant")
                errors += 1
        if d.slug != d.path.stem:
            print(f"✗ {d.path.relative_to(ROOT)} : le nom du fichier doit être le slug ({d.slug}.md)")
            errors += 1
        for c in d.meta.get("categories", []) or []:
            if c not in cat_slugs:
                # Toléré si la rubrique existe déjà dans WordPress (la synchro vérifie).
                warn(f"{d.path.name} : rubrique « {c} » absente de config/site.yml")
        status = d.meta.get("status", "publish")
        if status not in ("publish", "draft", "future", "private", "pending"):
            print(f"✗ {d.path.name} : statut « {status} » inconnu")
            errors += 1
        if status == "future":
            from datetime import datetime

            try:
                when = datetime.fromisoformat(str(d.meta.get("date")))
            except ValueError:
                when = None
            if not when:
                print(f"✗ {d.path.name} : publication programmée sans date valide")
                errors += 1
            elif when < datetime.now():
                warn(f"{d.path.name} : date de programmation passée, WordPress le publiera immédiatement")
        t, md = d.meta.get("seo_title", ""), d.meta.get("meta_description", "")
        if d.meta.get("origin") != "import":
            if not t or not (30 <= len(t) <= 65):
                warn(f"{d.path.name} : seo_title de {len(t)} caractères (idéal 30–65)")
            if not md or not (110 <= len(md) <= 160):
                warn(f"{d.path.name} : meta_description de {len(md)} caractères (idéal 110–160)")
            if d.kind == "post" and not d.meta.get("essentiel"):
                warn(f"{d.path.name} : pas de bloc « essentiel » (recommandé pour le GEO)")

    for slug, target in (cfg.get("canonical_overrides") or {}).items():
        if target.strip("/") not in slugs:
            print(f"✗ canonical_overrides : la cible {target} de « {slug} » n'existe pas dans le dépôt")
            errors += 1 if URLS_FILE.exists() else 0
    for d in docs:
        if "À COMPLÉTER" in d.body:
            warn(f"{d.path.name} : contient « À COMPLÉTER » (le déploiement en production est bloqué)")
        if d.kind == "page" and d.meta.get("origin") == "import":
            pass  # lancement progressif : les pages importées restent en ligne telles quelles

    for flag in ("front_page", "posts_page"):
        n = sum(1 for d in docs if d.meta.get(flag))
        if n > 1:
            print(f"✗ {n} contenus marqués {flag} (un seul autorisé)")
            errors += 1

    errors += check_pagination(cfg, docs)
    errors += check_links(cfg, docs)

    if URLS_FILE.exists():
        with URLS_FILE.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["type"] not in ("post", "page"):
                    continue
                path = urlsplit(row["url"]).path.strip("/").split("/")[-1]
                if path and path not in slugs:
                    print(f"✗ {row['url']} est dans le référentiel mais aucun contenu n'a le slug « {path} »")
                    errors += 1
    else:
        warn("urls.csv absent : lance le workflow « Import du site actuel »")

    print(f"{len(docs)} contenus vérifiés, {errors} erreur(s)")
    if errors:
        die("validation échouée")


if __name__ == "__main__":
    main()

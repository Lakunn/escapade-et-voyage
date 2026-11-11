"""Synchronisation dépôt → WordPress (création / mise à jour par slug).

Garde-fous « zéro 301 » :
- un contenu est toujours retrouvé par son slug (ou son wp_id) ; si le slug d'un contenu
  existant devait changer, la synchro s'ARRÊTE avant toute écriture ;
- rien n'est jamais supprimé ni dépublié : les contenus présents dans WordPress mais
  absents du dépôt sont seulement signalés ;
- les rubriques sont créées ou renommées, jamais re-sluggées.

Usage :
  python scripts/wp_sync.py            # simulation (aucune écriture)
  python scripts/wp_sync.py --apply    # écrit dans WordPress
  python scripts/wp_sync.py --apply --force   # ré-envoie même les contenus inchangés
"""
from __future__ import annotations

import argparse
import html
import sys
from pathlib import Path

import markdown

sys.path.insert(0, str(Path(__file__).parent))
from common import CONTENT, WP, Doc, all_docs, die, load_config, warn  # noqa: E402

MD_EXT = ["extra", "sane_lists"]  # les ancres des titres sont ajoutées par le thème


def render(doc: Doc) -> str:
    return markdown.markdown(doc.body, extensions=MD_EXT, output_format="html")


def essentiel(doc: Doc) -> str:
    pts = doc.meta.get("essentiel") or []
    return "\n".join(markdown.markdown(str(p)).removeprefix("<p>").removesuffix("</p>") for p in pts)


class Sync:
    def __init__(self, apply: bool, force: bool) -> None:
        self.apply, self.force = apply, force
        self.wp = WP(auth=True)
        self.cfg = load_config()
        self.changes = 0

    def log(self, msg: str) -> None:
        print(("" if self.apply else "[simulation] ") + msg)

    # -- rubriques -----------------------------------------------------------
    def sync_categories(self) -> dict[str, int]:
        existing = {c["slug"]: c for c in self.wp.get_all("categories", context="edit")}
        ids = {s: c["id"] for s, c in existing.items()}
        for conf in self.cfg.get("categories", []):
            slug, name = conf["slug"], conf["name"]
            desc = conf.get("intro", "")
            cur = existing.get(slug)
            if cur is None:
                self.log(f"rubrique créée : {slug} ({name})")
                if self.apply:
                    payload = {"slug": slug, "name": name, "description": desc}
                    if conf.get("parent") and conf["parent"] in ids:
                        payload["parent"] = ids[conf["parent"]]
                    ids[slug] = self.wp.post("categories", payload)["id"]
                self.changes += 1
            elif html.unescape(cur["name"]) != name or html.unescape(cur.get("description", "")) != desc:
                self.log(f"rubrique renommée : {slug} « {cur['name']} » → « {name} »")
                if self.apply:
                    self.wp.post(f"categories/{cur['id']}", {"name": name, "description": desc})
                self.changes += 1
        return ids

    # -- médias ----------------------------------------------------------------
    def cover(self, doc: Doc) -> int | None:
        if doc.meta.get("cover_id"):
            return int(doc.meta["cover_id"])
        rel = doc.meta.get("cover")
        if not rel:
            return None
        file = (CONTENT / rel).resolve()
        if not file.exists():
            die(f"{doc.path.name} : image introuvable {rel}")
        found = self.wp.get("media", search=file.stem, per_page=10)
        for m in found:
            if m.get("source_url", "").rsplit("/", 1)[-1].startswith(file.stem):
                return m["id"]
        self.log(f"image envoyée : {file.name}")
        if not self.apply:
            return None
        media = self.wp.upload(file)
        if doc.meta.get("cover_alt"):
            self.wp.post(f"media/{media['id']}", {"alt_text": doc.meta["cover_alt"]})
        return media["id"]

    # -- contenus --------------------------------------------------------------
    def find(self, doc: Doc) -> dict | None:
        endpoint = "pages" if doc.kind == "page" else "posts"
        if doc.meta.get("wp_id"):
            item = self.wp.get(f"{endpoint}/{doc.meta['wp_id']}", context="edit")
            if item["slug"] != doc.slug:
                die(
                    f"{doc.path.name} : le slug changerait « {item['slug']} » → « {doc.slug} ». "
                    "Ça casserait une URL existante : synchro annulée."
                )
            if doc.kind == "post" and self.cfg.get("category_in_url"):
                ids = {c["id"]: c["slug"] for c in self.wp.get_all("categories", context="edit")} if not hasattr(self, "_cats") else self._cats
                self._cats = ids
                current = sorted(ids.get(c, str(c)) for c in item.get("categories", []))
                wanted = sorted(doc.meta.get("categories") or [])
                if current != wanted:
                    die(
                        f"{doc.path.name} : les rubriques changeraient {current} → {wanted}. "
                        "Sur ce site la rubrique fait partie de l'URL : synchro annulée."
                    )
            return item
        found = self.wp.get(endpoint, slug=doc.slug, status="publish,draft,pending,private,future", context="edit")
        return found[0] if found else None

    def canonical(self, doc: Doc) -> str:
        return str(doc.meta.get("canonical") or (self.cfg.get("canonical_overrides") or {}).get(doc.slug, ""))

    def inline_media(self, html: str) -> str:
        """Téléverse les images locales (media/…) insérées dans le texte et remplace leur adresse."""
        import re as _re

        def repl(m):
            rel = m.group(1)
            file = (CONTENT / rel).resolve()
            if not file.exists():
                die(f"image introuvable : {rel}")
            cache = self.__dict__.setdefault("_media", {})
            if rel not in cache:
                found = [x for x in self.wp.get("media", search=file.stem, per_page=10)
                         if x.get("source_url", "").rsplit("/", 1)[-1].startswith(file.stem)]
                if found:
                    cache[rel] = found[0]["source_url"]
                elif self.apply:
                    self.log(f"image envoyée : {file.name}")
                    cache[rel] = self.wp.upload(file)["source_url"]
                else:
                    self.log(f"image à envoyer : {file.name}")
                    cache[rel] = rel
            return f'src="{cache[rel]}"'

        return _re.sub(r'src="(media/[^"]+)"', repl, html)

    def payload(self, doc: Doc, cat_ids: dict[str, int], page_ids: dict[str, int]) -> dict:
        m = doc.meta
        data = {
            "title": m["title"],
            "slug": doc.slug,
            "status": m.get("status", "publish"),
            "content": self.inline_media(render(doc)),
            "excerpt": m.get("dek", ""),
            "meta": {
                "vr_seo_title": m.get("seo_title", ""),
                "vr_meta_description": m.get("meta_description", ""),
                "vr_essentiel": essentiel(doc),
                "vr_noindex": bool(m.get("noindex", False)),
                "vr_source_hash": doc.source_hash(extra=self.canonical(doc)),
                "vr_canonical": self.canonical(doc),
            },
        }
        if m.get("date"):
            data["date"] = str(m["date"])
        if doc.kind == "post":
            missing = [c for c in m.get("categories", []) if c not in cat_ids]
            if missing and self.apply:
                die(f"{doc.path.name} : rubrique(s) inconnue(s) {missing} — à déclarer dans config/site.yml")
            data["categories"] = [cat_ids[c] for c in m.get("categories", []) if c in cat_ids]
            if m.get("sticky") is not None:
                data["sticky"] = bool(m["sticky"])
        else:
            if m.get("parent"):
                data["parent"] = page_ids.get(m["parent"], 0)
            elif m.get("parent_id"):
                data["parent"] = int(m["parent_id"])
            if m.get("menu_order") is not None:
                data["menu_order"] = int(m["menu_order"])
            data["template"] = m.get("template", "")
        return data

    def run(self) -> None:
        skip = set(self.cfg.get("legacy_redirects") or [])
        docs = [d for d in all_docs() if d.slug not in skip]
        for slug in sorted(skip):
            print(f"ignoré (redirigeait déjà avant la refonte) : /{slug}/")
        slugs = [(d.kind, d.slug) for d in docs]
        dupes = {s for s in slugs if slugs.count(s) > 1}
        if dupes:
            die(f"slugs en double dans le dépôt : {dupes}")

        # Lancement progressif : les contenus pas encore réécrits (origin: import) ne sont
        # jamais renvoyés vers WordPress. Ils restent en ligne tels quels jusqu'à leur réécriture.
        legacy = [d for d in docs if d.meta.get("origin") == "import"]
        if legacy:
            print(f"laissés tels quels dans WordPress (pas encore réécrits) : {len(legacy)} contenus")
        docs = [d for d in docs if d.meta.get("origin") != "import"]
        todo = [d.path.name for d in docs if "À COMPLÉTER" in d.body or "À COMPLÉTER" in str(d.meta)]
        if todo and self.apply:
            die(f"informations « À COMPLÉTER » dans : {', '.join(todo)} — déploiement bloqué")
        for name in todo:
            warn(f"informations à compléter avant le lancement : {name}")

        cat_ids = self.sync_categories()
        page_ids: dict[str, int] = {}
        repo_ids: set[int] = set()
        front_id = posts_id = None

        # Les pages d'abord (parents éventuels), puis les articles.
        # Pages sans parent d'abord, puis pages enfants, puis articles.
        for doc in sorted(docs, key=lambda d: (d.kind != "page", bool(d.meta.get("parent")), d.slug)):
            current = self.find(doc)
            data = self.payload(doc, cat_ids, page_ids)
            if current:
                repo_ids.add(current["id"])
                page_ids[doc.slug] = current["id"]
                same = (current.get("meta") or {}).get("vr_source_hash") == data["meta"]["vr_source_hash"]
                if same and not self.force:
                    pass
                else:
                    self.log(f"mis à jour : {doc.kind} /{doc.slug}/")
                    self.changes += 1
                    if self.apply:
                        cover = self.cover(doc)
                        if cover:
                            data["featured_media"] = cover
                        updated = self.wp.post(f"{'pages' if doc.kind == 'page' else 'posts'}/{current['id']}", data)
                        if updated.get("link") != current.get("link"):
                            die(f"l'URL de {doc.path.name} a changé ({current.get('link')} → {updated.get('link')}) : arrêt immédiat, à corriger à la main")
                item_id = current["id"]
            else:
                self.log(f"créé : {doc.kind} /{doc.slug}/")
                self.changes += 1
                item_id = None
                if self.apply:
                    cover = self.cover(doc)
                    if cover:
                        data["featured_media"] = cover
                    created = self.wp.post("pages" if doc.kind == "page" else "posts", data)
                    if created["slug"] != doc.slug:
                        die(f"WordPress a attribué le slug « {created['slug']} » au lieu de « {doc.slug} » (slug déjà pris ?)")
                    item_id = created["id"]
                    page_ids[doc.slug] = item_id
                    repo_ids.add(item_id)
            if doc.meta.get("front_page"):
                front_id = item_id
            if doc.meta.get("posts_page"):
                posts_id = item_id

        self.sync_settings(front_id, posts_id)
        self.report_orphans(repo_ids)
        print(f"\n{self.changes} changement(s) {'appliqué(s)' if self.apply else 'à appliquer'}.")

    def sync_settings(self, front_id: int | None, posts_id: int | None) -> None:
        brand = self.cfg.get("brand", {})
        wanted = {
            "title": brand.get("wp_blogname"),
            "description": brand.get("wp_blogdescription"),
        }
        if front_id:
            wanted.update({"show_on_front": "page", "page_on_front": front_id})
        if posts_id:
            wanted["page_for_posts"] = posts_id
        current = self.wp.get("settings")
        def same(a, b) -> bool:
            return html.unescape(str(a)) == html.unescape(str(b))

        diff = {k: v for k, v in wanted.items() if v not in (None, "") and not same(current.get(k), v)}
        if diff:
            self.log(f"réglages : {diff}")
            self.changes += 1
            if self.apply:
                self.wp.post("settings", diff)

    def report_orphans(self, repo_ids: set[int]) -> None:
        for endpoint in ("posts", "pages"):
            for item in self.wp.get_all(endpoint, status="publish", context="edit", _fields="id,link"):
                if item["id"] not in repo_ids:
                    warn(f"publié dans WordPress mais absent du dépôt (laissé tel quel) : {item['link']}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if not any(CONTENT.glob("*/*.md")):
        die("aucun contenu dans content/ — lance d'abord le workflow d'import")
    Sync(a.apply, a.force).run()


if __name__ == "__main__":
    main()

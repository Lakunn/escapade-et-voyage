"""Import du site actuel → dépôt.

1. Construit le référentiel d'URL (urls.csv) : sitemap + API + pagination des archives.
   Seules les URL qui répondent 200 SANS redirection sont retenues : ce sont celles à préserver.
2. Récupère chaque article / page publié(e) (texte intégral, title et meta description réels
   lus dans le HTML) et l'écrit en Markdown dans content/.
   Un fichier déjà réécrit (origin != import) n'est JAMAIS écrasé.

Usage : python scripts/wp_import.py [--urls-only]
L'import n'utilise que des données publiques (pas besoin d'authentification).
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify

sys.path.insert(0, str(Path(__file__).parent))
from common import CONTENT, UA, URLS_FILE, WP, norm_url, read_doc, site_url, warn, write_doc  # noqa: E402

S = requests.Session()
S.headers["User-Agent"] = UA


def status(url: str) -> tuple[int, str]:
    try:
        r = S.get(url, allow_redirects=False, timeout=30)
        return r.status_code, r.headers.get("Location", "")
    except requests.RequestException as e:
        return 0, str(e)


# --------------------------------------------------------------------------- #
# Référentiel d'URL
# --------------------------------------------------------------------------- #
def sitemap_urls(base: str) -> set[str]:
    found: set[str] = set()
    for index in ("/wp-sitemap.xml", "/sitemap_index.xml", "/sitemap.xml"):
        try:
            r = S.get(base + index, timeout=30)
        except requests.RequestException:
            continue
        if r.status_code != 200 or b"<" not in r.content[:200]:
            continue
        queue = [r.content]
        while queue:
            root = ET.fromstring(queue.pop())
            ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            for loc in root.findall(".//s:sitemap/s:loc", ns):
                sub = S.get(loc.text.strip(), timeout=30)
                if sub.status_code == 200:
                    queue.append(sub.content)
            for loc in root.findall(".//s:url/s:loc", ns):
                found.add(loc.text.strip())
        print(f"Sitemap {index} : {len(found)} URL")
        break
    return found


PAGE_RE = re.compile(r"/page/(\d+)/?$")


def paginated(url: str) -> list[str]:
    """Pages 2..N d'une archive, en suivant uniquement les liens de pagination présents dans le HTML.

    On ne « devine » pas /page/N/ : sur une page statique WordPress répond 200 pour n'importe quel N,
    ce qui ferait entrer de fausses URL dans le référentiel.
    """
    base = norm_url(url).rstrip("/")
    seen: set[str] = set()
    queue = [url]
    while queue and len(seen) < 60:
        r = S.get(queue.pop(), timeout=30)
        if r.status_code != 200:
            continue
        for a in BeautifulSoup(r.text, "html.parser").find_all("a", href=True):
            u = norm_url(a["href"])
            if u.startswith(base + "/page/") and PAGE_RE.search(u) and u not in seen:
                code, _ = status(u)
                if code == 200:
                    seen.add(u)
                    queue.append(u)
    return sorted(seen, key=lambda u: int(PAGE_RE.search(u).group(1)))


def build_url_baseline(wp: WP, posts: list[dict], pages: list[dict]) -> None:
    base = site_url()
    rows: dict[str, str] = {}

    def add(url: str, kind: str) -> None:
        rows.setdefault(norm_url(url), kind)

    add(base + "/", "home")
    for p in posts:
        add(p["link"], "post")
    for p in pages:
        add(p["link"], "page")
    for c in wp.get_all("categories", hide_empty="true"):
        add(c["link"], "category")
    for t in wp.get_all("tags", hide_empty="true"):
        add(t["link"], "tag")
    for u in wp.get_all("users"):
        add(u["link"], "author")
    for u in sitemap_urls(base):
        add(u, "sitemap")
    extra = Path(__file__).resolve().parent.parent / "config" / "extra_urls.txt"
    if extra.exists():  # ex. export Search Console : une URL par ligne
        for line in extra.read_text().splitlines():
            if line.strip().startswith("http"):
                add(line.strip(), "extra")

    # Pagination des archives (page des articles + rubriques + auteur).
    archives = [u for u, k in rows.items() if k in ("category", "tag", "author")]
    archives += [norm_url(p["link"]) for p in pages if p["slug"] in ("blog-seo", "blog")]
    archives.append(norm_url(base + "/"))  # accueil paginé (/page/2/) quand il liste les articles
    for a in archives:
        for u in paginated(a):
            add(u, "pagination")

    # Statut actuel de chaque URL.
    with ThreadPoolExecutor(8) as ex:
        results = dict(zip(rows, ex.map(status, rows)))

    keep, redirected, broken = [], [], []
    for url, kind in sorted(rows.items()):
        code, loc = results[url]
        if code == 200:
            keep.append((url, kind))
        elif 300 <= code < 400:
            redirected.append((url, code, loc))
        else:
            broken.append((url, code))

    with URLS_FILE.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["url", "type"])
        w.writerows(keep)
    print(f"urls.csv : {len(keep)} URL en 200 à préserver")
    for url, code, loc in redirected:
        warn(f"Déjà redirigée aujourd'hui (non retenue) : {url} → {code} {loc}")
    for url, code in broken:
        warn(f"Déjà en erreur aujourd'hui (non retenue) : {url} → {code}")


# --------------------------------------------------------------------------- #
# Contenus
# --------------------------------------------------------------------------- #
CUT_HEADINGS = re.compile(r"^\s*(autres articles à explorer|articles similaires|contact)\s*:?\s*$", re.I)


def page_head(url: str) -> dict:
    r = S.get(url, timeout=30)
    soup = BeautifulSoup(r.text, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else ""
    desc = soup.find("meta", attrs={"name": "description"})
    h1 = soup.find("h1")
    return {
        "seo_title": title,
        "meta_description": (desc.get("content", "").strip() if desc else ""),
        "h1": h1.get_text(" ", strip=True) if h1 else "",
    }


def clean_html(html: str) -> str:
    html = re.sub(r"\[/?(?:et_pb_|vc_|tdm?_|the_ad)[^\]]*\]", "", html)  # shortcodes de constructeurs (Divi, WPBakery, tagDiv) non rendus
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "form", "iframe", "button"]):
        tag.decompose()
    # Modules Divi de listes d'articles, boutons, séparateurs.
    for sel in [".et_pb_blog_grid", ".et_pb_blog_0", ".et_pb_posts", ".et_pb_button_module_wrapper", ".et_pb_divider", ".et_pb_social_media_follow"]:
        for tag in soup.select(sel):
            tag.decompose()
    # Coupe tout à partir des blocs « Autres articles à explorer » / « Contact ».
    for h in soup.find_all(re.compile("^h[1-6]$")):
        if CUT_HEADINGS.match(h.get_text(" ", strip=True)):
            for sib in list(h.find_all_next()):
                sib.decompose()
            h.decompose()
            break
    return str(soup)


def to_markdown(html: str) -> str:
    md = markdownify(clean_html(html), heading_style="ATX", bullets="-", strip=["span", "div", "section"])
    md = re.sub(r"\n{3,}", "\n\n", md)
    md = re.sub(r"[ \t]+\n", "\n", md)
    return md.strip()


def attach_special(item: dict, flag: str) -> str | None:
    """Rattache une page réécrite (front_page / posts_page) à la vraie page WordPress, quel que soit son slug."""
    for p in CONTENT.glob("pages/*.md"):
        d = read_doc(p)
        if d.meta.get(flag) and d.meta.get("origin") != "import":
            meta = {**d.meta, "slug": item["slug"], "wp_id": item["id"]}
            target = p.with_name(f"{item['slug']}.md")
            write_doc(target, meta, d.body)
            if target != p:
                p.unlink()
            return f"rattaché ({flag}) : {p.name} → page WordPress {item['id']} /{item['slug']}/"
    return None


def import_item(item: dict, kind: str, cats: dict[int, str], front_id: int, posts_id: int) -> str:
    slug = item["slug"]
    if kind == "page" and item["id"] in (front_id, posts_id):
        done = attach_special(item, "front_page" if item["id"] == front_id else "posts_page")
        if done:
            return done
    path = CONTENT / ("posts" if kind == "post" else "pages") / f"{slug}.md"
    if path.exists():
        existing = read_doc(path)
        if existing.meta.get("origin") != "import":
            return f"conservé (déjà réécrit) : {slug}"
    head = page_head(item["link"])
    meta = {
        "title": BeautifulSoup(item["title"]["rendered"], "html.parser").get_text(),
        "slug": slug,
        "status": "publish",
        "date": item["date"],
        "origin": "import",          # passer à « rewrite » une fois l'article réécrit
        "wp_id": item["id"],
        "url": item["link"],
        "seo_title": head["seo_title"],
        "meta_description": head["meta_description"],
    }
    if kind == "post":
        meta["categories"] = [cats[c] for c in item.get("categories", []) if c in cats]
    if item.get("featured_media"):
        meta["cover_id"] = item["featured_media"]
    if item["id"] == front_id:
        meta["front_page"] = True
    if item["id"] == posts_id:
        meta["posts_page"] = True
    if kind == "page" and item.get("parent"):
        meta["parent_id"] = item["parent"]
    body = to_markdown(item["content"]["rendered"])
    if head["h1"] and head["h1"] != meta["title"]:
        meta["h1_actuel"] = head["h1"]
    write_doc(path, meta, body)
    return f"importé : {kind} {slug} ({len(body.split())} mots)"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--urls-only", action="store_true")
    args = ap.parse_args()

    wp = WP(auth=False)
    posts = wp.get_all("posts", status="publish")
    pages = wp.get_all("pages", status="publish")
    print(f"{len(posts)} articles, {len(pages)} pages publiés")

    build_url_baseline(wp, posts, pages)
    if args.urls_only:
        return

    cats = {c["id"]: c["slug"] for c in wp.get_all("categories")}
    # page_on_front / page_for_posts ne sont pas publics : on les déduit.
    front_id = next((p["id"] for p in pages if norm_url(p["link"]) == norm_url(site_url() + "/")), 0)
    from common import load_config
    posts_slug = load_config().get("posts_page_slug", "")
    posts_id = next((p["id"] for p in pages if posts_slug and p["slug"] == posts_slug), 0)
    for p in posts:
        print(import_item(p, "post", cats, front_id, posts_id))
    for p in pages:
        print(import_item(p, "page", cats, front_id, posts_id))


if __name__ == "__main__":
    main()

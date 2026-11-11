"""Contrôle « zéro 301 » sur le site en ligne.

Chaque URL de urls.csv doit répondre 200, sans redirection, avec une balise canonical
pointant sur elle-même. Toute anomalie fait échouer le workflow.

Vérifie aussi les nouveaux contenus du dépôt et /llms.txt.
Usage : python scripts/check_urls.py [--base https://valentinrouault.com]
"""
from __future__ import annotations

import argparse
import time
import csv
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent))
from common import UA, URLS_FILE, all_docs, doc_path, load_config, norm_url, site_url  # noqa: E402

S = requests.Session()
S.headers["User-Agent"] = UA


EXPECTED_CANONICAL: dict[str, str] = {}


def check(url: str, kind: str) -> tuple[str, str, str]:
    # Hébergement mutualisé : on espace les requêtes et on réessaie les erreurs 5xx passagères.
    r = None
    for attempt in range(4):
        time.sleep(1.5 if attempt == 0 else 10 * attempt)
        try:
            r = S.get(url, allow_redirects=False, timeout=30)
        except requests.RequestException as e:
            if attempt == 3:
                return url, "KO", f"erreur réseau : {e}"
            continue
        if r.status_code < 500:
            break
    if 300 <= r.status_code < 400:
        return url, "KO", f"redirection {r.status_code} → {r.headers.get('Location')}"
    if r.status_code != 200:
        return url, "KO", f"HTTP {r.status_code}"
    if kind == "txt":
        return url, "OK", ""
    soup = BeautifulSoup(r.text, "html.parser")
    can = soup.find("link", rel="canonical")
    if not can or not can.get("href"):
        return url, "KO", "pas de balise canonical"
    if norm_url(can["href"]) != EXPECTED_CANONICAL.get(norm_url(url), norm_url(url)):
        return url, "KO", f"canonical différente : {can['href']}"
    robots = soup.find("meta", attrs={"name": "robots"})
    if robots and "noindex" in robots.get("content", "") and kind != "noindex-ok":
        return url, "ATTENTION", "page en noindex"
    return url, "OK", ""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=site_url())
    args = ap.parse_args()
    base = args.base.rstrip("/")

    targets: dict[str, str] = {}
    if URLS_FILE.exists():
        with URLS_FILE.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                targets[row["url"]] = row["type"]
    skip = set(load_config().get("legacy_redirects") or [])
    for d in all_docs():
        if d.slug in skip:
            continue
        if d.meta.get("status", "publish") == "publish" and not d.meta.get("front_page"):
            if d.meta.get("url"):
                continue  # contenu importé : son URL réelle est déjà dans urls.csv
            targets.setdefault(norm_url(base + doc_path(d)), "noindex-ok" if d.meta.get("noindex") else "new")
    targets[f"{base}/llms.txt"] = "txt"
    for d in all_docs():
        target = d.meta.get("canonical") or (load_config().get("canonical_overrides") or {}).get(d.slug)
        if target:
            EXPECTED_CANONICAL[norm_url(d.meta.get("url") or base + doc_path(d))] = norm_url(base + target)

    with ThreadPoolExecutor(2) as ex:
        results = list(ex.map(lambda kv: check(*kv), targets.items()))

    ko = [r for r in results if r[1] == "KO"]
    attn = [r for r in results if r[1] == "ATTENTION"]
    lines = [f"## Contrôle des URL — {len(results) - len(ko)}/{len(results)} OK", ""]
    if ko or attn:
        lines += ["| URL | Statut | Détail |", "|---|---|---|"]
        lines += [f"| {u} | {s} | {d} |" for u, s, d in ko + attn]
    report = "\n".join(lines)
    print(report)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(report + "\n")
    sys.exit(1 if ko else 0)


if __name__ == "__main__":
    main()

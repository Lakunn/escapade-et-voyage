"""Veille automatique : lit les flux RSS / Atom déclarés dans config/veille.yml, garde les
nouveautés qui correspondent aux mots-clés, et écrit un récapitulatif dans veille/AAAA-MM-JJ.md.

Lancé chaque semaine par le workflow « 4 · Veille » (et à la demande). Les éléments déjà vus
sont mémorisés dans veille/seen.json pour ne jamais être proposés deux fois.

Usage : python scripts/veille.py [--days 8]
"""
from __future__ import annotations

import argparse
import email.utils
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
import yaml

sys.path.insert(0, str(Path(__file__).parent))
from common import ROOT, UA, warn  # noqa: E402

CONF = ROOT / "config" / "veille.yml"
OUT = ROOT / "veille"
SEEN = OUT / "seen.json"
NS = {"atom": "http://www.w3.org/2005/Atom"}


def parse_date(text: str | None) -> datetime | None:
    if not text:
        return None
    text = text.strip()
    try:
        return email.utils.parsedate_to_datetime(text).astimezone(timezone.utc)
    except (TypeError, ValueError):
        pass
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def clean(text: str | None) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", text).strip()


def read_feed(url: str) -> list[dict]:
    r = requests.get(url, headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    items = []
    for it in root.iter("item"):  # RSS
        items.append({
            "title": clean(it.findtext("title")),
            "link": (it.findtext("link") or "").strip(),
            "date": parse_date(it.findtext("pubDate")),
            "summary": clean(it.findtext("description"))[:300],
        })
    for it in root.iter("{http://www.w3.org/2005/Atom}entry"):  # Atom
        link = it.find("atom:link[@rel='alternate']", NS)
        if link is None:
            link = it.find("atom:link", NS)
        items.append({
            "title": clean(it.findtext("atom:title", namespaces=NS)),
            "link": link.get("href", "") if link is not None else "",
            "date": parse_date(it.findtext("atom:updated", namespaces=NS) or it.findtext("atom:published", namespaces=NS)),
            "summary": clean(it.findtext("atom:summary", namespaces=NS) or it.findtext("atom:content", namespaces=NS))[:300],
        })
    return items


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=8)
    args = ap.parse_args()
    conf = yaml.safe_load(CONF.read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)
    seen = set(json.loads(SEEN.read_text())) if SEEN.exists() else set()
    since = datetime.now(timezone.utc) - timedelta(days=args.days)
    keywords = [k.lower() for k in conf.get("keywords", [])]
    exclude = [k.lower() for k in conf.get("exclude", [])]

    sections, broken = [], []
    for feed in conf.get("feeds", []):
        try:
            items = read_feed(feed["url"])
        except Exception as e:  # noqa: BLE001 — un flux en panne ne doit pas bloquer la veille
            broken.append(f"{feed['name']} ({e.__class__.__name__})")
            continue
        kept = []
        for it in items:
            key = hashlib.sha1((it["link"] or it["title"]).encode()).hexdigest()[:16]
            if key in seen or not it["title"]:
                continue
            if it["date"] and it["date"] < since:
                continue
            text = f"{it['title']} {it['summary']}".lower()
            if feed.get("filter", True) and keywords and not any(k in text for k in keywords):
                continue
            if any(k in text for k in exclude):
                continue
            seen.add(key)
            kept.append(it)
        if kept:
            lines = [f"### {feed['name']}", ""]
            for it in kept[: feed.get("max", 10)]:
                d = it["date"].strftime("%d/%m/%Y") if it["date"] else "date inconnue"
                lines.append(f"- [ ] **{it['title']}** ({d}) : {it['link']}")
                if it["summary"]:
                    lines.append(f"  > {it['summary']}")
            sections.append("\n".join(lines))

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    body = [f"# Veille du {today}", "", f"Nouveautés des {args.days} derniers jours, filtrées sur les mots-clés de `config/veille.yml`.", ""]
    body += ["Pour chaque sujet retenu : cocher la case, puis suivre le skill de rédaction (type « news »).", ""]
    body += sections or ["Aucune nouveauté pertinente cette semaine."]
    if broken:
        body += ["", "## Flux injoignables", ""] + [f"- {b}" for b in broken]
    target = OUT / f"{today}.md"
    if target.exists():
        if sections:  # second passage le même jour : on complète sans écraser
            with target.open("a", encoding="utf-8") as f:
                f.write("\n## Complément\n\n" + "\n\n".join(sections) + "\n")
    else:
        target.write_text("\n".join(body) + "\n", encoding="utf-8")
    SEEN.write_text(json.dumps(sorted(seen)), encoding="utf-8")
    print(f"veille/{today}.md : {sum(s.count('- [ ]') for s in sections)} élément(s), {len(broken)} flux en erreur")
    for b in broken:
        warn(f"flux injoignable : {b}")


if __name__ == "__main__":
    main()

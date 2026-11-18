"""Veille éditoriale (script commun aux 4 sites de Valentin : escapade-et-voyage.fr, guidecanin.fr,
valentinrouault.com, growww.app ; fichier identique dans les 4 dépôts, tout ce qui est propre au site est
dans config/veille.yml) : lit les flux (sites, Bluesky, alertes Google, X en option), regroupe les
nouveautés par sujet, les classe, et propose pour chaque sujet un angle qui apporte de la valeur par
rapport à ce qui est déjà publié.

Options de config/veille.yml : `keywords` / `exclude` globaux ; par flux `keywords` (remplacent la liste
globale : utile pour les flux anglais ou très larges), `filter: false`, `weight`, `lang`, `type` ;
`topics` (sujets suivis) ; `lang_defaut` (langue des flux sans `lang`, « en » par défaut) ; `min_sources` (sources distinctes pour
retenir un sujet, 2 par défaut : 1 pour un site dont la veille suit surtout des règles et des actualités pratiques) ; `angles` et `stop_extra` pour adapter les angles proposés et les mots ignorés.

Sorties (commitées par le workflow de veille du dépôt) :
- veille/AAAA-MM-JJ.md : le rapport du jour, sujets classés, sources, angle proposé, contenus à mettre à jour ;
- veille/plan.md : le plan d'articles glissant (les meilleurs sujets des derniers jours) ;
- veille/items.json : l'historique des éléments vus (sert à détecter les sujets qui montent).

Usage : python scripts/veille.py [--days 7]
"""
from __future__ import annotations

import argparse
import email.utils
import hashlib
import json
import math
import os
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]
UA = "Mozilla/5.0 (compatible; media-veille/1.0)"


def warn(msg: str) -> None:
    print(f"ATTENTION : {msg}", file=sys.stderr)


class Doc:
    def __init__(self, slug: str, meta: dict):
        self.kind, self.slug, self.meta = "post", slug, meta


def all_docs() -> list[Doc]:
    """Articles du dépôt (front matter des fichiers .md / .html de content/posts)."""
    out = []
    for p in sorted((ROOT / "content" / "posts").glob("*.*")):
        if p.suffix not in (".md", ".html"):
            continue
        text = p.read_text(encoding="utf-8")
        try:
            meta = yaml.safe_load(text.split("---")[1]) if text.startswith("---") else {}
        except yaml.YAMLError:
            meta = {}
        meta = meta or {}
        out.append(Doc(str(meta.get("slug") or p.stem), meta))
    return out

CONF = ROOT / "config" / "veille.yml"
OUT = ROOT / "veille"
HISTORY = OUT / "items.json"
NOW = datetime.now(timezone.utc)

STOP = set("""
a au aux avec ce ces dans de des du elle en et est il ils je la le les leur lui ma mais me même mes moi mon ne nos notre nous on ou où par pas pour qu que qui sa se ses son sur ta te tes toi ton tu un une vos votre vous c d j l m n s t y été être avoir fait faire plus moins comme tout tous toute toutes cette cet sans sous entre vers chez après avant aussi encore déjà très bien ça quoi quel quelle quels quelles comment pourquoi
the a an and or of to in on for with by from at as is are was were be been it its this that these those your you we our they their how what why when which who new now more most will can not no into about over after before vs via just get gets got using use used
""".split())

ANGLES = {  # remplaçables par `angles:` dans config/veille.yml
    "annonce": [
        "Ce qui change concrètement pour le lecteur français, avec la date d'application en France ou son absence.",
        "Vérifier sur la source primaire (texte officiel, page du service, annonce de l'entreprise) avant d'écrire.",
        "Lister ce qu'il faut faire, ne pas faire, et surveiller dans les 30 jours.",
    ],
    "etude": [
        "Relire la méthode de l'étude (échantillon, pays, période, définition des métriques) et la résumer honnêtement.",
        "Confronter les chiffres à au moins deux autres études ou à une source officielle.",
        "Dire ce que l'étude ne permet pas de conclure, et ce que cela implique pour le lecteur français.",
    ],
    "declaration": [
        "Citer la déclaration exacte (source primaire) et la replacer dans les déclarations précédentes sur le même sujet.",
        "Séparer ce qui est confirmé, ce qui est interprété par les médias, et ce qui reste inconnu.",
        "Traduire en décisions : qu'est-ce que le lecteur doit vérifier ou changer ?",
    ],
    "debat": [
        "Rassembler les positions en présence, avec leurs arguments et leurs données.",
        "Trancher quand les faits le permettent, sinon expliquer pourquoi on ne peut pas encore trancher.",
        "Proposer un test reproductible que le lecteur peut mener sur son propre site.",
    ],
}
CUES = {
    "etude": r"\b(study|studies|étude|data|analysis|analyse|report|rapport|survey|sondage|research|recherche|benchmark|\d+ ?%|million|billion|milliard)\b",
    "declaration": r"\b(says|said|confirms|confirme|explains|explique|mueller|sullivan|illyes|splitt|searchliaison|clarifies|précise|déclare)\b",
    "annonce": r"\b(launch|launches|launched|lance|rolling out|rolls out|déploie|déploiement|announce|announces|annonce|update|introduces|now available|disponible|expands|arrive|deprecat|retire|ends|fin de)\b",
}


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def has_any(text: str, words: list[str]) -> bool:
    """Un mot-clé ne compte qu'en début de mot (« tique » ne doit pas trouver « politique », ni « eta » « secretary ») ;
    il peut être suivi d'autres lettres (« chien » trouve « chiens »)."""
    return any(re.search(r"(?<![a-z0-9])" + re.escape(w), text) for w in words)


def tokens(text: str) -> set[str]:  # STOP est complété par `stop_extra` de la config (main)
    return {w for w in re.findall(r"[a-z0-9][a-z0-9\-\.]{2,}", norm(text)) if w not in STOP and not w.isdigit()}


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


def find(el, *names):
    for n in names:
        v = el.findtext(n)
        if v:
            return v
    return ""


def read_feed(url: str) -> list[dict]:
    r = requests.get(url, headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    items = []
    rss1 = "{http://purl.org/rss/1.0/}"
    dc = "{http://purl.org/dc/elements/1.1/}"
    atom = "{http://www.w3.org/2005/Atom}"
    for it in list(root.iter("item")) + list(root.iter(rss1 + "item")):  # RSS 2.0 et RSS 1.0 (RDF)
        desc = clean(find(it, "description", rss1 + "description"))
        title = clean(find(it, "title", rss1 + "title")) or desc[:140]
        items.append({
            "title": title,
            "link": find(it, "link", rss1 + "link").strip(),
            "date": parse_date(find(it, "pubDate", dc + "date")),
            "summary": desc[:400],
        })
    for it in root.iter(atom + "entry"):
        link = it.find(atom + "link[@rel='alternate']")
        if link is None:
            link = it.find(atom + "link")
        items.append({
            "title": clean(it.findtext(atom + "title")),
            "link": link.get("href", "") if link is not None else "",
            "date": parse_date(it.findtext(atom + "updated") or it.findtext(atom + "published")),
            "summary": clean(it.findtext(atom + "summary") or it.findtext(atom + "content"))[:400],
        })
    return items


def read_x(handle: str, token: str) -> list[dict]:
    h = {"Authorization": f"Bearer {token}", "User-Agent": UA}
    u = requests.get(f"https://api.x.com/2/users/by/username/{handle}", headers=h, timeout=30)
    u.raise_for_status()
    uid = u.json()["data"]["id"]
    t = requests.get(f"https://api.x.com/2/users/{uid}/tweets", params={"max_results": 20, "tweet.fields": "created_at", "exclude": "retweets,replies"}, headers=h, timeout=30)
    t.raise_for_status()
    return [{"title": clean(x["text"])[:200], "link": f"https://x.com/{handle}/status/{x['id']}", "date": parse_date(x.get("created_at")), "summary": clean(x["text"])} for x in t.json().get("data", [])]


def sources(conf: dict) -> list[dict]:
    out = [dict(f, kind="flux") for f in conf.get("feeds", [])]
    for b in conf.get("bluesky", []) or []:
        out.append({"name": f"Bluesky · {b['name']}", "url": f"https://bsky.app/profile/{b['handle']}/rss", "lang": "en", "weight": b.get("weight", 1), "type": "declaration", "kind": "bluesky"})
    for a in conf.get("google_alerts", []) or []:
        out.append(dict(a, lang=a.get("lang", "fr"), weight=a.get("weight", 1), type="media", kind="alerte", filter=False))
    return out


def classify(item: dict, source_type: str) -> str:
    text = norm(item["title"] + " " + item.get("summary", ""))
    for kind in ("etude", "declaration", "annonce"):
        if re.search(CUES[kind], text):
            return kind
    return {"officiel": "annonce", "etude": "etude", "declaration": "declaration"}.get(source_type, "debat")


def topic_of(item: dict, topics: list[dict]) -> str | None:
    text = " " + norm(item["title"] + " " + item.get("summary", "")) + " "
    for t in topics:
        if any(norm(m) in text for m in t["match"]):
            return t["id"]
    return None


def internal_matches(cluster_tokens: set[str], docs: list) -> list[str]:
    scored = []
    for d in docs:
        if d.kind != "post":
            continue
        dt = tokens(d.meta.get("title", "") + " " + d.slug.replace("-", " ") + " " + " ".join(d.meta.get("essentiel") or []))
        overlap = len(dt & cluster_tokens)
        if overlap >= 2:
            scored.append((overlap, f"/{d.slug}/"))
    return [s for _, s in sorted(scored, reverse=True)[:3]]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int)
    args = ap.parse_args()
    conf = yaml.safe_load(CONF.read_text(encoding="utf-8"))
    STOP.update(norm(w) for w in conf.get("stop_extra") or [])
    ANGLES.update(conf.get("angles") or {})
    days = args.days or conf.get("days", 7)
    OUT.mkdir(exist_ok=True)
    history: dict[str, dict] = {i["id"]: i for i in json.loads(HISTORY.read_text(encoding="utf-8"))} if HISTORY.exists() else {}
    keywords = [norm(k) for k in conf.get("keywords", [])]
    exclude = [norm(k) for k in conf.get("exclude", [])]
    topics = conf.get("topics", [])
    since = NOW - timedelta(days=days)

    broken, fetched, new = [], 0, 0
    feeds = sources(conf)
    token = os.environ.get("X_BEARER_TOKEN", "")
    if token:
        for x in conf.get("x_accounts", []) or []:
            feeds.append({"name": f"X · {x['name']}", "x": x["handle"], "lang": "en", "weight": x.get("weight", 1), "type": "declaration", "kind": "x", "filter": True})
    for feed in feeds:
        try:
            items = read_x(feed["x"], token) if feed.get("x") else read_feed(feed["url"])
        except Exception as e:  # noqa: BLE001 — une source en panne ne bloque pas la veille
            broken.append(f"{feed['name']} ({e.__class__.__name__})")
            continue
        for it in items:
            if not it["title"] or not it["link"]:
                continue
            if it["date"] and it["date"] < NOW - timedelta(days=conf.get("history_days", 45)):
                continue
            text = norm(f"{it['title']} {it['summary']}")
            fkw = [norm(k) for k in feed.get("keywords") or []] or keywords  # mots-clés propres au flux
            if feed.get("filter", True) and fkw and not has_any(text, fkw):
                continue
            if has_any(text, exclude):
                continue
            fetched += 1
            iid = hashlib.sha1(it["link"].encode()).hexdigest()[:16]
            if iid in history:
                continue
            new += 1
            history[iid] = {
                "id": iid, "title": it["title"], "link": it["link"], "summary": it["summary"],
                "date": (it["date"] or NOW).isoformat(), "seen": NOW.isoformat(),
                "source": feed["name"], "lang": feed.get("lang", conf.get("lang_defaut", "en")), "weight": feed.get("weight", 1),
                "type": classify(it, feed.get("type", "media")), "topic": topic_of(it, topics),
            }

    # Purge de l'historique
    limit = NOW - timedelta(days=conf.get("history_days", 45))
    history = {k: v for k, v in history.items() if datetime.fromisoformat(v["date"]) >= limit}
    HISTORY.write_text(json.dumps(sorted(history.values(), key=lambda i: i["date"], reverse=True), ensure_ascii=False, indent=1), encoding="utf-8")

    # Regroupement par sujet sur la fenêtre
    recent = [i for i in history.values() if datetime.fromisoformat(i["date"]) >= since]
    clusters: dict[str, list[dict]] = defaultdict(list)
    loose = []
    for i in recent:
        if i["topic"]:
            clusters[i["topic"]].append(i)
        else:
            loose.append(i)
    # éléments sans sujet prédéfini : regroupés s'ils partagent au moins 2 mots significatifs
    groups: list[list[dict]] = []
    for i in sorted(loose, key=lambda x: x["date"], reverse=True):
        tk = tokens(i["title"])
        for g in groups:
            if len(tk & tokens(" ".join(x["title"] for x in g))) >= 2:
                g.append(i)
                break
        else:
            groups.append([i])
    for n, g in enumerate(groups):
        clusters[f"libre-{n}"] = g

    labels = {t["id"]: t["label"] for t in topics}
    docs = list(all_docs())
    ranked = []
    for cid, items in clusters.items():
        srcs = {i["source"] for i in items}
        score = sum(max(i["weight"] for i in items if i["source"] == s) for s in srcs)
        fresh = max(datetime.fromisoformat(i["date"]) for i in items)
        score *= 1 + max(0, 3 - (NOW - fresh).days) / 3          # bonus de fraîcheur
        langs = {i["lang"] for i in items}
        gap = "en" in langs and "fr" not in langs
        if gap:
            score *= 1.3                                            # écart FR : sujet pas encore traité en français
        older = [h for h in history.values() if (h["topic"] == cid if not cid.startswith("libre") else False) and datetime.fromisoformat(h["date"]) < since]
        rising = len(items) > 2 * max(1, len(older) * days / max(1, conf.get("history_days", 45) - days))
        kind = max(("annonce", "etude", "declaration", "debat"), key=lambda k: sum(1 for i in items if i["type"] == k))
        label = labels.get(cid) or max(items, key=lambda i: i["weight"])["title"]
        tk = tokens(" ".join(i["title"] for i in items))
        ranked.append({"id": cid, "label": label, "score": round(score, 1), "items": sorted(items, key=lambda i: (-i["weight"], i["date"])),
                       "sources": len(srcs), "gap": gap, "rising": rising, "kind": kind, "update": internal_matches(tk, docs)})
    ranked.sort(key=lambda c: c["score"], reverse=True)
    # Sujet retenu : couvert par `min_sources` sources distinctes (2 par défaut), ou par une source de poids ≥ 3
    min_src = conf.get("min_sources", 2)
    top = [c for c in ranked if c["sources"] >= min_src or c["items"][0]["weight"] >= 3][: conf.get("keep_top", 12)]

    today = NOW.strftime("%Y-%m-%d")
    out = [f"# Veille du {today}", "",
           f"{len(recent)} éléments sur {days} jours, {new} nouveaux aujourd'hui, {len(ranked)} sujets. "
           "Classement : nombre de sources distinctes × poids des sources × fraîcheur, bonus si le sujet n'est pas encore traité en français.", ""]
    for n, c in enumerate(top, 1):
        tags = [f"score {c['score']}", f"{c['sources']} sources"]
        if c["gap"]:
            tags.append("**écart FR**")
        if c["rising"]:
            tags.append("**en hausse**")
        out += [f"## {n}. {c['label']}", "", f"_{' · '.join(tags)} · type dominant : {c['kind']}_", ""]
        out += ["**Sources**", ""]
        for i in c["items"][:8]:
            out.append(f"- {i['source']} ({i['date'][:10]}) : [{i['title']}]({i['link']})")
        out += ["", "**Angle à valeur ajoutée**", ""] + [f"- {a}" for a in ANGLES[c["kind"]]]
        if c["update"]:
            out += ["", "**Mettre à jour plutôt que créer** : " + ", ".join(c["update"]) + " (vérifier si le sujet y est déjà traité)."]
        out += ["", "**Décision** : [ ] article · [ ] mise à jour · [ ] ignorer", ""]
    if not top:
        out.append(f"Aucun sujet couvert par au moins {min_src} source(s) cette semaine.")
    if broken:
        out += ["", "## Sources injoignables", "", "À corriger ou retirer dans `config/veille.yml` :", ""] + [f"- {b}" for b in broken]
    if not token:
        out += ["", "_Comptes X non suivis : ajouter le secret `X_BEARER_TOKEN` pour les activer. Leurs déclarations sont relayées par Search Engine Roundtable._"]
    (OUT / f"{today}.md").write_text("\n".join(out) + "\n", encoding="utf-8")

    # Plan glissant : les 15 meilleurs sujets, avec le statut décidé à la main conservé
    plan = ["# Plan d'articles (mis à jour chaque jour par la veille)", "",
            "Un sujet entre dans le plan quand au moins deux sources en parlent, ou une source officielle. "
            "Avant d'écrire, suivre le skill `veille-valeur-ajoutee` : un article n'est justifié que s'il apporte quelque chose que les sources ne donnent pas.", "",
            "| Sujet | Score | Sources | Signal | Type | Contenu existant | Rapport |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for c in ranked[:15]:
        sig = " ".join(s for s, ok in (("écart FR", c["gap"]), ("en hausse", c["rising"])) if ok) or "–"
        plan.append(f"| {c['label'][:80]} | {c['score']} | {c['sources']} | {sig} | {c['kind']} | {', '.join(c['update']) or '–'} | [{today}]({today}.md) |")
    (OUT / "plan.md").write_text("\n".join(plan) + "\n", encoding="utf-8")

    print(f"veille/{today}.md : {fetched} éléments lus, {new} nouveaux, {len(top)} sujets retenus, {len(broken)} source(s) en erreur")
    for b in broken:
        warn(f"source injoignable : {b}")


if __name__ == "__main__":
    main()

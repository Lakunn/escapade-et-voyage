"""
Carte des mots-clés et calendrier éditorial d'un site (script commun aux 4 sites de Valentin :
escapade-et-voyage.fr, guidecanin.fr, valentinrouault.com, growww.app). Fichier identique dans les 4 dépôts :
le modifier dans l'un, puis le recopier dans les trois autres. Tout ce qui est propre au site est dans
config/keyword_seeds.yml.

1. Découverte (gratuite) : chaque graine est déclinée par les suggestions Google (graine seule, + a…z, + les
   déclinaisons du fichier), puis, si `second_niveau` est défini, les entités repérées (destinations, races…)
   sont déclinées à leur tour. Une requête suggérée tôt et sur plusieurs déclinaisons est très tapée : c'est
   l'indice de demande quand on n'a pas de volume.
2. Volumes, par ordre de priorité :
   a. config/volumes.yml : relevés à la main avec l'extension Keyword Surfer dans Chrome (Google, le plus fiable) ;
   b. DataForSEO (secrets DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD) : volumes Google Ads, ~0,075 $ les 1 000 ;
   c. Bing Webmaster Tools (secret BING_WEBMASTER_API_KEY, gratuit) : recherches Bing, converties en équivalent
      Google par le rapport médian observé sur les requêtes aussi mesurées avec Surfer (sinon `facteur_bing`) ;
   d. à défaut, l'indice de demande Google Suggest.
3. SERP des meilleures requêtes (DataForSEO si disponible, sinon SerpAPI : secret SERPAPI_API_KEY, 250 gratuites
   par mois partagées entre les sites) : « Autres questions », recherches associées, faisabilité (part du top 10
   tenue par des sites faibles selon le classement Tranco, des forums ou des plateformes).
4. Regroupement en articles (même SERP, même mois, même sujet), score = volume (ou demande) × faisabilité ×
   adéquation à la ligne éditoriale, calendrier à N articles par semaine.

Sorties : config/keywords.yml (lu par le skill de contenu du site) et keywords/calendrier.md.
Cache : keywords/.cache (suggestions 30 jours, SERP 14 jours, volumes 30 jours, Tranco 30 jours).

Usage :
    python scripts/keyword_map.py                 tout, selon les clés disponibles
    python scripts/keyword_map.py --serp 0        découverte et calendrier sans aucun appel payant
    python scripts/keyword_map.py --a-relever     requêtes d'articles sans volume, à passer dans Keyword Surfer
Lancé chaque mois par le workflow « Carte des mots-clés » (.github/workflows/keywords.yml).
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
import re
import string
import sys
import time
import unicodedata
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import median
from urllib.parse import urlsplit

import requests
import yaml

REPO = Path(__file__).resolve().parents[1]
SEEDS_FILE = REPO / "config" / "keyword_seeds.yml"
VOL_FILE = REPO / "config" / "volumes.yml"
OUT_YML = REPO / "config" / "keywords.yml"
OUT_MD = REPO / "keywords" / "calendrier.md"
CACHE = REPO / "keywords" / ".cache"
UA = "Mozilla/5.0 (compatible; media-keyword-map/1.0)"

MOIS = ["janvier", "fevrier", "mars", "avril", "mai", "juin", "juillet", "aout", "septembre", "octobre", "novembre", "decembre"]
MOIS_AFF = "janv. févr. mars avr. mai juin juil. août sept. oct. nov. déc.".split()
SAISONS = {"noel": [12], "hiver": [12, 1, 2], "ski": [1, 2], "printemps": [4, 5], "paques": [4], "ete": [7, 8],
           "automne": [10], "toussaint": [10], "nouvel an": [12], "saint valentin": [2], "pont": [5], "ascension": [5],
           "pentecote": [5], "rentree": [9], "black friday": [11], "soldes": [1, 7], "fete des meres": [5], "halloween": [10]}
STOP = {"de", "du", "des", "le", "la", "les", "l", "d", "a", "en", "au", "aux", "un", "une", "et", "pour", "avec", "ou"}
UGC = re.compile(r"(reddit|tripadvisor|forum|quora|youtube|facebook|tiktok|instagram|pinterest|doctissimo|commentcamarche)")
OFFICIAL = re.compile(r"(gouv|europa\.eu|ameli|service-public|diplomatie|\.gov|developers\.google|support\.google)")


# ---------------------------------------------------------------- texte

def norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text).lower().replace("'", " ").replace("’", " ")).encode("ascii", "ignore").decode()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


def dedupe_key(kw: str) -> str:
    words = [w[:-1] if len(w) > 3 and w.endswith(("s", "x")) else w for w in norm(kw).split() if not re.fullmatch(r"20\d\d", w)]
    return " ".join(sorted(w for w in words if w not in STOP))


def season_of(kw: str) -> list[int]:
    n = norm(kw)
    months = [i + 1 for i, m in enumerate(MOIS) if re.search(rf"\b{m}\b", n)]
    for word, ms in SAISONS.items():
        if re.search(rf"\b{word}\b", n):
            months += ms
    return sorted(set(months))


# ---------------------------------------------------------------- cache

def cache_get(kind: str, key: str, days: int):
    f = CACHE / kind / (hashlib.sha1(key.encode()).hexdigest()[:20] + ".json")
    if f.exists() and f.stat().st_mtime > time.time() - days * 86400:
        return json.loads(f.read_text(encoding="utf-8"))
    return None


def cache_put(kind: str, key: str, value) -> None:
    d = CACHE / kind
    d.mkdir(parents=True, exist_ok=True)
    (d / (hashlib.sha1(key.encode()).hexdigest()[:20] + ".json")).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------- sources

def suggest(q: str, lang: str, country: str) -> list[str]:
    hit = cache_get("suggest", f"{lang}:{country}:{q}", 30)
    if hit is not None:
        return hit
    for attempt in range(2):
        try:
            r = requests.get("https://suggestqueries.google.com/complete/search",
                             params={"client": "firefox", "q": q, "hl": lang, "gl": country.lower()},
                             headers={"User-Agent": UA}, timeout=10)
            r.raise_for_status()
            data = r.json()
            out = [str(s) for s in (data[1] if len(data) > 1 else [])]
            cache_put("suggest", f"{lang}:{country}:{q}", out)
            time.sleep(0.15)
            return out
        except (requests.RequestException, ValueError) as exc:
            if attempt:
                print("Suggest refusé :", q, str(exc)[:80])
            time.sleep(2)
    return []


def dfs_auth():
    login, pwd = os.getenv("DATAFORSEO_LOGIN", "").strip(), os.getenv("DATAFORSEO_PASSWORD", "").strip()
    return (login, pwd) if login and pwd else None


DFS_LOCATIONS = {"FR": 2250, "US": 2840, "GB": 2826, "BE": 2056, "CA": 2124, "CH": 2756}


def serp(q: str, lang: str, country: str) -> dict | None:
    """Top 10, PAA, recherches associées, présence d'AI Overview. DataForSEO sinon SerpAPI. Cache 14 jours."""
    key = f"{lang}:{country}:{q}"
    hit = cache_get("serp", key, 14)
    if hit is not None:
        return hit
    out = None
    auth = dfs_auth()
    if auth:
        r = requests.post("https://api.dataforseo.com/v3/serp/google/organic/live/advanced", auth=auth, timeout=60,
                          json=[{"keyword": q, "location_code": DFS_LOCATIONS.get(country.upper(), 2250),
                                 "language_code": lang, "depth": 10}])
        r.raise_for_status()
        items = (((r.json().get("tasks") or [{}])[0].get("result") or [{}])[0].get("items")) or []
        out = {"organic": [], "paa": [], "related": [], "aio": False}
        for it in items:
            t = it.get("type")
            if t == "organic":
                out["organic"].append({"url": it.get("url", ""), "domain": it.get("domain", "")})
            elif t == "people_also_ask":
                out["paa"] += [x.get("title", "") for x in it.get("items") or [] if x.get("title")]
            elif t == "related_searches":
                out["related"] += [x for x in it.get("items") or [] if isinstance(x, str)]
            elif t == "ai_overview":
                out["aio"] = True
    elif os.getenv("SERPAPI_API_KEY"):
        r = requests.get("https://serpapi.com/search.json", timeout=60, params={
            "engine": "google", "q": q, "hl": lang, "gl": country.lower(), "num": 10, "api_key": os.environ["SERPAPI_API_KEY"]})
        r.raise_for_status()
        d = r.json()
        if d.get("error"):
            raise RuntimeError(d["error"])
        out = {"organic": [{"url": o.get("link", ""), "domain": urlsplit(o.get("link", "")).netloc} for o in d.get("organic_results") or []],
               "paa": [x.get("question", "") for x in d.get("related_questions") or [] if x.get("question")],
               "related": [x.get("query", "") for x in d.get("related_searches") or [] if x.get("query")],
               "aio": bool(d.get("ai_overview"))}
    if out is not None:
        cache_put("serp", key, out)
    return out


def dfs_volumes(keywords: list[str], lang: str, country: str) -> dict[str, int]:
    auth = dfs_auth()
    out, missing = {}, []
    for k in keywords:
        hit = cache_get("vol_dfs", f"{lang}:{country}:{k.lower()}", 30)
        if hit is None:
            missing.append(k)
        else:
            out[k] = hit
    if auth and missing:
        clean = [" ".join(re.sub(r"[,!@%^()={};~`<>?\\|*]", " ", k).split()) for k in missing]
        clean = [k for k in clean if k and len(k) <= 80 and len(k.split()) <= 10]
        for i in range(0, len(clean), 1000):
            r = requests.post("https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live", auth=auth, timeout=120,
                              json=[{"keywords": clean[i:i + 1000], "location_code": DFS_LOCATIONS.get(country.upper(), 2250),
                                     "language_code": lang}])
            r.raise_for_status()
            for it in ((r.json().get("tasks") or [{}])[0].get("result") or []):
                if it.get("keyword"):
                    v = it.get("search_volume") or 0
                    out[it["keyword"]] = v
                    cache_put("vol_dfs", f"{lang}:{country}:{it['keyword'].lower()}", v)
    return out


def bing_volume(keyword: str, lang: str, country: str) -> int | None:
    """Recherches Bing mensuelles moyennes sur 12 mois (API officielle de Bing Webmaster Tools, gratuite)."""
    key = os.getenv("BING_WEBMASTER_API_KEY", "").strip()
    if not key:
        return None
    hit = cache_get("vol_bing", f"{lang}:{country}:{keyword}", 30)
    if hit is not None:
        return hit
    try:
        r = requests.get("https://ssl.bing.com/webmaster/api.svc/json/GetKeywordStats", timeout=30, params={
            "apikey": key, "q": keyword, "country": country.lower(), "language": f"{lang}-{country.upper()}"})
        r.raise_for_status()
        rows = r.json().get("d") or []
    except (requests.RequestException, ValueError):
        return None
    v = round(sum(int(x.get("Impressions") or 0) for x in rows[-52:]) / 12)  # 52 semaines → moyenne mensuelle
    cache_put("vol_bing", f"{lang}:{country}:{keyword}", v)
    return v


TRANCO_URL = "https://tranco-list.eu/top-1m.csv.zip"


def load_tranco() -> dict[str, int]:
    """Classement Tranco des 1 000 000 domaines les plus visités (gratuit). Repères : pinterest.com 54e,
    routard.com ~31 000e, generationvoyage.fr ~105 000e ; un petit site est au-delà de 300 000 ou absent."""
    f = CACHE / "tranco" / "top-1m.csv"
    if not f.exists() or f.stat().st_mtime < time.time() - 30 * 86400:
        f.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(requests.get(TRANCO_URL, timeout=180).content)) as z:
            f.write_bytes(z.read("top-1m.csv"))
    out = {}
    for line in f.read_text(encoding="utf-8").splitlines():
        rank, _, dom = line.partition(",")
        out[dom.strip()] = int(rank)
    return out


def tranco_rank(tranco: dict[str, int], domain: str) -> int | None:
    parts = domain.lower().removeprefix("www.").split(".")
    for i in range(len(parts) - 1):
        r = tranco.get(".".join(parts[i:]))
        if r:
            return r
    return None


def weakness_of(rank: int | None) -> float:
    """1 = concurrent battable par un site modeste, 0 = très fort."""
    if rank is None or rank > 500_000:
        return 1.0
    if rank > 150_000:
        return 0.8
    if rank > 50_000:
        return 0.5
    if rank > 10_000:
        return 0.25
    return 0.0


# ---------------------------------------------------------------- site

def front_matter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    try:
        return yaml.safe_load(text.split("---")[1]) or {}
    except yaml.YAMLError:
        return {}


def existing_slugs(cfg: dict) -> list[tuple[str, set[str]]]:
    """(slug, mots du slug) de chaque contenu existant : sert à repérer un sujet déjà traité sous un autre titre."""
    out = []
    for folder in cfg.get("contenus", ["content/posts"]):
        for p in sorted((REPO / folder).glob("*.*")):
            if p.suffix in (".md", ".html"):
                slug = str(front_matter(p).get("slug") or p.stem)
                out.append((slug, set(dedupe_key(slug.replace("-", " ")).split())))
    return out


def existing_posts(cfg: dict) -> dict[str, tuple]:
    out = {}
    for folder in cfg.get("contenus", ["content/posts"]):
        for p in sorted((REPO / folder).glob("*.*")):
            if p.suffix not in (".md", ".html"):
                continue
            fm = front_matter(p)
            slug = fm.get("slug") or p.stem
            for k in [fm.get("keyword"), fm.get("title")] + list(fm.get("keywords_secondaires") or []):
                if k:
                    out[dedupe_key(str(k))] = (slug, fm.get("status", "publish"), fm.get("date"))
    return out


# ---------------------------------------------------------------- programme

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--serp", type=int, help="nombre maximal de SERP (défaut : serp_max du fichier de graines)")
    ap.add_argument("--par-semaine", type=int)
    ap.add_argument("--semaines", type=int)
    ap.add_argument("--debut", help="premier lundi du calendrier (défaut : lundi suivant le dernier article programmé)")
    ap.add_argument("--a-relever", action="store_true", help="requêtes d'articles sans volume (pour Keyword Surfer)")
    args = ap.parse_args()

    if args.a_relever:
        data = yaml.safe_load(OUT_YML.read_text(encoding="utf-8"))
        rows = [a for a in data["articles"] if a.get("volume") is None and a.get("statut") == "idee"]
        print(json.dumps([[a["cle"]] + a["secondaires"][:8] for a in rows], ensure_ascii=False))
        return

    cfg = yaml.safe_load(SEEDS_FILE.read_text(encoding="utf-8"))
    lang, country = cfg.get("langue", "fr"), cfg.get("pays", "FR")
    excl = [norm(w) for w in cfg.get("exclure_mots") or []]
    serp_max = cfg.get("serp_max", 40) if args.serp is None else args.serp
    par_semaine = args.par_semaine or cfg.get("par_semaine", 3)
    semaines = args.semaines or cfg.get("semaines", 10)
    rules = [(r["slug"], float(r.get("adequation", 1.0)), re.compile(r["motif"])) for r in cfg.get("rubriques") or []]
    defaut = cfg.get("rubrique_defaut") or {"slug": "a-classer", "adequation": 0.4}
    FIT = {s: f for s, f, _ in rules} | {defaut["slug"]: float(defaut.get("adequation", 0.4))}
    coeur = set(cfg.get("rubriques_coeur") or [s for s, f, _ in rules if f >= 1.0])
    generic = {norm(w) for w in cfg.get("mots_habillage") or []}

    def rubrique_of(kw: str) -> str:
        n = norm(kw)
        for slug, _, pat in rules:
            if pat.search(n):
                return slug
        return defaut["slug"]

    # 1. Découverte
    cand: dict[str, dict] = {}

    def harvest(prefix: str, w: float, seed: str) -> None:
        for rank, s in enumerate(suggest(prefix, lang, country)):
            n = norm(s)
            if len(n.split()) < 2 or any(re.search(r"\b" + re.escape(e) + r"\b", n) for e in excl):
                continue
            c = cand.setdefault(dedupe_key(s), {"keyword": s, "demande": 0.0, "graines": set()})
            c["demande"] += w * (10 - min(rank, 9)) / 10
            c["graines"].add(seed)
            if len(s) < len(c["keyword"]):
                c["keyword"] = s

    for seed in cfg["graines"]:
        prefixes = [(seed, 2.0)] + [(f"{seed} {d}", 1.0) for d in cfg.get("declinaisons") or []] \
            + [(f"{seed} {c}", 0.7) for c in string.ascii_lowercase]
        for prefix, w in prefixes:
            harvest(prefix, w, seed)

    niv2 = cfg.get("second_niveau")
    if niv2:
        pat = re.compile(niv2["motif"])
        not_entity = {norm(w) for w in niv2.get("exclure_mots") or []} | set(MOIS)
        score, form = Counter(), {}
        for c in cand.values():
            m = pat.match(c["keyword"].lower())
            if not m:
                continue
            d = m.group(1).strip()
            nd = norm(d)
            if not nd or len(nd.split()) > 3 or set(nd.split()) & not_entity:
                continue
            score[nd] += c["demande"]
            form.setdefault(nd, d)
        entities = [form[d] for d, _ in score.most_common(niv2.get("max", 40))]
        print("Second niveau :", ", ".join(entities))
        for d in entities:
            for tpl in niv2.get("gabarits") or []:
                harvest(tpl.format(d=d), 1.0, f"entite:{d}")

    for c in cand.values():
        c["rubrique"] = rubrique_of(c["keyword"])
        c["saison"] = season_of(c["keyword"])
        c["graines"] = sorted(c["graines"])
    print(f"{len(cand)} requêtes découvertes par les suggestions")

    # 2. Volumes DataForSEO sur les meilleures candidates (les relevés Surfer s'appliquent aux articles, plus bas)
    by_demand = sorted(cand.values(), key=lambda c: -c["demande"] * FIT[c["rubrique"]])
    if dfs_auth():
        vols = dfs_volumes([c["keyword"] for c in by_demand[:1000]], lang, country)
        for k, v in vols.items():
            c = cand.get(dedupe_key(k))
            if c:
                c["volume"], c["volume_source"] = v, "DataForSEO"
        print(f"Volumes DataForSEO : {len(vols)}")

    def demand(c):
        return math.log10(c["volume"] + 10) * 2 if c.get("volume") is not None else c["demande"]

    ranked = sorted(cand.values(), key=lambda c: -demand(c) * FIT[c["rubrique"]])

    # Fenêtre du calendrier : après le dernier article déjà programmé
    existing = existing_posts(cfg)
    planned = []
    for hit in existing.values():
        try:
            planned.append(datetime.fromisoformat(str(hit[2])).date())
        except (TypeError, ValueError):
            pass
    last = max([d for d in planned if d >= date.today()] or [date.today()])
    start = date.fromisoformat(args.debut) if args.debut else last + timedelta(days=7 - last.weekday())
    end = start + timedelta(weeks=semaines)

    def windows(x) -> list[tuple[date, date]]:
        out = []
        for m in x.get("saison") or []:
            for y in (start.year, start.year + 1):
                first = date(y, m, 1)
                lo, hi = first - timedelta(weeks=10), first - timedelta(weeks=3)
                if hi >= start - timedelta(days=7):
                    out.append((lo, hi))
                    break
        return out

    def schedulable(x) -> bool:
        return not x.get("saison") or any(lo <= end and hi >= start for lo, hi in windows(x))

    # 3. SERP des meilleures requêtes, sans payer deux fois le même sujet
    synonyms = {"visiter": "partir", "aller": "partir", "vacance": "voyage", "sejour": "voyage", "ou": "", "quel": "", "quelle": ""}
    chosen, seen_keys = [], []
    for c in ranked:
        if len(chosen) >= max(serp_max, 1) * (1 if serp_max else 40):
            break
        if c["rubrique"] == defaut["slug"] or not schedulable(c):
            continue
        toks = {synonyms.get(t, t) for t in dedupe_key(c["keyword"]).split()} - {""}
        if any(len(toks & s) / max(1, min(len(toks), len(s))) >= 0.8 for s in seen_keys):
            continue
        seen_keys.append(toks)
        chosen.append(c)

    serps, no_key, stopped = {}, 0, False
    for c in chosen[:serp_max]:
        if stopped:  # quota épuisé ou panne : on ne prend plus que ce qui est en cache
            r = cache_get("serp", f"{lang}:{country}:{c['keyword']}", 14)
        else:
            try:
                r = serp(c["keyword"], lang, country)
            except Exception as exc:  # noqa: BLE001
                print("SERP interrompues :", str(exc)[:120])
                stopped, r = True, None
        if r is None:
            no_key += 1
            continue
        serps[c["keyword"]] = r
    if no_key:
        print(f"{no_key} SERP manquantes (pas de clé DATAFORSEO_* ni SERPAPI_API_KEY, ou quota) : faisabilité neutre pour ces requêtes")
    print(f"{len(serps)} SERP disponibles")
    tranco = load_tranco() if serps else {}
    for c in chosen:
        r = serps.get(c["keyword"])
        if not r:
            c.update(faisabilite=0.5, urls=[], top3=[], paa=[], associees=[])  # faisabilité inconnue : neutre
            continue
        top = r["organic"][:10]
        ranks, weak_w, weights, weak, official = [], [], [], 0, 0
        for pos, o in enumerate(top, 1):
            d = o["domain"].removeprefix("www.")
            rank = tranco_rank(tranco, d)
            ranks.append(rank or 2_000_000)
            w = 1.0 if UGC.search(o["url"]) else weakness_of(rank)
            weak_w.append(w)
            weights.append(2.0 if pos <= 5 else 1.0)
            weak += w >= 0.8
            official += bool(OFFICIAL.search(d)) and pos <= 5
        share = sum(w * k for w, k in zip(weak_w, weights)) / max(1, sum(weights))
        feas = (0.15 + 0.85 * share) * 0.85 ** official * (0.9 if r["aio"] else 1)
        c.update(faisabilite=round(feas, 2), tranco_median=int(median(ranks)) if ranks else None, faibles=weak,
                 officiels=official, aio=r["aio"], urls=[o["url"] for o in top],
                 top3=[o["domain"].removeprefix("www.") for o in top[:3]], paa=r["paa"], associees=r["related"])

    # 4. Articles : même SERP (4 URL communes sur 10), même mois, ou même sujet sans les mots d'habillage
    def month_signature(kw: str):
        months = season_of(kw)
        rest = set(dedupe_key(kw).split()) - set(MOIS) - {m[:-1] for m in MOIS}
        return frozenset(months) if months and generic and rest <= generic else None

    def topic_signature(kw: str):
        toks = {{"pote": "ami", "copain": "ami"}.get(t, t) for t in dedupe_key(kw).split()}
        sig = toks - generic
        return frozenset(sig) if sig and generic and not season_of(kw) else None

    def overlap(a: list[str], b: list[str]) -> float:
        sa, sb = set(a), set(b)
        return len(sa & sb) / min(len(sa), len(sb)) if sa and sb else 0.0

    clusters: list[list[dict]] = []
    for c in chosen:
        sig, tsig = month_signature(c["keyword"]), topic_signature(c["keyword"])
        for cl in clusters:
            hs, ht = month_signature(cl[0]["keyword"]), topic_signature(cl[0]["keyword"])
            if overlap(cl[0]["urls"], c["urls"]) >= 0.4 or (sig and hs and sig & hs) or (tsig and tsig == ht):
                cl.append(c)
                break
        else:
            clusters.append([c])
    heads = [(set(dedupe_key(cl[0]["keyword"]).split()), cl) for cl in clusters]
    satellites = defaultdict(list)
    chosen_ids = {id(c) for c in chosen}
    for c in ranked:
        if id(c) in chosen_ids or c["rubrique"] == defaut["slug"]:
            continue
        toks = set(dedupe_key(c["keyword"]).split())
        best = max(heads, key=lambda h: len(toks & h[0]) / max(1, len(h[0])), default=None)
        if best and toks >= best[0]:
            satellites[id(best[1])].append(c["keyword"])

    slugs = existing_slugs(cfg)
    manual = (yaml.safe_load(VOL_FILE.read_text(encoding="utf-8")) or {}).get("articles", {}) if VOL_FILE.exists() else {}
    articles = []
    for cl in clusters:
        head = cl[0]
        rub = Counter(c["rubrique"] for c in cl).most_common(1)[0][0]
        feas = sum(c["faisabilite"] for c in cl) / len(cl)
        paa = list(dict.fromkeys(q for c in cl for q in c["paa"]))
        statut, slug = "idee", None
        for c in cl:
            hit = existing.get(dedupe_key(c["keyword"]))
            if hit:
                slug, statut = hit[0], "publie" if hit[1] == "publish" else "programme"
        if statut == "idee":  # sujet peut-être déjà traité : les mots porteurs d'un slug existant sont tous dans la requête
            for s_slug, s_toks in slugs:
                core = s_toks - generic - {"guide", "conseil", "conseils", "astuce", "astuces"}
                if core and all(core <= set(dedupe_key(c["keyword"]).split()) for c in cl[:1]):
                    slug, statut = s_slug, "existe_peut_etre"
                    break
        a = {"cle": head["keyword"], "requete": head["keyword"], "rubrique": rub, "volume": head.get("volume"),
             "volume_source": head.get("volume_source"), "demande": round(sum(demand(c) for c in cl), 1),
             "faisabilite": round(feas, 2), "saison": sorted({m for c in cl for m in c["saison"]}),
             "tranco_median_top10": head.get("tranco_median"), "resultats_faibles_top10": head.get("faibles"),
             "officiels_top5": head.get("officiels"), "ai_overview": head.get("aio"), "top3": head.get("top3"),
             "secondaires": [c["keyword"] for c in cl[1:]] + satellites[id(cl)][:10], "variantes": {},
             "questions": paa[:8], "associees": (head.get("associees") or [])[:8], "statut": statut, "slug": slug}
        m = manual.get(a["cle"])
        if m:
            a.update(requete=m["requete"], volume=m["volume"], volume_source="Keyword Surfer", variantes=m.get("variantes") or {})
        articles.append(a)

    # Bing : volumes des articles encore sans volume, convertis en équivalent Google
    if os.getenv("BING_WEBMASTER_API_KEY"):
        pairs = [(a["volume"], bing_volume(a["requete"], lang, country)) for a in articles if a["volume_source"] == "Keyword Surfer"]
        ratios = [g / b for g, b in pairs if g and b]
        factor = median(ratios) if len(ratios) >= 5 else float(cfg.get("facteur_bing", 20))
        for a in articles:
            if a["volume"] is None:
                b = bing_volume(a["requete"], lang, country)
                if b is not None:
                    a["volume"], a["volume_source"] = round(b * factor), f"Bing x{factor:.0f}"
        print(f"Bing : facteur Google/Bing {factor:.1f} ({len(ratios)} requêtes de calibrage)")

    for a in articles:
        if a["volume"] is None:  # pas de volume : indice Suggest, minoré pour passer après les sujets mesurés
            a["score"] = round(a["demande"] * a["faisabilite"] * FIT[a["rubrique"]] * 0.5, 2)
            continue
        if a["volume"] < 50:
            a["statut"], a["score"] = ("ecarte" if a["statut"] == "idee" else a["statut"]), 0.0
            continue
        effective = a["volume"] + 0.3 * sum(a["variantes"].values())
        # log² : 12 000 recherches pèsent ~3 fois plus que 200 (un log simple ne donnait que 1,6 fois)
        a["score"] = round(math.log10(effective + 10) ** 2 / 2 * a["faisabilite"] * FIT[a["rubrique"]], 2)
    # Destinations ou thèmes prioritaires (config `focus`) : on couvre quelques sujets à fond plutôt que tout en surface
    focus = cfg.get("focus") or {}
    motifs = [re.compile(m, re.I) for m in focus.get("motifs") or []]
    for a in articles:
        if motifs and any(m.search(norm(a["requete"])) or m.search(a["requete"]) for m in motifs):
            a["focus"] = True
            a["score"] = round(a["score"] * float(focus.get("bonus", 1.6)), 2)
    articles.sort(key=lambda a: -a["score"])
    known = {dedupe_key(a["requete"]) for a in articles} | {dedupe_key(s) for a in articles for s in a["secondaires"]}
    idees_paa = sorted({q for a in articles for q in a["questions"] if dedupe_key(q) not in known})

    # 5. Calendrier : saisonniers 3 à 10 semaines avant leur mois, un même gabarit au plus une fois par semaine
    days = {1: [1], 2: [1, 4], 3: [0, 2, 4], 4: [0, 2, 4, 5], 5: [0, 1, 2, 3, 4]}.get(par_semaine, list(range(min(7, par_semaine))))
    slots = [start + timedelta(weeks=w, days=d) for w in range(semaines) for d in days]

    def template(kw: str) -> str:
        words = [{"visiter": "partir", "ou": "quand"}.get(w, w) for w in norm(kw).split()]
        return " ".join(words[:2])

    todo = [a for a in articles if a["statut"] == "idee" and a["score"] > 0]
    calendar, used, rub_count = [], set(), Counter()
    for slot in slots:
        pool = [a for a in todo if id(a) not in used]
        if not pool:
            break
        recent = [template(x["requete"]) for x in calendar[-len(days):]]

        def priority(a):
            p = a["score"]
            if a["saison"]:
                if not any(lo <= slot <= hi for lo, hi in windows(a)):
                    return float("-inf")
                p = p * 1.5 + 1
            if a["rubrique"] not in coeur:
                p -= 0.4 * rub_count[a["rubrique"]]
            if template(a["requete"]) in recent:
                p *= 0.4
            return p

        a = max(pool, key=priority)
        if priority(a) == float("-inf"):
            continue
        used.add(id(a))
        rub_count[a["rubrique"]] += 1
        a["date_prevue"] = slot.isoformat()
        calendar.append(a)

    today = date.today().isoformat()
    sources = Counter(a["volume_source"] or "indice Suggest" for a in articles)
    data = {"genere_le": today, "sources_volumes": dict(sources),
            "calendrier": [{"date": a["date_prevue"], "requete": a["requete"], "volume": a["volume"], "rubrique": a["rubrique"]}
                           for a in calendar],
            "articles": articles, "idees_paa": idees_paa[:150],
            "reserve": [{"requete": c["keyword"], "demande": round(c["demande"], 1), "volume": c.get("volume"), "rubrique": c["rubrique"]}
                        for c in ranked if id(c) not in chosen_ids][:400]}
    header = (f"# Carte des mots-clés, générée par scripts/keyword_map.py le {today}. Ne pas éditer à la main :\n"
              "# volumes manuels dans config/volumes.yml, graines et règles dans config/keyword_seeds.yml.\n")
    OUT_YML.write_text(header + yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=140), encoding="utf-8")

    def vol(a):
        if a.get("volume") is None:
            return "à relever"
        src = {"Keyword Surfer": "", "DataForSEO": " (DFS)"}.get(a["volume_source"], " (Bing)")
        return f"{a['volume']:,}".replace(",", " ") + src

    jours = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]
    L = [f"# Calendrier éditorial, généré le {today}", "",
         f"{len(cand)} requêtes découvertes, {len(serps)} SERP, {len(articles)} articles possibles, {len(calendar)} placés "
         f"({par_semaine} par semaine). Volumes : " + ", ".join(f"{k} {v}" for k, v in sources.items()) + ".", "",
         "Volume = recherches Google mensuelles (Keyword Surfer, DataForSEO ou Bing converti) ; « à relever » = pas encore "
         "mesuré, classé sur l'indice Google Suggest. Faisabilité = part du top 10 (top 5 compté double) tenue par des sites "
         "faibles (hors des 150 000 premiers domaines Tranco), des forums ou des plateformes. Score = volume × faisabilité × "
         "adéquation à la ligne éditoriale. Un même gabarit de titre au plus une fois par semaine.", "",
         "## Calendrier", "", "| Date | Requête principale | Volume/mois | Rubrique | Score | Faisab. | Saison | Questions à couvrir |",
         "|---|---|---|---|---|---|---|---|"]
    for a in calendar:
        d = date.fromisoformat(a["date_prevue"])
        s = ", ".join(MOIS_AFF[m - 1] for m in a["saison"]) or "toute l'année"
        L.append(f"| {jours[d.weekday()]} {d.strftime('%d/%m')} | {'★ ' if a.get('focus') else ''}{a['requete']} | {vol(a)} | {a['rubrique']} | {a['score']} | "
                 f"{a['faisabilite']} | {s} | {' · '.join(a['questions'][:3])} |")
    L += ["", "## Tous les articles possibles", "", "| Requête | Volume/mois | Rubrique | Score | Faisab. | Top 3 | Statut |",
          "|---|---|---|---|---|---|---|"]
    for a in articles:
        L.append(f"| {a['requete']} | {vol(a)} | {a['rubrique']} | {a['score']} | {a['faisabilite']} | {', '.join(a['top3'] or [])} | "
                 f"{a['statut']}{' (' + a['slug'] + ')' if a['slug'] else ''} |")
    L += ["", "## Questions « Autres questions » qui ouvrent d'autres sujets", ""] + [f"- {q}" for q in idees_paa[:60]]
    OUT_MD.parent.mkdir(exist_ok=True)
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Écrit : config/keywords.yml, keywords/calendrier.md ({len(calendar)} dates, {len(articles)} articles)")


if __name__ == "__main__":
    main()

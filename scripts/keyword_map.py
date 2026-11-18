"""
Carte des mots-clés et calendrier éditorial d'escapade-et-voyage.fr.

1. Découverte (gratuite) : chaque graine de config/keyword_seeds.yml est déclinée par les suggestions Google
   (graine seule, + a…z, + mots interrogatifs, + mois). Google classe ses suggestions par popularité : une
   requête suggérée tôt, et sur plusieurs déclinaisons, est très recherchée. C'est notre indice de demande
   quand on n'a pas de volume.
2. Tri : mots exclus (météo, marques, navigationnel…), doublons (accents, pluriels, mots vides), rubrique.
3. SERP des meilleures requêtes (cache 14 jours ; DataForSEO si la clé est dans l'outil, sinon SerpAPI) :
   « Autres questions » (PAA), recherches associées, faisabilité (part du top 10 tenue par des sites faibles
   selon le classement Tranco, des forums ou des plateformes ; malus si des sites officiels tiennent le top 5).
4. Regroupement en articles : deux requêtes qui partagent au moins 4 URL du top 10 = un seul article ; les
   PAA deviennent les H2/FAQ de l'article, et les PAA qui ouvrent un autre sujet deviennent des idées.
5. Score = demande × faisabilité × adéquation à la ligne éditoriale ; calendrier à N articles par semaine,
   les sujets saisonniers placés 6 à 10 semaines avant leur mois.

Sorties : config/keywords.yml (lu par le skill escapade-contenu) et keywords/calendrier.md.

Usage (venv de l'outil marketing-intelligence) :
    ../marketing-intelligence/.venv/Scripts/python.exe scripts/keyword_map.py
    … --serp 0                 découverte seule, sans aucun appel payant
    … --par-semaine 4 --semaines 10 --debut 2026-11-30
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import string
import sys
import time
import unicodedata
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import median

import yaml

REPO = Path(__file__).resolve().parents[1]
MI = REPO.parent / "marketing-intelligence"
os.environ.setdefault("MI_DB_PATH", str(MI / "data" / "ugc-cache.db"))
sys.path.insert(0, str(MI))
os.chdir(MI)  # les connecteurs lisent .env et data/ depuis la racine de l'outil

from dotenv import load_dotenv  # noqa: E402

load_dotenv(MI / ".env")

from analysis.serp_overlap import compute_overlap  # noqa: E402
from core import dataforseo as dfs  # noqa: E402
from core.google_suggest import fetch_suggestions  # noqa: E402

SEEDS_FILE = REPO / "config" / "keyword_seeds.yml"
OUT_YML = REPO / "config" / "keywords.yml"
OUT_MD = REPO / "keywords" / "calendrier.md"
CACHE = REPO / "keywords" / ".cache"
POSTS = REPO / "content" / "posts"

FIT = {"destinations": 1.0, "hors-des-sentiers-battus": 1.0, "voyager-malin": 0.9,
       "equipement-voyage": 0.75, "preparer-son-voyage": 0.7, "a-classer": 0.4}

RUBRIQUE_RULES = [
    ("equipement-voyage", r"\b(sac|valise|chaussures?|adaptateur|gourde|veste|tente|oreiller|trousse|cadenas|batterie|housse|sacoche|pochette|tenue|vetements?|liste)\b"),
    ("preparer-son-voyage", r"\b(assurance|vaccins?|passeport|visa|esta|eta|etias|permis|carte bancaire|formalites?|papiers|douane|ceam|carte d identite|sortie de territoire|paludisme|enceinte|bebe)\b"),
    ("hors-des-sentiers-battus", r"\b(meconnus?|meconnues?|insolites?|secrets?|peu touristiques?|hors des sentiers|sauvages?|preserves?|authentiques?|caches?)\b"),
    ("voyager-malin", r"\b(pas cher|pas chere|pas chers|budget|low cost|astuces?|billets?|vols?|interrail|bagages?|derniere minute|prix|cout|combien|economiser)\b"),
    ("destinations", r"\b(que faire|que voir|visiter|road ?trip|itineraire|voyage|week ?end|vacances|sejour|circuit|incontournables?|ou dormir|ou loger|quand partir|plages?|randonnees?|escapade|partir|destination|endroits?|villes?|iles?|pays)\b"),
]

UGC = re.compile(r"(reddit|tripadvisor|forum|quora|youtube|facebook|tiktok|instagram|pinterest)")
OFFICIAL = re.compile(r"(gouv|europa\.eu|ameli|service-public|diplomatie|\.gov|visit[a-z]+\.|tourisme|office-?de-?tourisme)")
MOIS = ["janvier", "fevrier", "mars", "avril", "mai", "juin", "juillet", "aout", "septembre", "octobre", "novembre", "decembre"]
MOIS_AFF = "janv. févr. mars avr. mai juin juil. août sept. oct. nov. déc.".split()
SAISONS = {"noel": [12], "hiver": [12, 1, 2], "ski": [1, 2], "printemps": [4, 5], "paques": [4], "ete": [7, 8],
           "automne": [10], "toussaint": [10], "nouvel an": [12], "saint valentin": [2], "pont": [5], "ascension": [5], "pentecote": [5]}
DEST_RE = re.compile(r"^(?:quand partir|quand visiter|voyage|road trip|visiter|partir)\s+(?:(?:en|au|aux|à|a|l'|le|la|les|à l'|a l')\s+)?(.+)$")
NOT_PLACE = set(MOIS) | {"pas", "cher", "chere", "famille", "amis", "ami", "pote", "potes", "soleil", "quel", "quelle", "ou", "tout",
             "compris", "seul", "seule", "hiver", "ete", "printemps", "automne", "vacances", "week", "end", "avion", "train",
             "bus", "organise", "groupe", "couple", "enfant", "enfants", "bebe", "chien", "derniere", "minute", "luxe",
             "moins", "plus", "quand", "comment", "pour", "avec", "sans", "agence", "voyage", "dans", "linguistique",
             "scolaire", "noces", "solo", "europe", "france", "monde", "etranger", "mer", "montagne", "chaud", "chaude",
             "fevrier", "aout", "decembre", "2026", "2027", "meilleur", "meilleure", "periode", "mois", "nouvel", "an"}
NOT_PLACE_PHRASES = {"usa", "asie", "afrique", "amerique"}
STOP = {"de", "du", "des", "le", "la", "les", "l", "d", "a", "en", "au", "aux", "un", "une", "et", "pour", "avec", "ou"}


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower().replace("'", " ").replace("’", " ")).encode("ascii", "ignore").decode()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


def dedupe_key(kw: str) -> str:
    words = [w[:-1] if len(w) > 3 and w.endswith(("s", "x")) else w for w in norm(kw).split() if not re.fullmatch(r"20\d\d", w)]
    return " ".join(sorted(w for w in words if w not in STOP))


def rubrique_of(kw: str) -> str:
    n = norm(kw)
    for rub, pattern in RUBRIQUE_RULES:
        if re.search(pattern, n):
            return rub
    return "a-classer"


def season_of(kw: str) -> list[int]:
    n = norm(kw)
    months = [i + 1 for i, m in enumerate(MOIS) if re.search(rf"\b{m}\b", n)]
    for word, ms in SAISONS.items():
        if re.search(rf"\b{word}\b", n):
            months += ms
    return sorted(set(months))


def suggest_cached(q: str) -> list[str]:
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / "suggest.json"
    data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    hit = data.get(q)
    if hit and hit["at"] > time.time() - 30 * 86400:
        return hit["s"]
    errs: list[str] = []
    s = fetch_suggestions(q, language_code="fr", country_code="FR", keep_query=True, errors=errs)
    if errs:  # une erreur 500 isolée arrive : un seul nouvel essai
        time.sleep(2)
        errs = []
        s = fetch_suggestions(q, language_code="fr", country_code="FR", keep_query=True, errors=errs)
    if errs:
        print("Suggest refusé :", q, errs[0])
        return []
    data[q] = {"at": time.time(), "s": s}
    f.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    time.sleep(0.15)
    return s


TRANCO_URL = "https://tranco-list.eu/top-1m.csv.zip"


def load_tranco() -> dict[str, int]:
    """Classement Tranco (1 million de domaines les plus visités, gratuit), retéléchargé chaque mois.
    Repères : pinterest.com 54e, routard.com ~31 000e, generationvoyage.fr ~105 000e ; un blog de voyage
    modeste est au-delà de 300 000 ou absent."""
    import io
    import zipfile

    import requests

    f = CACHE / "tranco" / "top-1m.csv"
    if not f.exists() or f.stat().st_mtime < time.time() - 30 * 86400:
        f.parent.mkdir(parents=True, exist_ok=True)
        data = requests.get(TRANCO_URL, timeout=120).content
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            f.write_bytes(z.read("top-1m.csv"))
    out = {}
    for line in f.read_text(encoding="utf-8").splitlines():
        rank, _, dom = line.partition(",")
        out[dom.strip()] = int(rank)
    return out


def tranco_rank(tranco: dict[str, int], domain: str) -> int | None:
    parts = domain.lower().split(".")
    for i in range(len(parts) - 1):
        r = tranco.get(".".join(parts[i:]))
        if r:
            return r
    return None


def weakness_of(rank: int | None) -> float:
    """1 = concurrent faible (battable par un site neuf), 0 = très fort."""
    if rank is None or rank > 500_000:
        return 1.0
    if rank > 150_000:
        return 0.8
    if rank > 50_000:
        return 0.5
    if rank > 10_000:
        return 0.25
    return 0.0


GENERIC = {"ou", "pas", "partir", "aller", "voyage", "voyager", "vacance", "destination", "escapade", "quand", "soleil", "pa",
           "cher", "chere", "quel", "quelle", "pay", "chaud", "chaleur", "famille", "ami", "week", "end", "sejour", "mois",
           "visiter", "debut", "fin", "europe", "monde", "avoir", "pour", "il", "fait", "petit", "budget", "tout", "compri"}


def month_signature(keyword: str) -> frozenset[int] | None:
    """Mois visés par une requête « où partir en <mois> » et ses variantes (soleil, pas cher, en famille…).
    Deux requêtes de ce type qui partagent un mois = un seul article (« Où partir en avril »)."""
    months = season_of(keyword)
    rest = set(dedupe_key(keyword).split()) - {m for m in MOIS} - {m[:-1] for m in MOIS} - {"aout", "fevrier", "decembre"}
    if months and rest <= GENERIC:
        return frozenset(months)
    return None


def topic_signature(keyword: str) -> frozenset[str] | None:
    """Sujet d'une requête sans les mots d'habillage : « voyage entre potes où aller » et « voyage entre amis
    destination » donnent tous deux {entre, ami} ; on garde famille et amis, qui changent le lecteur visé."""
    toks = {{"pote": "ami", "copain": "ami"}.get(t, t) for t in dedupe_key(keyword).split()}
    sig = toks - (GENERIC - {"famille", "ami", "monde"})
    return frozenset(sig) if sig and not season_of(keyword) else None


def template(keyword: str) -> str:
    """Gabarit d'une requête : « quand partir », « road trip », « voyage en »… (deux premiers mots normalisés)."""
    words = [{"visiter": "partir", "ou": "quand"}.get(w, w) for w in norm(keyword).split()]
    return " ".join(words[:2])


def existing_posts() -> dict[str, tuple[str, str, object]]:
    out = {}
    for p in POSTS.glob("*.md"):
        fm = yaml.safe_load(p.read_text(encoding="utf-8").split("---")[1])
        for k in [fm.get("keyword"), fm.get("title")] + list(fm.get("keywords_secondaires") or []):
            if k:
                out[dedupe_key(k)] = (fm["slug"], fm.get("status"), fm.get("date"))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--serp", type=int, help="nombre maximal de SERP (défaut : serp_max du fichier de graines)")
    ap.add_argument("--par-semaine", type=int, default=3)
    ap.add_argument("--semaines", type=int, default=12)
    ap.add_argument("--debut", help="premier lundi du calendrier (défaut : lundi suivant le dernier article programmé)")
    args = ap.parse_args()

    cfg = yaml.safe_load(SEEDS_FILE.read_text(encoding="utf-8"))
    excl = [norm(w) for w in cfg.get("exclure_mots") or []]
    serp_max = cfg.get("serp_max", 80) if args.serp is None else args.serp

    # 1. Découverte par les suggestions
    cand: dict[str, dict] = {}

    def harvest(prefix: str, w: float, seed: str) -> None:
        for rank, s in enumerate(suggest_cached(prefix)):
            n = norm(s)
            if len(n.split()) < 2 or any(re.search(r"\b" + re.escape(e) + r"\b", n) for e in excl):
                continue
            k = dedupe_key(s)
            c = cand.setdefault(k, {"keyword": s, "demande": 0.0, "vues": 0, "graines": set()})
            c["demande"] += w * (10 - min(rank, 9)) / 10
            c["vues"] += 1
            c["graines"].add(seed)
            if len(s) < len(c["keyword"]):
                c["keyword"] = s

    for seed in cfg["graines"]:
        prefixes = [(seed, 2.0)] + [(f"{seed} {d}", 1.0) for d in cfg.get("declinaisons") or []] \
            + [(f"{seed} {c}", 0.7) for c in string.ascii_lowercase]
        for prefix, w in prefixes:
            harvest(prefix, w, seed)

    # Second niveau : destinations repérées, déclinées en sujets de guide
    dest_score: Counter = Counter()
    dest_form: dict[str, str] = {}
    for c in cand.values():
        m = DEST_RE.match(c["keyword"].lower())
        if not m:
            continue
        d = m.group(1).strip()
        nd = norm(d)
        if not nd or len(nd.split()) > 3 or set(nd.split()) & NOT_PLACE or nd in NOT_PLACE_PHRASES:
            continue
        dest_score[nd] += c["demande"]
        dest_form.setdefault(nd, d)
    destinations = [dest_form[d] for d, _ in dest_score.most_common(cfg.get("destinations_max", 40))]
    print("Destinations déclinées :", ", ".join(destinations))
    for d in destinations:
        for tpl in cfg.get("declinaisons_destination") or []:
            harvest(tpl.format(d=d), 1.0, f"destination:{d}")

    for c in cand.values():
        c["rubrique"] = rubrique_of(c["keyword"])
        c["saison"] = season_of(c["keyword"])
        c["graines"] = sorted(c["graines"])
    print(f"{len(cand)} requêtes découvertes par les suggestions")

    # Volumes réels si la clé DataForSEO est disponible (sinon on garde l'indice de demande)
    try:
        dfs._auth()
        top = sorted(cand.values(), key=lambda c: -c["demande"])[:1000]
        for r in dfs.fetch_search_volume([c["keyword"] for c in top]):
            c = cand.get(dedupe_key(r.keyword))
            if c:
                c["volume"] = r.search_volume
    except Exception as exc:  # noqa: BLE001
        print("Volumes indisponibles, indice de demande Google Suggest utilisé :", str(exc)[:90])

    def demand(c):
        return math.log10((c.get("volume") or 0) + 10) * 2 if c.get("volume") is not None else c["demande"]

    ranked = sorted(cand.values(), key=lambda c: -demand(c) * FIT[c["rubrique"]])

    # Fenêtre du calendrier : un sujet saisonnier se publie 3 à 10 semaines avant son mois
    existing = existing_posts()
    planned = [hit[2] for hit in existing.values() if hit[2]]
    last = max((datetime.fromisoformat(str(d)).date() for d in planned), default=date.today())
    start = date.fromisoformat(args.debut) if args.debut else last + timedelta(days=7 - last.weekday())
    end = start + timedelta(weeks=args.semaines)

    def windows(c_or_a) -> list[tuple[date, date]]:
        out = []
        for m in c_or_a.get("saison") or []:
            for y in (start.year, start.year + 1):
                first = date(y, m, 1)
                lo, hi = first - timedelta(weeks=10), first - timedelta(weeks=3)
                if hi >= start - timedelta(days=7):
                    out.append((lo, hi))
                    break
        return out

    def schedulable(c) -> bool:
        return not c.get("saison") or any(lo <= end and hi >= start for lo, hi in windows(c))

    # 2. SERP des meilleures requêtes, en évitant de payer deux fois le même sujet
    synonyms = {"visiter": "partir", "aller": "partir", "vacance": "voyage", "sejour": "voyage", "ou": "", "quel": "", "quelle": ""}
    chosen, seen_keys = [], []
    for c in ranked:
        if len(chosen) >= serp_max:
            break
        if c["rubrique"] == "a-classer" or not schedulable(c):
            continue
        toks = {synonyms.get(t, t) for t in dedupe_key(c["keyword"]).split()} - {""}
        if any(len(toks & s) / max(1, min(len(toks), len(s))) >= 0.8 for s in seen_keys):
            continue
        seen_keys.append(toks)
        chosen.append(c)

    serps = {}
    for c in chosen:
        try:
            serps[c["keyword"]] = dfs.fetch_serp(c["keyword"], depth=10)
        except Exception as exc:  # noqa: BLE001
            print("SERP échouée :", c["keyword"], str(exc)[:120])
            break
    print(f"{len(serps)} SERP relevées")
    tranco = load_tranco()

    for c in chosen:
        r = serps.get(c["keyword"])
        if not r:
            continue
        top = r.organic_results[:10]
        ranks, weights, weakness, weak, official = [], [], [], 0, 0
        for o in top:
            d = o.domain.removeprefix("www.")
            rank = tranco_rank(tranco, d)
            ranks.append(rank or 2_000_000)
            w = 1.0 if UGC.search(o.url) else weakness_of(rank)
            weakness.append(w)
            weights.append(2.0 if o.position <= 5 else 1.0)
            weak += w >= 0.8
            if OFFICIAL.search(d) and o.position <= 5:
                official += 1
        share = sum(w * k for w, k in zip(weakness, weights)) / max(1, sum(weights))
        feas = (0.15 + 0.85 * share) * 0.85 ** official * (0.9 if r.ai_overview_present else 1)
        c.update(faisabilite=round(feas, 2), tranco_median=int(median(ranks)) if ranks else None, faibles=weak,
                 officiels=official, aio=r.ai_overview_present, urls=[o.url for o in top],
                 top3=[o.domain.removeprefix("www.") for o in top[:3]], paa=list(r.people_also_ask),
                 associees=list(r.related_searches))

    # 3. Articles : regroupement par recouvrement de SERP, puis requêtes proches sans SERP rattachées
    with_serp = [c for c in chosen if c.get("urls")]
    clusters: list[list[dict]] = []
    for c in with_serp:
        sig = month_signature(c["keyword"])
        for cl in clusters:
            head_sig = month_signature(cl[0]["keyword"])
            same_topic = topic_signature(c["keyword"]) is not None and topic_signature(c["keyword"]) == topic_signature(cl[0]["keyword"])
            if compute_overlap(cl[0]["urls"], c["urls"]) >= 0.4 or (sig and head_sig and sig & head_sig) or same_topic:
                cl.append(c)
                break
        else:
            clusters.append([c])
    heads = [(set(dedupe_key(cl[0]["keyword"]).split()), cl) for cl in clusters]
    satellites = defaultdict(list)
    for c in ranked:
        if c.get("urls") or c["rubrique"] == "a-classer":
            continue
        toks = set(dedupe_key(c["keyword"]).split())
        best = max(heads, key=lambda h: len(toks & h[0]) / max(1, len(h[0])), default=None)
        if best and len(toks & best[0]) / max(1, len(best[0])) >= 0.99:
            satellites[id(best[1])].append(c["keyword"])

    articles = []
    for cl in clusters:
        head = cl[0]
        dem = sum(demand(c) for c in cl)
        feas = sum(c["faisabilite"] for c in cl) / len(cl)
        rub = Counter(c["rubrique"] for c in cl).most_common(1)[0][0]
        paa = list(dict.fromkeys(q for c in cl for q in c["paa"]))
        statut, slug = "idee", None
        for c in cl:
            hit = existing.get(dedupe_key(c["keyword"]))
            if hit:
                slug, statut = hit[0], "publie" if hit[1] == "publish" else "programme"
        articles.append({
            "requete": head["keyword"], "rubrique": rub, "score": round(dem * feas * FIT[rub], 2),
            "demande": round(dem, 1), "volume": head.get("volume"), "faisabilite": round(feas, 2),
            "saison": sorted({m for c in cl for m in c["saison"]}),
            "tranco_median_top10": head.get("tranco_median"), "resultats_faibles_top10": head.get("faibles"),
            "officiels_top5": head.get("officiels"), "ai_overview": head.get("aio"), "top3": head.get("top3"),
            "secondaires": [c["keyword"] for c in cl[1:]] + satellites[id(cl)][:10],
            "questions": paa[:8], "associees": head.get("associees", [])[:8], "statut": statut, "slug": slug,
        })
    articles.sort(key=lambda a: -a["score"])

    # PAA qui ouvrent un sujet absent de la carte : idées pour les prochaines cartes
    known = {dedupe_key(a["requete"]) for a in articles} | {dedupe_key(s) for a in articles for s in a["secondaires"]}
    idees_paa = sorted({q for a in articles for q in a["questions"] if dedupe_key(q) not in known})

    # 4. Calendrier : N articles par semaine ; un sujet saisonnier n'entre que dans sa fenêtre (3 à 10 semaines
    # avant son mois) ; on alterne les rubriques secondaires et les gabarits (« quand partir… » deux fois de suite non).
    days = [0, 2, 4, 5][: args.par_semaine] if args.par_semaine <= 4 else list(range(args.par_semaine))
    slots = [start + timedelta(weeks=w, days=d) for w in range(args.semaines) for d in days]
    todo = [a for a in articles if a["statut"] == "idee"]
    calendar, used = [], set()
    rub_count = Counter()
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
            if a["rubrique"] not in ("destinations", "hors-des-sentiers-battus"):
                p -= 0.4 * rub_count[a["rubrique"]]
            if template(a["requete"]) in recent:  # un même gabarit au plus une fois par semaine
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
    header = (f"# Carte des mots-clés d'escapade-et-voyage.fr, générée par scripts/keyword_map.py le {today}.\n"
              "# Ne pas éditer à la main : relancer le script (statut et slug viennent du champ `keyword` des articles).\n")
    data = {"genere_le": today, "methode": "suggestions Google + PAA ; demande = indice Suggest" +
            ("" if any(a.get("volume") for a in articles) else " (pas de volume réel)"),
            "calendrier": [{"date": a["date_prevue"], "requete": a["requete"], "rubrique": a["rubrique"]} for a in calendar],
            "articles": articles, "idees_paa": idees_paa[:150],
            "reserve": [{"requete": c["keyword"], "demande": round(c["demande"], 1), "rubrique": c["rubrique"]}
                        for c in ranked if not c.get("urls")][:400]}
    OUT_YML.write_text(header + yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=140), encoding="utf-8")

    jours = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]
    L = [f"# Calendrier éditorial — généré le {today}", "",
         f"{len(cand)} requêtes découvertes, {len(serps)} SERP relevées, {len(articles)} articles possibles, "
         f"{len(calendar)} placés ({args.par_semaine} par semaine).", "",
         "Demande = indice Google Suggest (une requête suggérée tôt et sur plusieurs déclinaisons est très tapée). "
         "Faisabilité = part du top 10 (top 5 compté double) tenue par des sites faibles (hors des 150 000 premiers domaines Tranco), des forums ou des plateformes, avec un malus pour les "
         "sites officiels en top 5 et l'AI Overview. Score = demande × faisabilité × adéquation à la ligne éditoriale.", "",
         "## Calendrier", "", "| Date | Requête principale | Rubrique | Score | Faisab. | Saison | Questions à couvrir |",
         "|---|---|---|---|---|---|---|"]
    for a in calendar:
        d = date.fromisoformat(a["date_prevue"])
        s = ", ".join(MOIS_AFF[m - 1] for m in a["saison"]) or "toute l'année"
        L.append(f"| {jours[d.weekday()]} {d.strftime('%d/%m')} | {a['requete']} | {a['rubrique']} | {a['score']} | "
                 f"{a['faisabilite']} | {s} | {' · '.join(a['questions'][:3])} |")
    L += ["", "## Tous les articles possibles", "", "| Requête | Rubrique | Score | Faisab. | Top 3 | Statut |", "|---|---|---|---|---|---|"]
    for a in articles:
        L.append(f"| {a['requete']} | {a['rubrique']} | {a['score']} | {a['faisabilite']} | {', '.join(a['top3'] or [])} | "
                 f"{a['statut']}{' (' + a['slug'] + ')' if a['slug'] else ''} |")
    L += ["", "## Questions « Autres questions » qui ouvrent d'autres sujets", ""] + [f"- {q}" for q in idees_paa[:60]]
    OUT_MD.parent.mkdir(exist_ok=True)
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Écrit : config/keywords.yml, keywords/calendrier.md ({len(calendar)} dates)")


if __name__ == "__main__":
    main()

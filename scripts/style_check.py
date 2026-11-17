"""Contrôle de style : repère les tics d'écriture typiques des textes générés par IA.

Usage :
  python scripts/style_check.py content/posts/mon-article.md [autre.md …]
  python scripts/style_check.py --all            # tous les contenus réécrits ou nouveaux
  python scripts/style_check.py --strict …       # code de sortie 1 s'il reste des alertes bloquantes

Bloquant : tirets cadratins / demi-cadratins utilisés comme ponctuation, formules interdites,
emojis, typographie française (espace avant : ; ! ?), introduction et conclusion types.
Signalé : voix passive, phrases trop longues, gras excessif, énumérations en trois, vocabulaire IA fréquent,
transitions mécaniques, intertitres sur un seul moule,
questions rhétoriques en série, adverbes en -ment en excès.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import CONTENT, read_doc  # noqa: E402

# Formules creuses ou typiques des textes générés (minuscules, sans accent final requis).
BANNED = [
    "dans un monde où", "il est important de noter", "il convient de noter", "il est essentiel de",
    "il est crucial de", "en conclusion", "en résumé,", "pour conclure", "plongeons", "plongeon au cœur",
    "n'hésitez pas à", "véritable allié", "véritable atout", "incontournable", "à l'ère de",
    "dans cet article, nous allons", "dans cet article nous", "que vous soyez", "force est de constater",
    "il va sans dire", "au cœur de", "un monde de", "révolutionner", "booster", "game changer",
    "sans plus attendre", "vous l'aurez compris", "en somme", "le saviez-vous", "tout d'abord,",
    "décortiquer", "arsenal", "naviguer dans", "levier incontournable", "pierre angulaire",
    "boîte à outils", "en définitive", "nul doute que", "il est indéniable",
    # Ajouts du 17/11/2026 (grille algoproof, .claude/skills/*/algoproof.md § 3)
    "en constante évolution", "paysage numérique", "il est primordial de", "tout ce qu'il faut savoir",
    "tout ce que vous devez savoir", "guide complet", "guide ultime", "découvrons", "laissez-vous séduire",
    "laissez-vous tenter", "embarquez pour", "joyau", "écrin de", "trésor caché", "trésors cachés",
    "à couper le souffle", "vue imprenable", "véritable paradis", "havre de paix", "expérience inoubliable",
    "niché au cœur", "nichée au cœur", "niché entre", "nichée entre", "mélange unique", "riche patrimoine",
    "riche histoire", "à ne pas manquer", "un must", "faire du sens", "adresser un problème", "au final,",
    "dans cet article, découvrez", "dans ce guide, nous",
]
# Vocabulaire passe-partout des textes générés : acceptable à petite dose, signalé au-delà de 4 pour 1 000 mots.
SUSPECT = [
    "offre ", "offrent ", "permet de", "permettent de", "souligne", "témoigne", "favoriser", "garantir",
    "explorer", "découvrir", "expérience", "univers", "richesse", "authentique", "idéal pour", "parfait pour",
    "crucial", "essentiel", "optimal", "fascinant", "captivant", "inoubliable", "époustouflant", "sublime",
    "véritable", "dynamique", "harmonie", "en termes de", "dans le cadre de", "de manière significative",
]
INTRO_CLICHE = re.compile(r"^(vous rêvez|imaginez|envie de|bienvenue|vous êtes-vous déjà|qui n'a jamais|"
                          r"vous souhaitez|vous cherchez|que ce soit)", re.I)
TRANSITIONS = ("de plus", "en outre", "par ailleurs", "ainsi", "enfin", "en effet", "cependant", "néanmoins")
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐✅❌]")
DASH = re.compile(r"\s[—–]\s|[—]")  # tiret cadratin partout, demi-cadratin entouré d'espaces
PASSIVE = re.compile(
    r"\b(est|sont|était|étaient|sera|seront|serait|seraient|soit|soient|été|être)\s+"
    r"(?:\w+ment\s+)?(\w+(?:é|ée|és|ées|i|ie|ies|is|ise|ises|it|ite|its|ites|u|ue|us|ues|ert|erte|erts|ertes|int|inte|ints|intes))\b",
    re.I,
)
NOT_PARTICIPLE = {"souvent", "peu", "déjà", "pu", "su", "vu", "eu", "dû", "parti", "partis", "venu", "venue", "arrivé", "arrivée", "passé", "passée", "passés", "passées", "devenu", "devenue", "resté", "restée", "tout", "bout", "haut", "petit", "fort", "court", "doux", "faut", "plus", "nous", "vous", "tous", "dessus", "ici", "aussi", "ainsi", "parti"}
SPACE_BEFORE = re.compile(r"[^\s\d(\[`/:]([;!?])(?=\s|$)")
LIST3 = re.compile(r"\b(\w+), (\w+) et (\w+)\b")
ADVERB = re.compile(r"\b\w{4,}ment\b", re.I)


def strip_markdown(body: str) -> str:
    body = re.sub(r"```.*?```", "", body, flags=re.S)
    body = re.sub(r"`[^`]*`", "", body)
    body = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", body)
    body = re.sub(r"\]\([^)]*\)", "]", body)
    body = re.sub(r"<[^>]+>", "", body)
    body = re.sub(r"https?://\S+", "", body)
    return body


def sentences(text: str) -> list[str]:
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "|")) or line.endswith(":"):
            continue  # titres, tableaux, amorces de liste
        line = re.sub(r"^([-*>]|\d+\.)\s*", "", line)
        line = line.replace("**", "")
        out += [s.strip() for s in re.split(r"(?<=[.!?])\s+", line) if len(s.split()) > 2]
    return out


def check(path: Path) -> tuple[list[str], list[str]]:
    doc = read_doc(path)
    raw = doc.body
    text = strip_markdown(raw)
    meta_text = " ".join(str(doc.meta.get(k, "")) for k in ("title", "dek", "meta_description", "seo_title"))
    meta_text += " " + " ".join(str(x) for x in doc.meta.get("essentiel", []) or [])
    full = text + "\n" + meta_text
    low = full.lower()
    block, notes = [], []

    for m in DASH.finditer(full):
        ctx = full[max(0, m.start() - 30): m.end() + 30].replace("\n", " ")
        block.append(f"tiret long : « …{ctx.strip()}… » → virgule, deux-points, parenthèses ou nouvelle phrase")
    for b in BANNED:
        if b in low:
            block.append(f"formule à proscrire : « {b} »")
    if EMOJI.search(full):
        block.append("emoji dans le texte")
    for m in SPACE_BEFORE.finditer(full):
        ctx = full[max(0, m.start() - 20): m.end() + 5].replace("\n", " ")
        block.append(f"typographie : espace manquante avant « {m.group(1)} » dans « {ctx.strip()} »")

    paras = [l.strip() for l in re.split(r"\n\s*\n", raw) if l.strip() and not l.strip().startswith(("#", "|", "-", "*", "<", "!", "[", ">"))
             and not re.match(r"^\d+\.", l.strip())]
    if paras and INTRO_CLICHE.match(strip_markdown(paras[0])):
        block.append(f"introduction type IA : « {strip_markdown(paras[0])[:60]}… » → commencer par la réponse")
    for h in re.findall(r"^#{2,3}\s+(.+)$", raw, flags=re.M):
        if h.strip().lower().rstrip(" :") in ("introduction", "conclusion", "en conclusion", "pour conclure", "le mot de la fin"):
            block.append(f"intertitre « {h.strip()} » : finir sur une action concrète ou la FAQ")
    words_n = max(1, len(text.split()))
    sus = {w.strip(): low.count(w) for w in SUSPECT if low.count(w)}
    if sum(sus.values()) / words_n * 1000 > 4:
        top = ", ".join(f"{w} ×{n}" for w, n in sorted(sus.items(), key=lambda x: -x[1])[:8])
        notes.append(f"vocabulaire IA fréquent ({sum(sus.values())} pour {words_n} mots) : {top}")
    starts = [strip_markdown(pp).lower() for pp in paras]
    trans = sum(1 for pp in starts if pp.startswith(TRANSITIONS))
    if len(starts) >= 6 and trans / len(starts) > 0.25:
        notes.append(f"transitions mécaniques en tête de paragraphe ({trans} sur {len(starts)}) : de plus, en outre, ainsi…")
    h2 = re.findall(r"^##\s+(.+)$", raw, flags=re.M)
    if len(h2) >= 4 and sum(1 for h in h2 if " : " in h) / len(h2) > 0.75:
        notes.append("intertitres tous sur le même moule « X : Y » : varier")

    passives = [m.group(0) for m in PASSIVE.finditer(" ".join(sentences(text))) if m.group(2).lower() not in NOT_PARTICIPLE]
    sents = sentences(text)
    if sents and len(passives) / len(sents) > 0.12:
        notes.append(f"voix passive fréquente ({len(passives)} pour {len(sents)} phrases) : {', '.join(passives[:6])}…")
    longs = [s for s in sents if len(s.split()) > 32]
    for s in longs[:5]:
        notes.append(f"phrase longue ({len(s.split())} mots) : « {s[:90]}… »")
    # Le gras en tête d'élément de liste sert de repère : seul le gras du texte courant est compté.
    prose = "\n".join(l for l in raw.splitlines() if not re.match(r"^\s*([-*]|\d+\.)\s", l))
    bold = len(re.findall(r"\*\*[^*]+\*\*", prose))
    words = max(1, len(text.split()))
    if bold / words * 1000 > 12:
        notes.append(f"gras excessif ({bold} passages en gras pour {words} mots)")
    trios = LIST3.findall(text)
    if len(trios) > max(3, words // 400):
        notes.append(f"énumérations en trois très fréquentes ({len(trios)}) : varier le rythme")
    q = re.findall(r"\?\s+[A-ZÀ-Ý][^?.!]{3,80}\?", text)
    if len(q) >= 2:
        notes.append("questions rhétoriques enchaînées")
    adv = ADVERB.findall(text)
    if len(adv) / words * 1000 > 15:
        notes.append(f"beaucoup d'adverbes en -ment ({len(adv)})")
    if sents:
        lens = [len(s.split()) for s in sents]
        mean = sum(lens) / len(lens)
        var = sum((x - mean) ** 2 for x in lens) / len(lens)
        if var ** 0.5 < 5 and len(lens) > 15:
            notes.append(f"phrases de longueur trop uniforme (moyenne {mean:.0f} mots) : alterner courtes et longues")
    if re.search(r"\btu\b|\bton\b|\bta\b|\btes\b", text) and re.search(r"\bvous\b|\bvotre\b", text):
        notes.append("mélange tutoiement / vouvoiement")
    return block, notes


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    files = [Path(f) for f in a.files]
    if a.all:
        files = [p for p in sorted(CONTENT.glob("*/*.md")) if read_doc(p).meta.get("origin") != "import"]
    total_block = 0
    for f in files:
        block, notes = check(f)
        total_block += len(block)
        if not block and not notes:
            print(f"✓ {f.name}")
            continue
        print(f"\n{f.name}")
        for b in block:
            print(f"  ✗ {b}")
        for n in notes:
            print(f"  · {n}")
    print(f"\n{len(files)} fichier(s), {total_block} alerte(s) bloquante(s)")
    if a.strict and total_block:
        sys.exit(1)


if __name__ == "__main__":
    main()

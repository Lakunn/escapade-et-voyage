"""Construit la base du calculateur de budget : theme/escapade/assets/budget-data.json.

Sources combinées :
1. config/budget.yml : modèle de dépenses, coefficients, destinations et saisons ;
2. Banque mondiale : niveau des prix = parité de pouvoir d'achat (PA.NUS.PPP) / taux de change
   officiel (PA.NUS.FCRF), dernière année disponible par pays ;
3. nos articles : un article qui déclare `budget: {pays: TH, petit: 35, moyen: 70, gros: 180}`
   (euros par adulte et par jour, relevés sur place) remplace l'estimation pour ce pays.

Lancé par .github/workflows/budget.yml (chaque mois et à chaque modification), qui a accès à Internet.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import all_docs, doc_path  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "theme" / "escapade" / "assets" / "budget-data.json"
WB = "https://api.worldbank.org/v2/country/all/indicator/{code}?format=json&per_page=20000&date=2018:2026"
# Niveau des prix = facteur de conversion PPA (PA.NUS.PPP, unités locales par dollar international)
#                   / taux de change officiel (PA.NUS.FCRF, unités locales par dollar US).


def _series(code: str) -> dict:
    r = requests.get(WB.format(code=code), timeout=60, headers={"User-Agent": "escapade-et-voyage/1.0"})
    r.raise_for_status()
    payload = r.json()
    if not isinstance(payload, list) or len(payload) < 2 or not payload[1]:
        sys.exit(f"Réponse inattendue de la Banque mondiale pour {code} : {str(payload)[:300]}")
    out: dict = {}
    for row in payload[1]:
        iso2 = (row.get("country") or {}).get("id")
        if iso2 and len(iso2) == 2 and row.get("value") is not None:
            out.setdefault(iso2, {})[int(row["date"])] = float(row["value"])
    return out


def fetch_price_levels() -> dict:
    ppp, fx = _series("PA.NUS.PPP"), _series("PA.NUS.FCRF")
    out = {}
    for iso2, years in ppp.items():
        common = sorted(set(years) & set(fx.get(iso2, {})))
        if common and fx[iso2][common[-1]]:
            y = common[-1]  # dernière année où les deux séries sont renseignées
            out[iso2] = {"pli": round(years[y] / fx[iso2][y], 4), "annee": y}
    return out


def main() -> None:
    cfg = yaml.safe_load((ROOT / "config" / "budget.yml").read_text(encoding="utf-8"))
    levels = fetch_price_levels()
    if "FR" not in levels:
        sys.exit("Niveau des prix de la France introuvable : base non mise à jour.")
    fr = levels["FR"]["pli"]

    articles = {}
    for d in all_docs():
        b = d.meta.get("budget")
        if d.kind != "post" or not isinstance(b, dict) or not b.get("pays"):
            continue
        if d.meta.get("status", "publish") != "publish":
            continue
        articles[str(b["pays"]).upper()] = {
            "petit": b.get("petit"), "moyen": b.get("moyen"), "gros": b.get("gros"),
            "titre": d.meta.get("title"), "url": doc_path(d), "date": str(d.meta.get("date", ""))[:10],
        }

    destinations, absents = [], []
    for dest in cfg["destinations"]:
        iso = str(dest["pays"]).upper()
        lv = levels.get(iso)
        if not lv:
            absents.append(dest["nom"])
            continue
        item = {
            "nom": dest["nom"], "pays": iso, "haute": dest.get("haute", []), "basse": dest.get("basse", []),
            "ratio": round(lv["pli"] / fr, 4), "annee": lv["annee"],
        }
        if iso in articles:
            item["article"] = articles[iso]
        destinations.append(item)

    data = {
        "maj": date.today().isoformat(),
        "source": "Banque mondiale, PA.NUS.PPP / PA.NUS.FCRF (niveau des prix)",
        "annee_france": levels["FR"]["annee"],
        "modele": cfg["modele"], "elasticite": cfg["elasticite"], "coefficients": cfg["coefficients"],
        "destinations": sorted(destinations, key=lambda x: x["nom"]),
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(destinations)} destinations écrites dans {OUT.relative_to(ROOT)}")
    if absents:
        print("Sans donnée de prix (ignorées) : " + ", ".join(absents))


if __name__ == "__main__":
    main()

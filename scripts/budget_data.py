"""Construit la base du calculateur de budget : theme/escapade/assets/budget-data.json.

Sources combinées :
1. config/budget.yml : modèle de dépenses, coefficients, destinations et saisons ;
2. Banque mondiale, indicateur PA.NUS.PPPC.RF (niveau des prix : rapport entre parité de pouvoir
   d'achat et taux de change), dernière valeur disponible par pays ;
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
WB = "https://api.worldbank.org/v2/country/all/indicator/PA.NUS.PPPC.RF?format=json&per_page=20000&mrnev=1"


def fetch_price_levels() -> dict:
    r = requests.get(WB, timeout=60, headers={"User-Agent": "escapade-et-voyage/1.0"})
    r.raise_for_status()
    rows = r.json()[1] or []
    out = {}
    for row in rows:
        iso2 = (row.get("country") or {}).get("id")
        if iso2 and row.get("value") is not None and len(iso2) == 2:
            out[iso2] = {"pli": round(float(row["value"]), 4), "annee": int(row["date"])}
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
        "source": "Banque mondiale, PA.NUS.PPPC.RF (niveau des prix, PIB)",
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

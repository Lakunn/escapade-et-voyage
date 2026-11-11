"""Outils partagés : config, client REST WordPress, lecture des fichiers Markdown."""
from __future__ import annotations

import base64
import hashlib
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
CONFIG_FILE = ROOT / "config" / "site.yml"
URLS_FILE = ROOT / "urls.csv"
UA = "vr-media-pipeline/1.0 (+https://github.com/Lakunn/valentinrouault-media)"


def load_config() -> dict:
    return yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))


def site_url() -> str:
    return (os.environ.get("WP_URL") or load_config()["site_url"]).rstrip("/")


def norm_url(url: str) -> str:
    """Normalise une URL pour comparaison : schéma+hôte en minuscules, sans query ni fragment."""
    p = urlsplit(url.strip())
    path = p.path or "/"
    return f"{p.scheme.lower()}://{p.netloc.lower()}{path}"


def die(msg: str) -> None:
    print(f"::error::{msg}" if os.environ.get("GITHUB_ACTIONS") else f"ERREUR : {msg}", file=sys.stderr)
    sys.exit(1)


def warn(msg: str) -> None:
    print(f"::warning::{msg}" if os.environ.get("GITHUB_ACTIONS") else f"ATTENTION : {msg}")


# --------------------------------------------------------------------------- #
# Fichiers de contenu
# --------------------------------------------------------------------------- #
FRONT = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.S)


@dataclass
class Doc:
    path: Path
    meta: dict
    body: str
    kind: str = field(init=False)  # "post" | "page"

    def __post_init__(self) -> None:
        self.kind = "page" if self.path.parent.name == "pages" else "post"

    @property
    def slug(self) -> str:
        return str(self.meta["slug"]).strip("/")

    def source_hash(self, extra: str = "") -> str:
        raw = yaml.safe_dump(self.meta, sort_keys=True, allow_unicode=True) + self.body + extra
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def read_doc(path: Path) -> Doc:
    text = path.read_text(encoding="utf-8")
    m = FRONT.match(text)
    if not m:
        die(f"{path} : en-tête YAML (front matter) manquant")
    meta = yaml.safe_load(m.group(1)) or {}
    return Doc(path=path, meta=meta, body=m.group(2).strip() + "\n")


def write_doc(path: Path, meta: dict, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    head = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, width=1000).strip()
    path.write_text(f"---\n{head}\n---\n\n{body.strip()}\n", encoding="utf-8")


def all_docs() -> list[Doc]:
    docs = [read_doc(p) for p in sorted(CONTENT.glob("posts/*.md"))]
    docs += [read_doc(p) for p in sorted(CONTENT.glob("pages/*.md"))]
    return docs


# --------------------------------------------------------------------------- #
# Client REST
# --------------------------------------------------------------------------- #
class WP:
    def __init__(self, auth: bool = True) -> None:
        self.base = site_url() + "/wp-json/wp/v2"
        self.s = requests.Session()
        self.s.headers["User-Agent"] = UA
        if auth:
            user, pwd = os.environ.get("WP_USER"), os.environ.get("WP_APP_PASSWORD")
            if not user or not pwd:
                die("WP_USER / WP_APP_PASSWORD manquants (secrets GitHub)")
            token = base64.b64encode(f"{user}:{pwd}".encode()).decode()
            self.s.headers["Authorization"] = f"Basic {token}"

    def _req(self, method: str, path: str, **kw):
        url = path if path.startswith("http") else f"{self.base}/{path.lstrip('/')}"
        for attempt in range(4):
            r = self.s.request(method, url, timeout=60, **kw)
            if r.status_code in (429, 502, 503, 504) and attempt < 3:
                time.sleep(2 ** attempt * 2)
                continue
            if r.status_code >= 400:
                die(f"{method} {url} → HTTP {r.status_code} : {r.text[:400]}")
            return r
        return r

    def get(self, path: str, **params):
        return self._req("GET", path, params=params).json()

    def get_all(self, path: str, **params) -> list[dict]:
        out, page = [], 1
        while True:
            r = self._req("GET", path, params={**params, "per_page": 100, "page": page})
            out += r.json()
            if page >= int(r.headers.get("X-WP-TotalPages", 1)):
                return out
            page += 1

    def post(self, path: str, data: dict):
        return self._req("POST", path, json=data).json()

    def upload(self, file: Path) -> dict:
        mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp", "avif": "image/avif", "svg": "image/svg+xml"}
        ext = file.suffix.lower().lstrip(".")
        return self._req(
            "POST",
            "media",
            data=file.read_bytes(),
            headers={"Content-Disposition": f'attachment; filename="{file.name}"', "Content-Type": mime.get(ext, "application/octet-stream")},
        ).json()


def doc_path(doc: "Doc", cfg: dict | None = None) -> str:
    """Chemin public attendu d'un contenu (/parent/slug/ ou /rubrique/sous-rubrique/slug/)."""
    cfg = cfg or load_config()
    if doc.kind == "page":
        parts = [doc.meta["parent"]] if doc.meta.get("parent") else []
    elif cfg.get("category_in_url") and doc.meta.get("categories"):
        cats = {c["slug"]: c for c in cfg.get("categories", [])}
        # WordPress retient la rubrique d'identifiant le plus bas : on prend la première déclarée dans le fichier.
        chain, cur = [], doc.meta["categories"][0]
        while cur:
            chain.insert(0, cur)
            cur = (cats.get(cur) or {}).get("parent")
        parts = chain
    else:
        parts = []
    return "/" + "/".join(parts + [doc.slug]) + "/"

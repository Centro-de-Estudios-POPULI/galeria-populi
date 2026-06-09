"""
Catálogo de la galería.

Fuente canónica de metadata para el manifest: un sidecar JSON por gráfica en
data/meta/<slug>.json. Lo escriben tanto el motor de charts nativos
(populi_chart vía demos/scripts) como make_card.py (imágenes envueltas).
Así build_manifest no depende del método de generación.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
META_DIR = ROOT / "data" / "meta"


def register(slug, title, category, source, *, subtitle="", date="",
             tags=None, project="", fmt="square"):
    """Registra/actualiza la metadata de galería de una gráfica."""
    META_DIR.mkdir(parents=True, exist_ok=True)
    rec = {
        "slug": slug,
        "title": title,
        "subtitle": subtitle,
        "category": category,
        "source": source,
        "date": date,
        "tags": tags or [],
        "project": project,
        "format": fmt,
    }
    (META_DIR / f"{slug}.json").write_text(
        json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    return rec

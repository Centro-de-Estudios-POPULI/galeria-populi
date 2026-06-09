"""
Orquestador del banco de datos.

Para cada metadata en data/charts/*.json:
  1. localiza su chart crudo (campo "chart", o <mismo-nombre>.png)
  2. genera la tarjeta branded 1080x1080 -> public/graficas + public/thumbs
Luego reconstruye src/manifest.json.

Es el único paso que corre el GitHub Action: centraliza el branding, de modo
que los 16 repos solo aportan chart crudo + metadata.
"""
from __future__ import annotations
import json
from pathlib import Path
import build_manifest
import make_card
from PIL import Image

ROOT = make_card.ROOT
META_DIR = ROOT / "data" / "charts"
RAW_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".svg")


def find_raw(meta_path: Path, meta: dict) -> Path | None:
    if meta.get("chart"):
        cand = (META_DIR / meta["chart"]).resolve()
        return cand if cand.exists() else None
    for ext in RAW_EXTS:
        cand = meta_path.with_suffix(ext)
        if cand.exists():
            return cand
    return None


def main():
    built, skipped = 0, 0
    for mp in sorted(META_DIR.glob("*.json")):
        meta = json.loads(mp.read_text(encoding="utf-8"))
        meta.setdefault("slug", make_card.slugify(meta.get("title", mp.stem)))
        raw = find_raw(mp, meta)
        if not raw:
            print(f"SKIP {mp.name}: no encuentro chart crudo")
            skipped += 1
            continue
        card = make_card.build_card(raw, meta)
        (ROOT / "public" / "graficas").mkdir(parents=True, exist_ok=True)
        (ROOT / "public" / "thumbs").mkdir(parents=True, exist_ok=True)
        card.save(ROOT / "public" / "graficas" / f"{meta['slug']}.png", "PNG", optimize=True)
        card.resize((540, 540), Image.LANCZOS).save(
            ROOT / "public" / "thumbs" / f"{meta['slug']}.png", "PNG", optimize=True)
        print(f"OK   {meta['slug']}.png")
        built += 1
    print(f"\nTarjetas: {built} generadas, {skipped} omitidas")
    build_manifest.main()


if __name__ == "__main__":
    main()

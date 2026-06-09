"""
Constructor del índice de la galería.

Lee la metadata canónica de data/meta/*.json y verifica que exista el PNG final
en public/graficas/. Produce src/manifest.json — fuente única del buscador y la
grilla de la galería Astro.
"""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
META_DIR = ROOT / "data" / "meta"
GRAF_DIR = ROOT / "public" / "graficas"
THUMB_DIR = ROOT / "public" / "thumbs"
OUT = ROOT / "src" / "manifest.json"


def main():
    items = []
    for mp in sorted(META_DIR.glob("*.json")):
        m = json.loads(mp.read_text(encoding="utf-8"))
        slug = m.get("slug") or mp.stem
        png = GRAF_DIR / f"{slug}.png"
        if not png.exists():
            print(f"SKIP {slug}: falta public/graficas/{slug}.png")
            continue
        thumb = THUMB_DIR / f"{slug}.png"
        items.append({
            "slug": slug,
            "title": m.get("title", slug),
            "subtitle": m.get("subtitle", ""),
            "category": m.get("category", "Datos"),
            "source": m.get("source", ""),
            "date": m.get("date", ""),
            "tags": m.get("tags", []),
            "project": m.get("project", ""),
            "format": m.get("format", "square"),
            "image": f"/graficas/{slug}.png",
            "thumb": f"/thumbs/{slug}.png" if thumb.exists() else f"/graficas/{slug}.png",
        })

    items.sort(key=lambda x: x["date"], reverse=True)
    categories = sorted({i["category"] for i in items})
    manifest = {"count": len(items), "categories": categories, "items": items}
    OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"manifest.json  ·  {len(items)} graficas  ·  {len(categories)} categorias")


if __name__ == "__main__":
    main()

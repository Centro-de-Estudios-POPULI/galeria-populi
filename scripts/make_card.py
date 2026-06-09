"""
Generador de tarjetas branded POPULI — 1080x1080 para redes sociales.

Toma un chart (PNG con fondo transparente o blanco) + metadata y produce:
  - public/graficas/<slug>.png   (1080x1080, alta calidad, marca de agua + fuente)
  - public/thumbs/<slug>.png      (miniatura 540x540 para la galería)

Uso:
  python scripts/make_card.py --chart data/charts/ipc.png --meta data/charts/ipc.json
  python scripts/make_card.py --chart c.png --title "..." --source "INE" --category Inflación

La metadata (archivo .json o flags) define título, subtítulo, fuente, fecha,
categoría y tags. El chart es agnóstico al motor: vale cualquier PNG exportado
de ECharts, Plotly, matplotlib, Datawrapper, etc.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
from PIL import Image, ImageDraw
import brand_kit as bk

SIZE = 1080
MARGIN = 72
ROOT = bk.ROOT
C = bk.C


def load_meta(args) -> dict:
    meta = {}
    if args.meta:
        meta = json.loads(Path(args.meta).read_text(encoding="utf-8"))
    # los flags pisan el archivo
    for k in ("title", "subtitle", "source", "category", "date", "slug"):
        v = getattr(args, k, None)
        if v:
            meta[k] = v
    if args.tags:
        meta["tags"] = [t.strip() for t in args.tags.split(",") if t.strip()]
    meta.setdefault("title", "Sin título")
    meta.setdefault("category", "Datos")
    meta.setdefault("source", "Centro de Estudios POPULI")
    meta.setdefault("tags", [])
    meta.setdefault("date", datetime.now(timezone.utc).strftime("%Y-%m"))
    meta.setdefault("slug", slugify(meta["title"]))
    return meta


def slugify(s: str) -> str:
    import re
    import unicodedata
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "grafica"


def fit_chart(chart_path: Path, box_w: int, box_h: int) -> Image.Image:
    """Carga el chart, lo aplana sobre blanco y lo escala para caber en la caja."""
    img = Image.open(chart_path).convert("RGBA")
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    img = Image.alpha_composite(bg, img)
    ratio = min(box_w / img.width, box_h / img.height)
    new = (max(1, int(img.width * ratio)), max(1, int(img.height * ratio)))
    return img.resize(new, Image.LANCZOS)


def build_card(chart_path: Path, meta: dict) -> Image.Image:
    canvas = Image.new("RGBA", (SIZE, SIZE), bk.hex2rgb(C["paper"]))
    draw = ImageDraw.Draw(canvas)
    inner_w = SIZE - 2 * MARGIN

    # --- barra superior de color de marca ---
    draw.rectangle([0, 0, SIZE, 12], fill=bk.hex2rgb(C["red"]))

    # --- cabecera: wordmark + chip de categoría ---
    head_y = MARGIN
    bk.draw_wordmark(draw, MARGIN, head_y, scale=0.85)
    f_tag = bk.font("sans", 18)
    draw.text((MARGIN + 2, head_y + 74), BRAND_TAGLINE, font=f_tag, fill=bk.hex2rgb(C["muted"]))

    chip = meta["category"].upper()
    f_chip = bk.font("monoBold", 20)
    cw = bk.text_w(draw, chip, f_chip)
    chip_x1 = SIZE - MARGIN
    draw.rounded_rectangle([chip_x1 - cw - 36, head_y + 8, chip_x1, head_y + 50],
                           radius=21, fill=bk.hex2rgb(C["red"]))
    draw.text((chip_x1 - cw - 18, head_y + 16), chip, font=f_chip, fill=bk.hex2rgb(C["cream"]))

    # --- título con subrayado de acento ---
    f_title = bk.font("sans", 56)
    title_lines = bk.wrap(draw, meta["title"], f_title, inner_w)
    title_y = head_y + 120
    after_title = bk.draw_underline_title(
        draw, MARGIN, title_y, title_lines, f_title,
        fill=bk.hex2rgb(C["ink"]), accent=bk.hex2rgb(C["red"]),
        max_w=inner_w, underline_h=10)

    # --- subtítulo opcional ---
    cy = after_title + 26
    if meta.get("subtitle"):
        f_sub = bk.font("sans", 28)
        for ln in bk.wrap(draw, meta["subtitle"], f_sub, inner_w):
            draw.text((MARGIN, cy), ln, font=f_sub, fill=bk.hex2rgb(C["inkSoft"]))
            cy += 40
        cy += 6

    # --- zona del chart ---
    footer_h = 130
    chart_top = cy + 8
    chart_box_h = SIZE - MARGIN - footer_h - chart_top
    chart = fit_chart(chart_path, inner_w, chart_box_h)
    chart_x = MARGIN + (inner_w - chart.width) // 2
    chart_y = chart_top + (chart_box_h - chart.height) // 2
    canvas.alpha_composite(chart, (chart_x, max(chart_top, chart_y)))

    # --- pie: divisor + fuente + sitio + fecha ---
    fy = SIZE - MARGIN - footer_h + 30
    draw.line([MARGIN, fy, SIZE - MARGIN, fy], fill=bk.hex2rgb(C["grid"]), width=2)
    f_src = bk.font("mono", 21)
    f_src_b = bk.font("monoBold", 21)
    draw.text((MARGIN, fy + 18), "FUENTE  ", font=f_src_b, fill=bk.hex2rgb(C["red"]))
    src_x = MARGIN + bk.text_w(draw, "FUENTE  ", f_src_b)
    src_lines = bk.wrap(draw, meta["source"], f_src, inner_w - (src_x - MARGIN))
    draw.text((src_x, fy + 18), src_lines[0], font=f_src, fill=bk.hex2rgb(C["inkSoft"]))
    if len(src_lines) > 1:
        draw.text((src_x, fy + 44), src_lines[1], font=f_src, fill=bk.hex2rgb(C["inkSoft"]))

    f_site = bk.font("monoBold", 22)
    site_txt = f"{BRAND['site']}  ·  {meta['date']}"
    draw.text((SIZE - MARGIN, fy + 74), site_txt, font=f_site,
              fill=bk.hex2rgb(C["blue"]), anchor="rs")

    # --- marca de agua ---
    canvas = bk.draw_watermark(canvas, opacity=14, scale=2.4)
    return canvas.convert("RGB")


BRAND = bk.BRAND
BRAND_TAGLINE = BRAND["tagline"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chart", required=True)
    ap.add_argument("--meta")
    ap.add_argument("--title")
    ap.add_argument("--subtitle")
    ap.add_argument("--source")
    ap.add_argument("--category")
    ap.add_argument("--date")
    ap.add_argument("--tags")
    ap.add_argument("--slug")
    ap.add_argument("--outdir", default=str(ROOT / "public"))
    args = ap.parse_args()

    meta = load_meta(args)
    card = build_card(Path(args.chart), meta)

    out = Path(args.outdir)
    (out / "graficas").mkdir(parents=True, exist_ok=True)
    (out / "thumbs").mkdir(parents=True, exist_ok=True)
    full = out / "graficas" / f"{meta['slug']}.png"
    thumb = out / "thumbs" / f"{meta['slug']}.png"
    card.save(full, "PNG", optimize=True)
    card.resize((540, 540), Image.LANCZOS).save(thumb, "PNG", optimize=True)
    print(f"OK  {full.name}  ({full.stat().st_size // 1024} KB)")
    print(f"OK  {thumb.name}")


if __name__ == "__main__":
    main()

"""
Kit de marca POPULI — utilidades compartidas para componer tarjetas branded.

Carga la paleta y tipografías desde brand.json, y expone helpers para dibujar
el wordmark "Populi", la marca de agua y el pie de fuente sobre un lienzo Pillow.
"""
from __future__ import annotations
import json
from pathlib import Path
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONTS_DIR = ROOT / "assets" / "fonts"
BRAND = json.loads((ROOT / "brand.json").read_text(encoding="utf-8"))
C = BRAND["colors"]


def hex2rgb(h: str, alpha: int | None = None):
    h = h.lstrip("#")
    rgb = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    return rgb + (alpha,) if alpha is not None else rgb


@lru_cache(maxsize=64)
def font(key: str, size: int) -> ImageFont.FreeTypeFont:
    """key es una clave de brand.json['fonts'] o un nombre de archivo .ttf."""
    fname = BRAND["fonts"].get(key, key)
    return ImageFont.truetype(str(FONTS_DIR / fname), size)


def text_w(draw, s, f):
    return draw.textbbox((0, 0), s, font=f)[2]


def wrap(draw, text, f, max_w):
    """Envuelve texto por ancho en píxeles. Devuelve lista de líneas."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if text_w(draw, trial, f) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_wordmark(draw, x, y, scale=1.0):
    """Dibuja el wordmark 'Populi': P serif bold roja + 'opuli' italic tinta.
    Devuelve el ancho total dibujado."""
    p_size = int(64 * scale)
    rest_size = int(40 * scale)
    f_p = font("serif", p_size)
    f_rest = font("serifItalic", rest_size)
    # baseline compartida
    base_y = y + p_size
    draw.text((x, base_y), "P", font=f_p, fill=hex2rgb(C["red"]), anchor="ls")
    px = x + text_w(draw, "P", f_p) - int(6 * scale)
    draw.text((px, base_y), "opuli", font=f_rest, fill=hex2rgb(C["ink"]), anchor="ls")
    return px + text_w(draw, "opuli", f_rest) - x


def draw_underline_title(draw, x, y, lines, f, fill, accent, max_w,
                         line_gap=10, underline_h=8, underline_pad=6):
    """Dibuja un título multilínea con subrayado de acento bajo la última línea.
    Devuelve la y final (debajo del subrayado)."""
    cy = y
    line_h = (f.getbbox("Ág")[3] - f.getbbox("Ág")[1])
    for i, ln in enumerate(lines):
        draw.text((x, cy), ln, font=f, fill=fill)
        cy += line_h + line_gap
    # subrayado bajo la última línea, ancho proporcional a esa línea
    last_w = min(text_w(draw, lines[-1], f), max_w)
    uy = cy - line_gap + underline_pad
    draw.rounded_rectangle([x, uy, x + max(last_w, 120), uy + underline_h],
                           radius=underline_h // 2, fill=accent)
    return uy + underline_h


def draw_watermark(canvas, opacity=18, scale=3.0):
    """Marca de agua diagonal sutil con el wordmark, tileada sobre el lienzo."""
    W, H = canvas.size
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font("serif", int(60 * scale))
    txt = "POPULI"
    tile = Image.new("RGBA", (int(text_w(d, txt, f) + 80), int(80 * scale)), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile)
    td.text((0, 0), txt, font=f, fill=hex2rgb(C["red"], opacity))
    tile = tile.rotate(30, expand=True)
    step_x, step_y = int(tile.width * 0.9), int(tile.height * 1.1)
    for ty in range(-step_y, H + step_y, step_y):
        offset = (ty // step_y % 2) * (step_x // 2)
        for tx in range(-step_x + offset, W + step_x, step_x):
            layer.alpha_composite(tile, (tx, ty))
    return Image.alpha_composite(canvas.convert("RGBA"), layer)

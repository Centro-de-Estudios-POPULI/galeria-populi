"""
Tarjeta OG del Banco (public/og.png, 1200×630): lo que muestra WhatsApp, X o
LinkedIn al compartir la portada. Las páginas de cada gráfica usan su propio PNG.

    python viz/og_portada.py
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

VIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(VIZ))
import populi_style as ps

sys.stdout.reconfigure(encoding="utf-8")
ROOT = VIZ.parent
W, H = 1200, 630
MUESTRA = ["censo-poblacion-urbana", "fiscal-ic-pc", "mundo-pib-total", "pib-semestre-variacion"]


def fuente(nombre, px):
    return ImageFont.truetype(str(ps.FONTS_DIR / ps._FONT_FILES[nombre]), px)


img = Image.new("RGB", (W, H), ps._rgb(ps.COLORS["fondo"]))
d = ImageDraw.Draw(img)
d.rectangle([0, 0, W, 8], fill=ps._rgb(ps.COLORS["rojo"]))
# marca
d.text((72, 64), "P", font=fuente("Playfair Display", 54), fill=ps._rgb(ps.COLORS["rojo"]))
d.text((104, 74), "opuli", font=fuente("Playfair Display Italic", 40), fill=ps._rgb(ps.COLORS["tinta"]))
d.text((72, 150), "GRÁFICOS ABIERTOS · BOLIVIA", font=fuente("Inter Bold", 17), fill=ps._rgb(ps.COLORS["rojo"]))
d.text((72, 186), "Banco de", font=fuente("Playfair Display", 80), fill=ps._rgb(ps.COLORS["tinta"]))
d.text((72, 276), "Gráficos", font=fuente("Playfair Display Italic", 80), fill=ps._rgb(ps.COLORS["rojo"]))
d.text((72, 396), "Gráficas e indicadores de Bolivia con fuente verificada,", font=fuente("Inter", 24), fill=ps._rgb(ps.COLORS["cafe"]))
d.text((72, 430), "en alta resolución y listos para compartir.", font=fuente("Inter", 24), fill=ps._rgb(ps.COLORS["cafe"]))
d.text((72, 540), "Centro de Estudios POPULI", font=fuente("Inter Bold", 20), fill=ps._rgb(ps.COLORS["tinta"]))
d.text((72, 568), "centro-de-estudios-populi.github.io/galeria-populi", font=fuente("JetBrains Mono", 17), fill=ps._rgb(ps.COLORS["gris"]))

# cuatro miniaturas en abanico a la derecha
x0, y0, lado = 720, 70, 250
for i, slug in enumerate(MUESTRA):
    p = ROOT / "public" / "thumbs" / f"{slug}.webp"
    if not p.exists():
        continue
    th = Image.open(p).convert("RGB").resize((lado, lado), Image.LANCZOS)
    x, y = x0 + (i % 2) * (lado + 14), y0 + (i // 2) * (lado + 14)
    img.paste(th, (x, y))
    d.rectangle([x, y, x + lado, y + lado], outline=ps._rgb(ps.COLORS["borde"]), width=1)

out = ROOT / "public" / "og.png"
img.save(out, optimize=True)
print(f"OK {out} ({out.stat().st_size // 1024} KB)")

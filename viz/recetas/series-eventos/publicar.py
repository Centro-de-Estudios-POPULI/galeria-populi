"""
Publica la figura de esta receta al Banco de Gráficos (galería Astro).

Como la receta usa `componer()` directo (no `publicar()`), registramos la imagen
YA renderizada por figura.py: copia full-HD a public/graficas, miniatura, ficha y
reconstrucción del manifest. Ejecutar DESPUÉS de `python figura.py`.
"""
import json
import sys
import shutil
from pathlib import Path
from PIL import Image

PUB = Path(__file__).resolve().parent
VIZ = PUB.parents[1]                       # .../galeria-populi/viz
sys.path.insert(0, str(VIZ))
import populi_style as ps                  # noqa: E402
import catalogo                            # noqa: E402

SLUG = "monetario-reservas-oro-pignorado"
SRC = PUB / "output" / "reservas_oro_pignorado.png"

ROOT = catalogo.ROOT
GRAFICAS, CATALOGO = catalogo.GRAFICAS, catalogo.CATALOGO
THUMBS = ROOT / "public" / "thumbs"
for d in (GRAFICAS, THUMBS, CATALOGO):
    d.mkdir(parents=True, exist_ok=True)

# 1. Imagen full-HD (ya quantizada P-256) → public/graficas (copia byte a byte)
shutil.copyfile(SRC, GRAFICAS / f"{SLUG}.png")

# 2. Miniatura 600×600. Para una figura ANCHA de 2 paneles el recorte central
#    partiría ambos paneles → mejor encajar la figura completa (letterbox) sobre
#    el crema de marca: el preview se reconoce.
img = Image.open(SRC).convert("RGB")
th = img.copy()
th.thumbnail((600, 600), Image.LANCZOS)
canvas = Image.new("RGB", (600, 600), ps.COLORS["fondo"])
canvas.paste(th, ((600 - th.width) // 2, (600 - th.height) // 2))
canvas.quantize(colors=256, method=Image.MEDIANCUT, dither=Image.Dither.NONE).save(
    THUMBS / f"{SLUG}.png", "PNG", optimize=True)

# 3. Ficha (misma estructura que publicar(); política del Banco: solo imagen)
ficha = {
    "slug": SLUG,
    "titulo": "Bolivia: evolución de los componentes de las RIN",
    "subtitulo": "Componentes principales —oro y divisas—, evolución semanal · millones de USD",
    "categoria": "monetario",
    "fuente": ("Fuente: Banco Central de Bolivia (BCB), Estadísticas Semanales; "
               "Nota de Prensa NP10/2026. Elaboración: Centro de Estudios POPULI."),
    "tags": ["reservas internacionales", "oro", "oro pignorado", "divisas", "bcb", "monetario"],
    "fecha": "2026-06-18",
    "tipo": "series_eventos",
    "formato": "informe_horizontal",
    "imagen": f"graficas/{SLUG}.png",
    "thumb": f"thumbs/{SLUG}.png",
    "datos": None,
}
(CATALOGO / f"{SLUG}.json").write_text(
    json.dumps(ficha, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"ficha: {SLUG}")

# 4. Reconstruir el manifest consolidado para Astro
catalogo.build_manifest()
print("Publicada al Banco.")

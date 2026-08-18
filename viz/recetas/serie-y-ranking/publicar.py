"""
Publica la figura de esta receta al Banco de Gráficos.

Como la receta usa `componer()` directo (no `publicar()`), registramos la imagen
YA renderizada por figura.py: copia a public/graficas, miniatura, ficha y
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

SLUG = "pib-ipaec-2026"
SRC = PUB / "output" / "pib_ipaec_2026.png"

ROOT = catalogo.ROOT
GRAFICAS, CATALOGO = catalogo.GRAFICAS, catalogo.CATALOGO
THUMBS = ROOT / "public" / "thumbs"
for d in (GRAFICAS, THUMBS, CATALOGO):
    d.mkdir(parents=True, exist_ok=True)

# 1. Imagen (ya quantizada P-256 por ps.guardar) → public/graficas
shutil.copyfile(SRC, GRAFICAS / f"{SLUG}.png")

# 2. Miniatura 600×600. En una figura ANCHA de dos paneles el recorte central
#    partiría ambos paneles → encajar la figura completa (letterbox) sobre el
#    crema de marca, para que el preview se reconozca.
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
    "titulo": "Bolivia: Evolución del PIB",
    "subtitulo": "Variación en porcentaje · trimestres 2022–2026 y actividades del primer semestre de 2026",
    "categoria": "actividad",
    "fuente": "Fuente: Instituto Nacional de Estadística (INE), PIB trimestral base 2017; "
              "Banco Central de Bolivia (BCB), Reporte de Inflación y Política Monetaria "
              "(IpAEC). Elaboración: Centro de Estudios POPULI · Carlos Aranda.",
    "tags": ["pib", "ipaec", "actividad económica", "crecimiento", "recesión",
             "sectores", "construcción", "bcb", "ine", "2026"],
    "fecha": "2026-08-18",
    "tipo": "serie_y_ranking",
    "formato": "informe_panorama",
    "imagen": f"graficas/{SLUG}.png",
    "thumb": f"thumbs/{SLUG}.png",
    "datos": None,
}
(CATALOGO / f"{SLUG}.json").write_text(
    json.dumps(ficha, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"PUBLICADA  {SLUG}")

catalogo.build_manifest()

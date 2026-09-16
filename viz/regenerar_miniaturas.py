"""
Rehace la miniatura de cada lámina publicada SIN volver a renderizarla (lee el
PNG de public/graficas) y actualiza la ficha para que apunte al .webp.

    python viz/regenerar_miniaturas.py            # todas las que aún sean PNG
    python viz/regenerar_miniaturas.py --todas    # las 600 y pico, sin excepción

Se usó el 2026-09-16 al pasar de recorte-PNG a letterbox-WebP.
"""
import json
import sys
from pathlib import Path

from PIL import Image

VIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(VIZ))
import populi_style as ps

sys.stdout.reconfigure(encoding="utf-8")
ROOT = VIZ.parent
CAT = ROOT / "data" / "catalogo"
TODAS = "--todas" in sys.argv

n, borradas = 0, 0
for f in sorted(CAT.glob("*.json")):
    ficha = json.loads(f.read_text(encoding="utf-8"))
    if not TODAS and ficha.get("thumb", "").endswith(".webp"):
        continue
    png = ROOT / "public" / ficha["imagen"]
    if not png.exists():
        print(f"  ⚠️ sin PNG: {ficha['slug']}")
        continue
    with Image.open(png) as img:
        ps.miniatura(img, ROOT / "public" / "thumbs" / f"{ficha['slug']}.webp")
    viejo = ROOT / "public" / "thumbs" / f"{ficha['slug']}.png"
    if viejo.exists():
        viejo.unlink()
        borradas += 1
    ficha["thumb"] = f"thumbs/{ficha['slug']}.webp"
    f.write_text(json.dumps(ficha, ensure_ascii=False, indent=2), encoding="utf-8")
    n += 1
print(f"{n} miniaturas rehechas en WebP · {borradas} PNG viejos borrados")

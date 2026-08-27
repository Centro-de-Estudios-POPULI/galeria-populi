"""
Publica las dos laminas de esta receta al Banco de Graficos.

Como la receta usa `componer()` directo (no `publicar()`), se registran las
imagenes YA renderizadas por figura.py: copia a public/graficas, miniatura,
ficha y reconstruccion del manifest. Ejecutar DESPUES de `python figura.py`.

Ademas exporta el CSV de cada lamina: son datos publicos del INE y la tabla es
chica, asi que el Banco puede ofrecerla para descarga.
"""
import csv
import json
import shutil
import sys
from pathlib import Path

from PIL import Image

PUB = Path(__file__).resolve().parent
VIZ = PUB.parents[1]                       # .../galeria-populi/viz
sys.path.insert(0, str(VIZ))
import populi_style as ps                  # noqa: E402
import catalogo                            # noqa: E402
import figura                               # noqa: E402  (reusa leer() y CORTO)

ROOT = catalogo.ROOT
GRAFICAS, CATALOGO = catalogo.GRAFICAS, catalogo.CATALOGO
THUMBS = ROOT / "public" / "thumbs"
DATOS = ROOT / "public" / "datos"
for d in (GRAFICAS, THUMBS, CATALOGO, DATOS):
    d.mkdir(parents=True, exist_ok=True)

FUENTE = ("Fuente: Instituto Nacional de Estadística (INE), PIB trimestral base 2017; "
          "Banco Central de Bolivia (BCB), Reporte de Inflación y Política Monetaria "
          "(IpAEC). Elaboración: Centro de Estudios POPULI · Carlos Aranda.")
TAGS = ["pib", "sectores", "actividad económica", "primer semestre", "ipaec",
        "prepandemia", "ine", "bcb", "small multiples", "2026"]
FECHA = "2026-08-21"

LAMINAS = [
    {
        "slug": "pib-semestre-indice-2019",
        "png": "pib_semestre_indice_2019.png",
        "titulo": "Bolivia: Nivel del PIB Sectorial Frente a la Prepandemia",
        "subtitulo": "Índice del primer semestre (enero–junio), 2019 = 100 · "
                     "doce paneles: el PIB y los once sectores del INE",
        "bloque": "indice",
    },
    {
        "slug": "pib-semestre-variacion",
        "png": "pib_semestre_variacion.png",
        "titulo": "Bolivia: Crecimiento del PIB Sectorial",
        "subtitulo": "Variación interanual del primer semestre (enero–junio), en porcentaje · "
                     "doce paneles: el PIB y los once sectores del INE",
        "bloque": "variacion",
    },
]


def escribir_csv(destino, años, serie, orden, decimales):
    with open(destino, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["actividad"] + [str(a) for a in años])
        for clave in orden:
            w.writerow([figura.CORTO[clave]]
                       + [round(v, decimales) for v in serie[clave]])


orden, (a_idx, s_idx), (a_var, s_var) = figura.leer()
bloques = {"indice": (a_idx, s_idx, 1), "variacion": (a_var, s_var, 1)}

for L in LAMINAS:
    src = PUB / "output" / L["png"]
    if not src.exists():
        raise SystemExit("falta %s — corre primero `python figura.py`" % src.name)

    # 1. Imagen (ya quantizada P-256 por ps.guardar) -> public/graficas
    shutil.copyfile(src, GRAFICAS / f"{L['slug']}.png")

    # 2. Miniatura 600x600. El recorte central de ps.guardar partiria la
    #    cuadricula por la mitad: va la lamina completa en letterbox sobre el
    #    crema de marca, que es como se reconoce en la vitrina.
    img = Image.open(src).convert("RGB")
    th = img.copy()
    th.thumbnail((600, 600), Image.LANCZOS)
    lienzo = Image.new("RGB", (600, 600), ps.COLORS["fondo"])
    lienzo.paste(th, ((600 - th.width) // 2, (600 - th.height) // 2))
    lienzo.quantize(colors=256, method=Image.MEDIANCUT,
                    dither=Image.Dither.NONE).save(
        THUMBS / f"{L['slug']}.png", "PNG", optimize=True)

    # 3. Datos descargables
    años, serie, dec = bloques[L["bloque"]]
    escribir_csv(DATOS / f"{L['slug']}.csv", años, serie, orden, dec)

    # 4. Ficha
    ficha = {
        "slug": L["slug"],
        "titulo": L["titulo"],
        "subtitulo": L["subtitulo"],
        "categoria": "actividad",
        "fuente": FUENTE,
        "tags": TAGS,
        "fecha": FECHA,
        "tipo": "small_multiples",
        "formato": "informe_mosaico",
        "imagen": f"graficas/{L['slug']}.png",
        "thumb": f"thumbs/{L['slug']}.png",
        "datos": f"datos/{L['slug']}.csv",
    }
    (CATALOGO / f"{L['slug']}.json").write_text(
        json.dumps(ficha, ensure_ascii=False, indent=2), encoding="utf-8")
    print("PUBLICADA  %s" % L["slug"])

catalogo.build_manifest()

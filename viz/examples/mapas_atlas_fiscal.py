"""
Publica los mapas del ATLAS FISCAL MUNICIPAL (IGF) al Banco de Gráficos.
30 indicadores fiscales, gestión de referencia, por municipio.

Fuente de datos: `fiscal_data.json` (343 entidades × 30 indicadores × 10
gestiones) y `fiscal_catalogo.json` del repo Atlas-Fiscal-Municipal, unidos
por `sigep` al mapa MAESTRO de 343 (bo-geo-maestro), la misma geometría que
usan los mapas del Censo.

★ TODO SALE DEL CATÁLOGO (2026-09-16): el título de la lámina
  (`titulo_lamina`), la definición (`desc`, que va al subtítulo), la unidad, la
  dirección y el slug (`lam`). Antes había 30 títulos escritos a mano acá y la
  definición nunca llegaba a la lámina.

★ EL PIVOTE SIGUE LA REGLA DE `dominio()` DEL ATLAS: cero en los indicadores con
  signo, promedio nacional ponderado por población en los ratios (%), y la
  MEDIANA en los per cápita y montos. Antes acá se ponderaba todo, y los cinco
  per cápita quedaban hasta un quinto del rango corridos respecto de la web.

★ POBLACIÓN INE (2026-09-17): los cinco per cápita (Bs/hab) y el ponderador del
  promedio nacional usan la población proyectada por el INE (Revisión 2025, mitad de
  año), que llega ya dentro de `fiscal_data.json` (`pob`); ver `poblacion` en el
  catálogo. Antes eran los conteos censales 2012/2024 interpolados (~4 % menos).

    python viz/examples/mapas_atlas_fiscal.py
    python viz/examples/mapas_atlas_fiscal.py --solo=cp_it
"""
import sys
import json
from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd

VIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VIZ))
from catalogo import publicar, build_manifest
import populi_style as ps

sys.stdout.reconfigure(encoding="utf-8")
SOLO = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--solo=")), None)

ATLAS_DIR = (VIZ.parent.parent / "Observatorio de Presupuesto Fiscal Departamental"
             / "_github_atlas_fiscal")
ATLAS_URL = "https://centro-de-estudios-populi.github.io/Atlas-Fiscal-Municipal/mapa.html"
ATLAS_DATA = ATLAS_DIR / "fiscal_data.json"
ATLAS_CAT = ATLAS_DIR / "fiscal_catalogo.json"

GEO = VIZ.parent.parent / "bo-geo-maestro" / "geo" / "atlas_muni_343.topojson"
if not GEO.exists():
    GEO = VIZ / "geo" / "atlas_muni_343.topojson"
if not GEO.exists():
    sys.exit("⛔ no está el mapa maestro (bo-geo-maestro/geo/atlas_muni_343.topojson)")

FECHA = "2026-09-17"
AUTOR = "Carlos Aranda"
FUENTE = ("Fuente: Ministerio de Economía y Finanzas Públicas, ejecución "
          f"presupuestaria municipal (IGF). Elaboración: Centro de Estudios POPULI · {AUTOR}.")

MUN = json.loads(ATLAS_DATA.read_text(encoding="utf-8"))
CAT = json.loads(ATLAS_CAT.read_text(encoding="utf-8"))
INDS = [{**i, "id": i["key"], "grp": g["label"]}
        for g in CAT["grupos"] for i in g["indicadores"]]
ANIOS = CAT["anios"]
YEAR = str(ANIOS[-1])          # gestión de referencia = la última, como BASE_YI en la web
YI = len(ANIOS) - 1
print(f"Atlas: {len(MUN)} entidades · {len(INDS)} indicadores · gestión {YEAR}")

# --- geometría + tabla ancha de valores del año, unida por sigep ------------ #
gdf = gpd.read_file(GEO)                              # sigep, municipio, dpto, geom
filas = {}
for sigep, m in MUN.items():
    serie = m.get("s") or {}
    fila = {k: (v[YI] if isinstance(v, list) and len(v) > YI else None)
            for k, v in serie.items()}
    if any(v is not None for v in fila.values()):
        filas[sigep] = fila
vals = pd.DataFrame.from_dict(filas, orient="index")
vals.index.name = "sigep"
# Población de la gestión: el PESO del promedio nacional, igual que `agg()` en la web
vals["_pob"] = pd.Series({s: (m.get("pob") or [None])[YI]
                          if isinstance(m.get("pob"), list) and len(m["pob"]) > YI else None
                          for s, m in MUN.items()})
gdf = gdf.merge(vals, left_on="sigep", right_index=True, how="left")
algun = [i["id"] for i in INDS if i["id"] in gdf.columns]
cobertura = gdf[algun[0]].notna().sum() if algun else 0
print(f"Unidos {cobertura}/{len(gdf)} municipios con datos {YEAR}.\n")


def escala_de(ind):
    """= dominio() de mapa.html: cero · promedio nacional (%) · mediana (resto)."""
    v = gdf[ind["id"]].astype(float)
    if ind.get("div"):
        return ps.escala_atlas(v, direccion=ind.get("dir", 0), con_signo=True, piv_tipo="cero")
    if ind.get("unit") == "%":
        w = gdf["_pob"].astype(float)
        m = v.notna() & w.notna()
        piv = float((v[m] * w[m]).sum() / w[m].sum()) if m.any() and w[m].sum() > 0 else None
        return ps.escala_atlas(v, direccion=ind.get("dir", 0), pivote=piv,
                               piv_tipo="promedio nacional")
    return ps.escala_atlas(v, direccion=ind.get("dir", 0), conteo=True)   # mediana


n, sin_titulo = 0, []
for ind in INDS:
    iid = ind["id"]
    if SOLO and iid != SOLO:
        continue
    if iid not in gdf.columns:
        print(f"  (omitido {iid}: sin datos {YEAR})")
        continue
    unidad = ind.get("unit", "")
    pct = unidad == "%"
    sufijo = "%" if pct else (" Bs" if unidad.startswith("Bs") else "")
    titulo = ind.get("titulo_lamina")
    if not titulo:
        sin_titulo.append(iid)
        titulo = ind["label"]
    # Inter no tiene la delta griega garantizada en todas las instancias: se deletrea
    etiqueta = ind["label"].replace("ΔCxP", "variación de cuentas por pagar")
    desc = (ind.get("desc") or etiqueta).rstrip(".")
    subtitulo = f"{desc} — gestión {YEAR}, por municipio"
    escala = escala_de(ind)
    cmap, norm, info = escala
    slug = ind.get("lam") or f"fiscal-{iid.replace('_', '-')}"
    datos = gdf[["sigep", "municipio", "dpto", iid]].rename(
        columns={"municipio": "nombre"}).set_index("sigep")
    publicar(
        meta={"slug": slug, "tipo": "mapa",
              "titulo": f"Bolivia: {titulo}", "subtitulo": subtitulo,
              "fuente": FUENTE, "categoria": "fiscal",
              "tags": ["atlas fiscal", f"igf {YEAR}", "municipios", ind["grp"], iid],
              "fecha": FECHA, "formato": "red_vertical",
              "clave": iid, "atlas": "fiscal", "modo": YEAR, "anio": YEAR,
              "enlace": f"{ATLAS_URL}#i={iid}&g={YEAR}", "grupo": ind["grp"],
              "unidad": unidad, "indicador": etiqueta,
              "escala": {k: info[k] for k in ("lo", "piv", "piv_real", "hi", "piv_tipo")}},
        df=datos, gdf=gdf, value_col=iid, escala=escala,
        # Un decimal en los porcentajes y entero con miles en los Bs, como la página.
        sufijo=sufijo, label_fmt="{:.1f}" if pct else "{:.0f}", miles=not pct,
    )
    n += 1

build_manifest()
print(f"\n{n} mapas del Atlas Fiscal publicados al Banco (gestión {YEAR}).")
if sin_titulo:
    print(f"  ⚠️ sin `titulo_lamina` en el catálogo (se usó el rótulo técnico): {sin_titulo}")

"""
mapas_mundo.py — Publica indicadores mundiales (atlas "Nuestro Mundo en Datos")
como mapas coropléticos por país al Banco de Gráficos.

Lee la geodata mundial (viz/geo/world_110m.topojson + crosswalk M49→ISO3 +
nombres ES) y los indicadores del atlas (catalog.json + data/indicators/*.json),
elige un año reciente bien cubierto, y publica cada mapa con su EXPLICACIÓN
(qué mide la variable) incrustada, en formato horizontal Natural Earth.

Uso:
    python viz/examples/mapas_mundo.py            # muestra (lista SAMPLE)
    python viz/examples/mapas_mundo.py todos      # los 207 indicadores

Generación LOCAL (local-first): lee el atlas desde su carpeta hermana; luego
git add/commit/push de los PNG + manifest a la Galería.
"""
import sys
import json
import re
import unicodedata
from pathlib import Path

import geopandas as gpd
import pandas as pd

VIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VIZ))
from catalogo import publicar, build_manifest  # noqa: E402

# --- rutas --------------------------------------------------------------- #
GEO = VIZ / "geo"
ATLAS = Path(r"C:\Users\HP\OneDrive\Desktop\Proyectos\nuestro-mundo-en-datos")
ATLAS_DATA = ATLAS / "data"
FECHA = "2026-06-24"
AUTOR = "Carlos Aranda"

# muestra para validar el diseño antes de correr todos
SAMPLE = [
    "NY.GDP.PCAP.CD",                # PIB per cápita (verde · mejor)
    "FP.CPI.TOTL.ZG",                # Inflación (cálido · peor) — ya NO divergente
    "GOV_WGI_CC.EST",                # Control de corrupción (divergente, anclado en 0)
    "SH.H2O.BASW.ZS",                # Agua potable básica (verde · mejor) — cobertura alta
    "EFW.SUMMARY",                   # Libertad económica (verde) — Fraser EFW
    "OWID.human-development-index",  # IDH (verde) — OWID
    "SI.POV.GINI",                   # Gini (cálido · peor) — datos dispersos (prueba frescura/salvedad)
    "SP.DYN.LE00.IN",                # Esperanza de vida — unidad "años" -> "Años"
    "EN.GHG.CO2.PC.CE.AR5",          # CO₂ per cápita — "t por persona" -> "Toneladas por persona"
]


# --- geodata mundial: gdf base con iso3 + nombre ES ---------------------- #
def cargar_geo():
    g = gpd.read_file(GEO / "world_110m.topojson", layer="countries").set_crs(4326)
    cw = json.loads((GEO / "world_iso_crosswalk.json").read_text(encoding="utf-8"))
    rg = json.loads((GEO / "world_regions.json").read_text(encoding="utf-8"))
    g["iso3"] = g["id"].map(lambda v: cw.get(str(int(v))) if str(v).isdigit() else None)
    g.loc[g["name"] == "Kosovo", "iso3"] = "XKX"
    g["nombreEs"] = g["iso3"].map(lambda i: (rg.get(i, {}) or {}).get("name"))
    return g[["iso3", "nombreEs", "geometry"]]


# subíndices (CO₂, CH₄, N₂O…) → dígitos normales (Public Sans no trae el glifo)
_SUB = {0x2080 + i: str(i) for i in range(10)}


def limpiar(s):
    return (s or "").translate(_SUB).strip()


def formato_unidad(u):
    """Unidad para el subtítulo: expande abreviaturas de una letra (t -> Toneladas)
    y capitaliza la inicial cuando es una palabra (años -> Años), respetando los
    símbolos (kWh, kg, m³, US$, % no se tocan)."""
    u = limpiar(u)
    if not u:
        return ""
    u = re.sub(r"^t(?=\s|$)", "toneladas", u)        # 't por persona' -> 'toneladas por persona'
    m = re.match(r"^([a-záéíóúñ]+)", u)               # primera palabra en minúsculas
    if m and len(m.group(1)) >= 3:                    # palabra (no símbolo de 1-2 letras)
        u = u[0].upper() + u[1:]
    return u


def resumen_def(d, maxlen=240):
    """Explicación concisa y COMPLETA (sin '…') para el pie del mapa: primera frase,
    sin incisos entre rayas; si aún es larga, cierra en la última coma con punto."""
    d = limpiar(d)
    d = re.sub(r"\s*—[^—]*—\s*", " ", d)          # quita incisos —…—
    d = re.sub(r"\s{2,}", " ", d).strip()
    frase = re.split(r"(?<=[.;]) ", d)[0].strip() if d else ""
    if len(frase) > maxlen:                         # acortar en una coma, cerrar con punto
        corte = frase[:maxlen]
        corte = corte[:corte.rfind(",")] if "," in corte[:maxlen] else corte[:corte.rfind(" ")]
        frase = corte.strip(" ,;:")
    return frase.rstrip(" .,;:") + "." if frase else ""


def fuente_corta(org, default, maxlen=110):
    """Fuente compacta para el pie (algunos `org` traen citas larguísimas con URLs)."""
    s = limpiar(org or default or "Banco Mundial.")
    s = re.split(r"[;,]| uri:| publisher:| date ", s)[0].strip()
    if len(s) > maxlen:
        s = s[:maxlen].rsplit(" ", 1)[0] + "…"
    return s if s.endswith((".", "…")) else s + "."


def slugify(s):
    s = unicodedata.normalize("NFKD", limpiar(s)).encode("ascii", "ignore").decode()
    return "mundo-" + re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def serie_ultimo(raw, valid):
    """Último dato disponible de cada país real (ISO3 en `valid`).
    Devuelve {iso: valor} y {iso: año del dato}."""
    years = raw["years"]
    serie, yr_of = {}, {}
    for iso, arr in raw["data"].items():
        if iso not in valid:
            continue
        for i in range(len(arr) - 1, -1, -1):
            if arr[i] is not None:
                serie[iso] = arr[i]
                yr_of[iso] = years[i]
                break
    return serie, yr_of


def linea_frescura(yr_of):
    """Proxy de cobertura/actualidad: % de países con dato de los últimos 3 años
    respecto al año más reciente del indicador, con el año de referencia y una
    salvedad cuando ese porcentaje es bajo."""
    if not yr_of:
        return ""
    Y = max(yr_of.values())
    Y2 = Y - 2
    pct = round(100 * sum(1 for y in yr_of.values() if y >= Y2) / len(yr_of))
    txt = (f"Último dato disponible por país · {pct}% con registro reciente "
           f"({Y2}–{Y}) · año más reciente del indicador: {Y}.")
    if pct < 60:
        txt += " Parte de los datos es más antigua; léase como referencia."
    return txt


def paleta_para(name, category, signed):
    if signed:
        return "divergente"
    cl = (category or "").lower()
    nl = (name or "").lower()
    if "salud" in cl or "agua" in nl or "saneamiento" in nl:
        return "verde"
    if "ambient" in cl or "emis" in nl or "co₂" in nl or "gei" in nl:
        return "rojo"
    if "goberna" in cl or "institu" in cl:
        return "azul"
    return "calido"


def slugs_unicos(indicators):
    """Slug por id garantizando UNICIDAD. Si dos indicadores producen el mismo
    slug (p. ej. 'Índice de Capital Humano' del Banco Mundial vs 'Índice de
    capital humano' de Penn World Table — difieren solo en mayúsculas), el
    primero por id conserva el slug base y los demás reciben un sufijo con la
    fuente (prefijo del id: PWT.HC -> '-pwt'). Antes uno sobrescribía al otro y
    se perdía un mapa."""
    grupos = {}
    for ind in indicators:
        grupos.setdefault(slugify(ind["name"]), []).append(ind["id"])
    out = {}
    for base, ids in grupos.items():
        if len(ids) == 1:
            out[ids[0]] = base
            continue
        for k, iid in enumerate(sorted(ids)):
            tag = re.sub(r"[^a-z0-9]+", "-", re.split(r"[._]", iid)[0].lower()).strip("-")
            out[iid] = base if k == 0 else f"{base}-{tag}"
    return out


def publicar_indicador(gdf_base, meta, source_default, slug):
    iid = meta["id"]
    raw = json.loads((ATLAS_DATA / "indicators" / f"{iid}.json").read_text(encoding="utf-8"))
    valid = set(gdf_base["iso3"].dropna())
    serie, yr_of = serie_ultimo(raw, valid)        # ÚLTIMO dato disponible por país
    if len(serie) < 10:
        print(f"SKIP {iid}: solo {len(serie)} países con dato")
        return False

    gdf = gdf_base.copy()
    gdf["valor"] = gdf["iso3"].map(serie)
    vals = gdf["valor"].dropna()
    rng = float(vals.max() - vals.min())
    dec = 0 if rng >= 100 else (1 if rng >= 5 else 2)

    name = limpiar(meta["name"])
    unit = limpiar(meta.get("unit", ""))
    suf = "%" if "%" in unit else ""
    # paleta y escala según la curaduría del catálogo (family/scale); fallback heurístico
    pal = meta.get("family") or paleta_para(name, meta.get("category"),
                                            bool(vals.min() < 0 < vals.max()))
    fresh = linea_frescura(yr_of)
    fuente = (f"Fuente: {fuente_corta(meta.get('org'), source_default)} "
              f"Elaboración: Centro de Estudios POPULI · {AUTOR}.")

    publicar(
        meta={
            "slug": slug,
            "tipo": "mapa_mundial",
            "titulo": f"Mundo: {name}, por países",
            "subtitulo": (f"{formato_unidad(unit)} · último dato disponible"
                          if unit else "Último dato disponible"),
            "nota": resumen_def(meta.get("def", "")),   # explicación → pie
            "fuente": fuente,
            "categoria": "mundo",
            "tags": ["mundo", meta.get("category", ""), iid],
            "fecha": FECHA,
            "formato": "mundo",
        },
        df=None, gdf=gdf, value_col="valor",
        paleta=pal, sufijo=suf, label_fmt="{:." + str(dec) + "f}", freshness=fresh,
    )
    return True


def main():
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    catalog = json.loads((ATLAS_DATA / "catalog.json").read_text(encoding="utf-8"))
    source_default = catalog.get("source_default", "Banco Mundial.")
    by_id = {d["id"]: d for d in catalog["indicators"]}
    slug_by_id = slugs_unicos(catalog["indicators"])   # slugs únicos (sin colisiones)
    if arg == "todos":
        ids = list(by_id)
    elif arg == "ids":                                  # regenerar indicadores puntuales
        ids = sys.argv[2:]
    else:
        ids = SAMPLE

    gdf_base = cargar_geo()
    n = 0
    for iid in ids:
        meta = by_id.get(iid)
        if not meta:
            print(f"SKIP {iid}: no está en el catálogo")
            continue
        if publicar_indicador(gdf_base, meta, source_default, slug_by_id[iid]):
            n += 1
    build_manifest()
    print(f"\n{n} mapas mundiales publicados al Banco.")


if __name__ == "__main__":
    main()

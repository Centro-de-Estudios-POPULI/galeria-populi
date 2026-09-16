"""
Publica los mapas municipales del Censo al Banco de Gráficos, en los TRES modos
del Atlas Socioeconómico: 2024, 2012 y el cambio 2012→2024.

★★ LO MANEJA EL CATÁLOGO DEL ATLAS, NO UNA LISTA ESCRITA ACÁ. El título, la
   definición, el universo, la dirección de la rampa, el dominio (`dom` para
   los censos, `domd` para el cambio), quién tiene serie 2012 (`s12`) y el
   denominador de cada indicador (`den`) salen del MISMO catálogo que dibuja la
   web. Agregar un indicador al Atlas lo agrega acá solo.

★★ EL PIVOTE SE CALCULA CON LA MISMA REGLA QUE EL ATLAS (2026-09-16). Antes se
   ponderaba TODO por población, y el Atlas pondera cada indicador por SU
   denominador (agua por viviendas, emigración por emigrantes, brechas por la
   diferencia de sus dos componentes). Medido antes de cambiarlo: 80 de 208
   pivotes desfasados más del 1 % del rango dibujado; urbanización decía 65,9 %
   en la web y 68,4 % en la lámina. `pais_de()` replica `aggRaw()` del HTML y se
   lo pasa a `escala_atlas(pivote=…)`, con el mismo rótulo («país 2024»).

★ LOS SLUGS DE LAS 215 LÁMINAS DE 2024 NO CAMBIAN: salen de `lam`. Las de 2012
  y de cambio se derivan de él (`<lam>-2012`, `<lam>-cambio`). Lo que enlaza el
  tablero ya no es el `lam` sino el índice que publica `build_manifest()`.

★ SIN MALLA DEPARTAMENTAL (Carlos, 2026-09-16): la lámina es el mapa, con los
  343 municipios en borde fino y blanco. La malla es del tablero.

    python viz/examples/mapas_censo_todos.py                 # 2024 + 2012 + cambio
    python viz/examples/mapas_censo_todos.py --modo=2024     # sólo ese modo
    python viz/examples/mapas_censo_todos.py --solo=pct_urbano
    python viz/examples/mapas_censo_todos.py --ensayo        # sólo informa
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

VIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VIZ))
from catalogo import publicar, build_manifest
import populi_style as ps

# la consola de Windows es cp1252 y se atraganta con las flechas del informe
sys.stdout.reconfigure(encoding="utf-8")

ENSAYO = "--ensayo" in sys.argv
SOLO = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--solo=")), None)
_modo = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--modo=")), None)
MODOS = [_modo] if _modo else ["2024", "2012", "cambio"]

# Mapa MAESTRO de Bolivia: 343 municipios (339 del OEP + los 4 GAIOC de
# conversión total). Fuente: Proyectos/bo-geo-maestro (clave `sigep`).
GEO = VIZ.parent.parent / "bo-geo-maestro" / "geo" / "atlas_muni_343.topojson"
if not GEO.exists():                                   # respaldo local
    GEO = VIZ / "geo" / "atlas_muni_343.topojson"
if not GEO.exists():
    sys.exit("⛔ no está el mapa maestro (bo-geo-maestro/geo/atlas_muni_343.topojson)")

ATLAS = (VIZ.parent.parent / "Observatorio de Presupuesto Fiscal Departamental"
         / "_github_atlas_fiscal")
ATLAS_URL = "https://centro-de-estudios-populi.github.io/Atlas-Fiscal-Municipal/Mapa_Censo_2024_Bolivia.html"
CAT_ATLAS = ATLAS / "catalogo.json"
FECHA = "2026-09-16"
AUTOR = "Carlos Aranda"
FUENTE = {
    "2024": "Fuente: INE Bolivia, Censo de Población y Vivienda 2024.",
    "2012": "Fuente: INE Bolivia, Censo de Población y Vivienda 2012.",
    "cambio": "Fuente: INE Bolivia, Censos de Población y Vivienda 2012 y 2024.",
}
ELAB = f" Elaboración: Centro de Estudios POPULI · {AUTOR}."

if not CAT_ATLAS.exists():
    sys.exit(f"⛔ sin el catálogo del Atlas en {CAT_ATLAS}. Es la fuente de todo "
             "lo que se publica acá: título, universo, dirección y dominio.")


def leer(nombre, obligatorio=True):
    p = ATLAS / nombre
    if not p.exists():
        if obligatorio:
            sys.exit(f"⛔ falta {p}")
        return None
    return json.loads(p.read_text(encoding="utf-8"))


# --- geometría + datos ------------------------------------------------------ #
# Con el mapa maestro quedan 3 municipios SIN dato censal propio: Raqaypampa,
# Jatún Ayllu Yura y TIM. Son GAIOC cuya población el INE contabiliza dentro de
# su municipio padre, así que NO se les hereda el valor del padre —sería inventar
# un dato—: se dibujan en el gris de «sin dato». Aparecer en gris es información.
gdf = gpd.read_file(GEO)
DATA = {"2024": leer("data.json"), "2012": leer("data_2012.json")}
DEN = {"2024": leer("denominadores.json"), "2012": leer("denominadores_2012.json")}
assert DEN["2024"]["orden"] == DEN["2012"]["orden"], "los denominadores de 2012 y 2024 no comparten orden"
DEN_ORDEN = DEN["2024"]["orden"]
SIG = [s for s in gdf["sigep"]]
print(f"Geometría {len(gdf)} · datos 2024 {len(DATA['2024'])} · 2012 {len(DATA['2012'])}")

_c = json.loads(CAT_ATLAS.read_text(encoding="utf-8"))
IND = [(g["label"], i) for g in _c["grupos"] for i in g["indicadores"]]
print(f"Catálogo del Atlas: {len(IND)} indicadores · modos {MODOS}\n")


# --- la misma aritmética que el Atlas ---------------------------------------- #
def es_conteo(ind):
    return ind.get("agg") == "suma"


def v_de(anio, s, k):
    r = DATA[anio].get(s)
    v = r.get(k) if r else None
    return None if v is None or (isinstance(v, float) and np.isnan(v)) else v


def peso(anio, s, ind):
    """Ponderador de un municipio para agregar este indicador: su denominador
    propio (`den`) en el censo que se mira; población si no lo declara."""
    r = DATA[anio].get(s)
    if not r:
        return None
    D = DEN[anio]["municipios"].get(s) or DEN[anio]["municipios"].get(r.get("cod_ine"))
    den = ind.get("den")
    if not D or not den or den not in DEN_ORDEN:
        return r.get("pob_total")
    return D[DEN_ORDEN.index(den)]


def pais_de(ind, anio):
    """= aggRaw(rows, ind, DN) del HTML sobre los 343: la cifra del país."""
    agg = ind.get("agg")
    if agg == "suma":
        return sum(v for v in (v_de(anio, s, ind["key"]) for s in SIG) if v is not None)
    if agg == "no":
        return None

    def ponderado(k):
        n = d = 0.0
        for s in SIG:
            v, w = v_de(anio, s, k), peso(anio, s, ind)
            if v is not None and w is not None:
                n += v * w
                d += w
        return n / d if d else None

    if agg == "brecha" and ind.get("comp"):
        a, b = ponderado(ind["comp"][0]), ponderado(ind["comp"][1])
        return None if a is None or b is None else a - b
    return ponderado(ind["key"])


def valores(ind, modo):
    """Serie por sigep de lo que muestra el mapa en ese modo."""
    k = ind["key"]
    if modo == "cambio":
        out = {}
        for s in SIG:
            a, b = v_de("2012", s, k), v_de("2024", s, k)
            if a is None or b is None:
                out[s] = None
            else:
                out[s] = (100 * (b - a) / a if a else None) if es_conteo(ind) else b - a
        return pd.Series(out)
    return pd.Series({s: v_de(modo, s, k) for s in SIG})


def unidad_modo(ind, modo):
    u = ind.get("unit", "")
    if modo != "cambio":
        return u
    return "%" if es_conteo(ind) else ("pp" if u == "%" else u)


def formato_de(ind, modo):
    """(label_fmt, sufijo, miles) — como `fmtI`/`fmt`/`fmtD` del HTML."""
    u = unidad_modo(ind, modo)
    if modo != "cambio" and es_conteo(ind):
        return "{:.0f}", ("" if u == "hab" else " " + u), True
    if u == "%":
        return "{:.1f}", "%", False
    if u == "h/100m":
        return "{:.1f}", "", False
    return "{:.1f}", " " + u, False


def slug_de(texto):
    """Slug para los indicadores que todavía no tienen lámina. Los que ya la
    tienen conservan el suyo (`lam`)."""
    t = unicodedata.normalize("NFD", texto.lower()).encode("ascii", "ignore").decode()
    return "censo-" + re.sub(r"[^a-z0-9]+", "-", t).strip("-")


# --- publicación ------------------------------------------------------------ #
hechos, saltados, nuevos, choques = 0, [], [], {}
for grupo, ind in IND:
    col = ind["key"]
    if SOLO and col != SOLO:
        continue
    base_slug = ind.get("lam")
    if not base_slug:
        base_slug = slug_de(ind["label"])
        nuevos.append((col, base_slug))
    if base_slug in choques:
        saltados.append((col, f"su slug choca con {choques[base_slug]}"))
        continue
    choques[base_slug] = col

    for modo in MODOS:
        if modo != "2024" and not ind.get("s12"):
            continue                                   # este censo no lo puede dar
        vals = valores(ind, modo)
        con_dato = int(vals.notna().sum())
        if con_dato < 50:
            saltados.append((f"{col} [{modo}]", f"sólo {con_dato} municipios con dato"))
            continue
        gdf["_v"] = gdf["sigep"].map(vals).astype(float)

        # ── escala: dominio declarado + pivote con la regla del Atlas ──
        if modo == "cambio":
            dom = [-ind["domd"], ind["domd"]] if ind.get("domd") is not None else None
            escala = ps.escala_atlas(gdf["_v"], direccion=ind.get("dir", 0),
                                     con_signo=True, dominio=dom, piv_tipo="sin cambio")
        else:
            piv, tipo = None, None
            if not es_conteo(ind):
                piv = pais_de(ind, "2024")            # el país de 2024 en los DOS censos
                tipo = "país 2024"
            escala = ps.escala_atlas(gdf["_v"], direccion=ind.get("dir", 0),
                                     dominio=ind.get("dom"), conteo=es_conteo(ind),
                                     pivote=piv, piv_tipo=tipo)
        cmap, norm, info = escala
        fmt, suf, miles = formato_de(ind, modo)

        # ── textos ──
        uni = ind.get("universo") if ind.get("agg") != "suma" else None
        if modo == "cambio":
            titulo = f"Bolivia: {ind['label']}, cambio 2012–2024"
            if es_conteo(ind):
                sub = "Variación porcentual entre los censos de 2012 y 2024"
            elif ind.get("unit") == "%":
                sub = "Diferencia entre los censos de 2012 y 2024, en puntos porcentuales"
            else:
                sub = f"Diferencia entre los censos de 2012 y 2024, en {ind.get('unit', '')}".rstrip()
            if uni:
                sub += f" — {uni}"
            sub += ", por municipio"
        else:
            titulo = f"Bolivia: {ind['label']}" + (" (censo 2012)" if modo == "2012" else "")
            # El subtítulo es la DEFINICIÓN del catálogo más su universo: es lo
            # que hace que la lámina se entienda sola cuando viaja sin la web.
            # El universo se omite en los CONTEOS (un conteo no se divide por
            # nada) y «por municipio» no se repite si la definición ya lo dijo.
            sub = (ind.get("desc") or ind["label"]).rstrip(".")
            if uni:
                sub += f" — {uni}"
            if "municipio" not in sub.lower():
                sub += ", por municipio"

        slug = base_slug + {"2024": "", "2012": "-2012", "cambio": "-cambio"}[modo]
        tag_modo = {"2024": "censo 2024", "2012": "censo 2012", "cambio": "cambio 2012-2024"}[modo]
        enlace = f"{ATLAS_URL}#i={col}" + ("" if modo == "2024" else f"&a={modo}")

        if ENSAYO:
            hechos += 1
            print(f"  {slug:<48} {info['piv_tipo']:<12} {info['piv_real']!s:>12}  [{info['lo']:.3g}, {info['hi']:.3g}]")
            continue
        publicar(
            meta={"slug": slug, "tipo": "mapa",
                  "titulo": titulo, "subtitulo": sub,
                  "fuente": FUENTE[modo] + ELAB, "categoria": "censo",
                  "tags": [tag_modo, "municipios", col, grupo],
                  "fecha": FECHA, "formato": "red_vertical",
                  # ── vínculo declarado con el Atlas ──
                  "clave": col, "atlas": "censo", "modo": modo,
                  "anio": {"2024": "2024", "2012": "2012", "cambio": "2012-2024"}[modo],
                  "enlace": enlace, "grupo": grupo,
                  "universo": ind.get("universo"), "unidad": unidad_modo(ind, modo),
                  "escala": {k: info[k] for k in ("lo", "piv", "piv_real", "hi", "piv_tipo")}},
            df=(gdf[["sigep", "municipio", "dpto", "_v"]]
                .rename(columns={"municipio": "nombre", "_v": col}).set_index("sigep")),
            gdf=gdf, value_col="_v", sufijo=suf, label_fmt=fmt, miles=miles,
            signo=(modo == "cambio"), escala=escala,
        )
        hechos += 1

if not ENSAYO:
    build_manifest()
print(f"\n{hechos} mapas del Censo {'a publicar' if ENSAYO else 'publicados al Banco'}.")
if nuevos:
    print(f"  {len(nuevos)} son NUEVOS (no tenían lámina):")
    for col, slug in nuevos[:10]:
        print(f"     {col:<28} → {slug}")
if saltados:
    print(f"  {len(saltados)} saltados:")
    for col, por in saltados:
        print(f"     {col:<36} {por}")

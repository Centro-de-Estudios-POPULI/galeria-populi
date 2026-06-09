"""Genera los arquetipos editoriales POPULI con datos reales del IPC y los
registra en el catálogo de la galería (data/meta)."""
from __future__ import annotations
import json
import unicodedata
from pathlib import Path
import geopandas as gpd
from populi_chart import Chart, ROOT
import catalog

DATA = ROOT.parent / "populi-inflacion" / "data"
OUT = ROOT / "public" / "graficas"
SRC = "INE Bolivia — IPC base 2016"
GRAF = "Gráfico: Centro de Estudios POPULI   •   Fuente: INE Bolivia"
PROJ = "populi-inflacion"
DATE = "2026-05"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def _nrm(s):
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().strip().lower()


def yoy(serie):
    return (serie[-1]["valor"] / serie[-13]["valor"] - 1) * 100


# 1) BARRAS-TIEMPO — inflación anual, resaltando años clave
def demo_bar_timeseries():
    g = load("ipc_general.json")["indice"]
    by_year = {int(d["fecha"][:4]): d["valor"] for d in g if d["fecha"][5:7] == "12"}
    years = sorted(by_year)
    yy = [str(y) for y in years[1:]]
    infl = [(by_year[years[i]] / by_year[years[i - 1]] - 1) * 100 for i in range(1, len(years))]
    hi = [i for i, y in enumerate(yy) if y in ("2019", "2022", "2025")]
    slug = "demo-inflacion-anual"
    Chart(fmt="wide", category="Inflación",
          title="Inflación anual en Bolivia",
          highlight="2025 cierra como el año de mayor inflación en una década",
          intro="Variación de diciembre a diciembre del Índice de Precios al Consumidor",
          note="Inflación anual medida sobre el IPC (base 2016), Bolivia.",
          source=GRAF) \
        .bar_timeseries(yy, infl, highlight_idx=hi, label_fmt="{:.1f}%") \
        .save(OUT / f"{slug}.png")
    catalog.register(slug, "Inflación anual en Bolivia", "Inflación", SRC,
                     subtitle="Variación diciembre a diciembre del IPC",
                     date=DATE, tags=["inflación", "IPC", "anual", "precios"],
                     project=PROJ, fmt="wide")


# 2) RANKING — inflación interanual por división de gasto
def demo_ranking():
    div = load("ipc_divisiones.json")
    rows = [(k.split(maxsplit=1)[-1], yoy(v))
            for k, v in div.items() if k != "ÍNDICE GENERAL" and len(v) >= 13]
    labels = [r[0] for r in rows]
    vals = [r[1] for r in rows]
    slug = "demo-ranking-divisiones"
    Chart(fmt="portrait", category="Inflación",
          title="¿Qué empuja los precios?",
          highlight="Transporte y alimentos lideran el alza interanual",
          intro="Variación interanual del IPC por división de gasto",
          note="Variación de los últimos 12 meses por categoría de consumo.",
          source=GRAF) \
        .bar_ranking(labels, vals, label_fmt="{:+.1f}%") \
        .save(OUT / f"{slug}.png")
    catalog.register(slug, "¿Qué empuja los precios?", "Inflación", SRC,
                     subtitle="Inflación interanual por división de gasto",
                     date=DATE, tags=["inflación", "divisiones", "alimentos", "transporte"],
                     project=PROJ, fmt="portrait")


# 3) LÍNEA anotada — inflación interanual general
def demo_line():
    g = load("ipc_general.json")["indice"]
    f = [d["fecha"] for d in g]; v = [d["valor"] for d in g]
    xs, ys = [], []
    for i in range(12, len(v)):
        xs.append(f[i]); ys.append((v[i] / v[i - 12] - 1) * 100)
    xs, ys = xs[-60:], ys[-60:]
    slug = "demo-linea-interanual"
    Chart(fmt="wide", category="Inflación",
          title="El repunte de la inflación interanual",
          highlight=f"La inflación llega a {ys[-1]:.1f}% interanual".replace(".", ","),
          intro="Variación del IPC frente al mismo mes del año anterior",
          note="Serie mensual de los últimos 5 años.",
          source=GRAF) \
        .line_annotated(xs, ys, label_fmt="{:.1f}%") \
        .save(OUT / f"{slug}.png")
    catalog.register(slug, "El repunte de la inflación interanual", "Inflación", SRC,
                     subtitle="Variación interanual del IPC, serie mensual",
                     date=DATE, tags=["inflación", "interanual", "serie", "IPC"],
                     project=PROJ, fmt="wide")


# 4) MAPA COROPLÉTICO — inflación por departamento
def demo_choropleth():
    ciu = load("ipc_ciudades.json")
    dep_val = {}
    for _, e in ciu.items():
        if isinstance(e, dict) and e.get("departamento") and e.get("var_interanual"):
            dep_val[_nrm(e["departamento"])] = e["var_interanual"][-1]["valor"]
    gdf = gpd.read_file(DATA / "bolivia.geojson")
    gdf["valor"] = gdf["name"].map(lambda n: dep_val.get(_nrm(n)))
    gdf = gdf.dropna(subset=["valor"])
    hottest = gdf.loc[gdf["valor"].idxmax(), "name"]
    slug = "demo-mapa-inflacion"
    Chart(fmt="portrait", category="Inflación",
          title="La inflación no golpea igual a todo el país",
          highlight=f"{hottest} encabeza la inflación departamental",
          intro="Variación interanual del IPC por departamento (capital)",
          note="Proxy departamental: IPC de la ciudad capital / conurbación principal.",
          source=GRAF) \
        .choropleth(gdf, "valor", name_col="name", label_fmt="{:.1f}%") \
        .save(OUT / f"{slug}.png")
    catalog.register(slug, "La inflación no golpea igual a todo el país", "Inflación", SRC,
                     subtitle="Inflación interanual por departamento",
                     date=DATE, tags=["inflación", "mapa", "departamentos", "territorial"],
                     project=PROJ, fmt="portrait")


# 5) APILADAS — meses de inflación / estabilidad / deflación por año
def demo_stacked():
    g = load("ipc_general.json")["indice"]
    by_year = {}
    for i in range(1, len(g)):
        var = (g[i]["valor"] / g[i - 1]["valor"] - 1) * 100
        y = g[i]["fecha"][:4]
        b = by_year.setdefault(y, [0, 0, 0])
        b[0 if var > 0.2 else (2 if var < -0.2 else 1)] += 1
    years = [y for y in sorted(by_year) if sum(by_year[y]) == 12][-7:]
    series = {
        "Inflación": [by_year[y][0] for y in years],
        "Estable":   [by_year[y][1] for y in years],
        "Deflación": [by_year[y][2] for y in years],
    }
    slug = "demo-meses-inflacion"
    Chart(fmt="wide", category="Inflación",
          title="¿Cuántos meses del año suben los precios?",
          highlight="En 2025 casi todos los meses registran inflación",
          intro="Meses con inflación, estabilidad o deflación mensual, por año",
          note="Clasificación de la variación mensual del IPC general (umbral ±0,2%).",
          source=GRAF) \
        .stacked_bar(years, series, label_fmt="{:.0f}", min_label=1) \
        .save(OUT / f"{slug}.png")
    catalog.register(slug, "¿Cuántos meses del año suben los precios?", "Inflación", SRC,
                     subtitle="Meses de inflación, estabilidad o deflación por año",
                     date=DATE, tags=["inflación", "mensual", "estacionalidad"],
                     project=PROJ, fmt="wide")


# 6) DOT PLOT — inflación por ciudad: hace un año vs ahora
def demo_dotplot():
    ciu = load("ipc_ciudades.json")
    labels, a, b = [], [], []
    for city, e in ciu.items():
        if not (isinstance(e, dict) and e.get("var_interanual")):
            continue
        vi = e["var_interanual"]
        if len(vi) < 13 or _nrm(city) == "bolivia":
            continue
        labels.append(e.get("departamento", city)); a.append(vi[-13]["valor"]); b.append(vi[-1]["valor"])
    n_baja = sum(1 for x, y in zip(a, b) if y < x)
    slug = "demo-dotplot-ciudades"
    Chart(fmt="portrait", category="Inflación",
          title="La inflación cede frente a su pico",
          highlight=f"En {n_baja} de {len(labels)} ciudades la inflación es menor que hace un año",
          intro="Inflación interanual por ciudad: hace 12 meses vs. dato más reciente",
          note="Comparación de la variación interanual del IPC por ciudad capital.",
          source=GRAF) \
        .dot_plot(labels, a, b, a_name="Hace un año", b_name="Ahora", label_fmt="{:.0f}%") \
        .save(OUT / f"{slug}.png")
    catalog.register(slug, "La inflación cede frente a su pico", "Inflación", SRC,
                     subtitle="Inflación por ciudad: hace un año vs. ahora",
                     date=DATE, tags=["inflación", "ciudades", "comparación"],
                     project=PROJ, fmt="portrait")


if __name__ == "__main__":
    for fn in (demo_bar_timeseries, demo_ranking, demo_line,
               demo_choropleth, demo_stacked, demo_dotplot):
        fn()

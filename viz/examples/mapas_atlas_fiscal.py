"""
Publica los mapas del ATLAS FISCAL MUNICIPAL (IGF) al Banco de Gráficos.
30 indicadores fiscales, gestión 2025, por municipio.

Fuente de datos: los `const MUN_DATA` / `INDICATORS` embebidos en el HTML del
Atlas (repo Centro-de-Estudios-POPULI/Atlas-Fiscal-Municipal). Se extraen con un
parser brace-matching (respeta strings) y se unen por `sigep` a la MISMA geometría
que usan los mapas del Censo (viz/geo/bolivia_municipios_sigep.topojson), para
mantener una sola llave territorial en todo el Banco.

Política del Banco: solo se publica la imagen, no los datos crudos.
"""
import re
import sys
import json
from pathlib import Path
import geopandas as gpd
import pandas as pd

VIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VIZ))
from catalogo import publicar, build_manifest
import populi_style as ps

# El Atlas Fiscal dejó de tener los datos embebidos en el HTML: ahora publica
# `fiscal_data.json` (343 entidades × 30 indicadores × 10 gestiones) y
# `fiscal_catalogo.json` (años + grupos de indicadores). Leerlos es más robusto
# que scrapear `const MUN_DATA` del HTML, que es como se hacía y ya no funciona.
ATLAS_DIR = Path(r"C:\Users\HP\OneDrive\Desktop\Proyectos\Observatorio de Presupuesto Fiscal Departamental\_github_atlas_fiscal")
ATLAS_DATA = ATLAS_DIR / "fiscal_data.json"
ATLAS_CAT = ATLAS_DIR / "fiscal_catalogo.json"

# Mapa MAESTRO: 343 municipios (339 del OEP + los 4 GAIOC de conversión total).
# El anterior tenía 339 y dejaba fuera a Raqaypampa, Jatún Ayllu Yura, TIM y
# San Pedro de Macha. Fuente: Proyectos/bo-geo-maestro, clave de join `sigep`.
GEO = VIZ.parent.parent / "bo-geo-maestro" / "geo" / "atlas_muni_343.topojson"
if not GEO.exists():
    GEO = VIZ / "geo" / "atlas_muni_343.topojson"
YEAR = "2025"
FECHA = "2026-06-09"
AUTOR = "Carlos Aranda"   # investigador/a responsable (a futuro puede variar por gráfico)
FUENTE = ("Fuente: Ministerio de Economía y Finanzas Públicas, ejecución "
          f"presupuestaria municipal (IGF). Elaboración: Centro de Estudios POPULI · {AUTOR}.")


# --- extracción brace-matching de los `const X = {...}` / [...] -------------- #
def extraer(name, html):
    m = re.search(r"const\s+" + name + r"\s*=\s*", html)
    i = m.end()
    open_c = html[i]
    close_c = {"{": "}", "[": "]"}[open_c]
    depth = 0
    instr = False
    esc = False
    j = i
    while j < len(html):
        c = html[j]
        if instr:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                instr = False
        else:
            if c == '"':
                instr = True
            elif c == open_c:
                depth += 1
            elif c == close_c:
                depth -= 1
                if depth == 0:
                    j += 1
                    break
        j += 1
    return json.loads(html[i:j])


MUN = json.loads(ATLAS_DATA.read_text(encoding="utf-8"))
CAT = json.loads(ATLAS_CAT.read_text(encoding="utf-8"))

# El catálogo agrupa los indicadores; el script los quiere planos, con `id` y el
# nombre del grupo en `grp` (que va a las etiquetas de la ficha).
INDS = [{**i, "id": i["key"], "grp": g["label"]}
        for g in CAT["grupos"] for i in g["indicadores"]]

# Cada indicador viene como una serie de 10 valores, uno por gestión.
ANIOS = CAT["anios"]
YI = ANIOS.index(int(YEAR))
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
# Población de la gestión: es el PESO del pivote (promedio nacional ponderado),
# igual que el `agg(rows,ind,yi)` del atlas fiscal, que divide por r.pob[yi].
vals["_pob"] = pd.Series({s: (m.get("pob") or [None])[YI]
                          if isinstance(m.get("pob"), list) and len(m["pob"]) > YI else None
                          for s, m in MUN.items()})
gdf = gdf.merge(vals, left_on="sigep", right_index=True, how="left")
algun = [i["id"] for i in INDS if i["id"] in gdf.columns]
cobertura = gdf[algun[0]].notna().sum() if algun else 0
print(f"Unidos {cobertura}/{len(gdf)} municipios con datos {YEAR}.\n")

# --- títulos legibles (el `label` técnico del Atlas va al subtítulo) --------- #
TITULOS = {
    "cp_it": "Dependencia de la Coparticipación Tributaria",
    "idh_it": "Dependencia del IDH (renta hidrocarburífera)",
    "rp_it": "Autonomía fiscal: recursos propios",
    "rc_it": "Peso de los recursos de capital",
    "rc_ic": "Recursos de capital sobre el ingreso corriente",
    "cp_ic": "Coparticipación sobre el ingreso corriente",
    "idh_ic": "IDH sobre el ingreso corriente",
    "rp_ic": "Recursos propios sobre el ingreso corriente",
    "gc_gt": "Peso del gasto corriente",
    "ge_gt": "Esfuerzo de inversión pública",
    "f1_gt": "Carga de deuda financiera en el gasto",
    "f2_gt": "Carga de deuda flotante en el gasto",
    "s_adm": "Gasto en administración general",
    "s_edu": "Gasto en educación",
    "s_sal": "Gasto en salud",
    "s_eco": "Gasto en sectores económicos",
    "s_viv": "Gasto en vivienda e infraestructura",
    "s_prt": "Gasto en protección social",
    "s_seg": "Gasto en seguridad ciudadana",
    "s_med": "Gasto en medio ambiente",
    "s_cul": "Gasto en cultura y deporte",
    "it_pc": "Ingreso total por habitante",
    "sl_pc": "Gasto en salud por habitante",
    "ed_pc": "Gasto en educación por habitante",
    "inv_pc": "Inversión pública por habitante",
    "ic_pc": "Ingreso corriente por habitante",
    "rpf_ic": "Resultado fiscal antes de financiamiento",
    "dcj_ic": "Déficit de caja",
    "f1_it": "Deuda financiera sobre el ingreso total",
    "op_it": "Acumulación de deuda flotante (cuentas por pagar)",
}


# La paleta por nombre quedó obsoleta para estos mapas: ahora todos usan la MISMA
# escala del atlas de la página (una sola rampa divergente, orientada por `dir` y
# anclada en el promedio nacional ponderado). Con eso el rojo marca siempre el
# lado malo, y un municipio se lee igual en el Banco que en el Atlas.
def escala_de(ind):
    return ps.escala_atlas(gdf[ind["id"]], pesos=gdf["_pob"],
                           direccion=ind.get("dir", 0), con_signo=bool(ind.get("div")))


n = 0
for ind in INDS:
    iid = ind["id"]
    if iid not in gdf.columns:
        print(f"  (omitido {iid}: sin datos {YEAR})")
        continue
    unidad = ind.get("unit", "")
    pct = unidad == "%"
    sufijo = "%" if pct else (" Bs" if unidad.startswith("Bs") else "")
    titulo = TITULOS.get(iid, ind["label"])
    # la fuente "Public Sans" no tiene la delta griega (ΔCxP); la deletreamos
    etiqueta = ind["label"].replace("ΔCxP", "variación de cuentas por pagar")
    subtitulo = f"{etiqueta} ({unidad}) — por municipio · gestión {YEAR}"
    datos = gdf[["sigep", "municipio", "dpto", iid]].rename(
        columns={"municipio": "nombre"}).set_index("sigep")
    publicar(
        meta={"slug": f"fiscal-{iid.replace('_', '-')}", "tipo": "mapa",
              "titulo": f"Bolivia: {titulo}", "subtitulo": subtitulo,
              "fuente": FUENTE, "categoria": "fiscal",
              "tags": ["atlas fiscal", f"igf {YEAR}", "municipios", ind["grp"], iid],
              "fecha": FECHA, "formato": "red_vertical"},
        df=datos, gdf=gdf, value_col=iid, escala=escala_de(ind),
        # Un decimal en los porcentajes, igual que la página.
        sufijo=sufijo, label_fmt="{:.1f}" if pct else "{:.0f}",
    )
    n += 1

build_manifest()
print(f"\n{n} mapas del Atlas Fiscal publicados al Banco (gestión {YEAR}).")

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

ATLAS = Path(r"C:\Users\HP\OneDrive\Desktop\Proyectos\Observatorio de Presupuesto Fiscal Departamental\_github_atlas_fiscal\mapa.html")
GEO = VIZ / "geo" / "bolivia_municipios_sigep.topojson"
YEAR = "2025"
FECHA = "2026-06-09"
FUENTE = ("Fuente: Ministerio de Economía y Finanzas Públicas, ejecución "
          "presupuestaria municipal (IGF). Elaboración: Centro de Estudios POPULI.")


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


html = ATLAS.read_text(encoding="utf-8")
MUN = extraer("MUN_DATA", html)
INDS = extraer("INDICATORS", html)
print(f"Atlas: {len(MUN)} entidades · {len(INDS)} indicadores · gestión {YEAR}")

# --- geometría + tabla ancha de valores del año, unida por sigep ------------ #
gdf = gpd.read_file(GEO)                              # sigep, municipio, dpto, geom
filas = {}
for sigep, m in MUN.items():
    yr = m.get("y", {}).get(YEAR)
    if yr:
        filas[sigep] = yr
vals = pd.DataFrame.from_dict(filas, orient="index")
vals.index.name = "sigep"
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


def paleta_de(ind):
    if ind.get("div"):                # variables con signo → divergente en 0
        return "divergente"
    d = ind.get("dir", 0)
    return {1: "verde", -1: "calido"}.get(d, "azul")


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
        df=datos, gdf=gdf, value_col=iid, paleta=paleta_de(ind),
        sufijo=sufijo, label_fmt="{:.0f}",
    )
    n += 1

build_manifest()
print(f"\n{n} mapas del Atlas Fiscal publicados al Banco (gestión {YEAR}).")

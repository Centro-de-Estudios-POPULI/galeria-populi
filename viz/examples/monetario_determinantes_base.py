"""
Determinantes de la BASE MONETARIA del BCB (barras apiladas de contribución).

¿De qué fuente nace cada boliviano de base monetaria? Reservas internacionales,
crédito al sector público, crédito a bancos, OMA (se resta) y otras cuentas.
Vista en % de la base: hace inconfundible el cambio de régimen — de un dinero
sobre-respaldado en reservas (2005–2014) a uno creado por crédito al sector
público (dominancia fiscal, 2019→).

Datos reales: `populi-monetario/data/determinantes_base.json` (cuadro oficial
del BCB). Resolución ANUAL (dic. de cada año + último dato) para legibilidad.
Política del Banco: solo se publica la imagen.
"""
import sys
import json
from pathlib import Path
import pandas as pd

VIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VIZ))
from catalogo import publicar, build_manifest

SRC = Path(r"C:\Users\HP\OneDrive\Desktop\Proyectos\populi-monetario\data\determinantes_base.json")
FECHA = "2026-06-29"
AUTOR = "Carlos Aranda"
FUENTE = ("Fuente: Banco Central de Bolivia (BCB), Base Monetaria, Determinantes y "
          f"Componentes. Elaboración: Centro de Estudios POPULI · {AUTOR}.")

raw = json.loads(SRC.read_text(encoding="utf-8"))
serie = {o["date"]: o for o in raw["series"]}

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
_ud = raw["metadata"]["ultimo_dato"]            # "2026-04"
ULTIMA = f"{MESES[int(_ud[5:7]) - 1]} {_ud[:4]}"

# Snapshot anual: diciembre de cada año; para el año en curso, el último dato.
filas = []
y0 = 2005
y1 = int(_ud[:4])
for y in range(y0, y1 + 1):
    o = serie.get(f"{y}-12") or (serie[_ud] if y == y1 else None)
    if o is None:
        continue
    filas.append({
        "x": y,
        "rin": o["rin"],
        "cred_sp": o["cred_sp"],
        "cred_bancos": o["cred_bancos"],
        "oma_neg": -o["oma"],          # la OMA se RESTA → contribución negativa
        "otras": o["otras"],
        "base": o["base"],
    })
df = pd.DataFrame(filas).set_index("x").sort_index()
ult = df.iloc[-1]
print(f"{len(df)} años · último (base={ult.base:,.0f}): "
      f"RIN={ult.rin/ult.base:.0%}  CredSP={ult.cred_sp/ult.base:.0%}  "
      f"OMA={ult.oma_neg/ult.base:.0%}")

SERIES = ["rin", "cred_sp", "cred_bancos", "oma_neg", "otras"]
ETIQUETAS = ["Reservas Int. Netas", "Crédito al Sector Público", "Crédito a Bancos",
             "OMA (se resta)", "Otras Cuentas (Neto)"]
COLORES = ["serie_azul", "rojo", "serie_teal", "oro", "pizarra"]

# Tres regímenes (divisores en los años de quiebre).
FASES = [
    {"x0": y0, "x1": 2017, "texto": "Sobre-respaldo\nen reservas", "ha": "center"},
    {"x0": 2017, "x1": 2019, "texto": "Inflexión", "ha": "center"},
    {"x0": 2019, "x1": y1, "texto": "Dominancia\nfiscal", "ha": "center"},
]

publicar(
    meta={"slug": "monetario-determinantes-base", "tipo": "barras_apiladas",
          "titulo": "Bolivia: ¿De dónde nace el dinero que emite el BCB?",
          "subtitulo": f"Determinantes de la base monetaria, como % de la base · datos a {ULTIMA}",
          "nota": ("OMA = operaciones de mercado abierto (se restan, retiran liquidez). "
                   "Otras cuentas (neto) = patrimonio del BCB, deuda externa de largo plazo "
                   "y partidas netas. Los componentes suman el 100% de la base."),
          "fuente": FUENTE, "categoria": "monetario",
          "tags": ["base monetaria", "determinantes", "reservas internacionales",
                   "crédito al sector público", "dominancia fiscal", "bcb"],
          "fecha": FECHA, "formato": "red_cuadrada"},
    df=df,
    series=SERIES, etiquetas=ETIQUETAS, colores=COLORES,
    normalizar=True, y_sufijo="%", ancho=0.86,
    referencia=100, referencia_label="Base monetaria = 100%",
    fases=FASES, headroom_top=0.10, headroom_bottom=0.40,
    leyenda_loc="lower center", leyenda_ncol=3,
)

build_manifest()
print("\nDeterminantes de la base monetaria publicados al Banco.")

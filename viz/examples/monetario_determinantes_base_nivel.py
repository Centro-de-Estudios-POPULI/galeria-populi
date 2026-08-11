"""
Determinantes de la BASE MONETARIA del BCB — versión NIVEL (millones de Bs).

Misma descomposición que `monetario_determinantes_base.py` (que va en % de la
base), pero en NIVEL y serie MENSUAL desde 2005, en formato horizontal ancho.
Muestra a la vez el TAMAÑO (la base explota ~18×) y la COMPOSICIÓN (de reservas
a crédito al sector público). La línea negra es la base monetaria total.

Datos reales: `populi-monetario/data/determinantes_base.json` (cuadro oficial
del BCB). Política del Banco: solo se publica la imagen.
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
FUENTE = (f"Fuente: BCB (Base Monetaria, Determinantes y Componentes). "
          f"Elaboración: Centro de Estudios POPULI · {AUTOR}.")

raw = json.loads(SRC.read_text(encoding="utf-8"))
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
_ud = raw["metadata"]["ultimo_dato"]            # "2026-04"
ULTIMA = f"{MESES[int(_ud[5:7]) - 1]} {_ud[:4]}"


def to_x(d):                                    # "2005-03" -> 2005 + 2/12
    y, m = int(d[:4]), int(d[5:7])
    return y + (m - 1) / 12.0


filas = []
for o in raw["series"]:
    if o["date"] < "2005-01":
        continue
    filas.append({
        "x": to_x(o["date"]),
        "rin": o["rin"],
        "cred_sp": o["cred_sp"],
        "cred_bancos": o["cred_bancos"],
        "oma_neg": -o["oma"],          # la OMA se RESTA → contribución negativa
        "otras": o["otras"],
        "base": o["base"],
    })
df = pd.DataFrame(filas).set_index("x").sort_index()
ult = df.iloc[-1]
print(f"{len(df)} meses · base={ult.base:,.0f} MM (RIN={ult.rin:,.0f}  "
      f"CredSP={ult.cred_sp:,.0f}  OMA=-{-ult.oma_neg:,.0f})")

SERIES = ["rin", "cred_sp", "cred_bancos", "oma_neg", "otras"]
ETIQUETAS = ["Reservas Int. Netas", "Crédito al Sector Público", "Crédito a Bancos",
             "OMA (se resta)", "Otras Cuentas (Neto)"]
# Paleta editorial sobria (sin el royal/celeste #2563EB): azul petróleo profundo
# para reservas, rojo de marca para el crédito al SP (protagonista), verde bosque,
# oro y gris cálido para "Otras" (distinto del azul, no otro azul-gris).
# Cinco matices distinguibles incluso atenuados por la transparencia.
COLORES = ["#355F7A", "rojo", "#2E7D4F", "oro", "#8C8378"]

X_FIN = ult.name
FASES = [
    {"x0": 2005, "x1": 2017, "texto": "Sobre-respaldo en reservas", "ha": "center"},
    {"x0": 2017, "x1": 2019, "texto": "Inflexión", "ha": "center"},
    {"x0": 2019, "x1": X_FIN, "texto": "Dominancia fiscal", "ha": "center"},
]

publicar(
    meta={"slug": "monetario-determinantes-base-nivel", "tipo": "barras_apiladas",
          "titulo": "Bolivia: ¿De dónde nace el dinero que emite el BCB?",
          "subtitulo": f"Determinantes de la base monetaria · millones de Bs · serie mensual · datos a {ULTIMA}",
          "nota": ("OMA = operaciones de mercado abierto (se restan). Otras cuentas (neto) = "
                   "patrimonio del BCB, deuda externa de largo plazo y otras partidas. "
                   "Línea negra = base monetaria."),
          "fuente": FUENTE, "categoria": "monetario",
          "tags": ["base monetaria", "determinantes", "reservas internacionales",
                   "crédito al sector público", "dominancia fiscal", "bcb"],
          "fecha": FECHA, "formato": "informe_horizontal"},
    df=df,
    series=SERIES, etiquetas=ETIQUETAS, colores=COLORES,
    normalizar=False, y_miles=True, y_sufijo="", ancho=1.0, x_anios=True,
    alpha=0.58, total_lw=1.7, fuente_scale=0.8,
    total="base", total_label="Base monetaria", total_color="tinta",
    fases=FASES, headroom_top=0.10, headroom_bottom=0.20,
    leyenda_loc="lower center", leyenda_ncol=3,
)

build_manifest()
print("\nDeterminantes de la base monetaria (nivel, mensual) publicados al Banco.")

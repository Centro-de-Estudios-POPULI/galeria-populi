"""
Composición de las RESERVAS INTERNACIONALES del BCB (áreas apiladas).
Divisas, Oro y Otros (DEG + posición en el FMI), en millones de USD.

Datos reales: `populi-monetario/data/reservas_rin.json`. Relato por etapas:
el auge de materias primas (divisas), el descenso, y el agotamiento de las
divisas que deja al oro como sostén de la reserva.

Formato CUADRADO (1080×1080) — más legible que el vertical para series con
varias bandas. Política del Banco: solo se publica la imagen.
"""
import re
import sys
import json
from pathlib import Path
import pandas as pd

VIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VIZ))
from catalogo import publicar, build_manifest

SRC = Path(r"C:\Users\HP\OneDrive\Desktop\Proyectos\populi-monetario\data\reservas_rin.json")
FECHA = "2026-06-09"
FUENTE = ("Fuente: Banco Central de Bolivia (BCB), Estadísticas Semanales. "
          "Elaboración: Centro de Estudios POPULI.")

raw = json.loads(SRC.read_text(encoding="utf-8"))

# última fecha de la serie, en español (ultimo_dato = "2026-05-S4")
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
_ud = raw["metadata"]["ultimo_dato"]
ULTIMA = f"{MESES[int(_ud[5:7]) - 1]} {_ud[:4]}"


def to_x(d):
    m = re.match(r"^(\d{4})-(\d{2})(?:-S(\d))?$", d)
    y, mo, wk = int(m[1]), int(m[2]), m[3]
    frac = (int(wk) / 4.345) if wk else 0.0
    return y + (mo - 1 + frac) / 12


def num(v):
    return float(v) if v is not None else 0.0


filas = []
for o in raw["series"]:
    if o.get("rib") is None:
        continue
    otros = num(o.get("deg")) + num(o.get("fmi"))
    filas.append((to_x(o["date"]), num(o.get("divisas")), num(o.get("oro")), otros))
df = pd.DataFrame(filas, columns=["x", "divisas", "oro", "otros"]).set_index("x").sort_index()
ult = df.iloc[-1]
print(f"Composición: {len(df)} obs · último: divisas={ult.divisas:,.0f}  "
      f"oro={ult.oro:,.0f}  otros={ult.otros:,.0f}  (oro={ult.oro/(ult.sum()):.0%})")

# eventos/etapas estilo F&D: banda translúcida + etiqueta con guía y círculo.
# Fases reales (verificadas en los datos): auge hasta el PICO (nov-2014, 15.477 MM),
# decadencia hasta el piso (oct-2023), y revalorización del oro desde ~2024.
# ly = altura de la etiqueta (millones USD); dx = offset horizontal (>0 = derecha).
PICO = 2014 + 10 / 12  # noviembre 2014
EVENTOS = [
    {"x0": 2006, "x1": PICO, "texto": "Auge de\nmaterias primas", "ly": 12800,
     "dx": -8.4, "color": "serie_teal", "alpha": 0.12},
    {"x0": PICO, "x1": 2024, "texto": "Decadencia", "ly": 13400,
     "dx": 1.6, "color": "rojo", "alpha": 0.08},
    {"x0": 2024, "x1": df.index[-1], "texto": "Revalorización\ndel oro", "ly": 11000,
     "cx": 2024.6, "dx": 0.7, "color": "oro", "alpha": 0.16},
]

publicar(
    meta={"slug": "monetario-reservas-composicion", "tipo": "areas",
          "titulo": "Bolivia: ¿De qué están hechas las reservas del BCB?",
          "subtitulo": f"Reservas Internacionales Brutas por componente — millones de USD · datos a {ULTIMA}",
          "nota": "Otros = Derechos Especiales de Giro (DEG) y posición de reserva en el FMI.",
          "fuente": FUENTE, "categoria": "monetario",
          "tags": ["reservas internacionales", "oro", "divisas", "bcb", "composición"],
          "fecha": FECHA, "formato": "red_cuadrada"},
    df=df,
    series=["divisas", "oro", "otros"],
    etiquetas=["Divisas", "Oro", "Otros"],
    colores=["azul", "oro", "cafe"],
    y_sufijo="", normalizar=False, eventos=EVENTOS,
)

build_manifest()
print("\nComposición de reservas publicada al Banco.")

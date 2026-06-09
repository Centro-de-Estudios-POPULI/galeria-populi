"""Demo de los tipos de gráfico (barras, ranking, áreas, línea) en red_cuadrada."""
import sys
from pathlib import Path
import pandas as pd

VIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VIZ)); sys.path.insert(0, str(VIZ / "charts"))
import populi_style as ps
from barras import grafico_barras, grafico_barras_ranking
from areas import grafico_areas
from lineas import grafico_lineas

OUT = VIZ / "output"

# --- barras verticales: inflación anual ------------------------------------ #
anios = list(range(2015, 2026))
infl = [3.0, 4.0, 2.7, 1.5, 1.5, 0.7, 0.9, 3.1, 2.0, 9.0, 12.5]
grafico_barras(
    anios, infl, color="rojo", resaltar=[len(anios) - 1],
    titulo="La inflación cierra 2025 en su nivel más alto en una década",
    subtitulo="Variación anual del IPC, en %",
    fuente="Fuente: INE Bolivia. Elaboración: Centro de Estudios POPULI.",
    y_decimales=1, y_sufijo="%", archivo=str(OUT / "demo_barras.png"))

# --- ranking horizontal: variación por división ---------------------------- #
divisiones = ["Alimentos y bebidas", "Transporte", "Vivienda y servicios",
              "Salud", "Educación", "Restaurantes y hoteles", "Comunicaciones",
              "Recreación y cultura"]
var = [18.2, 11.4, 6.1, 5.0, 3.2, 9.8, -1.2, 2.1]
grafico_barras_ranking(
    divisiones, var, resaltar_top=3,
    titulo="Alimentos y transporte lideran el alza de precios en 2025",
    subtitulo="Variación interanual por división del IPC, en %",
    fuente="Fuente: INE Bolivia. Elaboración: Centro de Estudios POPULI.",
    archivo=str(OUT / "demo_ranking.png"))

# --- áreas apiladas: composición del gasto --------------------------------- #
df_a = pd.DataFrame({
    "Corriente": [62, 63, 65, 66, 68, 70],
    "Capital":   [30, 29, 27, 26, 24, 22],
    "Deuda":     [8, 8, 8, 8, 8, 8],
}, index=[2020, 2021, 2022, 2023, 2024, 2025])
grafico_areas(
    df_a, series=["Corriente", "Capital", "Deuda"], normalizar=True,
    colores=["rojo", "azul", "oro"],
    titulo="El gasto corriente gana peso en el presupuesto",
    subtitulo="Composición del gasto público, en % del total",
    fuente="Fuente: Ministerio de Economía. Elaboración: Centro de Estudios POPULI.",
    archivo=str(OUT / "demo_areas.png"))

# --- línea simple con punto final destacado -------------------------------- #
df_l = pd.DataFrame({
    "tc": [6.96] * 8 + [7.1, 7.6, 8.4, 9.2, 10.1, 11.3, 12.0],
}, index=list(range(2010, 2025)))
grafico_lineas(
    df_l, series=[{"y": "tc", "label": "Paralelo", "color": "rojo"}],
    destacar_fin=True, y_decimales=2,
    titulo="El tipo de cambio paralelo se dispara sobre el oficial",
    subtitulo="Bolivianos por dólar (promedio anual)",
    fuente="Fuente: estimaciones del Centro de Estudios POPULI.",
    archivo=str(OUT / "demo_linea.png"))

print("Listo: demo_barras / demo_ranking / demo_areas / demo_linea")

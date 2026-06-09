"""
Showcase del sistema final (Zilla Slab + Public Sans), formato vertical.
Gráfico estrella (líneas + bandas) + los 4 tipos, todo con el estándar POPULI.
"""
import sys
from pathlib import Path
import pandas as pd

VIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VIZ)); sys.path.insert(0, str(VIZ / "charts"))
import populi_style as ps
from lineas_bandas import grafico_lineas_bandas
from barras import grafico_barras, grafico_barras_ranking
from areas import grafico_areas
from lineas import grafico_lineas

OUT = VIZ / "output"

# --- estrella: líneas + bandas --------------------------------------------- #
meses = list(range(13))
df_h = pd.DataFrame({
    "debil":[0.00,0.06,0.085,0.11,0.11,0.135,0.185,0.19,0.195,0.205,0.235,0.265,0.315],
    "debil_lo":[0.00,0.02,0.04,0.07,0.08,0.10,0.13,0.14,0.15,0.16,0.175,0.20,0.225],
    "debil_hi":[0.00,0.11,0.16,0.22,0.245,0.27,0.315,0.34,0.37,0.41,0.45,0.49,0.52],
    "fuerte":[0.00,0.045,0.06,0.03,0.005,0.025,0.045,0.02,-0.01,-0.035,-0.03,-0.035,-0.005],
    "fuerte_lo":[0.00,-0.04,-0.07,-0.10,-0.155,-0.15,-0.10,-0.16,-0.20,-0.215,-0.20,-0.205,-0.215],
    "fuerte_hi":[0.00,0.09,0.12,0.13,0.135,0.15,0.165,0.17,0.175,0.185,0.19,0.195,0.20],
}, index=meses)
grafico_lineas_bandas(
    df_h, series=[
        {"y":"debil","lo":"debil_lo","hi":"debil_hi","label":"Anclaje\ndébil","color":"rojo"},
        {"y":"fuerte","lo":"fuerte_lo","hi":"fuerte_hi","label":"Anclaje\nfuerte","color":"azul"}],
    titulo="Los choques en precios de importación elevan la inflación donde el anclaje es débil",
    subtitulo="Efecto acumulado sobre el IPC, en puntos porcentuales", eje_x="Meses",
    fuente="Fuente: estimaciones del Centro de Estudios POPULI.",
    nota="Efecto acumulado ante un deterioro de 1 punto en los términos de intercambio.",
    y_decimales=2, archivo=str(OUT / "set_lineas_bandas.png"))

# --- barras verticales ----------------------------------------------------- #
anios = list(range(2015, 2026))
grafico_barras(anios, [3.0,4.0,2.7,1.5,1.5,0.7,0.9,3.1,2.0,9.0,12.5],
    color="rojo", resaltar=[len(anios)-1], y_decimales=1, y_sufijo="%",
    titulo="La inflación cierra 2025 en su nivel más alto en una década",
    subtitulo="Variación anual del IPC, en %",
    fuente="Fuente: INE Bolivia. Elaboración: Centro de Estudios POPULI.",
    archivo=str(OUT / "set_barras.png"))

# --- ranking horizontal ---------------------------------------------------- #
grafico_barras_ranking(
    ["Alimentos y bebidas","Transporte","Vivienda y servicios","Salud","Educación",
     "Restaurantes y hoteles","Comunicaciones","Recreación y cultura"],
    [18.2,11.4,6.1,5.0,3.2,9.8,-1.2,2.1], resaltar_top=3,
    titulo="Alimentos y transporte lideran el alza de precios en 2025",
    subtitulo="Variación interanual por división del IPC, en %",
    fuente="Fuente: INE Bolivia. Elaboración: Centro de Estudios POPULI.",
    archivo=str(OUT / "set_ranking.png"))

# --- áreas apiladas -------------------------------------------------------- #
df_a = pd.DataFrame({"Corriente":[62,63,65,66,68,70],"Capital":[30,29,27,26,24,22],
                     "Deuda":[8,8,8,8,8,8]}, index=[2020,2021,2022,2023,2024,2025])
grafico_areas(df_a, series=["Corriente","Capital","Deuda"], normalizar=True,
    colores=["rojo","azul","oro"],
    titulo="El gasto corriente gana peso en el presupuesto",
    subtitulo="Composición del gasto público, en % del total",
    fuente="Fuente: Ministerio de Economía. Elaboración: Centro de Estudios POPULI.",
    archivo=str(OUT / "set_areas.png"))

# --- línea simple ---------------------------------------------------------- #
df_l = pd.DataFrame({"tc":[6.96]*8+[7.1,7.6,8.4,9.2,10.1,11.3,12.0]}, index=list(range(2010,2025)))
grafico_lineas(df_l, series=[{"y":"tc","label":"Paralelo","color":"rojo"}],
    destacar_fin=True, y_decimales=2,
    titulo="El tipo de cambio paralelo se dispara sobre el oficial",
    subtitulo="Bolivianos por dólar (promedio anual)",
    fuente="Fuente: estimaciones del Centro de Estudios POPULI.",
    archivo=str(OUT / "set_linea.png"))

print("Showcase del sistema final listo (5 gráficas).")

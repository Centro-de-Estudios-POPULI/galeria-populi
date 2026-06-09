"""
Demo: reproducción del gráfico del FMI (choques de importación e inflación)
con la identidad POPULI. Se renderiza en dos variantes de titular —serif
Playfair y grotesca Archivo— para comparar la dirección estética.
"""
import sys
from pathlib import Path
import pandas as pd

VIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VIZ))
sys.path.insert(0, str(VIZ / "charts"))
import populi_style as ps
from lineas_bandas import grafico_lineas_bandas

# --- datos (aprox. de la figura original del FMI), meses 0..12 -------------- #
meses = list(range(13))
debil      = [0.00, 0.06, 0.085, 0.11, 0.11, 0.135, 0.185, 0.19, 0.195, 0.205, 0.235, 0.265, 0.315]
debil_lo   = [0.00, 0.02, 0.04,  0.07, 0.08, 0.10,  0.13,  0.14, 0.15,  0.16,  0.175, 0.20,  0.225]
debil_hi   = [0.00, 0.11, 0.16,  0.22, 0.245,0.27,  0.315, 0.34, 0.37,  0.41,  0.45,  0.49,  0.52]
fuerte     = [0.00, 0.045,0.06,  0.03, 0.005,0.025, 0.045, 0.02,-0.01, -0.035,-0.03, -0.035,-0.005]
fuerte_lo  = [0.00,-0.04,-0.07, -0.10,-0.155,-0.15,-0.10, -0.16,-0.20, -0.215,-0.20, -0.205,-0.215]
fuerte_hi  = [0.00, 0.09, 0.12,  0.13, 0.135,0.15,  0.165, 0.17, 0.175, 0.185, 0.19,  0.195, 0.20]

df = pd.DataFrame({
    "debil": debil, "debil_lo": debil_lo, "debil_hi": debil_hi,
    "fuerte": fuerte, "fuerte_lo": fuerte_lo, "fuerte_hi": fuerte_hi,
}, index=meses)

series = [
    {"y": "debil",  "lo": "debil_lo",  "hi": "debil_hi",
     "label": "Anclaje\ndébil",  "color": "rojo"},
    {"y": "fuerte", "lo": "fuerte_lo", "hi": "fuerte_hi",
     "label": "Anclaje\nfuerte", "color": "azul"},
]

comun = dict(
    df=df, series=series,
    titulo="Los choques en precios de importación elevan la inflación, sobre todo donde el anclaje de expectativas es débil",
    subtitulo="Efecto acumulado sobre el IPC, en puntos porcentuales",
    eje_x="Meses",
    fuente="Fuente: Haver Analytics, Consensus Economics y estimaciones del Centro de Estudios POPULI.",
    nota="Efecto acumulado de la inflación ante un deterioro de 1 punto porcentual en los términos de intercambio. Anclaje fuerte = percentil 75 del índice; anclaje débil = percentil 25.",
    formato="red_cuadrada",
    y_decimales=2,
)

# Variante A — titular serif (Playfair Display, como el sitio)
grafico_lineas_bandas(**comun, titulo_familia=ps.TITLE_SERIF,
                      archivo=str(VIZ / "output" / "demo_fmi_serif.png"))

# Variante B — titular grotesca (Archivo, como el FMI)
grafico_lineas_bandas(**comun, titulo_familia=ps.TITLE_SANS,
                      archivo=str(VIZ / "output" / "demo_fmi_sans.png"))

print("Listo: output/demo_fmi_serif.png  y  output/demo_fmi_sans.png")

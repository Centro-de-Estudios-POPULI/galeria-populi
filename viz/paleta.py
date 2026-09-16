"""
POPULI — paleta de colores oficial. FUENTE ÚNICA DE VERDAD.

Origen: documento «Paleta de colores» (Carlos Aranda), validado el 2026-08-08 con el
validador de la skill dataviz sobre superficie clara #FAF8F3 y oscura #0B0E13.

NO editar los valores en los repos que la usan: se copia este archivo tal cual.
Si algo tiene que cambiar, cambia acá y se re-copia.

Sitio espejo en CSS: paleta.css  ·  Para JS/embeds: paleta.json (generado por exportar.py)
"""

# ─── Rampa editorial de 10 tonos, frío → cálido ──────────────────────────────
RAMP = [
    "#001219",  # 0  navy casi negro
    "#005F73",  # 1  petróleo
    "#0A9396",  # 2  turquesa
    "#94D2BD",  # 3  menta
    "#E9D8A6",  # 4  arena
    "#EE9B00",  # 5  naranja vibrante  ← el "oro" de la marca
    "#E57D22",  # 6  naranja quemado
    "#DF5D25",  # 7  rojo anaranjado
    "#C71E1D",  # 8  rojo ladrillo     ← COLOR PRINCIPAL DE MARCA
    "#9B2226",  # 9  granate
]

# ─── Identidad ───────────────────────────────────────────────────────────────
BRAND = "#C71E1D"        # ancla de marca · datos · botones · enlaces
BRAND_DEEP = "#8B1A1A"   # oxblood · heros, campos grandes, hover
BRAND_LIGHT = "#E8706B"  # SOLO texto sobre fondo oscuro (de fondo da 3:1 con blanco)
GOLD = "#EE9B00"         # acento sobre fondo oscuro
GOLD_INK = "#A86E00"     # el mismo oro para texto sobre fondo claro
# El logo del sitio (Logo.astro): «opuli» va en este café sobre papel y en este
# papel sobre oscuro; la P en BRAND (claro) o BRAND_LIGHT (oscuro).
LOGO_INK = "#3D2B1F"
LOGO_PAPER = "#F5EFE0"

# ─── Neutros (ya compartidos con el sitio) ───────────────────────────────────
BG = "#FAF8F3"           # fondo claro
BG_DARK = "#0B0E13"      # fondo oscuro
CARD = "#FFFFFF"
CARD_DARK = "#141414"
GRID = "#E2DDD3"         # grilla
GRID_DARK = "#2A3A50"
INK = "#001219"          # tinta / ejes
INK_DARK = "#E2E8F0"
MUTED = "#5C6B70"
MUTED_DARK = "#8A9699"
MUTED_LIGHT = "#8A9699"  # notas al pie sobre fondo claro (mismo valor que el apagado oscuro)

# ─── Series de datos ─────────────────────────────────────────────────────────
# Las 4 validadas: pasan las 5 verificaciones en tema claro Y oscuro con los
# mismos valores, sin re-escalonar. Usar estas cuando hay 4 series o menos.
# ⚠️ SERIE_1 y SERIE_4 NUNCA adyacentes: ΔE 9,1, se confunden entre sí.
SERIES_4 = ["#C71E1D", "#0A9396", "#EE9B00", "#9B2226"]

# ⚠️ #EE9B00 da 2,12:1 de contraste → si lleva etiqueta, que sea visible o usar tabla.

# ─── Categórica extendida: 4 familias × 3 pasos = 12 ─────────────────────────
# Para gráficos de muchas series (sectores del PIB, países). 9 de los 12 tonos
# salen de la rampa; los otros 3 son derivados directos.
# Ventaja editorial: series emparentadas pueden compartir familia.
FAMILIES = {
    "rojo":     ["#E8706B", "#C71E1D", "#8B1A1A"],
    "turquesa": ["#94D2BD", "#0A9396", "#005F73"],
    "ambar":    ["#E9D8A6", "#EE9B00", "#A86E00"],
    "tierra":   ["#E57D22", "#DF5D25", "#9B2226"],
}

# Orden de asignación pensado para que las PRIMERAS series sean las más separadas
# entre sí: no recorre familia por familia ni paso por paso, va alternando.
# Con 5 series se obtienen 5 colores inconfundibles; recién del 9 en adelante
# empiezan a aparecer dos tonos de la misma familia.
CATEGORICAL_12 = [
    "#C71E1D",  # 1  rojo base
    "#0A9396",  # 2  turquesa base
    "#EE9B00",  # 3  ámbar base
    "#005F73",  # 4  turquesa oscuro
    "#DF5D25",  # 5  tierra base
    "#94D2BD",  # 6  turquesa claro
    "#9B2226",  # 7  tierra oscuro
    "#E9D8A6",  # 8  ámbar claro
    "#8B1A1A",  # 9  rojo oscuro
    "#E8706B",  # 10 rojo claro
    "#A86E00",  # 11 ámbar oscuro
    "#E57D22",  # 12 tierra claro
]

# Ordinal de 4 pasos (cuartiles, quintiles cortos): frío → cálido = mejor → peor.
# No usar la categórica para datos ordenados: el orden se pierde.
ORDINAL_4 = ["#0A9396", "#94D2BD", "#EE9B00", "#C71E1D"]

# ─── Semánticos: estado, NO identidad ────────────────────────────────────────
# Se usan para signo y dirección. No mezclar con las series categóricas.
POSITIVE = "#0A9396"   # alza · bueno · superávit
NEGATIVE = "#C71E1D"   # baja · malo · déficit
NEUTRAL = "#8A9699"
NEUTRAL_DARK = "#6E7A7D"
HIGHLIGHT_MUTED = "#B9BEC0"       # el «resto» en el patrón destacado+gris
HIGHLIGHT_MUTED_DARK = "#4A5457"

# ⚠️ EXCEPCIÓN documentada: en el monitor del dólar, rojo = VENTA y turquesa =
# COMPRA. Ahí el color es información, no identidad. No migrar por regla general.

# ─── Escalas continuas (mapas y coropletas) ──────────────────────────────────
SEQUENTIAL_WARM = ["#E9D8A6", "#EE9B00", "#DF5D25", "#C71E1D", "#9B2226"]
SEQUENTIAL_COOL = ["#94D2BD", "#0A9396", "#005F73", "#001219"]
DIVERGING = ["#005F73", "#0A9396", "#94D2BD", "#E9D8A6", "#EE9B00", "#C71E1D"]

# ★ RAMPA OFICIAL DE LOS MAPAS MUNICIPALES (declarada oficial el 2026-09-16).
# Es la que pintan el Atlas Socioeconómico, el Atlas Fiscal y las láminas del
# Banco de Gráficos —los tres, tono por tono— y difiere de la rampa editorial en
# tres pasos, los tres a propósito y medidos sobre el mapa:
#   · #00323D en vez de #001219: el navy da 1,01:1 contra la línea municipal
#     oscura y el borde desaparece; el petróleo profundo sí se separa.
#   · #EDA13E en vez de #EE9B00: el oro puro, al 70 % de opacidad sobre el
#     telón, vibra más que sus vecinos y el escalón se lee como un salto.
#   · #8F1F22 en vez de #9B2226: mismo motivo en el extremo cálido.
# Divergente de NUEVE pasos: petróleo profundo · arena de bisagra · granate.
# Se orienta por `dir` (+1 invierte) y se ancla en un centro real (país,
# mediana o cero). Los que la consumen la COPIAN de acá; `verificar.py` del
# Banco aborta si alguno de los tres la tiene distinta.
DIVERGING_MAPA = ["#00323D", "#005F73", "#0A9396", "#94D2BD", "#E9D8A6",
                  "#EDA13E", "#DF5D25", "#C71E1D", "#8F1F22"]
NO_DATA = "#DFE5EA"      # «sin dato» en los mapas, en los tres productos

# Tintes de papel para el extremo bajo de una escala secuencial: más claros que
# cualquier tono de la rampa pero distintos del fondo #FAF8F3, para que el valor
# bajo no se confunda con el papel. Derivados, no inventados por producto.
TINT_ROJO = "#F8E5E3"    # = --color-populi-tint del sitio
TINT_TURQUESA = "#D9EAE6"
BRAND_DEEPEST = "#6B0300"  # = --color-populi-deep del sitio (extremo de la roja)

# ─── Tipografía (cerrada 2026-08-10) ─────────────────────────────────────────
FONT_DISPLAY = "Playfair Display"   # titulares y títulos de gráfico
FONT_BODY = "Inter"                 # texto, ejes, tooltips, etiquetas
FONT_MONO = "JetBrains Mono"        # cifras y KPIs

GOOGLE_FONTS_HREF = (
    "https://fonts.googleapis.com/css2"
    "?family=Playfair+Display:ital,wght@0,600;0,700;1,400"
    "&family=Inter:wght@400;500;600;700"
    "&family=JetBrains+Mono:wght@500;600;700"
    "&display=swap"
)


def categorical(n: int) -> list:
    """Devuelve n colores categóricos bien separados."""
    if n <= 4:
        return SERIES_4[:n]
    if n <= 12:
        return CATEGORICAL_12[:n]
    raise ValueError(
        f"{n} series es demasiado para una categórica legible. "
        "Usar el patrón destacado+gris (una serie en #C71E1D, el resto en gris)."
    )


def highlight(n: int, index: int, muted: str = HIGHLIGHT_MUTED) -> list:
    """Patrón editorial: una serie destacada en rojo de marca, el resto en gris.
    Es la respuesta correcta cuando hay muchas series y solo importa una
    (p. ej. Bolivia contra el resto del mundo)."""
    return [BRAND if i == index else muted for i in range(n)]

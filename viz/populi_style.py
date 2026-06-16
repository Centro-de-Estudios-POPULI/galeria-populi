"""
populi_style.py — Núcleo de identidad visual del Centro de Estudios POPULI.

Regla de oro: la paleta, las tipografías, los formatos y los elementos de marca
viven AQUÍ. Ningún gráfico define colores o fuentes por su cuenta.

Estética: editorial sobria tipo FMI / The Economist —
  · fondo cálido claro, mucho aire
  · solo eje inferior; grilla horizontal tenue
  · etiquetas de serie al final de la línea (sin leyenda)
  · bandas de confianza suaves debajo de las líneas
  · pie con fuente (gris pequeño) + wordmark POPULI + firma roja

Los colores y fuentes provienen de los tokens REALES del sitio populi.org.bo
(astro-frontend/src/styles/global.css), no de aproximaciones.

API pública principal:
    import populi_style as ps
    fig, ax = ps.nueva_figura("red_cuadrada")
    ps.aplicar_estilo_ejes(ax)
    ...  # dibujar con ps.col("rojo"), etc.
    ps.componer(fig, ax, titulo=..., subtitulo=..., fuente=..., nota=...,
                formato="red_cuadrada", titulo_familia=ps.TITLE_SERIF)
    ps.guardar(fig, "output/mi-grafico.png", formato="red_cuadrada")
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import FuncFormatter
from PIL import Image, ImageDraw, ImageFont

# --------------------------------------------------------------------------- #
# Rutas
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parent.parent      # galeria-populi/
FONTS_DIR = ROOT / "assets" / "fonts"

# --------------------------------------------------------------------------- #
# Paleta — tokens reales del sitio (global.css). Fuente de la verdad.
# --------------------------------------------------------------------------- #
COLORS = {
    # Identidad
    "rojo":        "#8B1A1A",   # --color-populi  (serie principal / marca)
    "rojo_oscuro": "#6B0300",   # --color-populi-dark
    "rojo_claro":  "#C00000",   # --color-populi-light
    "oro":         "#D4A017",   # --color-populi-gold (acento puntual)
    # Tonos cálidos
    "crema":       "#F5EFE0",   # --color-cream
    "cafe":        "#5C3D1E",   # --color-brown  (texto/ejes secundarios)
    "cafe_oscuro": "#3D2B1F",   # --color-brown-dark (cuerpo de texto)
    # Sobrios / contraste
    "azul":        "#0D1B2A",   # --color-navy  (2ª serie)
    "azul_claro":  "#1A2940",   # --color-navy-light
    "pizarra":     "#475569",   # --color-slate (texto terciario)
    "pizarra_cl":  "#64748B",   # --color-slate-light
    # Neutros
    "fondo":       "#FAF8F3",   # --color-warm-white  (fondo de figura)
    "gris_claro":  "#F1EDE5",   # --color-light-gray
    "borde":       "#E2DDD3",   # --color-border (grilla)
    # Texto
    "tinta":       "#2B2420",   # títulos / línea de cero
    "gris":        "#8C8378",   # notas de fuente, texto terciario cálido
    # Paleta de series cuantitativas (del sitio, sección "Chart colors")
    "serie_azul":    "#2563EB",
    "serie_teal":    "#0D9488",
    "serie_ambar":   "#D97706",
    "serie_rosa":    "#E11D48",
    "serie_esmeralda": "#059669",
}

# Secuencia categórica por defecto (sobria, empieza por la marca)
PALETTE = [
    COLORS["rojo"], COLORS["azul"], COLORS["oro"], COLORS["serie_teal"],
    COLORS["cafe"], COLORS["serie_ambar"], COLORS["pizarra"],
]


def col(nombre: str) -> str:
    """Resuelve un color por nombre de paleta; si ya es HEX, lo devuelve igual."""
    if isinstance(nombre, str) and nombre.startswith("#"):
        return nombre
    return COLORS.get(nombre, nombre)


def _rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def aclarar(hex_color: str, cantidad: float) -> str:
    """Mezcla el color con blanco (cantidad 0..1)."""
    r, g, b = _rgb(col(hex_color))
    return "#%02x%02x%02x" % tuple(int(c + (255 - c) * cantidad) for c in (r, g, b))


def contraste_texto(hex_color: str) -> str:
    """Texto crema u oscuro según luminancia del fondo."""
    r, g, b = _rgb(col(hex_color))
    return COLORS["tinta"] if (0.299 * r + 0.587 * g + 0.114 * b) > 150 else COLORS["crema"]


# Paletas para mapas/escalas continuas, ancladas en la marca POPULI. Todas
# arrancan en un tono claro DISTINTO del fondo (#FAF8F3) para que el valor bajo
# no se confunda con el papel.
# Paletas afinadas para ARMONIZAR con el rojo ladrillo de marca (#8B1A1A): tonos
# cálidos análogos, un teal/azul-petróleo complementario y un slate apagado
# (no "icy") — todos conviven bien con el rojo del wordmark/firma.
PALETAS = {
    # secuencial cálida (ancha, multitono) — análoga al rojo, la más versátil
    "calido":     ["#F6E6BE", "#E6B24A", "#CF7B33", "#B23A2C", "#8B1A1A", "#5E1010"],
    # secuencial roja monocroma — sobria, editorial
    "rojo":       ["#F3D9D2", "#D98E80", "#BC4B3F", "#8B1A1A", "#5E1010"],
    # secuencial slate/azul apagado — neutro cálido-frío que acompaña al rojo
    "azul":       ["#E6EAEF", "#A9B7C6", "#647D97", "#3A516B", "#22344A"],
    # secuencial teal/petróleo — complemento del rojo, apagado (no neón)
    "verde":      ["#E3EDEA", "#9AC4B9", "#4F9E90", "#2C7468", "#16504A"],
    # divergente slate↔crema cálida↔rojo — para variables con signo (TwoSlopeNorm)
    "divergente": ["#3A516B", "#7E94A8", "#EFE7D6", "#CB7A6D", "#8B1A1A"],
}


def colormap(nombre: str = "calido"):
    """Devuelve un LinearSegmentedColormap de marca por nombre (ver PALETAS)."""
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list(f"populi_{nombre}",
                                             PALETAS.get(nombre, PALETAS["calido"]))


# --------------------------------------------------------------------------- #
# Tipografía — fuentes del sitio (Playfair Display + Inter + mono), con fallback
# --------------------------------------------------------------------------- #
# familia matplotlib -> archivo .ttf en assets/fonts
_FONT_FILES = {
    "Playfair Display": "PlayfairDisplay.ttf",
    "Playfair Display Italic": "PlayfairDisplay-Italic.ttf",
    "Inter": "Inter.ttf",
    "Archivo": "Archivo.ttf",
    "Source Serif 4": "SourceSerif4.ttf",
    "IBM Plex Mono": "IBMPlexMono-Regular.ttf",
    "IBM Plex Mono SemiBold": "IBMPlexMono-SemiBold.ttf",
    # titular de redes — serif (display)
    "Fraunces": "Fraunces-Display.ttf",            # display serif (peso Black, opsz 144)
    "Spectral ExtraBold": "Spectral-ExtraBold.ttf",  # serif elegante
    "Zilla Slab": "ZillaSlab-Bold.ttf",            # slab serif sturdy
    # sans humanistas (tipo Whitney/FMI) — regular para texto, Bold para titular
    "Public Sans": "PublicSans-Regular.ttf",
    "Public Sans Bold": "PublicSans-Bold.ttf",
    "Source Sans 3": "SourceSans3-Regular.ttf",
    "Source Sans 3 Bold": "SourceSans3-Bold.ttf",
    "Mulish Bold": "Mulish-Bold.ttf",
}

_REGISTERED = set()
for _name, _file in _FONT_FILES.items():
    _fp = FONTS_DIR / _file
    if _fp.exists():
        try:
            font_manager.fontManager.addfont(str(_fp))
            _REGISTERED.add(_name)
        except Exception:
            pass

# Roles tipográficos (con fallback si una fuente faltara)
TITLE_SERIF = "Playfair Display" if "Playfair Display" in _REGISTERED else "DejaVu Serif"
TITLE_SANS = "Archivo" if "Archivo" in _REGISTERED else "DejaVu Sans"
# Estándar POPULI (elegido 2026-06-09): cuerpo y números en Public Sans
# (sans humanista, look FMI de una sola familia).
BODY = "Public Sans" if "Public Sans" in _REGISTERED else "Inter"
MONO = "Public Sans" if "Public Sans" in _REGISTERED else "IBM Plex Mono"


def fp(familia, size_px=None, weight="normal"):
    """FontProperties robusto: si la familia está en _FONT_FILES la resuelve por
    ARCHIVO (evita fallos de resolución por nombre); si no, por nombre de familia."""
    kw = {"weight": weight}
    if size_px is not None:
        kw["size"] = _px2pt(size_px)
    f = _FONT_FILES.get(familia)
    if f and (FONTS_DIR / f).exists():
        return font_manager.FontProperties(fname=str(FONTS_DIR / f), **kw)
    return font_manager.FontProperties(family=familia, **kw)


def set_tema(texto="Public Sans", numeros="Public Sans"):
    """Define la familia de TEXTO (subtítulo, notas, etiquetas, ejes) y de los
    NÚMEROS. Por defecto = estándar POPULI (Public Sans en todo). Pasar otra
    familia para experimentar; set_tema() restablece el estándar."""
    global BODY, MONO
    BODY, MONO = texto, numeros

# Titular por formato: serif (Playfair, como la web/informes) para soportes de
# informe; grotesca (Archivo, como el FMI) para redes — más legible en miniatura.
# Titular estándar POPULI (elegido 2026-06-09): Zilla Slab (slab serif, robusta)
# en todos los formatos, emparejado con cuerpo Public Sans.
TITLE_REDES = "Zilla Slab" if "Zilla Slab" in _REGISTERED else TITLE_SERIF
TITLE_BY_FORMAT = {
    "informe":       TITLE_REDES,
    "informe_ancho": TITLE_REDES,
    "red_cuadrada":  TITLE_REDES,
    "red_vertical":  TITLE_REDES,
    "red_historia":  TITLE_REDES,
    "mundo":         TITLE_REDES,
}
TITLE_FONT = TITLE_REDES   # fallback


def titular_familia(formato: str) -> str:
    return TITLE_BY_FORMAT.get(formato, TITLE_FONT)

plt.rcParams.update({
    "font.family": BODY,
    "svg.fonttype": "none",
    "axes.unicode_minus": False,
    "figure.dpi": 100,
})

# --------------------------------------------------------------------------- #
# Formatos de salida — tamaño, dpi y escala tipográfica
# --------------------------------------------------------------------------- #
# Tamaños base definidos a un ancho de referencia de 1080 px; se escalan por
# (ancho_real / 1080). Así un mismo gráfico se ve coherente en cualquier formato.
FORMATS = {
    # nombre          (W,    H),    dpi
    "informe":       (1800, 1800),  # ~9x9 in @200dpi -> PDF/HTML/presentaciones
    "informe_ancho": (2000, 1200),
    "red_cuadrada":  (1080, 1080),  # Instagram / X feed
    "red_vertical":  (1080, 1350),  # IG retrato
    "red_historia":  (1080, 1920),  # stories
    "mundo":         (2600, 2046),  # mapa mundial PANORÁMICO (estilo OWID); +10% de alto para el mapa
}
DPI = 200

# Escala tipográfica (px @ ancho 1080). Proporciones tipo FMI: titular grande,
# subtítulo claramente menor, números/ejes discretos.
SIZES = {
    "titulo":     52,
    "subtitulo":  29,
    "eje":        25,
    "fin_linea":  27,   # etiqueta al final de cada serie
    "anotacion":  26,   # número-héroe
    "dato":       23,   # etiquetas de dato (barras/puntos)
    "fuente":     22,   # pie de fuente / nota
    "leyenda":    23,
    "wordmark":   52,
}

# Márgenes (px @ 1080)
MARGIN = 72
TOP = 56
BOTTOM = 46


def _px2pt(px: float) -> float:
    return px * 72.0 / DPI


# --------------------------------------------------------------------------- #
# Formato numérico al español (coma decimal)
# --------------------------------------------------------------------------- #
def es_num(valor: float, decimales: int = 1, miles: bool = False) -> str:
    """Formatea un número al español: coma decimal y punto de miles opcional."""
    s = f"{valor:,.{decimales}f}"          # 1,234.5
    if miles:
        s = s.replace(",", " ").replace(".", ",").replace(" ", ".")
    else:
        s = s.replace(",", "").replace(".", ",")
    return s


def formateador_es(decimales: int = 1, sufijo: str = "", miles: bool = False):
    """FuncFormatter para ejes con coma decimal y sufijo opcional (ej. '%')."""
    return FuncFormatter(lambda v, _pos: es_num(v, decimales, miles) + sufijo)


# --------------------------------------------------------------------------- #
# Construcción de figura y estilo de ejes
# --------------------------------------------------------------------------- #
# Factor de supersampling de calidad: 2 = render a 2160 px de ancho base
# (full HD+, nítido en cualquier pantalla). Todo el estilo escala con sc=W/1080,
# así que el diseño es idéntico, solo con más resolución.
ESCALA = 2


# Ancho de referencia tipográfica por formato. El panorámico "mundo" usa una
# referencia mayor: al ensanchar el lienzo, las fuentes NO crecen, así el texto
# del pie entra en menos líneas y el mapa queda más grande (mismo tamaño de letra
# que el formato anterior de 2000 px de ancho).
SC_REF = {"mundo": 1405}


def _spec(formato: str):
    W, H = FORMATS[formato]
    W, H = int(W * ESCALA), int(H * ESCALA)
    return W, H, W / float(SC_REF.get(formato, 1080))


def nueva_figura(formato: str = "red_vertical"):
    """Crea figura + eje vacíos con el fondo de marca. El eje se reposiciona en
    componer(); aquí solo se devuelve para dibujar los datos."""
    W, H, _ = _spec(formato)
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
    fig.patch.set_facecolor(COLORS["fondo"])
    ax = fig.add_axes([0.1, 0.18, 0.85, 0.55])
    ax.set_facecolor(COLORS["fondo"])
    fig._ps_formato = formato
    return fig, ax


def aplicar_estilo_ejes(ax, cero: bool = False, grid_y: bool = True):
    """Estilo editorial FMI: sin spines salvo el inferior (café), grilla
    horizontal tenue, ticks discretos. cero=True dibuja la línea y=0."""
    _, _, sc = _spec(getattr(ax.figure, "_ps_formato", "red_cuadrada"))
    ax.set_facecolor(COLORS["fondo"])
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(COLORS["cafe"])
    ax.spines["bottom"].set_linewidth(1.2 * sc)
    ax.tick_params(axis="x", length=5 * sc, width=1.0 * sc, color=COLORS["cafe"],
                   labelsize=_px2pt(SIZES["eje"] * sc), labelcolor=COLORS["cafe"], pad=6 * sc)
    ax.tick_params(axis="y", length=0, labelsize=_px2pt(SIZES["eje"] * sc),
                   labelcolor=COLORS["cafe"], pad=6 * sc)
    if grid_y:
        ax.grid(axis="y", color=COLORS["borde"], linewidth=1.0 * sc, alpha=0.9, zorder=0)
        ax.set_axisbelow(True)
    if cero:
        ax.axhline(0, color=COLORS["tinta"], linewidth=1.3 * sc, zorder=3)
    # la tipografía de las marcas se fija definitivamente en componer() (tras
    # cualquier recolocación de ticks), usando la familia de NÚMEROS del tema.
    return ax


def ticks_x_enteros(ax, x, paso=None):
    """Fija marcas del eje X en enteros dentro del rango de datos (sin fantasmas
    fuera de los datos al ensanchar el xlim para las etiquetas)."""
    import numpy as _np
    x = _np.asarray(x)
    lo, hi = int(_np.floor(x.min())), int(_np.ceil(x.max()))
    if paso is None:
        span = max(1, hi - lo)
        paso = max(1, round(span / 6))
        paso = int(np.ceil(paso / 2.0) * 2) if span > 12 else paso  # pasos pares en rangos largos
    ax.set_xticks(list(range(lo, hi + 1, paso)))


def etiquetas_fin_linea(ax, etiquetas, expandir=0.16):
    """Coloca el nombre de cada serie al final de su línea (estilo FMI) y
    amplía el xlim a la derecha para que quepan. `etiquetas` = lista de
    (x, y, texto, color)."""
    _, _, sc = _spec(getattr(ax.figure, "_ps_formato", "red_cuadrada"))
    x0, x1 = ax.get_xlim()
    ax.set_xlim(x0, x1 + (x1 - x0) * expandir)
    for x, y, texto, color in etiquetas:
        ax.annotate(texto, (x, y), xytext=(10 * sc, 0), textcoords="offset points",
                    va="center", ha="left", color=col(color), zorder=6,
                    fontproperties=fp(BODY, SIZES["fin_linea"] * sc, weight="bold"))


# --------------------------------------------------------------------------- #
# Marca: wordmark "Populi" (P serif rojo + opuli italic tinta)
# --------------------------------------------------------------------------- #
def _wordmark_img(altura_px: int, color_p: str | None = None) -> Image.Image:
    s = altura_px / 64.0
    f_p = ImageFont.truetype(str(FONTS_DIR / _FONT_FILES["Playfair Display"]), int(64 * s))
    f_rest = ImageFont.truetype(str(FONTS_DIR / _FONT_FILES["Playfair Display Italic"]), int(40 * s))
    tmp = ImageDraw.Draw(Image.new("RGBA", (4, 4)))
    w_p = tmp.textlength("P", font=f_p)
    w_rest = tmp.textlength("opuli", font=f_rest)
    W = int(w_p + w_rest + 8 * s)
    H = int(64 * s + 12 * s)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    base = int(64 * s)
    d.text((0, base), "P", font=f_p, fill=_rgb(col(color_p) if color_p else COLORS["rojo"]), anchor="ls")
    d.text((int(w_p - 5 * s), base), "opuli", font=f_rest, fill=_rgb(COLORS["tinta"]), anchor="ls")
    return img


# --------------------------------------------------------------------------- #
# Composición: título, subtítulo, pie de marca + reposicionar el eje
# --------------------------------------------------------------------------- #
def _wrap_px(texto, size_px, max_w, font_file):
    f = ImageFont.truetype(str(FONTS_DIR / font_file), int(size_px))
    medir = ImageDraw.Draw(Image.new("RGB", (4, 4)))
    palabras, lineas, cur = texto.split(), [], ""
    for w in palabras:
        trial = f"{cur} {w}".strip()
        if medir.textlength(trial, font=f) <= max_w or not cur:
            cur = trial
        else:
            lineas.append(cur)
            cur = w
    if cur:
        lineas.append(cur)
    return lineas


def componer(fig, ax, titulo="", subtitulo="", fuente="", nota="",
             formato="red_vertical", titulo_familia=None, gutter_izq=0, mapa=False,
             acento_p=None, acento_linea=None, margen=None, top=None, bottom=None,
             wordmark_top=False, freshness="", sub_scale=1.0):
    """Dibuja título/subtítulo arriba y el pie de marca abajo, y reposiciona el
    eje del gráfico en el espacio central. Llamar DESPUÉS de dibujar los datos.
    margen/top/bottom (px @1080) permiten un ajuste puntual por gráfico; si no
    se pasan rigen los globales MARGIN/TOP/BOTTOM."""
    W, H, sc = _spec(formato)
    fig._ps_formato = formato
    fam = titulo_familia or titular_familia(formato)
    fam_file = _FONT_FILES.get(fam, "Inter.ttf")
    _bottom = (bottom if bottom is not None else BOTTOM)
    M = (margen if margen is not None else MARGIN) * sc
    max_w = W - 2 * M

    s_tit = SIZES["titulo"] * sc
    s_sub = SIZES["subtitulo"] * sc * sub_scale
    s_src = SIZES["fuente"] * sc

    def fy(px):
        return 1 - px / H

    # ---- wordmark: arriba-derecha (estilo OWID, p. ej. mapas) o abajo-derecha ----
    wm = _wordmark_img(int(SIZES["wordmark"] * sc), color_p=acento_p)
    wm_left_px = W - wm.width - M
    title_max_w = max_w
    if wordmark_top:
        wm_yo = H - int((top if top is not None else TOP) * sc) - wm.height
        fig.figimage(np.asarray(wm), xo=int(wm_left_px), yo=int(wm_yo),
                     origin="upper", zorder=6)
        rule_y = (wm_yo - 8 * sc) / H
        fig.add_artist(plt.Line2D([wm_left_px / W, (W - M) / W], [rule_y, rule_y],
                                  transform=fig.transFigure,
                                  color=col(acento_linea) if acento_linea else COLORS["rojo"],
                                  linewidth=2.4 * sc, zorder=6, solid_capstyle="butt"))
        title_max_w = max_w - wm.width - 28 * sc   # el título cede ancho al logo

    # ---- cabecera ----
    # El titular se renderiza apuntando al ARCHIVO de fuente (FontProperties por
    # ruta), evitando problemas de resolución por nombre de familia.
    fp_tit = font_manager.FontProperties(fname=str(FONTS_DIR / fam_file),
                                         size=_px2pt(s_tit), weight="bold")
    cur = (top if top is not None else TOP) * sc
    for ln in _wrap_px(titulo, s_tit, title_max_w, fam_file):
        fig.text(M / W, fy(cur), ln, fontproperties=fp_tit,
                 color=COLORS["tinta"], va="top", ha="left")
        cur += s_tit * 1.18
    body_file = _FONT_FILES.get(BODY, "Inter.ttf")
    if subtitulo:
        cur += 14 * sc
        for ln in _wrap_px(subtitulo, s_sub, max_w, body_file):
            fig.text(M / W, fy(cur), ln, fontproperties=fp(BODY, s_sub),
                     color=COLORS["cafe"], va="top", ha="left")
            cur += s_sub * 1.26
    chart_top = cur + 30 * sc

    # ---- pie de página -------------------------------------------------- #
    # Con el wordmark arriba, el pie usa TODO el ancho; si no, va abajo-derecha y
    # el texto se acota a su izquierda (comportamiento previo, intacto).
    if wordmark_top:
        txt_max_w = max_w
        rule_top_px = H                      # no hay regla inferior que limite el pie
    else:
        fig.figimage(np.asarray(wm), xo=int(wm_left_px), yo=int(_bottom * sc),
                     origin="upper", zorder=6)
        rule_y = (_bottom * sc + wm.height + 7 * sc) / H
        fig.add_artist(plt.Line2D([wm_left_px / W, (W - M) / W], [rule_y, rule_y],
                                  transform=fig.transFigure,
                                  color=col(acento_linea) if acento_linea else COLORS["rojo"],
                                  linewidth=2.4 * sc, zorder=6, solid_capstyle="butt"))
        rule_top_px = H - (rule_y * H) - 4 * sc
        txt_max_w = max_w - wm.width - 36 * sc

    fcur = H - _bottom * sc
    if fuente:
        for ln in reversed(_wrap_px(fuente, s_src, txt_max_w, body_file)):
            fig.text(M / W, fy(fcur), ln, fontproperties=fp(BODY, s_src),
                     color=COLORS["gris"], va="bottom", ha="left")
            fcur -= s_src * 1.42
    if nota:
        fcur -= 4 * sc
        for ln in reversed(_wrap_px(nota, s_src, txt_max_w, body_file)):
            fig.text(M / W, fy(fcur), ln, fontproperties=fp(BODY, s_src),
                     color=COLORS["gris"], va="bottom", ha="left")
            fcur -= s_src * 1.4
    if freshness:
        fcur -= 4 * sc
        for ln in reversed(_wrap_px(freshness, s_src, txt_max_w, body_file)):
            fig.text(M / W, fy(fcur), ln, fontproperties=fp(BODY, s_src),
                     color=COLORS["cafe"], va="bottom", ha="left")
            fcur -= s_src * 1.4
    text_top_px = fcur - 4 * sc
    footer_top = min(text_top_px, rule_top_px) - 20 * sc

    # ---- modo MAPA: el eje ocupa TODA el área disponible (sin ejes ni números,
    # márgenes laterales chicos). El propio gráfico de mapa inscribe la geometría.
    if mapa:
        # mismo margen lateral que título/pie → todo alineado al mismo encuadre
        ax.set_position([M / W, (H - footer_top) / H,
                         (W - 2 * M) / W, (footer_top - chart_top) / H])
        return ax

    # ---- reposicionar el eje en el espacio central ----
    # Espacio bajo el eje: números del eje X + (si la hay) etiqueta de eje
    # ("Meses") + un respiro antes del pie. Más holgado si hay etiqueta de eje.
    xtick_room = (122 if ax.get_xlabel() else 76) * sc
    chart_bottom = footer_top - xtick_room
    # Alineación tipo FMI: el bloque de números del eje Y se ubica DENTRO del
    # margen, de modo que su borde izquierdo coincide con el del título. El área
    # de trazado se inserta a la derecha por el ancho de las etiquetas Y.
    fig.canvas.draw()
    num_file = _FONT_FILES.get(MONO, "IBMPlexMono-Regular.ttf")
    fp_num = fp(MONO, SIZES["eje"] * sc)
    # fijar la familia de NÚMEROS en las marcas (tras cualquier recolocación)
    for lbl in ax.get_xticklabels():
        lbl.set_fontproperties(fp_num)
    extra = 0
    if gutter_izq == 0:
        for lbl in ax.get_yticklabels():
            lbl.set_fontproperties(fp_num)
        labels = [t.get_text() for t in ax.get_yticklabels() if t.get_text()]
        if labels:
            fy_font = ImageFont.truetype(str(FONTS_DIR / num_file), int(SIZES["eje"] * sc))
            medir = ImageDraw.Draw(Image.new("RGB", (4, 4)))
            w_lbl = max(medir.textlength(l, font=fy_font) for l in labels)
            extra = w_lbl + 6 * sc * DPI / 72.0   # ancho etiqueta + pad del tick (pad va en pt)
    left = (M + gutter_izq * sc + extra) / W
    width = (W - 2 * M - gutter_izq * sc - extra) / W
    bottom = (H - chart_bottom) / H
    height = max(0.05, (chart_bottom - chart_top) / H)
    ax.set_position([left, bottom, width, height])

    # Corrección EXACTA: medir el borde izquierdo REAL de las etiquetas del eje Y
    # (tras redibujar) y desplazar el gráfico para que ese borde coincida con el
    # título (en x = M). Robusto frente a métricas de fuente, signo menos, sufijos.
    if gutter_izq == 0:
        fig.canvas.draw()
        rend = fig.canvas.get_renderer()
        exts = [l.get_window_extent(rend) for l in ax.get_yticklabels() if l.get_text()]
        if exts:
            delta = M - min(e.x0 for e in exts)
            if abs(delta) > 1:
                pos = ax.get_position()
                ax.set_position([pos.x0 + delta / W, pos.y0,
                                 pos.width - delta / W, pos.height])
    return ax


# --------------------------------------------------------------------------- #
# Guardado: PNG (+ SVG opcional) + miniatura cuadrada para la galería
# --------------------------------------------------------------------------- #
def guardar(fig, archivo, formato="red_vertical", svg=False, thumb=True):
    archivo = Path(archivo)
    archivo.parent.mkdir(parents=True, exist_ok=True)
    if svg:
        fig.savefig(archivo.with_suffix(".svg"), facecolor=COLORS["fondo"])
    fig.savefig(archivo, dpi=DPI, facecolor=COLORS["fondo"])
    plt.close(fig)
    # Optimización sin pérdida visible: paleta de 256 colores (estos gráficos usan
    # pocos tonos) → ~60% menos peso, lo que permite el doble de resolución sin
    # que el sitio pese de más. La nitidez/resolución NO se tocan.
    img = Image.open(archivo).convert("RGB")
    _quantizar(img).save(archivo, optimize=True)
    if thumb:
        thumbs = ROOT / "public" / "thumbs"
        thumbs.mkdir(parents=True, exist_ok=True)
        side = min(img.size)
        th = (img.crop(((img.width - side) // 2, 0, (img.width + side) // 2, side))
                 .resize((600, 600), Image.LANCZOS))
        _quantizar(th).save(thumbs / archivo.name, "PNG", optimize=True)
    kb = archivo.stat().st_size // 1024
    print(f"OK   {archivo.name}  ({formato}, {kb} KB)")
    return archivo


def _quantizar(img, colores=256):
    """Reduce a paleta de N colores (visualmente idéntico en gráficos de pocos
    tonos) para optimizar el peso del PNG sin perder nitidez ni resolución."""
    return img.convert("RGB").quantize(
        colors=colores, method=Image.MEDIANCUT, dither=Image.Dither.NONE)

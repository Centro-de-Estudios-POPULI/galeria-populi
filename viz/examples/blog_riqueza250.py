"""
Láminas del Banco desde la entrada del blog «La riqueza de las naciones cumple 250 años» (Carlos
Aranda, 2026-09-30), y la lámina grande con las diez regresiones para compartir en redes.

    python viz/examples/blog_riqueza250.py                       # las 14 + manifiesto + contrato
    python viz/examples/blog_riqueza250.py --solo=hockey,mosaico
    python viz/examples/blog_riqueza250.py --blog                # además copia los PNG al blog

`--blog` deja los PNG en `blog-graficos/descargas/` del sitio: son los que baja el botón
«Descargar imagen» de cada gráfico de la entrada (mismo origen, así el atributo `download` vale).

Tipografía del BLOG, no la del Banco: titular en Playfair Display 700 (instancia estática) y cuerpo y
cifras en Inter, como los embeds. Los datos son los MISMOS CSV que alimentan los gráficos del blog, y
la tendencia es la MISMA cuenta (`ajuste.py` del motor del blog, que es la del OLE): si se rehace un
lado y no el otro, la lámina y el embed dejan de coincidir. Nada de datos al repo: el Banco publica la
imagen.
"""
import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import matplotlib.patheffects as pe
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

VIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(VIZ))
import populi_style as ps   # noqa: E402
import catalogo as CAT      # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

ENTRADA = Path.home() / "OneDrive" / "Desktop" / "entradas_nuevas" / "la-riqueza-de-las-naciones-250"
BLOG = Path.home() / "OneDrive" / "Desktop" / "Proyectos" / "populi-wordpress" / "astro-frontend"
sys.path.insert(0, str(BLOG / "scripts" / "graficos"))
from ajuste import ajustar, ALFA   # noqa: E402  — la tendencia del embed, no una parecida

FICHA = json.loads((ENTRADA / "ficha.json").read_text(encoding="utf-8"))
SPEC = {c["id"]: c for c in FICHA["charts"]}
TITULO_ENTRADA = (ENTRADA / FICHA["doc"]).read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
URL = f"https://populi.org.bo/blog/{FICHA['slug']}/"
DESCARGAS = BLOG / "public" / "blog-graficos" / "descargas"

FECHA = "2026-09-30"
AUTOR = "Elaboración: Centro de Estudios POPULI · Carlos Aranda."
GRUPO = "Blog · La riqueza de las naciones, 250 años"
TAGS = ["Blog", "crecimiento económico", "Adam Smith", "mundo"]

TIT = "Playfair Display Bold"          # el titular de los embeds del blog
ps.set_tema("Inter", "Inter")          # cifras de los ejes en Inter, como en el blog
P = ps._pal
ROJO, TINTA, PIZARRA, TENUE, FONDO = P.BRAND, P.INK, P.MUTED, P.HIGHLIGHT_MUTED, ps.COLORS["fondo"]
F_LIN, F_MOS = "informe_horizontal", "informe_mosaico"


# --------------------------------------------------------------------------- #
# Piezas comunes
# --------------------------------------------------------------------------- #
def ficha(slug, titulo, subtitulo, fuente, nota, tipo, formato, tags):
    return {"slug": slug, "titulo": titulo, "subtitulo": subtitulo, "categoria": "mundo",
            "fuente": fuente, "nota": nota, "tags": TAGS + tags, "fecha": FECHA, "datos": None,
            "grupo": GRUPO, "enlace": URL, "enlace_etiqueta": "Ver en el blog",
            "documento": {"titulo": TITULO_ENTRADA, "url": URL, "fecha": FICHA["date"]},
            "tipo": tipo, "formato": formato}


HECHAS = []


def cerrar(fig, meta):
    ps.guardar(fig, CAT.GRAFICAS / f"{meta['slug']}.png", formato=meta["formato"])
    CAT.registrar(meta, meta["tipo"], meta["formato"])
    HECHAS.append(meta["slug"])


def componer(fig, ax, meta):
    # abajo, SÓLO la fuente (Carlos): la explicación va en la ficha del Banco, donde se profundiza
    ps.componer(fig, ax, titulo=meta["titulo"], subtitulo=meta["subtitulo"], fuente=meta["fuente"],
                nota="", formato=meta["formato"], titulo_familia=TIT)


def estilo(ax, sc, eje="y"):
    ps.aplicar_estilo_ejes(ax, grid_y=False)
    ax.spines["bottom"].set_capstyle("butt")   # el extremo proyectado asomaba 4 px pasado W − M
    ax.grid(axis=eje, color=ps.COLORS["borde"], linewidth=1.0 * sc, linestyle=(0, (1.6, 2.6)), zorder=0)
    ax.set_axisbelow(True)


def miles(v, d=0):
    return ps.es_num(v, d, True)


def encajar(fig, ax, textos, limite_px):
    """Encoge el ancho del eje hasta que ningún rótulo pase de limite_px (el borde W − M)."""
    W = fig.bbox.width
    for _ in range(8):
        fig.canvas.draw()
        r = fig.canvas.get_renderer()
        over = max(t.get_window_extent(r).x1 for t in textos) - limite_px
        if over <= 1:
            return
        p = ax.get_position()
        ax.set_position([p.x0, p.y0, p.width - over / W, p.height])


def encajar_eje(fig, ax, limite_px):
    """El eje termina donde termina el wordmark (W − M): la línea base asoma unos px por su
    grosor y el último rótulo del eje X cuelga media palabra; se mide y se encoge el ancho."""
    W = fig.bbox.width
    for _ in range(6):
        fig.canvas.draw()
        r = fig.canvas.get_renderer()
        ext = [ax.spines["bottom"].get_window_extent(r).x1]
        ext += [l.get_window_extent(r).x1 for l in ax.get_xticklabels() if l.get_text()]
        over = max(ext) - limite_px
        if over <= 0.5:
            return
        p = ax.get_position()
        ax.set_position([p.x0, p.y0, p.width - (over + 1) / W, p.height])


def rotular_fin(fig, ax, items, sc, x_ancla, s_px):
    """«nombre  valor» a la derecha de x_ancla, sin encimarse (como el rótulo final del blog).
    Si el rótulo se aleja de la punta de su línea, una guía punteada lo une a ella."""
    fig.canvas.draw()
    T = ax.transData
    x_disp = T.transform((x_ancla, 1))[0]
    alto = s_px * 1.34
    ys = [T.transform((x_ancla, it["y"]))[1] for it in items]
    orden = sorted(range(len(items)), key=lambda i: ys[i])
    pos = [ys[i] for i in orden]
    for _ in range(800):
        mov = False
        for k in range(len(pos) - 1):
            d = pos[k + 1] - pos[k]
            if d < alto - 0.5:
                e = (alto - d) / 2
                pos[k] -= e
                pos[k + 1] += e
                mov = True
        if not mov:
            break
    inv = T.inverted()
    textos = []
    for k, i in enumerate(orden):
        it = items[i]
        y_lab = inv.transform((x_disp, pos[k]))[1]
        if it["x"] < x_ancla or abs(pos[k] - ys[i]) > alto * 0.25:
            ax.plot([it["x"], x_ancla], [it["y"], y_lab], color=TENUE, linewidth=0.9 * sc,
                    linestyle=(0, (1, 1.6)), zorder=3, clip_on=False)
        nom = ax.annotate(it["nombre"], xy=(x_ancla, y_lab), xytext=(7 * sc, 0), textcoords="offset points",
                          ha="left", va="center", color=it["color"], fontproperties=ps.fp(ps.BOLD, s_px),
                          annotation_clip=False, zorder=6)
        val = ax.annotate(it["valor"], xy=(1, 0.5), xycoords=nom, xytext=(6 * sc, 0), textcoords="offset points",
                          ha="left", va="center", color=it["color"], fontproperties=ps.fp(ps.BOLD, s_px),
                          annotation_clip=False, zorder=6)
        textos += [nom, val]
    return textos


def oraciones(texto):
    return [o.strip().rstrip(".") + "." for o in texto.split(". ") if o.strip()]


# --------------------------------------------------------------------------- #
# 1 y 2 · El palo de hockey (lineal y logarítmico) · 3 · los tres males
# --------------------------------------------------------------------------- #
# Decisión de Carlos (2026-09-30): en las láminas de líneas los nombres de las series van ARRIBA,
# en una leyenda, no al final de cada línea; y el lienzo es cuadrado, como el de las burbujas.
# (columna, color): el orden es el de la ficha del blog
SERIES_G1 = [("Reino Unido", "#0A9396"), ("Países Bajos", P.GOLD), ("Mundo", TINTA), ("Bolivia", ROJO)]
SERIES_G3 = [("Pobreza extrema", ROJO), ("Mortalidad antes de los 5 años", P.GOLD),
             ("Analfabetismo adulto", "#0A9396")]


def leyenda_lineas(fig, ax, series, W, H, sc, M):
    """Leyenda de líneas sobre el gráfico, alineada al margen; el eje le cede ese alto. Todas en
    un renglón si entran en el ancho útil; si no, de a dos."""
    p = ax.get_position()
    s_ley = ps.SIZES["leyenda"] * sc
    hs = [Line2D([0], [0], color=c, linewidth=2.6 * sc, solid_capstyle="butt") for _, c in series]
    nombres = [n for n, _ in series]

    def poner(ncol):
        return fig.legend(hs, nombres, loc="upper left", bbox_to_anchor=(M / W, (p.y1 * H + 8 * sc) / H),
                          ncol=ncol, frameon=False, prop=ps.fp(ps.BODY, s_ley),
                          labelcolor=ps.COLORS["cafe_oscuro"], handletextpad=0.55, columnspacing=1.6,
                          borderaxespad=0, borderpad=0, handlelength=1.4, labelspacing=0.55)
    ley, filas = poner(len(series)), 1
    fig.canvas.draw()
    if ley.get_window_extent(fig.canvas.get_renderer()).x1 > W - M:
        ley.remove()
        filas = math.ceil(len(series) / 2)
        ley = poner(2)
    alto = filas * s_ley * 1.55 + 34 * sc
    ax.set_position([p.x0, p.y0, p.width, p.height - alto / H])


def hockey(log=False):
    F = "informe_5x4"
    W, H, sc = ps._spec(F)
    M = ps.MARGIN * sc
    spec = SPEC["nb-rn250-escala-logaritmica" if log else "nb-rn250-palo-de-hockey"]
    df = pd.read_csv(ENTRADA / spec["dataset"])
    x0, x1 = int(df.anio.min()), int(df.anio.max())

    fig, ax = ps.nueva_figura(F)
    for col, c in SERIES_G1:
        d = df[["anio", col]].dropna()
        ax.plot(d.anio, d[col], color=c, linewidth=(2.2 if col == "Bolivia" else 1.8) * sc,
                zorder=5 if col == "Bolivia" else 4, solid_capstyle="round", solid_joinstyle="round")
    estilo(ax, sc)
    if log:
        ax.set_yscale("log")
        ax.set_ylim(950, 100000)
        ax.set_yticks([1000, 10000, 100000])
        ax.minorticks_off()
    else:
        ax.set_ylim(0, 52000)
        ax.set_yticks(range(0, 50001, 10000))
    ax.yaxis.set_major_formatter(ps.formateador_es(0, miles=True))
    ax.set_xlim(x0 - 6, x1 + 4)
    ax.set_xticks(list(range(1300, 2001, 100)))
    ax.xaxis.set_major_formatter(ps.formateador_es(0))

    # 1776: la marca vertical del blog, con su rótulo arriba, del lado libre
    ax.axvline(1776, color=PIZARRA, linewidth=1.1 * sc, linestyle=(0, (4, 3)), zorder=2)
    ax.annotate(spec["vline"]["label"], (1776, 1), xycoords=("data", "axes fraction"),
                xytext=(-8 * sc, -2 * sc), textcoords="offset points", ha="right", va="top",
                color=PIZARRA, fontproperties=ps.fp(ps.BODY, ps.SIZES["dato"] * sc))

    if log:
        meta = ficha("blog-riqueza250-escala-logaritmica",
                     "Siete siglos de ingreso, en escala logarítmica",
                     f"PIB per cápita en dólares internacionales de 2011 (PPA), {x0}–{x1}",
                     "Fuente: " + spec["source"] + ". " + AUTOR,
                     "Cada línea de la grilla multiplica el ingreso por diez: una pendiente constante es "
                     "una tasa de crecimiento constante. Inglaterra hasta 1700 y provincia de Holanda hasta "
                     "1807; el mundo, en las fechas que estima el proyecto Maddison desde 1820.",
                     "lineas", F, ["PIB per cápita", "Maddison", "escala logarítmica", "Reino Unido", "Bolivia"])
    else:
        meta = ficha("blog-riqueza250-palo-de-hockey",
                     "Siete siglos de ingreso por persona",
                     f"PIB per cápita en dólares internacionales de 2011 (PPA), {x0}–{x1}",
                     "Fuente: " + spec["source"] + ". " + AUTOR,
                     "Inglaterra hasta 1700 y provincia de Holanda hasta 1807; el mundo, en las fechas que "
                     "estima el proyecto Maddison desde 1820.",
                     "lineas", F, ["PIB per cápita", "Maddison", "Revolución Industrial", "Reino Unido", "Bolivia"])
    componer(fig, ax, meta)
    leyenda_lineas(fig, ax, SERIES_G1, W, H, sc, M)
    encajar_eje(fig, ax, W - M)
    cerrar(fig, meta)


def males():
    F = "informe_5x4"
    W, H, sc = ps._spec(F)
    M = ps.MARGIN * sc
    spec = SPEC["nb-rn250-males-en-retirada"]
    df = pd.read_csv(ENTRADA / spec["dataset"])
    x0, x1 = int(df.anio.min()), int(df.anio.max())
    fig, ax = ps.nueva_figura(F)
    for col, c in SERIES_G3:
        d = df[["anio", col]].dropna()
        ax.plot(d.anio, d[col], color=c, linewidth=2.0 * sc, zorder=4,
                solid_capstyle="round", solid_joinstyle="round")
    estilo(ax, sc)
    ax.set_ylim(0, 100)
    ax.set_yticks(range(0, 101, 20))
    ax.yaxis.set_major_formatter(ps.formateador_es(0, " %"))
    ax.set_xlim(x0 - 2, x1 + 2)
    ax.set_xticks(list(range(1800, 2021, 50)))
    ax.xaxis.set_major_formatter(ps.formateador_es(0))
    meta = ficha("blog-riqueza250-males-en-retirada",
                 "Pobreza, mortalidad y analfabetismo en el mundo",
                 f"Porcentaje de la población mundial, {x0}–{x1}",
                 "Fuente: " + spec["source"] + ". " + AUTOR,
                 "Pobreza extrema: personas sin lo necesario para cubrir sus necesidades básicas. Mortalidad: "
                 "niños que mueren antes de cumplir cinco años. Analfabetismo: adultos que no saben leer ni "
                 "escribir; la serie enlaza fuentes distintas y su tropiezo alrededor de 1950 debe leerse con "
                 "cautela.",
                 "lineas", F, ["pobreza extrema", "mortalidad infantil", "alfabetización", "Our World in Data"])
    componer(fig, ax, meta)
    leyenda_lineas(fig, ax, SERIES_G3, W, H, sc, M)
    encajar_eje(fig, ax, W - M)
    cerrar(fig, meta)


# --------------------------------------------------------------------------- #
# 4 a 13 · Burbujas: el ingreso y cada indicador · 14 · el mosaico de las diez
# --------------------------------------------------------------------------- #
BUR = SPEC["nb-rn250-ingreso-y-bienestar"]
G4 = pd.read_csv(ENTRADA / BUR["dataset"])
GRUPOS = [g["name"] for g in BUR["groups"]]
GCOL = {g["name"]: g["color"] for g in BUR["groups"]}
IND = {i["col"]: i for i in BUR["indicators"]}
FOCO = BUR["focus"]
P0 = G4.poblacion.max()
LX = np.log10(G4.pib_pc)
XMIN, XMAX = 10 ** (LX.min() - 0.12), 10 ** (LX.max() + 0.12)
# capas como en el embed: el grupo con la burbuja más grande al fondo, el del foco arriba
_tope = G4.groupby("grupo").poblacion.max()
_foco_g = G4.loc[G4.iso3 == FOCO, "grupo"].iloc[0]
ORDEN_Z = sorted(GRUPOS, key=lambda g: (g == _foco_g, -_tope[g]))
FORMA = {"lineal": "lineal", "cuadratico": "cuadrática", "exponencial": "exponencial"}
TITULO_IND = {
    "esperanza_vida": "Ingreso por persona y esperanza de vida",
    "mortalidad_5": "Ingreso por persona y mortalidad en la niñez",
    "mort_materna": "Ingreso por persona y mortalidad materna",
    "hambre": "Ingreso por persona y hambre",
    "escolaridad": "Ingreso por persona y años de estudio",
    "idh": "Ingreso por persona y desarrollo humano",
    "satisfaccion": "Ingreso por persona y satisfacción con la vida",
    "horas": "Ingreso por persona y horas de trabajo",
    "pobreza": "Ingreso por persona y pobreza extrema",
    "co2": "Ingreso por persona y emisiones de carbono",
}
# rótulo de panel del mosaico: negrita real y Cada Palabra En Mayúscula (preposiciones en minúscula)
PANEL = {
    "esperanza_vida": ("Esperanza de Vida", "años"),
    "mortalidad_5": ("Mortalidad en la Niñez", "% antes de los 5 años"),
    "mort_materna": ("Mortalidad Materna", "por 100.000 nacidos vivos"),
    "hambre": ("Hambre", "% subalimentado"),
    "escolaridad": ("Años de Estudio", "adultos de 25 o más"),
    "idh": ("Desarrollo Humano", "IDH, de 0 a 1"),
    "satisfaccion": ("Satisfacción con la Vida", "de 0 a 10"),
    "horas": ("Horas de Trabajo", "al año por ocupado"),
    "pobreza": ("Pobreza Extrema", "% bajo US$ 3 al día"),
    "co2": ("Emisiones de CO₂", "toneladas por persona"),
}
X_TICKS = [1000, 2000, 5000, 10000, 20000, 50000, 100000]
FUENTE_CORTA = {
    "esperanza_vida": "Banco Mundial (2026)",
    "mortalidad_5": "Banco Mundial (2026), con datos de UN IGME",
    "mort_materna": "Banco Mundial (2026), con estimaciones de la OMS",
    "hambre": "Banco Mundial (2026), con datos de la FAO",
    "escolaridad": "PNUD, Informe sobre Desarrollo Humano 2025",
    "idh": "PNUD, Informe sobre Desarrollo Humano 2025",
    "satisfaccion": "World Happiness Report 2026 (encuesta de Gallup)",
    "horas": "Penn World Table 11.0",
    "pobreza": "Banco Mundial (2026), Plataforma de Pobreza y Desigualdad",
    "co2": "Global Carbon Budget 2025, sin cambio de uso de suelo",
}
AVISO = {   # sólo lo que cambia la lectura del gráfico
    "idh": "El IDH incluye el ingreso.",
    "hambre": "La FAO no publica cifras bajo 2,5 %: esos países van en 2,5.",
    "pobreza": "Línea de US$ 3 diarios (PPA de 2021).",
}
# en la lámina, China se rotula arriba: adentro la tapan las burbujas rojas vecinas
ROTULOS_LAMINA = {"CHN": "top", "IND": "in", "USA": "top"}


def tendencia(col):
    """La misma cuenta del embed: forma declarada en la ficha, sobre log10 del ingreso, línea
    sólo si p < 0,05. Devuelve (x, curva, inferior, superior, r, n, forma) o None."""
    d = G4[["pib_pc", col]].dropna()
    lx, y = list(np.log10(d.pib_pc)), list(d[col])
    r = float(np.corrcoef(lx, y)[0, 1])
    a = ajustar(lx, y, IND[col]["trend"], False)
    if a["p"] >= ALFA:
        return None, r, len(y)
    gx = np.linspace(min(lx), max(lx), 160)
    banda = np.array([a["banda"](v) for v in gx])
    return (10 ** gx, np.array([a["f"](v) for v in gx]), banda[:, 0], banda[:, 1]), r, len(y)


def dibujar_burbujas(ax, col, sc, max_d_px, rotulos=True, s_rot=None, lw_tend=1.0, anillo=1.0):
    """Burbujas (área ∝ población), tendencia con su banda y Bolivia con anillo. Devuelve r y n."""
    ind = IND[col]
    y0, y1 = ind["min"], ind["max"]
    pt = 72.0 / ps.DPI                                   # px → puntos tipográficos
    d = G4[["iso3", "pais", "grupo", "poblacion", "pib_pc", col]].dropna()
    diam = lambda p: np.maximum(3.5 * sc, max_d_px * np.sqrt(p / P0))
    for z, g in enumerate(ORDEN_Z, start=2):
        s = d[d.grupo == g].sort_values("poblacion", ascending=False)
        ax.scatter(s.pib_pc, s[col], s=(diam(s.poblacion) * pt) ** 2, color=GCOL[g], alpha=0.85,
                   edgecolors=FONDO, linewidths=0.9 * sc, zorder=z)
    tr, r, n = tendencia(col)
    if tr:
        gx, f, lo, hi = tr
        ax.fill_between(gx, np.clip(lo, y0, y1), np.clip(hi, y0, y1), color=TINTA, alpha=0.085,
                        linewidth=0, zorder=1)
        ax.plot(gx, np.clip(f, y0, y1), color=TINTA, alpha=0.62, linewidth=1.1 * sc * lw_tend,
                solid_capstyle="round", zorder=len(GRUPOS) + 3)
    fb = d[d.iso3 == FOCO]
    if len(fb):
        dd = float(diam(fb.poblacion.iloc[0]))
        ax.scatter(fb.pib_pc, fb[col], s=((dd + 10 * sc * anillo) * pt) ** 2, facecolors="none", edgecolors=TINTA,
                   linewidths=1.05 * sc * anillo, zorder=len(GRUPOS) + 5)
        if rotulos:
            ax.annotate("Bolivia", (fb.pib_pc.iloc[0], fb[col].iloc[0]), xytext=((dd / 2 + 13 * sc) * pt, 0),
                        textcoords="offset points", ha="left", va="center", color=TINTA,
                        fontproperties=ps.fp(ps.BOLD, s_rot), zorder=len(GRUPOS) + 6,
                        path_effects=[pe.withStroke(linewidth=3.2 * sc, foreground=FONDO)])
    if rotulos:
        for iso, modo in ROTULOS_LAMINA.items():
            fila = d[d.iso3 == iso]
            if not len(fila):
                continue
            nombre, dd = fila.pais.iloc[0], float(diam(fila.poblacion.iloc[0]))
            xy = (fila.pib_pc.iloc[0], fila[col].iloc[0])
            if modo == "in":
                ax.annotate(nombre, xy, ha="center", va="center", color=FONDO,
                            fontproperties=ps.fp(ps.BOLD, s_rot * 0.92), zorder=len(GRUPOS) + 4)
            else:
                ax.annotate(nombre, xy, xytext=(0, (dd / 2 + 6 * sc) * pt), textcoords="offset points",
                            ha="center", va="bottom", color=PIZARRA, fontproperties=ps.fp(ps.BOLD, s_rot * 0.92),
                            zorder=len(GRUPOS) + 4,
                            path_effects=[pe.withStroke(linewidth=3.2 * sc, foreground=FONDO)])
    ax.set_xscale("log")
    ax.set_xlim(XMIN, XMAX)
    rango, v = y1 - y0, d[col]
    ax.set_ylim(y0 - (0.04 * rango if v.min() < y0 + 0.03 * rango else 0),
                y1 + (0.04 * rango if v.max() > y1 - 0.03 * rango else 0))
    ax.minorticks_off()
    return r, n, tr


def ejes_y(ax, col, paso_mult=1):
    ind = IND[col]
    paso = ind["step"] * paso_mult
    ticks = np.arange(ind["min"], ind["max"] + paso / 2, paso)
    ax.set_yticks(ticks)
    dec = 0 if all(abs(t - round(t)) < 1e-9 for t in ticks) else 1
    ax.yaxis.set_major_formatter(ps.formateador_es(dec, miles=True))


def leyenda_regiones(fig, x_px, y_px, W, H, sc, s_px, ncol):
    hs = [Line2D([0], [0], marker="o", linestyle="", markersize=s_px * 0.62 * 72 / ps.DPI,
                 markerfacecolor=GCOL[g], markeredgecolor=GCOL[g], alpha=0.9) for g in GRUPOS]
    return fig.legend(hs, GRUPOS, loc="upper left", bbox_to_anchor=(x_px / W, y_px / H), ncol=ncol,
                      frameon=False, prop=ps.fp(ps.BODY, s_px), labelcolor=ps.COLORS["cafe_oscuro"],
                      handletextpad=0.35, columnspacing=1.5, borderaxespad=0, borderpad=0,
                      handlelength=0.9, labelspacing=0.55)


def burbuja(col):
    F = "informe_cuadrado"
    W, H, sc = ps._spec(F)
    M = ps.MARGIN * sc
    ind = IND[col]
    fig, ax = ps.nueva_figura(F)
    s_rot = ps.SIZES["dato"] * sc
    r, n, tr = dibujar_burbujas(ax, col, sc, max_d_px=0.062 * (W - 2 * M), s_rot=s_rot)
    estilo(ax, sc)
    ejes_y(ax, col)
    ax.set_xticks([t for t in X_TICKS if XMIN <= t <= XMAX])
    ax.xaxis.set_major_formatter(ps.formateador_es(0, miles=True))

    unidad = f" ({ind['unit']})" if ind.get("unit") else ""
    anio = ind["yr"].split(" ")[0] if ind["yr"][:1].isdigit() else ind["yr"]
    linea = f" Línea: tendencia {FORMA[ind['trend']]}; sombra: confianza del 95 %." if tr else ""
    nota = (f"r = {ps.es_num(r, 2).replace('-', '−')}, {n} países.{linea} Tamaño: población. "
            + AVISO.get(col, "")).strip()
    fte = FUENTE_CORTA[col]
    meta = ficha(f"blog-riqueza250-ingreso-{col.replace('_', '-')}", TITULO_IND[col],
                 f"{ind['label']}{unidad}, {anio}. Eje horizontal: PIB per cápita de 2024 (PPA), en escala logarítmica",
                 f"Fuente: {fte}" + ("" if fte.startswith("Banco Mundial") else "; Banco Mundial (PIB per cápita)")
                 + f"; Maddison (regiones). {AUTOR}",
                 nota, "dispersion", F,
                 ["PIB per cápita", "regresión", ind["btn"], "Bolivia"])
    componer(fig, ax, meta)
    # la leyenda de regiones entre el subtítulo y el gráfico: el eje cede ese alto
    p = ax.get_position()
    s_ley = ps.SIZES["leyenda"] * sc
    alto_ley = 2 * s_ley * 1.55 + 26 * sc
    ley = leyenda_regiones(fig, M, p.y1 * H + 6 * sc, W, H, sc, s_ley, ncol=3)
    fig.canvas.draw()
    if ley.get_window_extent(fig.canvas.get_renderer()).x1 > W - M:
        ley.remove()
        alto_ley = 3 * s_ley * 1.55 + 26 * sc
        leyenda_regiones(fig, M, p.y1 * H + 6 * sc, W, H, sc, s_ley, ncol=2)
    ax.set_position([p.x0, p.y0, p.width, p.height - alto_ley / H])
    encajar_eje(fig, ax, W - M)
    cerrar(fig, meta)


def mosaico():
    F = F_MOS
    W, H, sc = ps._spec(F)
    M = ps.MARGIN * sc
    COLS, ROWS = 5, 2
    orden = [i["col"] for i in BUR["indicators"]]
    fig, axd = ps.nueva_figura(F)
    axd.set_xticks([]); axd.set_yticks([])
    meta = ficha("blog-riqueza250-ingreso-y-bienestar-mosaico",
                 "Ingreso por persona y bienestar: diez indicadores",
                 "Cada indicador frente al PIB per cápita de 2024 en dólares internacionales de 2021 "
                 "(PPA, escala logarítmica)",
                 "Fuente: Banco Mundial, Indicadores del Desarrollo Mundial; PNUD, Informe sobre Desarrollo "
                 "Humano 2025; Penn World Table 11.0; World Happiness Report 2026; Global Carbon Budget 2025; "
                 "Maddison Project Database 2023 (regiones). " + AUTOR,
                 "Cada burbuja es un país; su tamaño, la población; su color, la región según Maddison. La línea "
                 "es la tendencia (lineal, cuadrática o exponencial, según el indicador) y la sombra, su banda "
                 "de confianza del 95 %; r es la correlación con el logaritmo del ingreso. Bolivia va con anillo.",
                 "small_multiples", F, ["PIB per cápita", "regresión", "bienestar", "redes"])
    componer(fig, axd, meta)
    pos = axd.get_position()
    axd.set_visible(False)

    s_ley = ps.SIZES["leyenda"] * sc
    alto_ley = 2 * s_ley * 1.55 + 34 * sc
    leyenda_regiones(fig, M, pos.y1 * H + 4 * sc, W, H, sc, s_ley, ncol=3)
    grid_w, grid_h = pos.width * W, pos.height * H - alto_ley
    gap_y, rot_h = 64 * sc, 66 * sc
    cellH = (grid_h - (ROWS - 1) * gap_y) / ROWS
    panelH = cellH - rot_h
    s_eje = ps.SIZES["eje"] * sc * 0.82
    fp_eje = ps.fp(ps.BODY, s_eje)
    s_rot, s_uni = ps.SIZES["leyenda"] * sc * 0.97, ps.SIZES["fuente"] * sc * 0.92

    ejes, celdas = [], []
    for i, col in enumerate(orden):
        c, r_ = i % COLS, i // COLS
        cx = pos.x0 * W + c * (grid_w / COLS)
        cy = pos.y0 * H + (ROWS - 1 - r_) * (cellH + gap_y)
        ax = fig.add_axes([cx / W, cy / H, (grid_w / COLS - 40 * sc) / W, panelH / H])
        r, n, tr = dibujar_burbujas(ax, col, sc, max_d_px=0.16 * grid_w / COLS, rotulos=False, lw_tend=0.95, anillo=0.8)
        estilo(ax, sc)
        ejes_y(ax, col, paso_mult=2 if (IND[col]["max"] - IND[col]["min"]) / IND[col]["step"] > 5 else 1)
        ax.set_xticks([t for t in (1000, 10000, 100000) if XMIN <= t <= XMAX])
        ax.xaxis.set_major_formatter(ps.formateador_es(0, miles=True))
        ax.tick_params(axis="x", length=4 * sc, pad=4 * sc)
        for lbl in ax.get_xticklabels() + ax.get_yticklabels():
            lbl.set_fontproperties(fp_eje)
        # la r va a la esquina que la nube deja libre: arriba a la izquierda si sube, a la derecha si baja
        ax.text(0.97 if r < 0 else 0.03, 0.97, f"r = {ps.es_num(r, 2).replace('-', '−')}", transform=ax.transAxes,
                ha="right" if r < 0 else "left", va="top", color=PIZARRA,
                fontproperties=ps.fp(ps.BOLD, s_eje), zorder=20,
                path_effects=[pe.withStroke(linewidth=3 * sc, foreground=FONDO)])
        ejes.append(ax); celdas.append((cx, cy))

    # Encuadre en dos pasadas (la receta de small-multiples): los diez paneles miden EXACTAMENTE
    # lo mismo, con un canal libre fijo entre la tinta de una columna y la de la siguiente
    for _ in range(4):
        fig.canvas.draw()
        rend = fig.canvas.get_renderer()
        izq, der = [], []
        for ax in ejes:
            p = ax.get_position()
            sx, aw0 = p.x0 * W, p.width * W
            x0s = [l.get_window_extent(rend).x0 for l in ax.get_yticklabels() if l.get_text()]
            izq.append(sx - min(x0s) if x0s else 0.0)
            x1s = [l.get_window_extent(rend).x1 for l in ax.get_xticklabels() if l.get_text()]
            x1s.append(ax.spines["bottom"].get_window_extent(rend).x1)
            der.append(max(x1s) - (sx + aw0))
        B = [max(izq[c::COLS]) for c in range(COLS)]
        R = [max(der[c::COLS]) for c in range(COLS)]
        K = max(R[c] + B[c + 1] for c in range(COLS - 1)) + 46 * sc
        ancho = (grid_w - B[0] - R[-1] - (COLS - 1) * K) / COLS
        paso = ancho + K
        columnas = [pos.x0 * W + B[0] + c * paso for c in range(COLS)]
        for i, ax in enumerate(ejes):
            p = ax.get_position()
            ax.set_position([columnas[i % COLS] / W, p.y0, ancho / W, p.height])
    # rótulo de cada panel al borde de su celda (a plomo con el título en la primera columna)
    for i, col in enumerate(orden):
        cx = columnas[i % COLS] - B[i % COLS]
        cy = celdas[i][1]
        nom, uni = PANEL[col]
        fig.text(cx / W, (cy + panelH + 12 * sc + s_uni * 1.25) / H, nom, fontproperties=ps.fp(ps.BOLD, s_rot),
                 color=ps.COLORS["cafe_oscuro"], va="bottom", ha="left")
        fig.text(cx / W, (cy + panelH + 10 * sc) / H, uni, fontproperties=ps.fp(ps.BODY, s_uni),
                 color=PIZARRA, va="bottom", ha="left")
    cerrar(fig, meta)


def copiar_al_blog():
    """Los PNG que baja el botón «Descargar imagen» de la entrada (mismo origen que el embed)."""
    DESCARGAS.mkdir(parents=True, exist_ok=True)
    for slug in HECHAS:
        shutil.copy2(CAT.GRAFICAS / f"{slug}.png", DESCARGAS / f"{slug}.png")
    print(f"→ {len(HECHAS)} PNG copiados a {DESCARGAS}")


LAMINAS = {"hockey": lambda: hockey(False), "log": lambda: hockey(True), "males": males,
           "burbujas": lambda: [burbuja(i["col"]) for i in BUR["indicators"]], "mosaico": mosaico}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo", default="", help="coma: " + ",".join(LAMINAS))
    ap.add_argument("--blog", action="store_true", help="copia los PNG a blog-graficos/descargas")
    ap.add_argument("--sin-contrato", action="store_true", help="no corre verificar.py (iterar el diseño)")
    args = ap.parse_args()
    for s in [s for s in args.solo.split(",") if s] or list(LAMINAS):
        LAMINAS[s]()
    CAT.build_manifest()
    if args.blog:
        copiar_al_blog()
    if args.sin_contrato:
        return
    r = subprocess.run([sys.executable, str(VIZ / "verificar.py")], cwd=VIZ.parent,
                       capture_output=True, text=True, encoding="utf-8")
    print("\n".join(r.stdout.strip().splitlines()[-3:]))
    if r.returncode:
        raise SystemExit("⛔ el contrato del Banco no pasa:\n" + r.stdout[-1500:] + r.stderr[-800:])


if __name__ == "__main__":
    main()

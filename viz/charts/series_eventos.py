"""
Serie temporal anotada con eventos — helpers del estilo "figura de publicación".

Este módulo NO dibuja la figura completa: aporta las piezas reutilizables del
estilo editorial POPULI para series temporales económicas:

  · eje de fechas con ticks mensuales en español (`ticks_mensuales`, `estilo_eje`)
  · sistema de anotación de eventos: banda translúcida sobre la semana del hito
    + callout (texto, con guía y círculo en paneles grandes) (`marcar_eventos`)

La composición concreta (cuántos paneles, apilado vs. small multiples, layout de
cada callout) vive en el script de autoría de cada gráfico (ver
`viz/recetas/series-eventos/figura.py`). Así el "estilo" se reutiliza sin
encorsetar el relato de cada publicación.

Todo el color/tipografía sale de `populi_style.py`; este módulo no inventa nada.
"""
import datetime as dt
from matplotlib.dates import date2num
import populi_style as ps

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

# Negrita REAL: hay que cargar el archivo Bold; weight="bold" sobre un fname
# Regular no sintetiza negrita en matplotlib.
BOLD = "Public Sans Bold" if "Public Sans Bold" in ps._REGISTERED else ps.BODY


# ── Color semántico de los eventos ──────────────────────────────────────────
def colores_evento():
    """Paleta por defecto: ingreso (teal) · caída (rojo) · estimado (pizarra)."""
    return {
        "up":   ps.col("serie_teal"),   # ingreso / suba
        "down": ps.COLORS["rojo"],      # caída
        "est":  ps.COLORS["pizarra"],   # punto estimado / proyección
    }


def color_evento(e, paleta=None):
    """Color de un evento según `estimated` (prioritario) y `dir` (up/down)."""
    p = paleta or colores_evento()
    if e.get("estimated"):
        return p["est"]
    return p["up"] if e.get("dir") == "up" else p["down"]


# ── Eje de fechas (ticks mensuales en español) ──────────────────────────────
def ticks_mensuales(dates):
    """Un tick por mes presente en `dates` (lista de datetime.date).
    Etiqueta con año bajo el mes solo en enero y diciembre."""
    ticks, labels, seen = [], [], set()
    for d in dates:
        key = (d.year, d.month)
        if key in seen:
            continue
        seen.add(key)
        ticks.append(date2num(dt.date(d.year, d.month, 1)))
        labels.append(f"{MESES[d.month-1]}\n{d.year}" if d.month in (1, 12) else MESES[d.month-1])
    return ticks, labels


def estilo_eje(ax, dates, sc, y_decimales=0, y_miles=True):
    """Aplica el look editorial POPULI a un panel de serie temporal:
    fondo crema, solo eje X (café), grilla Y tenue, ticks mensuales y números
    con separador de miles. `sc` = factor de escala del formato (ver ps._spec)."""
    ax.set_facecolor(ps.COLORS["fondo"])
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(ps.COLORS["cafe"])
    ax.spines["bottom"].set_linewidth(1.2 * sc)
    ax.grid(axis="y", color=ps.COLORS["borde"], linewidth=1.0 * sc, alpha=0.9, zorder=0)
    ax.set_axisbelow(True)
    t, l = ticks_mensuales(dates)
    ax.set_xticks(t)
    ax.set_xticklabels(l)
    ax.tick_params(axis="x", length=5 * sc, width=1.0 * sc, color=ps.COLORS["cafe"],
                   labelcolor=ps.COLORS["cafe"], pad=6 * sc)
    ax.tick_params(axis="y", length=0, labelcolor=ps.COLORS["cafe"], pad=5 * sc)
    for lbl in ax.get_xticklabels():
        lbl.set_fontproperties(ps.fp(ps.BODY, ps.SIZES["eje"] * 0.80 * sc))
    for lbl in ax.get_yticklabels():
        lbl.set_fontproperties(ps.fp(ps.MONO, ps.SIZES["eje"] * 0.80 * sc))
    ax.yaxis.set_major_formatter(ps.formateador_es(y_decimales, "", miles=y_miles))


# ── Anotación de eventos (banda + punto + guía + etiqueta) ───────────────────
def marcar_eventos(ax, eventos, *, x, fechas, panel, ymin, ymax, sc=1.0, serie_y=None,
                   layout=None, abbr=None, detalle=None, paleta=None,
                   banda_alpha=0.18):
    """Dibuja los eventos cuyo `panels` incluye `panel`, estilo editorial:
    banda translúcida sobre la semana del hito · punto hueco sobre la línea ·
    guía vertical fina hasta una etiqueta de dos líneas (nombre en negrita +
    detalle gris). La etiqueta se ancla a una ALTURA limpia (fracción `ly` del
    panel), no encima del dato, para que respire.

    Cada evento es un dict con: `date` (ISO), `dir` ('up'|'down'),
    `short` (texto), `panels` (lista) y opcional `estimated`.

    Parámetros:
      · `x`        array de posiciones (date2num) alineado con `fechas`.
      · `fechas`   lista de fechas ISO en el mismo orden que `x`.
      · `ymin/ymax` rango del panel (para situar la etiqueta por fracción).
      · `serie_y`  valores de la serie (ancla el punto y la guía al dato real).
      · `layout`   dict {(panel, date): {ly, dx}} — `ly` = altura 0-1 de la base
                   de la etiqueta; `dx` = corrimiento horizontal del bloque
                   (fracción del rango X; la etiqueta va siempre centrada).
      · `banda_alpha` opacidad de la banda; 0 = sin banda (solo punto + guía).
      · `abbr`     dict {(panel, date): "nombre"} (1ª línea; def. `short`).
      · `detalle`  dict {(panel, date): "detalle"} (2ª línea, gris; opcional).
      · `banda_alpha` opacidad de la banda de la semana.
    """
    layout = layout or {}
    abbr = abbr or {}
    detalle = detalle or {}
    f_nom = ps.fp(BOLD, ps.SIZES["dato"] * 0.86 * sc)        # nombre: negrita real, +chico
    f_det = ps.fp(ps.BODY, ps.SIZES["dato"] * 0.72 * sc)     # detalle: gris, +chico

    # alto de la línea de detalle en UNIDADES DE DATO (para apilar nombre encima)
    rng = ymax - ymin
    ax_h_pt = ax.get_position().height * ax.figure.get_figheight() * 72.0
    dpp = rng / ax_h_pt if ax_h_pt else 0.0          # unidades de dato por punto
    det_dh = (ps.SIZES["dato"] * 0.72 * sc * 72.0 / ps.DPI) * 1.25 * dpp

    for e in eventos:
        if panel not in e.get("panels", []):
            continue
        if e["date"] not in fechas:
            continue
        i = fechas.index(e["date"])
        if i <= 0:
            continue
        col = color_evento(e, paleta)
        if banda_alpha > 0:
            ax.axvspan(x[i-1], x[i], color=col, alpha=banda_alpha, linewidth=0, zorder=2)

        lay = layout.get((panel, e["date"]), dict(ly=0.90, dx=0.0))
        ly = lay.get("ly", 0.90)
        dxf = lay.get("dx", 0.0)
        cx = x[i]
        xa = cx + dxf * (x[-1] - x[0])               # ancla horizontal del bloque
        yv = serie_y[i] if serie_y is not None else (ymin + ly * rng)
        y0 = ymin + ly * rng                         # base del bloque de etiqueta
        nom = abbr.get((panel, e["date"]), e["short"])
        det = detalle.get((panel, e["date"]), "")

        if serie_y is not None:
            ax.scatter([cx], [yv], s=40 * sc, facecolors=ps.COLORS["fondo"],
                       edgecolors=col, linewidths=1.6 * sc, zorder=9)
        # línea base (detalle si lo hay, si no el nombre) lleva la guía al punto;
        # AMBAS líneas centradas sobre el mismo ancla (xa)
        base, base_fp, base_col = (det, f_det, ps.COLORS["gris"]) if det else (nom, f_nom, col)
        ax.annotate(base, xy=(cx, yv), xytext=(xa, y0), textcoords="data",
                    ha="center", va="bottom", fontproperties=base_fp, color=base_col, zorder=10,
                    arrowprops=dict(arrowstyle="-", color=col, lw=1.0 * sc, alpha=0.55,
                                    shrinkA=4, shrinkB=6))
        if det:   # nombre en negrita, apilado y centrado encima del detalle
            ax.text(xa, y0 + det_dh, nom, ha="center", va="bottom",
                    fontproperties=f_nom, color=col, zorder=10)

"""
barras_apiladas.py — Barras apiladas de CONTRIBUCIÓN (admiten valores negativos).

  grafico_barras_apiladas(df, series=["c1","c2",...], ...)

A diferencia de `areas.py` (áreas apiladas, solo valores positivos), aquí cada
componente puede ser positivo o negativo: los positivos se apilan hacia arriba y
los negativos hacia abajo desde la línea de cero. Es el formato canónico de los
gráficos de "determinantes/factores" de un banco central, donde una serie puede
cruzar el cero (p. ej. el crédito al sector público) sin dejar huecos — algo que
un gráfico de áreas no resuelve.

Opciones clave:
  normalizar=True   cada barra se escala a % del total neto (suma de las series),
                    de modo que la composición sume 100 %.
  total=<col>       traza una línea con el total (p. ej. la base monetaria).
  referencia=<y>    línea horizontal de referencia (p. ej. 100 en modo %).
  fases=[...]       divisores verticales tenues + etiqueta de etapa (estilo FMI).
  leyenda=True      leyenda compacta sin marco (las bandas con signo no se pueden
                    rotular al final como en áreas).
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
from matplotlib.patches import Patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import populi_style as ps


def grafico_barras_apiladas(df, series, etiquetas=None, colores=None,
                            titulo="", subtitulo="", fuente="", nota="",
                            normalizar=False, total=None, total_label="Total",
                            total_color="tinta", referencia=None, referencia_label="",
                            formato="red_cuadrada", archivo=None, titulo_familia=None,
                            y_sufijo="", y_decimales=0, y_miles=False, ancho=0.82,
                            alpha=1.0, total_lw=2.6, fuente_scale=1.0,
                            leyenda=True, leyenda_loc="lower center", leyenda_ncol=3,
                            headroom_top=0.0, headroom_bottom=0.0, x_anios=False,
                            fases=None, rotulos=None, margen=None, top=None, bottom=None):
    fig, ax = ps.nueva_figura(formato)
    _, _, sc = ps._spec(formato)
    x = df.index.to_numpy(dtype=float)
    nombres = etiquetas or list(series)
    cols = [ps.col(c) for c in (colores or ps.PALETTE)]
    datos = {s: df[s].to_numpy(dtype=float) for s in series}

    if normalizar:                       # cada componente como % del total neto
        neto = np.sum([datos[s] for s in series], axis=0)
        neto = np.where(neto == 0, np.nan, neto)
        datos = {s: datos[s] / neto * 100.0 for s in series}

    ancho_x = ancho * (float(np.min(np.diff(x))) if len(x) > 1 else 1.0)
    pos = np.zeros(len(x))
    neg = np.zeros(len(x))
    for k, s in enumerate(series):
        v = datos[s]
        c = cols[k % len(cols)]
        base_k = np.where(v >= 0, pos, neg)
        ax.bar(x, v, bottom=base_k, width=ancho_x, color=c, alpha=alpha,
               linewidth=0, zorder=3, align="center")
        pos = pos + np.where(v >= 0, v, 0.0)
        neg = neg + np.where(v < 0, v, 0.0)

    ps.aplicar_estilo_ejes(ax, cero=True)        # línea de y=0 (clave aquí)
    ax.yaxis.set_major_formatter(ps.formateador_es(y_decimales, y_sufijo, miles=y_miles))
    # marcas X en años enteros: si la x ya es entera, o si x_anios=True (x decimal
    # que representa años, p. ej. una serie mensual como 2005 + (mes-1)/12)
    if x_anios or all(float(v).is_integer() for v in x):
        ps.ticks_x_enteros(ax, x)
    ax.margins(x=0.01, y=0.06)

    # franjas de aire arriba (para etiquetas de fase) y abajo (para la leyenda),
    # de modo que ni las fases ni la leyenda se encimen con las barras.
    # Guardamos la banda de DATOS para acotar ahí los divisores de fase.
    ydata_lo, ydata_hi = ax.get_ylim()
    if headroom_top or headroom_bottom:
        rng = ydata_hi - ydata_lo
        ax.set_ylim(ydata_lo - rng * headroom_bottom, ydata_hi + rng * headroom_top)

    import matplotlib.patheffects as pe
    halo = [pe.withStroke(linewidth=3.2 * sc, foreground=ps.COLORS["fondo"])]

    # línea de referencia (p. ej. 100% en modo normalizado)
    if referencia is not None:
        ax.axhline(referencia, color=ps.COLORS["cafe"], linewidth=1.2 * sc,
                   linestyle=(0, (5, 4)), alpha=0.7, zorder=4)
        if referencia_label:
            t = ax.annotate(referencia_label, (x[0], referencia), xytext=(2 * sc, 5 * sc),
                            textcoords="offset points", va="bottom", ha="left",
                            color=ps.COLORS["cafe"], zorder=8,
                            fontproperties=ps.fp(ps.BODY, ps.SIZES["dato"] * 0.9 * sc, weight="bold"))
            t.set_path_effects(halo)

    # línea de total (p. ej. base monetaria, en modo nivel)
    if total is not None and not normalizar:
        tv = df[total].to_numpy(dtype=float)
        ax.plot(x, tv, color=ps.col(total_color), linewidth=total_lw * sc, zorder=6,
                solid_capstyle="round")
        ax.scatter([x[-1]], [tv[-1]], s=26 * sc, color=ps.col(total_color),
                   edgecolors=ps.COLORS["fondo"], linewidths=1.2 * sc, zorder=7)

    # fases: divisores verticales tenues (acotados a la banda de datos, sin
    # invadir las franjas de leyenda/encabezado) + etiqueta de etapa arriba
    if fases:
        y0, y1 = ax.get_ylim()
        bordes = sorted({f["x0"] for f in fases} | {f["x1"] for f in fases})
        for b in bordes:
            ax.plot([b, b], [ydata_lo, ydata_hi], color=ps.COLORS["cafe"],
                    linewidth=0.9 * sc, linestyle=(0, (5, 4)), alpha=0.34, zorder=2)
        f_an = ps.fp(ps.BODY, ps.SIZES["dato"] * 0.92 * sc, weight="bold")
        for f in fases:
            xm = f.get("lx", (f["x0"] + f["x1"]) / 2)
            ym = y0 + (y1 - y0) * f.get("ly", 0.965)
            t = ax.text(xm, ym, f["texto"], ha=f.get("ha", "center"), va="top",
                        fontproperties=f_an, color=ps.COLORS["cafe"], zorder=7,
                        linespacing=1.1)
            t.set_path_effects(halo)

    # rótulos libres dentro del gráfico (coords de datos)
    if rotulos:
        f_rot = ps.fp(ps.BODY, ps.SIZES["fin_linea"] * 0.9 * sc, weight="bold")
        for r in rotulos:
            ax.text(r["x"], r["y"], r["texto"], fontproperties=f_rot,
                    color=ps.col(r.get("color", "tinta")), ha=r.get("ha", "center"),
                    va=r.get("va", "center"), zorder=9)

    # leyenda compacta sin marco (incluye el total si lo hay)
    if leyenda:
        handles = [Patch(facecolor=cols[k % len(cols)], edgecolor="none", label=nombres[k])
                   for k in range(len(series))]
        if total is not None and not normalizar:
            from matplotlib.lines import Line2D
            handles.append(Line2D([0], [0], color=ps.col(total_color),
                                  linewidth=total_lw * sc, label=total_label))
        leg = ax.legend(handles=handles, loc=leyenda_loc, ncol=leyenda_ncol,
                        frameon=False, handlelength=1.1, handleheight=1.1,
                        columnspacing=1.2, labelspacing=0.5, borderpad=0.2,
                        prop=ps.fp(ps.BODY, ps.SIZES["leyenda"] * sc))
        for t in leg.get_texts():
            t.set_color(ps.COLORS["cafe_oscuro"])

    ps.componer(fig, ax, titulo, subtitulo, fuente, nota, formato, titulo_familia,
                margen=margen, top=top, bottom=bottom, fuente_scale=fuente_scale)
    if archivo:
        ps.guardar(fig, archivo, formato=formato)
    return fig, ax

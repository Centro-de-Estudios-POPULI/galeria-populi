"""
areas.py — Áreas apiladas (composición a lo largo del tiempo).

  grafico_areas(df, series=["col1","col2",...], normalizar=False, ...)

`series` es la lista de columnas a apilar (de abajo hacia arriba). Con
normalizar=True se convierte a 100 %. Etiqueta cada banda al final (estilo FMI).
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import populi_style as ps


def grafico_areas(df, series, etiquetas=None, titulo="", subtitulo="", fuente="",
                  nota="", normalizar=False, colores=None, formato="red_vertical",
                  archivo=None, titulo_familia=None, y_sufijo="%",
                  lineas_division=True, fases=None, alpha=0.82, eventos=None,
                  margen=None, top=None, bottom=None, division_px=0.6,
                  y_miles=False, rotulos=None, guias=None):
    """Áreas apiladas. `alpha` controla la transparencia de las bandas.
    `lineas_division` traza una línea fina en el borde superior de cada banda.
    `fases` = lista de {"x0","x1","texto", lx?,ly?,ha?} dibuja divisores verticales
    tenues en los límites y una etiqueta de etapa (por defecto centrada arriba).
    `eventos` = lista de {"x0","x1","texto","ly","dx"} marca cada periodo con una
    banda vertical translúcida y una etiqueta conectada por una guía fina que
    termina en un círculo abierto sobre la banda (estilo IMF F&D). `ly` = altura
    de la etiqueta (coords de datos); `dx` = desplazamiento horizontal del texto
    respecto al centro de la banda (negativo = texto a la izquierda)."""
    fig, ax = ps.nueva_figura(formato)
    _, _, sc = ps._spec(formato)
    x = df.index.to_numpy()
    datos = np.array([df[c].to_numpy(dtype=float) for c in series])  # (series, x)
    if normalizar:
        datos = datos / datos.sum(axis=0) * 100.0
    nombres = etiquetas or list(series)
    cols = [ps.col(c) for c in (colores or ps.PALETTE)]

    acum = np.zeros(datos.shape[1])
    fin = []
    for k, nombre in enumerate(nombres):
        c = cols[k % len(cols)]
        ax.fill_between(x, acum, acum + datos[k], color=c, alpha=alpha,
                        linewidth=0, zorder=3)
        # línea de división muy fina en el borde superior de la banda (estilo FMI)
        if lineas_division:
            ax.plot(x, acum + datos[k], color=ps.COLORS["fondo"],
                    linewidth=division_px * sc, zorder=4, solid_capstyle="round")
        fin.append((x[-1], acum[-1] + datos[k][-1] / 2, nombre, c))
        acum += datos[k]

    ps.aplicar_estilo_ejes(ax, grid_y=not normalizar)
    if normalizar:
        ax.set_ylim(0, 100)
    else:                       # sin negativos: el eje arranca exacto en 0
        ax.set_ylim(bottom=0)
    ax.yaxis.set_major_formatter(ps.formateador_es(0, y_sufijo, miles=y_miles))
    if all(float(v).is_integer() for v in x):
        ps.ticks_x_enteros(ax, x)
    else:  # x decimal (años): poda marcas fuera del rango (evita un 2030 vacío)
        ax.set_xticks([t for t in ax.get_xticks() if x.min() <= t <= x.max()])
    ax.margins(x=0.0)

    # --- eventos/etapas estilo F&D: banda translúcida + guía con círculo ----- #
    # cada evento: {"x0","x1","texto","ly","dx", alpha?, divisor?}. dx>0 pone el
    # texto a la DERECHA del círculo (útil cuando el blanco está a ese lado).
    if eventos:
        f_ev = ps.fp(ps.BODY, ps.SIZES["dato"] * 0.9 * sc)
        ylo, yhi = ax.get_ylim()
        for e in eventos:
            cx = e.get("cx", (e["x0"] + e["x1"]) / 2)      # posición del círculo
            a = e.get("alpha", 0.06)
            if a > 0:
                ax.axvspan(e["x0"], e["x1"], color=ps.col(e.get("color", "rojo")),
                           alpha=a, linewidth=0, zorder=2)
            if e.get("divisor"):                           # línea tenue de era
                ax.plot([e["x0"], e["x0"]], [ylo, yhi], color=ps.COLORS["cafe"],
                        linewidth=0.8 * sc, alpha=0.28, zorder=5)
            ly = e["ly"]
            dx = e.get("dx", -10)
            tx = cx + dx
            ha = "right" if dx < 0 else "left"
            gap = 0.4 if dx < 0 else -0.4                  # respiro texto↔guía
            ax.plot([tx + gap, cx], [ly, ly], color=ps.COLORS["cafe"],
                    linewidth=1.0 * sc, zorder=7, solid_capstyle="round")
            ax.scatter([cx], [ly], s=40 * sc, facecolors=ps.COLORS["fondo"],
                       edgecolors=ps.COLORS["cafe"], linewidths=1.1 * sc, zorder=8)
            ax.text(tx, ly, e["texto"], ha=ha, va="center", fontproperties=f_ev,
                    color=ps.COLORS["cafe"], zorder=8, linespacing=1.12)

    # --- alertas de texto por etapas (estilo divisor vertical, alternativo) -- #
    if fases:
        y0, y1 = ax.get_ylim()
        bordes = sorted({f["x0"] for f in fases} | {f["x1"] for f in fases})
        for b in bordes:
            ax.plot([b, b], [y0, y1], color=ps.COLORS["cafe"], linewidth=0.9 * sc,
                    linestyle=(0, (5, 4)), alpha=0.38, zorder=6)
        f_an = ps.fp(ps.BODY, ps.SIZES["dato"] * 0.9 * sc)   # tags de etapa discretos
        for f in fases:
            xm = f.get("lx", (f["x0"] + f["x1"]) / 2)
            ym = y1 * f.get("ly", 0.95)
            ax.text(xm, ym, f["texto"], ha=f.get("ha", "center"), va="top",
                    fontproperties=f_an, color=ps.COLORS["cafe"], zorder=7,
                    linespacing=1.12)

    # rotulos = [{x, y, texto, color, ha?, va?}] rotula las series DENTRO de sus
    # bandas (coords de datos) en vez de al final de la línea; guias = [{x,y0,y1}]
    # traza guías verticales finas (para señalar bandas demasiado angostas).
    if rotulos is None:
        ps.etiquetas_fin_linea(ax, fin, expandir=0.22)
    else:
        f_rot = ps.fp(ps.BODY, ps.SIZES["fin_linea"] * 0.88 * sc, weight="bold")
        for r in rotulos:
            ax.text(r["x"], r["y"], r["texto"], fontproperties=f_rot,
                    color=ps.col(r.get("color", "tinta")), ha=r.get("ha", "center"),
                    va=r.get("va", "center"), zorder=9)
        for g in (guias or []):
            ax.plot([g["x"], g["x"]], [g["y0"], g["y1"]], color=ps.COLORS["cafe"],
                    linewidth=1.0 * sc, zorder=9, solid_capstyle="round")
    ps.componer(fig, ax, titulo, subtitulo, fuente, nota, formato, titulo_familia,
                margen=margen, top=top, bottom=bottom)
    if archivo:
        ps.guardar(fig, archivo, formato=formato)
    return fig, ax

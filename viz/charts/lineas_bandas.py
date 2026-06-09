"""
lineas_bandas.py — Líneas con bandas de confianza (estilo IRF / FMI).

El gráfico insignia: una o más series temporales, cada una con una banda
opcional (intervalo de confianza) dibujada suavemente debajo de la línea, y la
etiqueta de la serie al final de su trazo (sin leyenda).

API:
    from charts.lineas_bandas import grafico_lineas_bandas
    grafico_lineas_bandas(
        df,                         # índice = eje X
        series=[
            {"y": "col", "lo": "col_lo", "hi": "col_hi",
             "label": "Etiqueta", "color": "rojo"},   # color por nombre o HEX
            ...
        ],
        titulo=..., subtitulo=..., eje_x=..., fuente=..., nota=...,
        formato="red_vertical", archivo="output/grafico.png",
    )
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import populi_style as ps


def grafico_lineas_bandas(df, series, titulo="", subtitulo="", eje_x="",
                          fuente="", nota="", formato="red_vertical",
                          archivo=None, titulo_familia=None, cero=None,
                          y_decimales=2, y_sufijo=""):
    """Dibuja líneas + bandas con la identidad POPULI. Devuelve (fig, ax)."""
    fig, ax = ps.nueva_figura(formato)
    _, _, sc = ps._spec(formato)
    x = df.index.to_numpy()

    fin = []
    hay_negativos = False
    for s in series:
        color = ps.col(s.get("color", "rojo"))
        y = df[s["y"]].to_numpy()
        hay_negativos = hay_negativos or (y.min() < 0)
        # banda de confianza, debajo de la línea
        if s.get("lo") and s.get("hi"):
            ax.fill_between(x, df[s["lo"]].to_numpy(), df[s["hi"]].to_numpy(),
                            color=color, alpha=0.16, linewidth=0, zorder=1)
        ax.plot(x, y, color=color, linewidth=3.6 * sc, solid_capstyle="round",
                solid_joinstyle="round", zorder=4)
        if s.get("label"):
            fin.append((x[-1], y[-1], s["label"], color))

    # línea de cero si hay valores negativos (salvo override explícito)
    dibujar_cero = hay_negativos if cero is None else cero
    ps.aplicar_estilo_ejes(ax, cero=dibujar_cero)
    ax.yaxis.set_major_formatter(ps.formateador_es(y_decimales, y_sufijo))
    if eje_x:
        # labelpad va en PUNTOS; ~10pt ≈ 28px de separación a los números del eje
        ax.set_xlabel(eje_x, color=ps.COLORS["cafe"], labelpad=10 * sc,
                      fontproperties=ps.fp(ps.BODY, ps.SIZES["eje"] * sc))
    ax.margins(x=0.02)
    # ticks enteros si el eje X es entero (evita marcas fantasma al ensanchar)
    if all(float(v).is_integer() for v in x):
        ps.ticks_x_enteros(ax, x)
    else:  # x decimal (años): poda marcas fuera del rango (evita un 2030 vacío)
        ax.set_xticks([t for t in ax.get_xticks() if x.min() <= t <= x.max()])
    ps.etiquetas_fin_linea(ax, fin)

    ps.componer(fig, ax, titulo=titulo, subtitulo=subtitulo, fuente=fuente,
                nota=nota, formato=formato, titulo_familia=titulo_familia)
    if archivo:
        ps.guardar(fig, archivo, formato=formato)
    return fig, ax

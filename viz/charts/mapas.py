"""
mapas.py — Mapas coropléticos (GeoPandas) con la identidad POPULI.

Hereda el estilo de populi_style: título/subtítulo alineados y pie de marca. El
mapa usa la proporción geográfica real (corrección por latitud), sin ejes, y se
inscribe centrado en el área disponible. La escala de color va en una FRANJA
propia arriba (no se encima con el mapa).

  grafico_mapa(gdf, value_col, titulo=…, leyenda=…, paleta="calido", …)

Paletas (ver populi_style.PALETAS): "calido" (default, secuencial ancha),
"rojo", "azul", "verde" (secuenciales) y "divergente" (azul↔crema↔rojo, con
TwoSlopeNorm centrada en 0, para variables con signo).

`gdf` debe traer ya unida la columna `value_col`. Los polígonos sin dato (NaN)
se pintan en gris neutro.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import populi_style as ps


# color de acento (P y/o línea de firma) según la paleta del mapa
PALETA_ACENTO = {
    "calido": "#8B1A1A", "rojo": "#8B1A1A", "azul": "#1A2940",
    "verde": "#0D7E72", "divergente": "#8B1A1A",
}


def grafico_mapa(gdf, value_col, titulo="", subtitulo="", fuente="", nota="",
                 formato="red_vertical", archivo=None, titulo_familia=None,
                 paleta="calido", leyenda="", label_fmt="{:.0f}", sufijo="",
                 acento_p=None, acento_linea=None):
    from matplotlib.colors import Normalize, TwoSlopeNorm
    fig, ax = ps.nueva_figura(formato)
    W, H, sc = ps._spec(formato)

    diverging = (paleta == "divergente")
    cmap = ps.colormap(paleta)
    vals = gdf[value_col].astype(float)
    vmin, vmax = float(np.nanmin(vals)), float(np.nanmax(vals))
    if diverging:
        m = max(abs(vmin), abs(vmax)) or 1.0
        norm = TwoSlopeNorm(vmin=-m, vcenter=0, vmax=m)
    else:
        norm = Normalize(vmin, vmax)

    # municipios sin dato → gris neutro; el resto coloreado
    falta = gdf[gdf[value_col].isna()]
    if len(falta):
        falta.plot(ax=ax, color=ps.COLORS["gris_claro"],
                   edgecolor=ps.COLORS["fondo"], linewidth=0.4 * sc, zorder=2)
    gdf[gdf[value_col].notna()].plot(
        ax=ax, column=value_col, cmap=cmap, norm=norm,
        edgecolor=ps.COLORS["fondo"], linewidth=0.4 * sc, zorder=3)

    ax.axis("off")
    minx, miny, maxx, maxy = gdf.total_bounds
    cosf = np.cos(np.radians((miny + maxy) / 2))

    # cabecera + pie en modo MAPA (el eje ocupa toda el área disponible)
    ps.componer(fig, ax, titulo, subtitulo, fuente, nota, formato, titulo_familia,
                mapa=True, acento_p=acento_p, acento_linea=acento_linea)

    # ---- encuadre: el mapa llena la ALTURA y se alinea a la izquierda; la
    # columna derecha (esquina NE de Bolivia, vacía) aloja la leyenda vertical ----
    pos = ax.get_position()
    bx0, by0 = pos.x0 * W, pos.y0 * H
    bw, bh = pos.width * W, pos.height * H
    right = bx0 + bw                                       # margen derecho del encuadre
    target = (maxy - miny) / ((maxx - minx) * cosf)        # alto/ancho geográfico
    leg_col = 112 * sc                                     # columna reservada a la leyenda
    nh = bh
    nw = nh / target
    if nw > bw - leg_col:                                  # si no cabe a lo ancho
        nw, nh = bw - leg_col, (bw - leg_col) * target
    ax.set_position([bx0 / W, (by0 + (bh - nh) / 2) / H, nw / W, nh / H])
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)

    # ---- termómetro vertical arriba-derecha. Las CIFRAS se alinean exacto al
    # margen derecho (borde respetado, igual que el wordmark) y la barra queda a
    # su izquierda. La unidad va en el subtítulo, no se rotula aquí. ----
    smin = ps.es_num(vmin, _dec(label_fmt)) + sufijo
    smax = ps.es_num(vmax, _dec(label_fmt)) + sufijo
    from PIL import Image as _I, ImageDraw as _D, ImageFont as _F
    _ff = _F.truetype(str(ps.FONTS_DIR / ps._FONT_FILES.get(ps.MONO, "IBMPlexMono-Regular.ttf")),
                      int(ps.SIZES["leyenda"] * sc))
    lab_w = max(_D.Draw(_I.new("RGB", (4, 4))).textlength(s, font=_ff) for s in (smin, smax))
    f_num = ps.fp(ps.MONO, ps.SIZES["leyenda"] * sc)
    bar_w, bar_h = 18 * sc, bh * 0.46
    bar_x = right - lab_w - 12 * sc - bar_w
    bar_top = by0 + bh - 26 * sc
    bar = fig.add_axes([bar_x / W, (bar_top - bar_h) / H, bar_w / W, bar_h / H])
    bar.imshow(np.linspace(1, 0, 256).reshape(-1, 1), aspect="auto", cmap=cmap)
    bar.axis("off")
    fig.text(right / W, bar_top / H, smax, fontproperties=f_num,
             color=ps.COLORS["cafe"], va="center", ha="right")
    fig.text(right / W, (bar_top - bar_h) / H, smin, fontproperties=f_num,
             color=ps.COLORS["cafe"], va="center", ha="right")

    if archivo:
        ps.guardar(fig, archivo, formato=formato)
    return fig, ax


def _dec(fmt):
    import re
    m = re.search(r"\.(\d+)f", fmt)
    return int(m.group(1)) if m else 0

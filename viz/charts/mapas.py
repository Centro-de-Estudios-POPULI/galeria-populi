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
                 acento_p=None, acento_linea=None, escala=None, bordes=None):
    """`escala` = salida de ps.escala_atlas() → usa la MISMA escala que el atlas
    de la página (divergente con ancla real y rampa orientada por dirección) y
    dibuja el pivote rotulado en el termómetro. Sin `escala` se conserva el
    comportamiento viejo: secuencial lineal entre mínimo y máximo."""
    from matplotlib.colors import Normalize, TwoSlopeNorm
    fig, ax = ps.nueva_figura(formato)
    W, H, sc = ps._spec(formato)

    vals = gdf[value_col].astype(float)
    if escala is not None:
        cmap, norm, info = escala
        lo_lbl, hi_lbl = info["lo"], info["hi"]
        recorte = info["recorte"]
    else:
        diverging = (paleta == "divergente")
        cmap = ps.colormap(paleta)
        vmin, vmax = float(np.nanmin(vals)), float(np.nanmax(vals))
        if diverging:
            m = max(abs(vmin), abs(vmax)) or 1.0
            norm = TwoSlopeNorm(vmin=-m, vcenter=0, vmax=m)
        else:
            norm = Normalize(vmin, vmax)
        info, recorte = None, False
        lo_lbl, hi_lbl = vmin, vmax

    # municipios sin dato → gris neutro; el resto coloreado
    falta = gdf[gdf[value_col].isna()]
    if len(falta):
        falta.plot(ax=ax, color=ps.COLORS["gris_claro"],
                   edgecolor=ps.COLORS["fondo"], linewidth=0.4 * sc, zorder=2)
    gdf[gdf[value_col].notna()].plot(
        ax=ax, column=value_col, cmap=cmap, norm=norm,
        edgecolor=ps.COLORS["fondo"], linewidth=0.4 * sc, zorder=3)

    # ★ LÍMITES DEPARTAMENTALES, como en el tablero. Con 343 municipios dibujados
    #   todos con la misma línea no hay forma de ver dónde termina Cochabamba: el
    #   país es una sola mancha de 343 piezas. Va ENCIMA de los rellenos y más
    #   gruesa que la municipal — es la jerarquía la que se lee, no el color, así
    #   que no compite con la rampa.
    #   Llega ya calculada (`bordes`): disolver los 343 por departamento en cada
    #   una de las 215 láminas sería repetir el mismo trabajo 215 veces.
    if bordes is not None:
        bordes.plot(ax=ax, color=ps.COLORS["pizarra"], linewidth=0.9 * sc,
                    zorder=4, alpha=.85)

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
    # Con recorte p02/p98 los extremos de la barra NO son el mínimo y el máximo:
    # se rotulan ≤ y ≥ para no hacer pasar un percentil por un extremo real.
    smin = ("≤" if recorte else "") + ps.es_num(lo_lbl, _dec(label_fmt)) + sufijo
    smax = ("≥" if recorte else "") + ps.es_num(hi_lbl, _dec(label_fmt)) + sufijo
    # ⚠️ SE ROTULA EL PIVOTE REAL, NO EL RECORTADO. Cuando el ancla cae pegada a
    #    un extremo se la corre hacia adentro para que la rampa no se degenere,
    #    pero entonces el número dibujado YA NO ES la mediana ni el país:
    #    publicarlo con ese nombre es rebautizar un borde con el nombre de una
    #    estadística. En «Población total» la leyenda decía «mediana 18.580»
    #    cuando la mediana es 12.296.
    _pr = info.get("piv_real") if info else None
    _recortado = info and _pr is not None and abs(_pr - info["piv"]) > 1e-9
    spiv = ps.es_num(_pr if _recortado else info["piv"], _dec(label_fmt)) + sufijo if info else ""
    from PIL import Image as _I, ImageDraw as _D, ImageFont as _F
    _ff = _F.truetype(str(ps.FONTS_DIR / ps._FONT_FILES.get(ps.MONO, "IBMPlexMono-Regular.ttf")),
                      int(ps.SIZES["leyenda"] * sc))
    _med = _D.Draw(_I.new("RGB", (4, 4)))
    lab_w = max(_med.textlength(s, font=_ff) for s in (smin, smax, spiv) if s)
    f_num = ps.fp(ps.MONO, ps.SIZES["leyenda"] * sc)
    f_cap = ps.fp(ps.BODY, ps.SIZES["leyenda"] * sc * 0.8, weight="bold")
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

    if info:
        # ── PIVOTE ──────────────────────────────────────────────────────────
        # TwoSlopeNorm manda el pivote al 0,5 del eje de color, así que cae
        # exacto en la mitad VISUAL de la barra aunque no esté en la mitad
        # numérica. Se marca y se NOMBRA: sin el rótulo cualquiera supone que es
        # el punto medio entre mínimo y máximo, que es justo lo que no es.
        bar.axhline(127.5, color=ps.COLORS["fondo"], lw=2.2 * sc, zorder=4)
        bar.axhline(127.5, color=ps.COLORS["tinta"], lw=0.9 * sc, zorder=5)
        y_piv = bar_top - bar_h / 2
        fig.text((bar_x - 5 * sc) / W, y_piv / H,
                 ("país" if info["piv_tipo"] == "país" else info["piv_tipo"])
                 + ("*" if _recortado else ""),
                 fontproperties=f_cap, color=ps.COLORS["gris"],
                 va="center", ha="right")
        fig.text(right / W, y_piv / H, spiv, fontproperties=f_num,
                 color=ps.COLORS["tinta"], va="center", ha="right")
        # Los extremos REALES sólo se declaran cuando el recorte los escondió.
        # En una lámina que viaja sola a redes, el municipio del extremo suele
        # ser la noticia.
        lineas = []
        if recorte:
            lineas += [f"mín {ps.es_num(info['min'], _dec(label_fmt))}{sufijo}",
                       f"máx {ps.es_num(info['max'], _dec(label_fmt))}{sufijo}"]
        # el asterisco del rótulo se explica: la marca está corrida hacia adentro
        # para que la rampa no se degenere, y el número es el REAL
        if _recortado:
            lineas.append(f"*marca en {ps.es_num(info['piv'], _dec(label_fmt))}{sufijo}")
        if lineas:
            f_ex = ps.fp(ps.MONO, ps.SIZES["leyenda"] * sc * 0.78)
            # En renglones y no en una línea corrida: se estiraba más allá del
            # ancho de la barra y rompía la columna de la leyenda.
            for i, ex in enumerate(lineas):
                fig.text(right / W, (bar_top - bar_h - (34 + i * 20) * sc) / H, ex,
                         fontproperties=f_ex, color=ps.COLORS["gris"],
                         va="center", ha="right")

    if archivo:
        ps.guardar(fig, archivo, formato=formato)
    return fig, ax


def _dec(fmt):
    import re
    m = re.search(r"\.(\d+)f", fmt)
    return int(m.group(1)) if m else 0

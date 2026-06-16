"""
mapa_mundial.py — Mapa coroplético MUNDIAL (Natural Earth) con identidad POPULI.

Variante HORIZONTAL de mapas.py para datos por país (clave ISO3):
  · proyección Natural Earth (mundo ~2:1) que LLENA el ancho; Antártida fuera,
  · escala de color por CUANTILES clasificados (como el atlas): cada paso = igual
    número de países → mapas nítidos aunque haya outliers (CO₂, inflación…),
  · LEYENDA limpia en una banda DEBAJO del mapa (franjas de color + cortes + chip
    "Sin dato"), sin montarse sobre tierra,
  · PANEL DE EXPLICACIÓN de la variable (qué mide), para quien ve el mapa.

    grafico_mapa_mundial(gdf, value_col, titulo=…, subtitulo=…, explicacion=…,
                         paleta="calido", sufijo="%", label_fmt="{:.0f}")

`gdf` trae geometría de país en lon/lat (EPSG:4326), la columna `value_col` ya
unida y, opcionalmente, `iso3` (para descartar la Antártida). NaN → gris neutro.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import populi_style as ps

PALETA_ACENTO = {
    "calido": "#8B1A1A", "rojo": "#8B1A1A", "azul": "#1A2940",
    "verde": "#0D7E72", "divergente": "#8B1A1A",
}


def _dec(fmt):
    m = re.search(r"\.(\d+)f", fmt)
    return int(m.group(1)) if m else 0


def _compacto(v, suf=""):
    """Formato compacto al español, igual que el atlas web: 150k · 100M · 1,4 mil M."""
    a = abs(v)
    u = ""
    if a >= 1e12:
        v /= 1e12; u = " B"
    elif a >= 1e9:
        v /= 1e9; u = " mil M"
    elif a >= 1e6:
        v /= 1e6; u = "M"
    elif a >= 1e3:
        v /= 1e3; u = "k"
    sa = abs(v)
    d = 1 if u else (0 if sa >= 100 else 1 if sa >= 1 else 2)
    s = f"{v:.{d}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s.replace(".", ",") + u + suf


def _escala_cuantiles(vals, paleta, nb=6, divergente=False):
    """Devuelve (ListedColormap, BoundaryNorm, bounds, colors).
    Divergente -> cortes SIMÉTRICOS anclados en 0 (como el atlas web); si no,
    por cuantiles (cada paso = igual nº de países)."""
    from matplotlib.colors import ListedColormap, BoundaryNorm
    base = ps.colormap(paleta)
    if divergente:
        m = max(abs(float(np.min(vals))), abs(float(np.max(vals)))) or 1.0
        bounds = np.array([-m, -m * .5, -m * .2, -m * .05, m * .05, m * .2, m * .5, m])
    else:
        bounds = np.unique(np.round(np.quantile(vals, np.linspace(0, 1, nb + 1)), 6))
        if len(bounds) < 3:                       # casi constante → escala mínima
            lo, hi = float(np.min(vals)), float(np.max(vals))
            bounds = np.array([lo, (lo + hi) / 2 or 1e-9, hi]) if hi > lo else np.array([lo, lo + 1])
    ncol = len(bounds) - 1
    colors = [base(i / (ncol - 1)) if ncol > 1 else base(0.5) for i in range(ncol)]
    return ListedColormap(colors), BoundaryNorm(bounds, ncol), bounds, colors


def grafico_mapa_mundial(gdf, value_col, titulo="", subtitulo="", fuente="", nota="",
                         formato="mundo", archivo=None, titulo_familia=None,
                         paleta="calido", leyenda="", freshness="",
                         label_fmt="{:.0f}", sufijo="", acento_p=None, acento_linea=None):
    from matplotlib.patches import Rectangle

    W, H, sc = ps._spec(formato)
    fig, ax = ps.nueva_figura(formato)

    # ---- proyección Natural Earth + quitar Antártida ----
    g = gdf
    try:
        g = g.set_crs(4326, allow_override=True)
    except Exception:
        pass
    if "iso3" in g.columns:
        g = g[g["iso3"] != "ATA"]
    # Países que CRUZAN el antimeridiano (Rusia, EE.UU., Fiji, Nueva Zelanda…) se
    # parten correctamente en ±180 con la librería `antimeridian`: así no dibujan
    # una franja horizontal Y aparecen COMPLETOS (la masa de Rusia cruza los 180°;
    # antes desaparecía o salía con bandas).
    import antimeridian

    def _fix_anti(geom):
        try:
            if geom.geom_type == "MultiPolygon":
                return antimeridian.fix_multi_polygon(geom, fix_winding=True)
            if geom.geom_type == "Polygon":
                return antimeridian.fix_polygon(geom, fix_winding=True)
        except Exception:
            return geom
        return geom

    bnd = g.geometry.bounds
    cruza = (bnd["maxx"] - bnd["minx"]) > 180
    if cruza.any():
        g.loc[cruza, "geometry"] = g.loc[cruza, "geometry"].apply(_fix_anti)
    g = g.explode(index_parts=False)
    g = g.to_crs("+proj=natearth")

    # ---- escala de color por cuantiles ----
    vals = g[value_col].astype(float)
    es_div = (paleta == "divergente")
    cmap, norm, bounds, colors = _escala_cuantiles(vals.dropna().values, paleta, divergente=es_div)

    falta = g[g[value_col].isna()]
    if len(falta):
        falta.plot(ax=ax, color=ps.COLORS["gris_claro"],
                   edgecolor=ps.COLORS["fondo"], linewidth=0.5 * sc, zorder=2)
    g[g[value_col].notna()].plot(
        ax=ax, column=value_col, cmap=cmap, norm=norm,
        edgecolor=ps.COLORS["fondo"], linewidth=0.5 * sc, zorder=3)
    ax.axis("off")
    ax.set_aspect("auto")   # geopandas deja 'equal' y encoge la caja; lo soltamos ANTES de medir
    minx, miny, maxx, maxy = g.total_bounds

    # cabecera + pie de marca (modo mapa: el eje ocupa el área central)
    ps.componer(fig, ax, titulo, subtitulo, fuente, nota, formato, titulo_familia,
                mapa=True, acento_p=acento_p, acento_linea=acento_linea,
                wordmark_top=True, freshness=freshness, sub_scale=0.8)

    pos = ax.get_position()
    cx0, cy0 = pos.x0 * W, pos.y0 * H
    cw, ch = pos.width * W, pos.height * H

    # ---- mapa: margen lateral menor que el texto (full-bleed suave) para que sea
    # GRANDE; al quedar limitado por el alto, aprovecha el espacio vertical extra.
    # La leyenda va en una banda justo debajo, alineada al mapa.
    mm = 40 * sc
    lh = 100 * sc                              # banda de leyenda (barra + valores)
    target = (maxy - miny) / (maxx - minx)
    avail_w = W - 2 * mm
    band_h = ch - lh
    nw, nh = avail_w, avail_w * target
    if nh > band_h:
        nh, nw = band_h, band_h / target
    mx = (W - nw) / 2
    my = (cy0 + ch) - nh                       # mapa arriba; leyenda debajo
    ax.set_position([mx / W, my / H, nw / W, nh / H])
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)
    ax.set_aspect("auto")

    # ---- leyenda CLASIFICADA full-width bajo el mapa (estilo OWID), alineada al
    # mapa: "Sin dato" (trama) a la izquierda; barra a todo el ancho; valores de
    # CADA corte (como el atlas web) debajo de la barra.
    from PIL import ImageFont as _IF, ImageDraw as _ID, Image as _IM
    f_num = ps.fp(ps.MONO, ps.SIZES["leyenda"] * sc)
    n = len(colors)
    sw_h = 16 * sc
    leg_x0, leg_x1 = mx, mx + nw
    bar_y = my - 56 * sc                       # justo debajo del mapa

    nd_sw = 42 * sc
    _fnt = _IF.truetype(str(ps.FONTS_DIR / ps._FONT_FILES[ps.MONO]), int(ps.SIZES["leyenda"] * sc))
    nd_txt_w = _ID.Draw(_IM.new("RGB", (4, 4))).textlength("Sin dato", font=_fnt)
    fig.add_artist(Rectangle((leg_x0 / W, bar_y / H), nd_sw / W, sw_h / H,
                             transform=fig.transFigure, facecolor=ps.COLORS["fondo"],
                             edgecolor=ps.COLORS["gris"], hatch="////", linewidth=0.8 * sc, zorder=6))
    fig.text((leg_x0 + nd_sw + 10 * sc) / W, (bar_y + sw_h / 2) / H, "Sin dato",
             fontproperties=f_num, color=ps.COLORS["gris"], va="center", ha="left")

    bar_x = leg_x0 + nd_sw + 10 * sc + nd_txt_w + 46 * sc
    bar_w = leg_x1 - bar_x
    sw_w = bar_w / n
    for i, c in enumerate(colors):
        fig.add_artist(Rectangle(((bar_x + i * sw_w) / W, bar_y / H), sw_w / W, sw_h / H,
                                 transform=fig.transFigure, facecolor=c,
                                 edgecolor=ps.COLORS["fondo"], linewidth=0.8 * sc, zorder=6))

    # valores en CADA borde, debajo de la barra (divergente: min · 0 · max)
    if es_div:
        pts = [(0.0, bounds[0]), (n / 2.0, 0.0), (float(n), bounds[-1])]
    else:
        pts = [(float(j), bounds[j]) for j in range(len(bounds))]
    for j, val in pts:
        x = bar_x + j * sw_w
        ha = "left" if j <= 0 else ("right" if j >= n else "center")
        fig.text(x / W, (bar_y - 9 * sc) / H, _compacto(val, sufijo),
                 fontproperties=f_num, color=ps.COLORS["cafe"], va="top", ha=ha)
    if leyenda:
        fig.text(leg_x0 / W, (bar_y + sw_h + 10 * sc) / H, leyenda,
                 fontproperties=f_num, color=ps.COLORS["gris"], va="bottom", ha="left")

    if archivo:
        ps.guardar(fig, archivo, formato=formato)
    return fig, ax

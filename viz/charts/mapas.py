"""
mapas.py — Mapas coropléticos (GeoPandas) con la identidad POPULI.

Hereda el estilo de populi_style: título/subtítulo alineados y pie de marca. El
mapa usa la proporción geográfica real (corrección por latitud), sin ejes, y se
inscribe pegado al margen izquierdo, tan grande como deje el bloque de la leyenda. La escala de color va en un termómetro
vertical a la derecha.

  grafico_mapa(gdf, value_col, titulo=…, escala=ps.escala_atlas(...), …)

★ EL MAPA ES EL MAPA, NO EL TABLERO (Carlos, 2026-09-16). La lámina dibuja los
  343 municipios con un borde FINO Y BLANCO, y nada más: sin la malla
  departamental gruesa que sí lleva el Atlas en pantalla. En la web la malla
  ayuda a orientarse mientras se navega; en una lámina que viaja sola el país es
  el relleno, y una segunda jerarquía de líneas compite con la rampa.

Paletas (ver populi_style.PALETAS) para el modo sin `escala`: "calido",
"rojo", "azul", "verde" (secuenciales) y "divergente" (con TwoSlopeNorm en 0).
Los polígonos sin dato (NaN) van en el gris de «sin dato» de la paleta oficial,
el mismo que pintan los atlas.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import populi_style as ps

# color de acento (P y/o línea de firma) según la paleta del mapa — de la marca
PALETA_ACENTO = {
    "calido": ps.COLORS["rojo_oscuro"], "rojo": ps.COLORS["rojo_oscuro"],
    "azul": ps.COLORS["azul"], "verde": ps.COLORS["serie_azul"],
    "divergente": ps.COLORS["rojo_oscuro"],
}

# borde municipal: blanco, fino. El mismo en los que tienen dato y en los que no.
BORDE_MUNI = "#FFFFFF"
LW_MUNI = 0.35


def grafico_mapa(gdf, value_col, titulo="", subtitulo="", fuente="", nota="",
                 formato="red_vertical", archivo=None, titulo_familia=None,
                 paleta="calido", leyenda="", label_fmt="{:.0f}", sufijo="",
                 acento_p=None, acento_linea=None, escala=None, miles=False,
                 signo=False):
    """`escala` = salida de ps.escala_atlas() → usa la MISMA escala que el atlas
    de la página (divergente con ancla real y rampa orientada por dirección) y
    dibuja el pivote rotulado en el termómetro. Sin `escala` se conserva el
    comportamiento viejo: secuencial lineal entre mínimo y máximo.
    `miles`  → separador de miles en las cifras del termómetro (conteos).
    `signo`  → las cifras positivas llevan «+» (mapas de cambio)."""
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

    # municipios sin dato → gris «sin dato» de la paleta; el resto coloreado.
    # Borde fino y blanco en todos (ver cabecera).
    falta = gdf[gdf[value_col].isna()]
    if len(falta):
        falta.plot(ax=ax, color=ps.COLORS["gris_claro"],
                   edgecolor=BORDE_MUNI, linewidth=LW_MUNI * sc, zorder=2)
    gdf[gdf[value_col].notna()].plot(
        ax=ax, column=value_col, cmap=cmap, norm=norm,
        edgecolor=BORDE_MUNI, linewidth=LW_MUNI * sc, zorder=3)

    ax.axis("off")
    minx, miny, maxx, maxy = gdf.total_bounds
    cosf = np.cos(np.radians((miny + maxy) / 2))

    # cabecera + pie en modo MAPA (el eje ocupa toda el área disponible)
    ps.componer(fig, ax, titulo, subtitulo, fuente, nota, formato, titulo_familia,
                mapa=True, acento_p=acento_p, acento_linea=acento_linea)

    # ---- encuadre (reescrito 2026-09-17, Carlos: «el termómetro más a la
    # derecha y que el mapa respire») -------------------------------------
    # ⛔ ANTES se leía `ax.get_position()` ACTIVA: geopandas fija aspecto 1,0 y
    #    matplotlib ya había angostado la caja (936 → 852 px) antes de que este
    #    código la midiera. Resultado: el mapa nacía angosto (739 px en vez de
    #    ~820), corrido 43 px del margen del título, y las cifras del termómetro
    #    quedaban a 965 px cuando el margen es 1008. Se lee la caja ORIGINAL que
    #    dejó componer(), y el aspecto se fija acá (1/cos φ, el mismo con que se
    #    calcula `target`), así lo dibujado es lo calculado.
    # ★ El mapa crece hasta donde la TIERRA no toca el bloque de la leyenda: se
    #   recorta la unión de los municipios a la franja de latitudes que ocupa la
    #   leyenda y se exige aire entre su borde este y el rótulo más a la
    #   izquierda. Es lo que hace la diferencia entre «≥8,0%» y «≥218.819 hab»:
    #   la columna fija de 112 px ni alcanzaba para los conteos ni hacía falta
    #   en los porcentajes.
    pos = ax.get_position(original=True)
    bx0, by0 = pos.x0 * W, pos.y0 * H
    bw, bh = pos.width * W, pos.height * H
    right = bx0 + bw                                       # = W − M: el margen del título y del wordmark
    target = (maxy - miny) / ((maxx - minx) * cosf)        # alto/ancho geográfico

    dec = _dec(label_fmt)

    def num(v):
        s = ps.es_num(abs(v), dec, miles) if signo else ps.es_num(v, dec, miles)
        if signo:
            s = ("+" if v > 0 else "−" if v < 0 else "") + s
        return s + sufijo

    # Con recorte p02/p98 (o dominio declarado) los extremos de la barra NO son
    # el mínimo y el máximo: se rotulan ≤ y ≥, como la leyenda de la web.
    smin = ("≤" if recorte else "") + num(lo_lbl)
    smax = ("≥" if recorte else "") + num(hi_lbl)
    # ⚠️ SE ROTULA EL PIVOTE REAL, NO EL RECORTADO. Cuando el ancla cae pegada a
    #    un extremo se la corre hacia adentro para que la rampa no se degenere,
    #    pero entonces el número dibujado YA NO ES la mediana ni el país:
    #    publicarlo con ese nombre es rebautizar un borde con el nombre de una
    #    estadística. En «Población total» la leyenda decía «mediana 18.580»
    #    cuando la mediana es 12.296.
    _pr = info.get("piv_real") if info else None
    _recortado = info and _pr is not None and abs(_pr - info["piv"]) > 1e-9
    spiv = num(_pr if _recortado else info["piv"]) if info else ""
    from PIL import Image as _I, ImageDraw as _D, ImageFont as _F
    _ff = _F.truetype(str(ps.FONTS_DIR / ps._FONT_FILES.get(ps.MONO, "JetBrainsMono-Regular.ttf")),
                      int(ps.SIZES["leyenda"] * sc))
    _fc = _F.truetype(str(ps.FONTS_DIR / ps._FONT_FILES.get(ps.BOLD, "Inter.ttf")),
                      int(ps.SIZES["leyenda"] * sc * 0.8))
    _med = _D.Draw(_I.new("RGB", (4, 4)))
    lab_w = max(_med.textlength(s, font=_ff) for s in (smin, smax, spiv) if s)
    f_num = ps.fp(ps.MONO, ps.SIZES["leyenda"] * sc)
    f_cap = ps.fp(ps.BOLD, ps.SIZES["leyenda"] * sc * 0.8)      # negrita REAL
    # 0,42 de la caja (antes 0,46): la barra termina ANTES de la latitud donde
    # Santa Cruz se acerca al borde este del encuadre, y el mapa puede llenar
    # la altura sin que la leyenda le dispute el ancho.
    bar_w, bar_h = 18 * sc, bh * 0.42
    bar_x = right - lab_w - 12 * sc - bar_w
    bar_top = by0 + bh - 26 * sc                           # desde ABAJO (coordenadas de figura)

    # Todo lo que la leyenda va a escribir se decide ACÁ, antes de encuadrar,
    # porque el ancho del bloque y su piso son lo que limita al mapa.
    captions, lineas, ref2_fila = [], [], None
    if info:
        captions.append(info["piv_tipo"] + ("*" if _recortado else ""))
        if recorte:
            lineas += [f"mín {num(info['min'])}", f"máx {num(info['max'])}"]
        if _recortado:
            lineas.append(f"*marca en {num(info['piv'])}")
        # ── SEGUNDA REFERENCIA ──────────────────────────────────────────────
        # Si el pivote es un umbral declarado (reemplazo 2,1 en la TGF), el
        # país sigue en la leyenda como marca fina en la barra. Con aire respecto
        # de los extremos y del pivote va EN SU FILA (caption a la izquierda,
        # cifra a la derecha, en gris); si no cabe, a los renglones de abajo.
        _r2 = info.get("ref2")
        if _r2 is not None and lo_lbl < _r2 < hi_lbl and abs(_r2 - info["piv"]) > (hi_lbl - lo_lbl) * .04:
            frac = float(norm(_r2))                        # 0 = abajo, 1 = arriba, 0,5 = pivote
            r2_tipo = info.get("ref2_tipo", "país")
            if 0.09 < frac < 0.91 and abs(frac - 0.5) > 0.09:
                ref2_fila = (frac, r2_tipo)
                captions.append(r2_tipo)
            else:
                ref2_fila = (frac, None)
                lineas.append(f"{r2_tipo} {num(_r2)}")
    # ── el bloque de la leyenda, pieza por pieza: cada texto ocupa SU fila y
    #    sólo ahí tiene que despejar la tierra. Medir el bloque entero por su
    #    rótulo más ancho (el caption del pivote) era exigirle al mapa que se
    #    corriera de una franja de latitudes donde ese rótulo ni está.
    _fx = _F.truetype(str(ps.FONTS_DIR / ps._FONT_FILES.get(ps.MONO, "JetBrainsMono-Regular.ttf")),
                      int(ps.SIZES["leyenda"] * sc * 0.78))
    h_txt = ps.SIZES["leyenda"] * sc
    # ★ Los renglones de extremos (mín/máx/marca) van al RINCÓN INFERIOR DERECHO
    #   de la caja, no debajo de la barra: debajo de la barra caen sobre la
    #   latitud donde Santa Cruz llega al borde este, y con tres renglones anchos
    #   («máx 1.610.982») el mapa de población perdía un cuarto de su alto. El
    #   rincón SE del encuadre es Chaco paraguayo: no hay tierra boliviana ahí.
    y_linea = lambda i: by0 + 10 * sc + (len(lineas) - 1 - i) * 20 * sc
    piezas = [(right - lab_w, bar_top - h_txt / 2, bar_top + h_txt / 2),          # ≥ máx
              (right - lab_w, bar_top - bar_h - h_txt / 2, bar_top - bar_h + h_txt / 2),  # ≤ mín
              (bar_x, bar_top - bar_h, bar_top)]                                  # barra + cifras
    if captions:
        y_piv = bar_top - bar_h / 2
        piezas.append((bar_x - 5 * sc - _med.textlength(captions[0], font=_fc),
                       y_piv - h_txt / 2, y_piv + h_txt / 2))
    if ref2_fila is not None and ref2_fila[1]:
        y_r2 = bar_top - bar_h * (1 - ref2_fila[0])
        piezas.append((bar_x - 5 * sc - _med.textlength(ref2_fila[1], font=_fc),
                       y_r2 - h_txt / 2, y_r2 + h_txt / 2))
    for i, ex in enumerate(lineas):
        y_i = y_linea(i)
        piezas.append((right - _med.textlength(ex, font=_fx), y_i - h_txt * .4, y_i + h_txt * .4))

    # El mapa: llena la altura, pegado al margen izquierdo del título, y sólo
    # cede tamaño si la tierra bajo alguna pieza de la leyenda se le acerca.
    union = _union_de(gdf)
    aire = 16 * sc
    lat_de = lambda y, nh, m_top: maxy - (m_top - y) / nh * (maxy - miny)

    def cabe(nh):
        nw = nh / target
        if nw > bw:
            return False
        m_top = by0 + (bh - nh) / 2 + nh                   # borde superior del mapa (desde abajo)
        for x_izq, y_lo, y_hi in piezas:
            lat_lo, lat_hi = max(lat_de(y_lo, nh, m_top), miny), min(lat_de(y_hi, nh, m_top), maxy)
            if lat_hi <= lat_lo:
                continue                                   # la pieza cae fuera del mapa
            rec = _clip(union, minx, lat_lo, maxx, lat_hi)
            if rec.is_empty:
                continue
            if bx0 + (rec.bounds[2] - minx) / (maxx - minx) * nw + aire > x_izq:
                return False
        return True

    nh = bh
    while nh > bh * 0.55 and not cabe(nh):
        nh -= 2 * sc
    nw = nh / target
    ax.set_position([bx0 / W, (by0 + (bh - nh) / 2) / H, nw / W, nh / H])
    ax.set_aspect(1 / cosf, adjustable="box", anchor="C")
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)

    # ---- termómetro vertical arriba-derecha. Las CIFRAS se alinean exacto al
    # margen derecho (borde respetado, igual que el wordmark) y la barra queda a
    # su izquierda. ----
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
        # numérica. Se marca y se NOMBRA con el rótulo que trae la escala
        # («país 2024», «promedio nacional», «mediana», «cero», «sin cambio»):
        # el mismo que la web, para que la lámina y el tablero digan lo mismo.
        bar.axhline(127.5, color=ps.COLORS["fondo"], lw=2.2 * sc, zorder=4)
        bar.axhline(127.5, color=ps.COLORS["tinta"], lw=0.9 * sc, zorder=5)
        y_piv = bar_top - bar_h / 2
        fig.text((bar_x - 5 * sc) / W, y_piv / H, captions[0],
                 fontproperties=f_cap, color=ps.COLORS["gris"],
                 va="center", ha="right")
        fig.text(right / W, y_piv / H, spiv, fontproperties=f_num,
                 color=ps.COLORS["tinta"], va="center", ha="right")
        if ref2_fila is not None:
            frac, r2_tipo = ref2_fila
            bar.axhline((1 - frac) * 255, color=ps.COLORS["fondo"], lw=1.6 * sc, zorder=4)
            bar.axhline((1 - frac) * 255, color=ps.COLORS["gris"], lw=0.7 * sc, zorder=5)
            if r2_tipo:
                y_r2 = bar_top - bar_h * (1 - frac)
                fig.text((bar_x - 5 * sc) / W, y_r2 / H, r2_tipo, fontproperties=f_cap,
                         color=ps.COLORS["gris"], va="center", ha="right")
                fig.text(right / W, y_r2 / H, num(info["ref2"]), fontproperties=f_num,
                         color=ps.COLORS["gris"], va="center", ha="right")
        # Los extremos REALES sólo se declaran cuando el recorte los escondió.
        # En una lámina que viaja sola a redes, el municipio del extremo suele
        # ser la noticia. En renglones, no en una línea corrida.
        if lineas:
            f_ex = ps.fp(ps.MONO, ps.SIZES["leyenda"] * sc * 0.78)
            for i, ex in enumerate(lineas):
                fig.text(right / W, y_linea(i) / H, ex,
                         fontproperties=f_ex, color=ps.COLORS["gris"],
                         va="center", ha="right")

    if archivo:
        ps.guardar(fig, archivo, formato=formato)
    return fig, ax


_UNION = {}


def _union_de(gdf):
    """Unión de todos los polígonos, cacheada por identidad de la capa: se usa
    para medir hasta dónde llega la TIERRA bajo la leyenda, y calcularla por
    lámina costaría medio segundo en cada una de las 600."""
    k = (len(gdf), tuple(round(v, 6) for v in gdf.total_bounds))
    if k not in _UNION:
        g = gdf.geometry
        _UNION[k] = g.union_all() if hasattr(g, "union_all") else g.unary_union
    return _UNION[k]


def _clip(geom, xmin, ymin, xmax, ymax):
    from shapely import clip_by_rect
    return clip_by_rect(geom, xmin, ymin, xmax, ymax)


def _dec(fmt):
    m = re.search(r"\.(\d+)f", fmt)
    return int(m.group(1)) if m else 0

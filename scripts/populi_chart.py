"""
Motor de gráficas editoriales POPULI.

Estilo inspirado en Datawrapper: una sola composición cohesiva con título en
negrita, subtítulo resaltado en banda de color, intro, etiquetas de datos
directas, ejes mínimos, pie con fuente + wordmark, y marca de agua sutil.

Todo se dibuja sobre la figura matplotlib (no es un marco que envuelve un PNG):
el título, el resaltado y el chart forman una unidad. El formato (relación de
aspecto) se adapta al tipo de gráfico.

API:
    from populi_chart import Chart, FORMATS
    c = Chart(fmt="wide", title=..., highlight=..., intro=..., note=..., source=...)
    c.bar_timeseries(years, values, highlight_idx=[...], fmt_label="{:.2f}")
    c.save("public/graficas/mi-slug.png")
"""
from __future__ import annotations
import io
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch
from PIL import Image, ImageDraw, ImageFont
import brand_kit as bk

ROOT = bk.ROOT
C = bk.C
DPI = 200

FORMATS = {
    "square":    (1080, 1080),
    "portrait":  (1080, 1350),
    "story":     (1080, 1920),
    "wide":      (1280, 1000),
    "landscape": (1200, 675),
}

PALETTE = bk.BRAND["palette"]
MONO = "IBM Plex Mono"   # cifras y etiquetas de datos
BODY = "Inter"           # intro, notas, nombres de categoría

# Escala tipográfica (px a 1080 de ancho; se escala con el formato).
# Jerarquía editorial: kicker < titular-héroe; subtítulo e info claramente menores.
SZ = {
    "kicker":    34,   # título-kicker (tema), arriba en negro
    "headline":  44,   # titular-héroe con banda de color (lo más grande)
    "subtitle":  25,   # subtítulo / indicador ("variación interanual del IPC")
    "note":      20,   # nota al pie + fuente
    "annot":     25,   # número-héroe anotado (línea)
    "label":     21,   # etiqueta de dato sobre barra/punto
    "label_sm":  18,   # etiquetas secundarias (apiladas, dot plot 'antes')
    "axis":      19,   # marcas de eje
    "legend":    18,   # leyenda
    "map_name":  17,   # nombre de región en mapa
    "map_val":   18,   # valor en mapa
}

# El resaltado (banda + barras destacadas) varía según el tema de la gráfica.
CATEGORY_ACCENTS = {
    "inflacion": C["red"],
    "fiscal": C["teal"],
    "presupuesto": C["teal"],
    "monetario": C["blue"],
    "actividad": C["amber"],
    "actividad economica": C["amber"],
    "empleo": C["blue"],
    "libertad economica": C["redDark"],
    "precios": C["red"],
}


def _nrm(s):
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return s.strip().lower()


def accent_for(category: str) -> str:
    return CATEGORY_ACCENTS.get(_nrm(category), C["red"])


def _contrast_text(hex_color: str) -> str:
    """Texto crema u oscuro según luminancia del color de fondo."""
    r, g, b = bk.hex2rgb(hex_color)
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    return C["ink"] if lum > 150 else C["cream"]


def _lighten(hex_color: str, amount: float) -> str:
    r, g, b = bk.hex2rgb(hex_color)
    return "#%02x%02x%02x" % tuple(int(c + (255 - c) * amount) for c in (r, g, b))


_MINOR = {"y", "e", "o", "u", "de", "del", "la", "el", "los", "las",
          "en", "a", "por", "con", "para", "al", "sin"}


def titlecase_es(s: str) -> str:
    """Title case respetando conectores en minúscula (estilo español)."""
    words = s.split()
    out = []
    for i, w in enumerate(words):
        lw = w.lower()
        out.append(lw if (i > 0 and lw in _MINOR) else lw[:1].upper() + lw[1:])
    return " ".join(out)


def wrap_label(s: str, maxchars: int = 22, max_lines: int = 2) -> str:
    """Envuelve una etiqueta a un máximo de líneas; añade … si excede."""
    words, lines, cur = s.split(), [], ""
    for w in words:
        if len(f"{cur} {w}".strip()) <= maxchars or not cur:
            cur = f"{cur} {w}".strip()
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(".,") + "…"
    return "\n".join(lines)

# registrar tipografías de marca en matplotlib
for _fp in (ROOT / "assets" / "fonts").glob("*.ttf"):
    font_manager.fontManager.addfont(str(_fp))
plt.rcParams.update({
    "font.family": "Inter",
    "svg.fonttype": "none",
    "axes.unicode_minus": False,
})

# medidor de texto en píxeles (PIL) — coherente con el render final
_MEASURE = ImageDraw.Draw(Image.new("RGB", (4, 4)))


def _px2pt(px: float) -> float:
    return px * 72.0 / DPI


# familia matplotlib -> archivo .ttf (para medir el wrap con la fuente real)
HEADLINE_FILES = {
    "Inter": "Inter.ttf",
    "Playfair Display": "PlayfairDisplay.ttf",
    "Archivo": "Archivo.ttf",
    "Source Serif 4": "SourceSerif4.ttf",
}


def loc(s: str) -> str:
    """Localiza números al español: separador decimal con coma."""
    return s.replace(".", ",")


def wrap_px(text: str, size_px: float, max_w: float, font_file: str = "Inter.ttf") -> list[str]:
    f = ImageFont.truetype(str(ROOT / "assets" / "fonts" / font_file), int(size_px))
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if _MEASURE.textlength(trial, font=f) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _logo_img(height_px: int) -> Image.Image:
    """Wordmark 'Populi' transparente, para incrustar abajo-dcha."""
    s = height_px / 64.0
    w, h = int(height_px * 3.4), int(height_px * 1.35)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bk.draw_wordmark(d, 2, 2, scale=s)
    return img


class Chart:
    def __init__(self, fmt="wide", title="", highlight="", intro="", note="",
                 source="", category="", accent=None, highlight_text=None,
                 headline_family="Archivo"):
        self.W, self.H = FORMATS[fmt]
        self.fmt = fmt
        self.title = title
        self.highlight = highlight
        self.intro = intro
        self.note = note
        self.source = source
        self.category = category
        self.accent = accent or accent_for(category)
        self.hl_text = highlight_text or _contrast_text(self.accent)
        self.headline_family = headline_family
        self._headline_file = HEADLINE_FILES.get(headline_family, "Inter.ttf")
        self.fig = plt.figure(figsize=(self.W / DPI, self.H / DPI), dpi=DPI)
        self.fig.patch.set_facecolor(C["paper"])
        self.ax = None
        self._num_axis = None     # 'y' si el eje Y muestra cifras (-> mono al guardar)
        self._build_chrome()

    # ---- layout: cabecera y pie alrededor del eje del chart ----
    def _build_chrome(self):
        W, H = self.W, self.H
        M = 72                      # margen lateral
        TOP, BOT = 60, 52
        scale = W / 1080.0          # escala relativa al ancho del formato
        s_kick = SZ["kicker"] * scale
        s_head = SZ["headline"] * scale
        s_sub = SZ["subtitle"] * scale
        s_note = SZ["note"] * scale
        max_w = W - 2 * M

        def fy(px):                 # px desde arriba -> fracción figura
            return 1 - px / H

        hf = self.headline_family
        hfile = self._headline_file
        cur = TOP
        # kicker / título-tema (puede ir en varias líneas)
        for ln in wrap_px(self.title, s_kick, max_w, hfile):
            self.fig.text(M / W, fy(cur), ln, fontsize=_px2pt(s_kick), fontfamily=hf,
                          fontweight="bold", color=C["ink"], va="top", ha="left")
            cur += s_kick * 1.16
        cur += 12 * scale
        # titular-héroe con banda (una banda por línea, estilo Datawrapper)
        if self.highlight:
            for ln in wrap_px(self.highlight, s_head, max_w, hfile):
                self.fig.text(M / W, fy(cur), ln, fontsize=_px2pt(s_head), fontfamily=hf,
                              fontweight="bold", color=self.hl_text, va="top", ha="left",
                              bbox=dict(boxstyle="square,pad=0.24", fc=self.accent, ec="none"))
                cur += s_head * 1.28
            cur += 4 * scale
        # subtítulo / indicador (gris)
        if self.intro:
            cur += 14 * scale
            for ln in wrap_px(self.intro, s_sub, max_w):
                self.fig.text(M / W, fy(cur), ln, fontsize=_px2pt(s_sub),
                              color=C["inkSoft"], va="top", ha="left")
                cur += s_sub * 1.28
        chart_top = cur + 26 * scale

        # ---- pie (se apila desde abajo) ----
        fcur = H - BOT
        # wordmark abajo-derecha
        logo = _logo_img(int(46 * scale))
        self.fig.figimage(np.asarray(logo), xo=W - logo.width - M + 10,
                          yo=BOT - 8, origin="upper", zorder=5)
        # línea de fuente
        if self.source:
            self.fig.text(M / W, fy(fcur), self.source, fontsize=_px2pt(s_note),
                          color=C["inkSoft"], va="bottom", ha="left")
            fcur -= s_note * 1.5
        # nota / descripción
        if self.note:
            for ln in reversed(wrap_px(self.note, s_note, max_w - 120 * scale)):
                self.fig.text(M / W, fy(fcur), ln, fontsize=_px2pt(s_note),
                              color=C["muted"], va="bottom", ha="left")
                fcur -= s_note * 1.4
        footer_top = fcur - 16 * scale

        # ---- eje del chart en el espacio central ----
        # se deja holgura bajo el eje para las etiquetas del eje X (no chocan con el pie)
        xtick_room = 52 * scale
        chart_bottom = footer_top - xtick_room
        left = M / W
        width = (W - 2 * M) / W
        bottom = (H - chart_bottom) / H
        height = (chart_bottom - chart_top) / H
        self.ax = self.fig.add_axes([left, bottom, width, max(0.05, height)])
        self._scale = scale
        self._max_w = max_w

    def _watermark(self):
        self.fig.text(0.5, 0.46, "POPULI", fontsize=_px2pt(180 * self._scale),
                      fontfamily="Playfair Display", fontweight="bold",
                      color=self.accent, alpha=0.05, ha="center", va="center",
                      rotation=28, zorder=0)

    # ---- estilos de eje comunes ----
    def _minimal_y(self, ax, fmt="{:.0f}"):
        from matplotlib.ticker import FuncFormatter, MaxNLocator
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.spines["bottom"].set_color(C["grid"])
        ax.tick_params(left=False, bottom=False, labelsize=_px2pt(SZ["axis"] * self._scale),
                       colors=C["muted"])
        ax.grid(axis="y", color=C["grid"], linewidth=0.9, alpha=0.8)
        ax.set_axisbelow(True)
        # marcas "redondas" (5, 10, 20...), evitando pasos como 2,5
        ax.yaxis.set_major_locator(MaxNLocator(nbins=5, steps=[1, 2, 2.5, 5, 10], prune=None))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: loc(f"{v:g}")))

    # =================== TIPOS DE GRÁFICA ===================
    def bar_timeseries(self, x, y, highlight_idx=None, label_fmt="{:.2f}",
                       y_max=None):
        """Barras verticales por periodo; resalta índices clave con etiqueta directa."""
        ax = self.ax
        highlight_idx = set(highlight_idx or [])
        sc = self._scale
        pale = _lighten(self.accent, 0.72)
        colors = [self.accent if i in highlight_idx else pale for i in range(len(y))]
        ax.bar(range(len(y)), y, color=colors, width=0.82)
        for i in highlight_idx:
            ax.text(i, y[i], loc(label_fmt.format(y[i])), ha="center", va="bottom",
                    fontsize=_px2pt(SZ["label"] * sc), fontweight="bold", fontfamily=MONO,
                    color=C["inkSoft"])
        ticks = sorted({i for i in range(len(x))
                        if (str(x[i]).isdigit() and str(x[i])[-1] in "05") or i in highlight_idx})
        ax.set_xticks(ticks)
        ax.set_xticklabels([x[i] for i in ticks], fontsize=_px2pt(SZ["axis"] * sc), fontfamily=MONO)
        if y_max:
            ax.set_ylim(0, y_max)
        self._minimal_y(ax)
        self._num_axis = "y"
        ax.margins(x=0.01)
        self._watermark()
        return self

    def bar_ranking(self, labels, values, label_fmt="{:+.1f}%", highlight_top=0,
                    label_gutter_px=300):
        """Barras horizontales ordenadas (ranking), etiqueta al final de cada barra.
        Reserva un margen izquierdo (gutter) para los nombres de categoría."""
        ax = self.ax
        sc = self._scale
        # ampliar margen izquierdo para que quepan las etiquetas de categoría
        pos = ax.get_position()
        new_x0 = (72 + label_gutter_px * sc) / self.W
        ax.set_position([new_x0, pos.y0, (pos.x0 + pos.width) - new_x0, pos.height])
        order = np.argsort(values)
        labels = [labels[i] for i in order]
        values = [values[i] for i in order]
        n = len(values)
        neg = C["blue"] if self.accent == C["teal"] else C["teal"]
        cmap_pale = _lighten(self.accent, 0.6)
        colors = [self.accent if (n - 1 - i) < highlight_top else cmap_pale for i in range(n)]
        if highlight_top == 0:
            colors = [self.accent if v >= 0 else neg for v in values]
        ax.barh(range(n), values, color=colors, height=0.74)
        vmax = max(abs(v) for v in values)
        for i, v in enumerate(values):
            ax.text(v + (vmax * 0.015 if v >= 0 else -vmax * 0.015), i, loc(label_fmt.format(v)),
                    va="center", ha="left" if v >= 0 else "right", fontfamily=MONO,
                    fontsize=_px2pt(SZ["label"] * sc), fontweight="bold", color=C["inkSoft"])
        ax.set_yticks(range(n))
        disp = [wrap_label(titlecase_es(l)) for l in labels]
        ax.set_yticklabels(disp, fontsize=_px2pt(SZ["label"] * sc), color=C["ink"], fontfamily=BODY)
        ax.axvline(0, color=C["grid"], linewidth=1)
        ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
        ax.tick_params(left=False, bottom=False, labelbottom=False)
        ax.margins(x=0.16, y=0.04)
        self._watermark()
        return self

    def line_annotated(self, x, y, label_fmt="{:.1f}%", area=True):
        """Línea con punto final destacado y etiqueta; relleno suave opcional."""
        ax = self.ax
        sc = self._scale
        xi = range(len(y))
        ax.plot(xi, y, color=self.accent, linewidth=3.4 * sc, solid_capstyle="round")
        if area:
            ax.fill_between(xi, y, min(y), color=self.accent, alpha=0.08)
        ax.scatter([len(y) - 1], [y[-1]], color=self.accent, s=90 * sc, zorder=5)
        ax.annotate(loc(label_fmt.format(y[-1])), (len(y) - 1, y[-1]),
                    textcoords="offset points", xytext=(-10, 12), fontfamily=MONO,
                    fontsize=_px2pt(SZ["annot"] * sc), fontweight="bold", color=self.accent, ha="right")
        step = max(1, len(x) // 6)
        ax.set_xticks(range(0, len(x), step))
        ax.set_xticklabels([x[i] for i in range(0, len(x), step)], fontsize=_px2pt(SZ["axis"] * sc),
                           fontfamily=MONO)
        self._minimal_y(ax)
        self._num_axis = "y"
        ax.margins(x=0.02)
        self._watermark()
        return self

    def stacked_bar(self, x, series, normalize=False, label_fmt="{:.0f}%",
                    min_label=6.0):
        """Barras apiladas (composición). series = {nombre: [valores por x]}.
        normalize=True las vuelve 100%. Etiqueta segmentos suficientemente altos."""
        ax = self.ax
        sc = self._scale
        names = list(series)
        data = np.array([series[n] for n in names], dtype=float)  # (series, x)
        if normalize:
            data = data / data.sum(axis=0) * 100.0
        bottoms = np.zeros(data.shape[1])
        for k, name in enumerate(names):
            col = PALETTE[k % len(PALETTE)]
            ax.bar(range(len(x)), data[k], bottom=bottoms, width=0.74,
                   color=col, label=name)
            for i, v in enumerate(data[k]):
                if v >= min_label:
                    ax.text(i, bottoms[i] + v / 2, loc(label_fmt.format(v)),
                            ha="center", va="center", fontsize=_px2pt(SZ["label_sm"] * sc),
                            fontweight="bold", fontfamily=MONO, color=_contrast_text(col))
            bottoms += data[k]
        ax.set_xticks(range(len(x)))
        ax.set_xticklabels(x, fontsize=_px2pt(SZ["axis"] * sc), fontfamily=MONO)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.spines["bottom"].set_color(C["grid"])
        ax.tick_params(left=False, bottom=False, labelleft=False)
        if normalize:
            ax.set_ylim(0, 100)
        ax.margins(x=0.02)
        ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=min(len(names), 3),
                  frameon=False, fontsize=_px2pt(SZ["legend"] * sc), handlelength=1.1,
                  columnspacing=1.4, borderpad=0)
        self._watermark()
        return self

    def dot_plot(self, labels, a, b, a_name="Antes", b_name="Ahora",
                 label_fmt="{:.1f}", label_gutter_px=300):
        """Dot plot de comparación: una línea conecta dos valores (a→b) por fila."""
        ax = self.ax
        sc = self._scale
        pos = ax.get_position()
        new_x0 = (72 + label_gutter_px * sc) / self.W
        ax.set_position([new_x0, pos.y0, (pos.x0 + pos.width) - new_x0, pos.height])
        order = sorted(range(len(labels)), key=lambda i: b[i])
        labels = [labels[i] for i in order]; a = [a[i] for i in order]; b = [b[i] for i in order]
        c_a = _lighten(C["muted"], 0.2)
        c_b = self.accent
        for i in range(len(labels)):
            ax.plot([a[i], b[i]], [i, i], color=C["grid"], linewidth=3 * sc, zorder=1)
        ax.scatter(a, range(len(labels)), color=c_a, s=150 * sc, zorder=3, label=a_name)
        ax.scatter(b, range(len(labels)), color=c_b, s=150 * sc, zorder=3, label=b_name)
        span = (max(max(a), max(b)) - min(min(a), min(b))) or 1
        off = span * 0.045
        for i in range(len(labels)):
            # cada valor etiquetado junto a su punto, hacia afuera de la línea
            if b[i] >= a[i]:
                bx, bha, gx, gha = b[i] + off, "left", a[i] - off, "right"
            else:
                bx, bha, gx, gha = b[i] - off, "right", a[i] + off, "left"
            ax.text(bx, i, loc(label_fmt.format(b[i])), ha=bha, va="center", fontfamily=MONO,
                    fontsize=_px2pt(SZ["label"] * sc), fontweight="bold", color=c_b)
            ax.text(gx, i, loc(label_fmt.format(a[i])), ha=gha, va="center", fontfamily=MONO,
                    fontsize=_px2pt(SZ["label_sm"] * sc), color=c_a)
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels([wrap_label(titlecase_es(l)) for l in labels],
                           fontsize=_px2pt(SZ["label"] * sc), color=C["ink"], fontfamily=BODY)
        ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
        ax.tick_params(left=False, bottom=False, labelbottom=False)
        ax.margins(x=0.12, y=0.06)
        ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2,
                  frameon=False, fontsize=_px2pt(SZ["legend"] * sc), handletextpad=0.3,
                  columnspacing=1.6)
        self._watermark()
        return self

    def choropleth(self, gdf, value_col, name_col="name", label_fmt="{:.1f}",
                   cmap=None, legend_label=""):
        """Mapa coroplético con etiquetas tipo callout a los lados (con líneas
        guía) y leyenda de escala de color. Dibuja los polígonos a mano para
        evitar el bug de path codes de geopandas.plot en MultiPolygons."""
        ax = self.ax
        sc = self._scale
        from matplotlib.colors import LinearSegmentedColormap, Normalize
        from matplotlib.patches import Polygon as MplPoly
        cmap = cmap or LinearSegmentedColormap.from_list(
            "populi", [_lighten(self.accent, 0.78), self.accent, C["redDark"]])
        vals = gdf[value_col].astype(float)
        norm = Normalize(vmin=vals.min(), vmax=vals.max())

        def rings(geom):
            polys = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
            return [list(p.exterior.coords) for p in polys]

        for _, row in gdf.iterrows():
            fc = cmap(norm(float(row[value_col])))
            for ext in rings(row.geometry):
                ax.add_patch(MplPoly(ext, closed=True, facecolor=fc,
                                     edgecolor="white", linewidth=1.8 * sc, zorder=2))

        minx, miny, maxx, maxy = gdf.total_bounds
        cx = (minx + maxx) / 2
        span_y = maxy - miny

        # repartir etiquetas en dos columnas (izq/dcha) según el lado del depto
        rows = [(r[name_col], float(r[value_col]), r.geometry.representative_point())
                for _, r in gdf.iterrows()]
        left = sorted([t for t in rows if t[2].x < cx], key=lambda t: -t[2].y)
        right = sorted([t for t in rows if t[2].x >= cx], key=lambda t: -t[2].y)

        def place(col, lx, ha):
            n = len(col)
            if not n:
                return
            # posiciones verticales repartidas uniformemente
            top, bot = maxy - span_y * 0.04, miny + span_y * 0.04
            ys = [top - (top - bot) * i / max(1, n - 1) for i in range(n)]
            for (name, val, pt), ly in zip(col, ys):
                ax.plot([lx, pt.x], [ly, pt.y], color=C["muted"], lw=1.0 * sc,
                        alpha=0.6, zorder=3)
                ax.scatter([pt.x], [pt.y], s=10 * sc, color=C["ink"], zorder=4)
                ax.annotate(name, (lx, ly), xytext=(0, 2), textcoords="offset points",
                            ha=ha, va="bottom", fontsize=_px2pt(SZ["map_name"] * sc),
                            fontfamily=BODY, fontweight="bold", color=C["ink"], zorder=5)
                ax.annotate(loc(label_fmt.format(val)), (lx, ly), xytext=(0, -2),
                            textcoords="offset points", ha=ha, va="top",
                            fontsize=_px2pt(SZ["map_val"] * sc), fontfamily=MONO,
                            fontweight="bold", color=self.accent, zorder=5)

        gx = (maxx - minx)
        place(left, minx - gx * 0.16, "right")
        place(right, maxx + gx * 0.16, "left")

        # leyenda de escala (gradiente horizontal) arriba-izquierda del mapa
        import numpy as _np
        grad = _np.linspace(0, 1, 100).reshape(1, -1)
        cax = ax.inset_axes([0.0, 1.02, 0.42, 0.025])
        cax.imshow(grad, aspect="auto", cmap=cmap)
        cax.set_xticks([]); cax.set_yticks([])
        for sp in cax.spines.values():
            sp.set_visible(False)
        cax.text(0, 1.8, loc(label_fmt.format(vals.min())), transform=cax.transAxes,
                 ha="left", va="bottom", fontsize=_px2pt(SZ["legend"] * sc), fontfamily=MONO, color=C["muted"])
        cax.text(1, 1.8, loc(label_fmt.format(vals.max())), transform=cax.transAxes,
                 ha="right", va="bottom", fontsize=_px2pt(SZ["legend"] * sc), fontfamily=MONO, color=C["muted"])

        ax.set_xlim(minx - gx * 0.30, maxx + gx * 0.30)
        ax.set_ylim(miny - span_y * 0.04, maxy + span_y * 0.04)
        ax.axis("off")
        ax.set_aspect("equal")
        self._watermark()
        return self

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        # las cifras del eje Y (autoticks) se pasan a mono tras dibujar
        if self._num_axis == "y" and self.ax is not None:
            self.fig.canvas.draw()
            plt.setp(self.ax.get_yticklabels(), fontfamily=MONO)
        self.fig.savefig(path, dpi=DPI, facecolor=C["paper"])
        plt.close(self.fig)
        # miniatura cuadrada para la galería
        img = Image.open(path).convert("RGB")
        side = min(img.size)
        img.crop(((img.width - side) // 2, 0, (img.width + side) // 2, side)) \
           .resize((540, 540), Image.LANCZOS) \
           .save(ROOT / "public" / "thumbs" / path.name, "PNG", optimize=True)
        print(f"OK   {path.name}  ({self.fmt}, {path.stat().st_size // 1024} KB)")
        return path


def _halo():
    import matplotlib.patheffects as pe
    return [pe.withStroke(linewidth=3, foreground="white")]

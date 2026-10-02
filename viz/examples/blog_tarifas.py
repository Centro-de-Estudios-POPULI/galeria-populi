"""
Láminas del Banco desde la entrada del blog «El servicio de transporte que nos deben: 36 años de
legislación de tarifas y compromisos» (Carlos Aranda, 2026-10-01).

    python viz/examples/blog_tarifas.py                      # las 4 + manifiesto + contrato
    python viz/examples/blog_tarifas.py --solo=pasaje,micro
    python viz/examples/blog_tarifas.py --blog               # además copia los PNG al blog

`--blog` deja los PNG en `blog-graficos/descargas/` del sitio: son los que baja el botón
«Descargar imagen» de cada gráfico de la entrada (mismo origen, así el atributo `download` vale).

Los datos son los MISMOS que dibujan los embeds: se importa `build_embeds.py` de la carpeta de la
entrada (lee tarifas.csv, motivos.csv y compromisos.csv de la consulta del Observatorio Legislativo y
arma las mismas listas) y antes de dibujar se corre su verificación (montos y citas contra el texto de
cada norma): si no pasa, no hay lámina. Tipografía del blog (Playfair Display 700 + Inter), como en
`blog_riqueza250.py`. Nada de datos al repo: el Banco publica la imagen.
"""
import argparse
import contextlib
import io
import itertools
import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle, Wedge
from matplotlib.transforms import Affine2D
from PIL import Image, ImageDraw, ImageFont

VIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(VIZ))
import populi_style as ps   # noqa: E402
import catalogo as CAT      # noqa: E402

ENTRADA = Path.home() / "OneDrive" / "Desktop" / "entradas_nuevas" / "el-micro-que-nos-deben"
BLOG = Path.home() / "OneDrive" / "Desktop" / "Proyectos" / "populi-wordpress" / "astro-frontend"
sys.path.insert(0, str(ENTRADA))
import build_embeds as be   # noqa: E402  — los datos y las listas de los embeds, no unos parecidos
sys.path.insert(0, str(be.CONS))
import compromisos as cpc   # noqa: E402  — de la consulta: sin_cruces() y la definición de «buen estado»

sys.stdout.reconfigure(encoding="utf-8")

FICHA = json.loads((ENTRADA / "ficha.json").read_text(encoding="utf-8"))
TITULO_ENTRADA = (ENTRADA / FICHA["doc"]).read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
URL = f"https://populi.org.bo/blog/{FICHA['slug']}/"
DESCARGAS = BLOG / "public" / "blog-graficos" / "descargas"

FECHA = "2026-10-02"
FUENTE = ("Fuente: normas de la Biblioteca Legislativa del Concejo Municipal de Santa Cruz de la Sierra, "
          "sistematizadas por el Observatorio Legislativo Municipal de POPULI (en construcción); corte al "
          f"{date.fromisoformat(be.CORTE):%d/%m/%Y}. Elaboración: Centro de Estudios POPULI · Carlos Aranda.")
GRUPO = "Blog · Tarifas y compromisos del transporte en Santa Cruz"
TAGS = ["Blog", "transporte público", "Santa Cruz de la Sierra", "Concejo Municipal", "normas municipales"]

TIT = "Playfair Display Bold"          # el titular de los embeds del blog
ps.set_tema("Inter", "Inter")          # cifras en Inter, como en el blog
P = ps._pal
ROJO, ORO, TIERRA = P.BRAND, P.GOLD, P.FAMILIES["tierra"][1]
TURQ, PETR = P.FAMILIES["turquesa"][1], P.FAMILIES["turquesa"][2]   # los del embed: #0A9396 y #005F73
TINTA, PIZARRA, GRIS, TENUE, GRILLA = P.INK, P.MUTED, P.NEUTRAL, P.HIGHLIGHT_MUTED, P.GRID
FONDO, CARD = ps.COLORS["fondo"], P.CARD
# los criterios del cuadro de motivos, con el color del embed (be.COLS usa variables CSS en dos)
COLOR_MOTIVO = {"pedido": ROJO, "combustible": ORO, "estudio": TURQ, "bolsillo": PETR, "cuenta": TINTA,
                "exigencias": TIERRA}
assert [k for k, _, _ in be.COLS] == list(COLOR_MOTIVO), "be.COLS cambió: revisar COLOR_MOTIVO"


# --------------------------------------------------------------------------- #
# Piezas comunes
# --------------------------------------------------------------------------- #
def ficha(slug, titulo, subtitulo, nota, tipo, formato, tags):
    return {"slug": slug, "titulo": titulo, "subtitulo": subtitulo, "categoria": "instituciones",
            "fuente": FUENTE, "nota": nota, "tags": TAGS + tags, "fecha": FECHA, "datos": None,
            "grupo": GRUPO, "enlace": URL, "enlace_etiqueta": "Ver en el blog",
            "documento": {"titulo": TITULO_ENTRADA, "url": URL, "fecha": FICHA["date"]},
            "tipo": tipo, "formato": formato}


HECHAS = []


def componer(fig, ax, meta):
    # abajo, SÓLO la fuente (Carlos): la explicación va en la ficha del Banco, donde se profundiza
    ps.componer(fig, ax, titulo=meta["titulo"], subtitulo=meta["subtitulo"], fuente=meta["fuente"],
                nota="", formato=meta["formato"], titulo_familia=TIT)


def cerrar(fig, meta):
    W, _, sc = ps._spec(meta["formato"])
    choques(fig, meta["slug"], W, ps.MARGIN * sc)
    png = CAT.GRAFICAS / f"{meta['slug']}.png"
    ps.guardar(fig, png, formato=meta["formato"])
    tinta_fuera(png, ps.MARGIN * sc)
    CAT.registrar(meta, meta["tipo"], meta["formato"])
    HECHAS.append(meta["slug"])


def choques(fig, nombre, W, margen):
    """Ningún texto se pisa con otro ni sale del margen lateral (como `revisar()` de la consulta)."""
    fig.canvas.draw()
    rr = fig.canvas.get_renderer()
    textos = list(fig.texts) + [t for lg in fig.legends for t in lg.get_texts()]
    for a in fig.axes:
        textos += list(a.texts)
        if a.axison:
            (lx, hx), (ly, hy) = sorted(a.get_xlim()), sorted(a.get_ylim())
            textos += [t for t in a.get_xticklabels() if lx <= t.get_position()[0] <= hx]
            textos += [t for t in a.get_yticklabels() if ly <= t.get_position()[1] <= hy]
    cajas = [(t.get_text().replace("\n", " ")[:40], t.get_window_extent(rr))
             for t in textos if t.get_visible() and t.get_text().strip()]
    malos = [f"fuera del margen: «{x}»" for x, b in cajas if b.x0 < margen - 1 or b.x1 > W - margen + 1]
    for (t1, b1), (t2, b2) in itertools.combinations(cajas, 2):
        if b1.x0 < b2.x1 - 1 and b2.x0 < b1.x1 - 1 and b1.y0 < b2.y1 - 1 and b2.y0 < b1.y1 - 1:
            malos.append(f"se pisan: «{t1}» y «{t2}»")
    print(f"  {nombre}: {len(cajas)} textos, " + ("sin choques" if not malos else f"{len(malos)} PROBLEMAS"))
    for m in malos:
        print("    ⚠ " + m)


def tinta_fuera(png, margen):
    """Sobre el PNG, no a ojo: ninguna tinta fuera de [M, W − M] (la regla del wordmark)."""
    im = np.asarray(Image.open(png).convert("RGB")).astype(int)
    fondo = np.array([int(FONDO[i:i + 2], 16) for i in (1, 3, 5)])
    tinta = (np.abs(im - fondo).sum(axis=2) > 24).any(axis=0)
    m = int(round(margen))
    fuera = int(tinta[:m - 1].sum() + tinta[im.shape[1] - m + 1:].sum())
    print(f"  tinta fuera del margen: {'ninguna' if not fuera else f'⚠ {fuera} columnas'}")


_FUENTES = {}


def ancho(texto, fam, s_px):
    """Ancho en px de un texto (la misma medida que `_wrap_px` del motor)."""
    k = (fam, int(s_px))
    if k not in _FUENTES:
        _FUENTES[k] = ImageFont.truetype(str(ps.FONTS_DIR / ps._FONT_FILES[fam]), int(s_px))
    return ImageDraw.Draw(Image.new("RGB", (4, 4))).textlength(texto, font=_FUENTES[k])


def T(iso):
    """Fecha → año con decimales (como el `T` de los embeds)."""
    d = date.fromisoformat(iso)
    return d.year + (d - date(d.year, 1, 1)).days / (date(d.year + 1, 1, 1) - date(d.year, 1, 1)).days


def estilo(ax, sc):
    ps.aplicar_estilo_ejes(ax, grid_y=False)
    ax.spines["bottom"].set_capstyle("butt")   # el extremo proyectado asomaba 4 px pasado W − M
    ax.grid(axis="y", color=GRILLA, linewidth=1.0 * sc, linestyle=(0, (1.6, 2.6)), zorder=0)
    ax.set_axisbelow(True)


def encajar_eje(fig, ax, limite_px):
    """El eje termina donde termina el wordmark (W − M): se mide el último rótulo y la línea base."""
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


def lienzo(fig, ax, W, H, sc):
    """Eje apagado de margen a margen, en PÍXELES de la figura (y hacia arriba), para cuadros y
    dibujos; baja hasta donde irían los rótulos del eje x. Devuelve ancho, alto y Y(y desde arriba)."""
    ax.axis("off")
    p = ax.get_position()
    M = ps.MARGIN * sc
    b = ps.SIZES["eje"] * sc * 2.6 / H
    ax.set_position([M / W, p.y0 - b, (W - 2 * M) / W, p.height + b])
    p = ax.get_position()
    w, h = p.width * W, p.height * H
    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    return w, h, (lambda y: h - y)


def superposicion(fig, W, H):
    """Eje transparente del tamaño de la figura, en px: para leyendas dibujadas a mano."""
    ov = fig.add_axes([0, 0, 1, 1], zorder=5)
    ov.axis("off")
    ov.set_xlim(0, W)
    ov.set_ylim(0, H)
    return ov


# --- glifos de estado, los de los embeds (r: radio en px de la figura; scatter, sirve en cualquier eje)
def glifo(ax, x, y, cls, r, sc, z=6):
    s = lambda rr: (2 * rr * 72 / ps.DPI) ** 2   # noqa: E731  diámetro en px → área en puntos²
    kw = dict(zorder=z, clip_on=False)
    if cls == "vig":
        ax.scatter([x], [y], s=s(r), marker="o", facecolor=TURQ, edgecolor="none", **kw)
    elif cls == "blando":
        ax.scatter([x], [y], s=s(r * 0.84), marker="o", facecolor=FONDO, edgecolor=ORO, linewidth=1.3 * sc, **kw)
    elif cls == "prensa":
        ax.scatter([x], [y], s=s(r * 0.84), marker="o", facecolor=FONDO, edgecolor=ROJO, linewidth=1.05 * sc,
                   linestyles=[(0, (2.0, 1.4))], **kw)
    elif cls == "derog":
        ax.scatter([x], [y], s=s(r * 0.8), marker="s", facecolor=GRIS, edgecolor="none", **kw)
    else:   # nada: una cruz gris
        ax.scatter([x], [y], s=s(r * 0.78), marker="x", color=GRIS, linewidth=1.5 * sc, **kw)


def leyenda_glifos(ax, entradas, x0, y_top, w_max, s_px, sc, r, dibujar=True):
    """Leyenda de glifos en filas, alineada a la izquierda (px de `ax`, y hacia arriba).
    Devuelve el alto que ocupa."""
    x, y, paso = x0, y_top - s_px * 0.62, s_px * 1.75
    for cls, txt in entradas:
        w = 2 * r + 0.45 * s_px + ancho(txt, ps.BODY, s_px)
        if x > x0 and x + w > x0 + w_max:
            x, y = x0, y - paso
        if dibujar:
            glifo(ax, x + r, y, cls, r, sc)
            ax.text(x + 2 * r + 0.45 * s_px, y, txt, ha="left", va="center_baseline", color=TINTA,
                    fontproperties=ps.fp(ps.BODY, s_px), zorder=6)
        x += w + 1.6 * s_px
    return y_top - y + s_px * 0.62


def leyenda_lineas(fig, ax, series, W, H, sc, M):
    """Leyenda de líneas sobre el gráfico, alineada al margen; el eje le cede ese alto."""
    p = ax.get_position()
    s_ley = ps.SIZES["leyenda"] * sc
    hs = [Line2D([0], [0], color=c, linewidth=2.6 * sc, solid_capstyle="butt") for _, c in series]
    fig.legend(hs, [n for n, _ in series], loc="upper left", bbox_to_anchor=(M / W, (p.y1 * H + 8 * sc) / H),
               ncol=len(series), frameon=False, prop=ps.fp(ps.BODY, s_ley), labelcolor=TINTA,
               handletextpad=0.55, columnspacing=1.6, borderaxespad=0, borderpad=0, handlelength=1.4)
    ax.set_position([p.x0, p.y0, p.width, p.height - (s_ley * 1.55 + 34 * sc) / H])


# --------------------------------------------------------------------------- #
# 1 · El pasaje, 1990-2026
# --------------------------------------------------------------------------- #
def pasaje():
    F = "informe_5x4"
    W, H, sc = ps._spec(F)
    M = ps.MARGIN * sc
    filas = sorted((r for r in be.tarifas if r["tipo"] in be.EN_GRAFICO), key=lambda r: r["fecha"])
    items = [be.item_de(r) for r in be.motivos]
    COL = {"mayores": ROJO, "universitarios": TURQ, "escolares": ORO}
    nombres = dict(be.SERIES)
    r_pt = 7 * sc * 72 / ps.DPI * 2             # el símbolo de 7 px del embed, a la escala de la lámina

    fig, ax = ps.nueva_figura(F)
    # la franja del decreto que solo consta en la prensa: de esa decisión a la siguiente
    ip = [i for i, it in enumerate(items) if it["prensa"]]
    assert len(ip) == 1, "se esperaba una sola decisión de prensa"
    prensa = items[ip[0]]
    b0, b1 = prensa["t"], items[ip[0] + 1]["t"]
    ax.axvspan(T(b0), T(b1), color=TINTA, alpha=0.06, linewidth=0, zorder=0)
    ax.text((T(b0) + T(b1)) / 2, 0.06, "prensa", ha="center", va="bottom", color=PIZARRA,
            fontproperties=ps.fp(ps.BODY, ps.SIZES["dato"] * sc * 0.82), zorder=2)

    for k in ("escolares", "universitarios", "mayores"):
        pts = [(r["fecha"], be.num(r[k])) for r in filas if be.num(r[k]) is not None]
        g = k == "mayores"
        xs, ys = [T(f) for f, _ in pts] + [T(be.CORTE)], [v for _, v in pts] + [pts[-1][1]]
        ax.plot(xs, ys, drawstyle="steps-post", color=COL[k], linewidth=(2.3 if g else 1.4) * sc,
                zorder=4 if g else 3, solid_joinstyle="miter", solid_capstyle="butt")
        if not g:   # puntos huecos solo donde cambia el monto
            cambios, prev = [], None
            for f, y in pts:
                if y != prev:
                    cambios.append((T(f), y))
                prev = y
            ax.scatter(*zip(*cambios), s=r_pt ** 2, facecolor=FONDO, edgecolor=COL[k], linewidth=1.15 * sc,
                       zorder=5)
    # las decisiones: un punto por norma; la vigente, llena y con su monto (como el embed al abrir)
    sel = len(items) - 1
    for i, it in enumerate(items):
        ax.scatter([T(it["t"])], [it["a"]], s=r_pt ** 2, facecolor=ROJO if i == sel else FONDO, edgecolor=ROJO,
                   linewidth=1.15 * sc, zorder=6, linestyles=[(0, (2, 1.4))] if it["prensa"] else ["solid"])
    it = items[sel]
    ax.annotate("Bs " + ps.es_num(it["a"], 2), (T(it["t"]), it["a"]), xytext=(-9 * sc, 0),
                textcoords="offset points", ha="right", va="center", color=ROJO,
                fontproperties=ps.fp(ps.BOLD, ps.SIZES["dato"] * sc * 1.05), zorder=7)

    estilo(ax, sc)
    ax.set_xlim(1990, 2027)
    ax.set_xticks(range(1990, 2026, 5))
    ax.xaxis.set_major_formatter(ps.formateador_es(0))
    ax.set_ylim(0, 3.5)
    ax.set_yticks(np.arange(0, 3.51, 0.5))
    ax.yaxis.set_major_formatter(ps.formateador_es(2))

    a0, a1 = filas[0]["fecha"][:4], be.CORTE[:4]
    meta = ficha("blog-tarifas-pasaje", "El pasaje de micro en Santa Cruz de la Sierra",
                 f"Tarifa aprobada, en bolivianos corrientes, {a0}–{a1}",
                 f"Cada círculo rojo es una de las {len(items)} normas que fijaron o cambiaron el pasaje; el lleno "
                 f"es la vigente, Bs {ps.es_num(it['a'], 2)} desde la {it['inst']} ({it['f']}). El de borde "
                 f"punteado, Bs {ps.es_num(prensa['a'], 2)} desde el {prensa['f']}, es un decreto que solo consta "
                 "en la prensa; la franja sombreada marca ese tramo. Los círculos huecos de las tarifas "
                 "preferenciales marcan cuándo cambian; hasta 2005 universitarios y escolares pagaban lo mismo y "
                 "la línea turquesa cubre a la amarilla. En mayo de 1993 una transitoria mantuvo el monto y quitó "
                 "el recargo nocturno.",
                 "lineas", F, ["pasaje", "tarifas", "micro"])
    componer(fig, ax, meta)
    leyenda_lineas(fig, ax, [(nombres[k], COL[k]) for k in ("mayores", "universitarios", "escolares")],
                   W, H, sc, M)
    encajar_eje(fig, ax, W - M)
    cerrar(fig, meta)


# --------------------------------------------------------------------------- #
# 2 · Con qué argumento subió: el cuadro de motivos
# --------------------------------------------------------------------------- #
def motivos():
    F = "informe_cuadrado"
    W, H, sc = ps._spec(F)
    items = [be.item_de(r) for r in be.motivos]
    n = len(items)
    assert sum(1 for r in be.motivos if r["cuenta"] == "1") == 0, "el cuadro dice que ninguna publica la cuenta"
    meta = ficha("blog-tarifas-motivos", "Los argumentos de las normas del pasaje de micro",
                 f"Lo que invoca cada decisión según su propio texto, Santa Cruz de la Sierra, "
                 f"{items[0]['t'][:4]}–{items[-1]['t'][:4]}",
                 f"Una fila por cada una de las {n} normas que fijaron o cambiaron el pasaje. Ninguna publica la "
                 "cuenta: ni los costos ni una fórmula. La transitoria de mayo de 1993 le ordenó al alcalde "
                 "presentar la fórmula en 60 días y no aparece en ninguna norma posterior; esa misma transitoria "
                 "mantuvo el monto y quitó el recargo nocturno («mismo monto»). El decreto de febrero de 2025 "
                 "solo consta en la prensa.",
                 "cuadro", F, ["pasaje", "tarifas", "motivos", "estudio de costos"])
    fig, ax = ps.nueva_figura(F)
    componer(fig, ax, meta)
    w, h, Y = lienzo(fig, ax, W, H, sc)

    s_ley, s_cab = ps.SIZES["leyenda"] * sc, ps.SIZES["dato"] * sc * 0.92
    s_yr, s_in, s_pie = ps.SIZES["dato"] * sc * 1.08, ps.SIZES["dato"] * sc * 0.82, ps.SIZES["dato"] * sc

    def punto(x, y, v, color, r):
        if v == "1":
            ax.add_patch(Circle((x, y), r, facecolor=color, linewidth=0, zorder=5))
        elif v == "0":
            ax.add_patch(Circle((x, y), r * 0.5, facecolor="none", edgecolor=TENUE, linewidth=0.8 * sc, zorder=5))
        elif v == "p":   # la pide, no la trae: medio lleno
            ax.add_patch(Wedge((x, y), r * 0.9, 90, 270, facecolor=color, linewidth=0, zorder=5))
            ax.add_patch(Circle((x, y), r * 0.9, facecolor="none", edgecolor=color, linewidth=1.0 * sc, zorder=6))
        else:            # solo en la prensa: anillo punteado
            ax.add_patch(Circle((x, y), r * 0.88, facecolor="none", edgecolor=color, linewidth=1.0 * sc,
                                linestyle=(0, (2.2, 1.6)), zorder=5))

    # leyenda arriba, en una fila
    x, y_l, rl = 0.0, s_ley * 0.62, s_ley * 0.36
    for v, txt in (("1", "la norma lo invoca"), ("0", "no lo menciona"), ("p", "la pide, no la trae"),
                   ("s", "solo en la prensa")):
        punto(x + rl, Y(y_l), v, TINTA, rl)
        ax.text(x + 2 * rl + 0.45 * s_ley, Y(y_l), txt, ha="left", va="center_baseline", color=TINTA,
                fontproperties=ps.fp(ps.BODY, s_ley))
        x += 2 * rl + 0.45 * s_ley + ancho(txt, ps.BODY, s_ley) + 1.6 * s_ley
    assert x - 1.6 * s_ley <= w, "la leyenda del cuadro no entra en una fila"

    # columnas: la de la decisión y seis criterios
    c_norma = 0.29 * w
    cw = (w - c_norma) / len(be.COLS)
    cx = {k: c_norma + (i + 0.5) * cw for i, (k, _, _) in enumerate(be.COLS)}
    cab = {k: ps._wrap_px(nombre, s_cab, cw - 18 * sc, ps._FONT_FILES[ps.BOLD]) for k, nombre, _ in be.COLS}
    alto_cab = max(len(v) for v in cab.values()) * s_cab * 1.22 + 26 * sc
    alto_pie = s_pie * 2.2
    y_cab = y_l + s_ley * 0.62 + 40 * sc
    y_cuerpo = y_cab + alto_cab
    alto_fila = (h - y_cuerpo - alto_pie - 4 * sc) / n
    y_pie = y_cuerpo + n * alto_fila
    r_on = min(alto_fila * 0.2, cw * 0.16)

    # la columna de «la cuenta», sombreada de arriba abajo: la que ninguna norma publica
    ax.add_patch(Rectangle((cx["cuenta"] - cw / 2, Y(y_pie + alto_pie)), cw, y_pie + alto_pie - y_cab,
                           facecolor=TINTA, alpha=0.045, linewidth=0, zorder=1))
    for yy, lw in ((y_cab, 2.0), (y_cuerpo, 1.0), (y_pie, 1.0), (y_pie + alto_pie, 2.0)):
        ax.plot([0, w], [Y(yy)] * 2, color=TINTA, linewidth=lw * 0.55 * sc, solid_capstyle="butt", zorder=3)
    for i in range(1, n):
        ax.plot([0, w], [Y(y_cuerpo + i * alto_fila)] * 2, color=GRILLA, linewidth=0.55 * sc,
                solid_capstyle="butt", zorder=2)

    # cabecera: el nombre de cada criterio, al pie de su celda
    base = y_cuerpo - 13 * sc
    ax.text(0, Y(base), "Decisión", ha="left", va="baseline", color=TINTA, fontproperties=ps.fp(ps.BOLD, s_cab))
    for k, _, _ in be.COLS:
        for j, ln in enumerate(reversed(cab[k])):
            ax.text(cx[k], Y(base - j * s_cab * 1.22), ln, ha="center", va="baseline",
                    color=ROJO if k == "cuenta" else TINTA, fontproperties=ps.fp(ps.BOLD, s_cab))

    # filas: año (con el mes si hubo dos ese año), monto y norma
    x_monto = max(ancho(it["chip"], ps.BOLD, s_yr) for it in items) + 0.8 * s_yr
    for i, (r, it) in enumerate(zip(be.motivos, items)):
        yc = y_cuerpo + (i + 0.5) * alto_fila
        ax.text(0, Y(yc - 4 * sc), it["chip"], ha="left", va="baseline", color=TINTA,
                fontproperties=ps.fp(ps.BOLD, s_yr))
        ax.text(x_monto, Y(yc - 4 * sc), "Bs " + ps.es_num(it["a"], 2), ha="left", va="baseline", color=ROJO,
                fontproperties=ps.fp(ps.BOLD, s_yr))
        sub = it["corto"] + (" · prensa" if it["prensa"] else "") + (" · mismo monto" if it["de"] == it["a"] else "")
        ax.text(0, Y(yc + 5 * sc), sub, ha="left", va="top", color=PIZARRA, fontproperties=ps.fp(ps.BODY, s_in))
        for k, _, _ in be.COLS:
            punto(cx[k], Y(yc), r[k], COLOR_MOTIVO[k], r_on)

    # pie: cuántas decisiones invocan cada criterio
    yc = y_pie + alto_pie / 2
    ax.text(0, Y(yc), f"De {n} decisiones", ha="left", va="center_baseline", color=TINTA,
            fontproperties=ps.fp(ps.BOLD, s_pie))
    for k, _, _ in be.COLS:
        tot = sum(1 for r in be.motivos if r[k] == "1")
        ax.text(cx[k], Y(yc), str(tot), ha="center", va="center_baseline", color=ROJO if k == "cuenta" else TINTA,
                fontproperties=ps.fp(ps.BOLD, s_pie))
    cerrar(fig, meta)


# --------------------------------------------------------------------------- #
# 3 · Lo que se exigió a cambio, en el tiempo
# --------------------------------------------------------------------------- #
LEY_COMP = [("vig", "Exigido y vigente"), ("blando", "Sin plazo, sin cifra o solo incentivo"),
            ("prensa", "Solo en la prensa"), ("derog", "Derogado (la línea, mientras rigió)"),
            ("nada", "Ninguna norma lo exige")]


def compromisos():
    F = "informe_5x4"
    W, H, sc = ps._spec(F)
    M = ps.MARGIN * sc
    CI = be.comp_items()
    dims = be.DIMS
    # misma dimensión y fechas a menos de PEGADOS años: se apilan en vertical dentro de su franja. El embed
    # apila solo el mismo día, a 0,26; en la lámina el cuadrado de 2019 pisaba al anillo de 2019 (seis meses
    # después) y los cuatro de 2013 se fundían: se apila por cercanía y a PASO_PILA, con puntos que caben.
    PEGADOS, PASO_PILA = 0.75, 0.3
    pos = [0.0] * len(CI)
    for d in dims:
        grupos = []
        for i in sorted((i for i, it in enumerate(CI) if it["dim"] == d), key=lambda i: (T(CI[i]["t"]), i)):
            if grupos and T(CI[i]["t"]) - T(CI[grupos[-1][-1]]["t"]) < PEGADOS:
                grupos[-1].append(i)
            else:
                grupos.append([i])
        for g in grupos:
            for k, i in enumerate(g):
                pos[i] = dims.index(d) + (k - (len(g) - 1) / 2) * PASO_PILA

    fig, ax = ps.nueva_figura(F)
    r = 8 * sc                                         # radio en px: el apilado de cuatro cabe en su franja
    for i, it in enumerate(CI):
        if it["hasta"]:
            ax.plot([T(it["t"]), T(it["hasta"])], [pos[i]] * 2, color=GRIS, linewidth=1.0 * sc,
                    linestyle=(0, (4, 3)), zorder=2)
            ax.plot([T(it["hasta"])] * 2, [pos[i] - 0.13, pos[i] + 0.13], color=GRIS, linewidth=1.0 * sc,
                    solid_capstyle="butt", zorder=2)
        glifo(ax, T(it["t"]), pos[i], it["cls"], r, sc)
    ax.set_xlim(1990, 2027.5)
    ax.set_ylim(len(dims) - 0.35, -0.65)
    estilo(ax, sc)
    ax.set_xticks(range(1990, 2026, 5))
    ax.xaxis.set_major_formatter(ps.formateador_es(0))
    ax.set_yticks(range(len(dims)))
    ax.set_yticklabels(dims)

    n_normas = sum(1 for c in CI if c["cls"] not in ("prensa", "nada"))
    n_prensa = sum(1 for c in CI if c["cls"] == "prensa")
    vig = sum(1 for c in CI if c["cls"] == "vig")
    mismo = sum(1 for c in CI if c["t"] == "2013-04-19")
    meta = ficha("blog-tarifas-compromisos", "Compromisos exigidos al transporte público",
                 f"Santa Cruz de la Sierra, {CI[0]['t'][:4]}–{be.CORTE[:4]}. Cada punto es un compromiso, en la "
                 "fecha de la norma que lo exigió, según su ámbito",
                 f"Los {n_normas} compromisos que las normas exigieron desde {CI[0]['t'][:4]}, más {n_prensa} del "
                 f"decreto de 2025 que solo constan en la prensa y uno que ninguna norma pide (el aire "
                 f"acondicionado). {vig} siguen vigentes; {mismo} llegaron el mismo día, con la Ordenanza Municipal "
                 "029/2013. Los puntos de un mismo ámbito con fechas cercanas se apilan dentro de su franja.",
                 "linea_tiempo", F, ["compromisos", "gas natural", "Ordenanza Municipal 029/2013", "micro"])
    componer(fig, ax, meta)

    # la leyenda arriba; el eje le cede ese alto
    s_ley, rl = ps.SIZES["leyenda"] * sc, ps.SIZES["leyenda"] * sc * 0.36
    p = ax.get_position()
    y_ley = p.y1 * H + 8 * sc
    alto = leyenda_glifos(None, LEY_COMP, M, y_ley, W - 2 * M, s_ley, sc, rl, dibujar=False)
    ax.set_position([p.x0, p.y0, p.width, p.height - (alto + 30 * sc) / H])
    leyenda_glifos(superposicion(fig, W, H), LEY_COMP, M, y_ley, W - 2 * M, s_ley, sc, rl)
    # los ámbitos a la izquierda, a plomo con el margen
    ax.tick_params(axis="y", labelcolor=TINTA, pad=(p.x0 * W - M) * 72 / ps.DPI)
    for l in ax.get_yticklabels():
        l.set_horizontalalignment("left")
    encajar_eje(fig, ax, W - M)
    cerrar(fig, meta)


# --------------------------------------------------------------------------- #
# 4 · El micro que exigen las normas en 2026
# --------------------------------------------------------------------------- #
# El dibujo es el de la consulta del Observatorio (compromisos.py, micro()), con los estados y colores
# del embed. Cada llamada: (compromisos de compromisos.csv que reúne, rótulo, dónde apunta en el micro).
# Lo que no tiene lugar en la carrocería va a la lista de abajo; lo derogado, a su propia fila.
X0, X1, S0, ALTO = 54, 112, 32, 19.5          # carrocería, en unidades del dibujo
TECHO = S0 + ALTO + 2.6
LLAMADAS_IZQ = [
    (["Cámaras y GPS"], "Cámaras y GPS", (X0 + 2.1, S0 + 17.6)),
    (["Conductor uniformado", "Licencia B, seguro y AFP"], "Chofer: uniforme, licencia B y AFP", (X0 + 4.2, S0 + 13.4)),
    (["Tarifa a la vista"], "Tarifa a la vista", (X0 + 2.3, S0 + 8.9)),
    (["Cierre de puertas"], "Cierre de puertas", (X0 + 10.2, S0 + 12)),
    (["Limitador de velocidad"], "Limitador de velocidad", (X0 + 0.3, S0 + 3.5)),
    (["Fabricado después de 2005"], "Fabricado después de 2005", (64, S0 + 4.3)),
    (["Antigüedad máxima: sin cifra"], "Antigüedad máxima: sin cifra", (61.2, S0 - 2.6)),
]
LLAMADAS_DER = [
    (["GNV «paulatino»", "Gas: solo incentivo"], "Gas natural: solo incentivo", (84.5, TECHO + 2.4)),
    (["Aire acondicionado"], "Aire acondicionado", (99, TECHO + 2.6)),
    (["Techo elevado"], "Techo elevado", (X1 - 3, S0 + ALTO + 2.6)),
    (["Microbús de 20 asientos"], "Microbús de 20 asientos", (X0 + 41, S0 + 13.5)),
    (["Buen estado*"], "Buen estado", (X0 + 33, S0 + 5)),
    (["Extintor y basurero"], "Extintor, basurero y gel", (X0 + 28, S0 + 13.5)),
    (["Altura interior de 1,80 m"], "Altura interior de 1,80 m", (X1 - 2.6, S0 + 12)),
    (["EURO IV"], "Emisiones EURO IV", (X1 + 1.5, S0 - 1.9)),
]
# lo que dice cada norma, cuando el rótulo no alcanza
NORMA_EXTRA = {"Fabricado después de 2005": " · altas desde 2014"}
# las llamadas que reúnen dos compromisos: sus dos normas en un renglón (dos renglones pisaban a la vecina)
NORMA_LLAMADA = {"Chofer: uniforme, licencia B y AFP": "OM 018/1998 · OM 029/2013, art. 2.12",
                 "Gas natural: solo incentivo": "OM 029/2013 · Ley 1216: incentivo"}
NOMBRE_LISTA = {"Boleto": "Boleto de viaje", "Registro único": "Registro Único del Transporte",
                "Cobro electrónico": "Cobro electrónico en 60 días",
                "Paradas con refugio": "Alcaldía: paradas con refugio",
                "Casetas y rutas pavimentadas": "Alcaldía: casetas y rutas pavimentadas"}


def norma_de(it):
    if it["cls"] == "nada":
        return "ninguna norma lo exige"
    return be.corto(it["norma"]) + NORMA_EXTRA.get(it["corto"], "")


def dibujar_micro(ax, T_, sc):
    """El micro de costado (frente a la izquierda), en unidades del dibujo; T_ las lleva al lienzo."""
    lw = 1.2 * sc
    kw = dict(transform=T_)
    ax.plot([X0 - 6, X1 + 8], [S0 - 4.3] * 2, color=TENUE, linewidth=1.0 * sc, zorder=1, **kw)
    ax.add_patch(FancyBboxPatch((X0, S0), X1 - X0, ALTO, boxstyle="round,pad=0,rounding_size=1.2",
                                facecolor=CARD, edgecolor=TINTA, linewidth=lw, zorder=2, **kw))
    ax.add_patch(Rectangle((X0 + 0.4, S0 + ALTO - 2.4), X1 - X0 - 0.8, 2.0, facecolor=TINTA, alpha=0.08,
                           linewidth=0, zorder=2, **kw))
    ax.add_patch(Rectangle((X0 + 1.5, S0 + ALTO), X1 - X0 - 3, 2.6, facecolor=CARD, edgecolor=TINTA,
                           linewidth=lw, zorder=2, **kw))                                    # techo elevado
    for xc in (66, 79):                                                                     # tanques de GNV
        ax.add_patch(FancyBboxPatch((xc, TECHO), 11, 2.4, boxstyle="round,pad=0,rounding_size=1.2",
                                    facecolor=FONDO, edgecolor=ORO, linewidth=1.1 * sc,
                                    linestyle=(0, (2.4, 1.6)), zorder=2, **kw))
    ax.add_patch(Rectangle((94, TECHO), 10, 2.6, facecolor="none", edgecolor=GRIS, linewidth=1.0 * sc,
                           linestyle=(0, (1.5, 1.5)), zorder=2, **kw))                       # aire: ausente
    for ya, yb in ((0.3, 2.3), (2.3, 0.3)):
        ax.plot([96, 102], [TECHO + ya, TECHO + yb], color=GRIS, linewidth=0.9 * sc, zorder=3, **kw)
    ax.plot([58, 58], [TECHO, TECHO + 3.2], color=TINTA, linewidth=0.9 * sc, zorder=3, **kw)   # antena GPS
    ax.add_patch(Circle((58, TECHO + 3.5), 0.55, color=TINTA, zorder=3, **kw))
    ax.add_patch(Rectangle((X0 + 0.6, S0 + 7), 5.6, 11.4, facecolor=TENUE, alpha=0.55, edgecolor=TINTA,
                           linewidth=0.9 * sc, zorder=3, **kw))                              # parabrisas
    ax.add_patch(Rectangle((X0 + 1.2, S0 + 17.2), 1.8, 0.9, facecolor=TINTA, zorder=4, **kw))   # cámara
    ax.add_patch(Circle((X0 + 4.2, S0 + 13.4), 1.3, color=PIZARRA, zorder=4, **kw))             # chofer
    ax.add_patch(Rectangle((X0 + 1.1, S0 + 8.0), 2.4, 1.8, facecolor=CARD, edgecolor=TINTA, linewidth=0.8 * sc,
                           zorder=4, **kw))                                                  # tarifa a la vista
    ax.add_patch(Rectangle((X0 + 7.2, S0 + 1), 6, 17.6, facecolor=CARD, edgecolor=TINTA, linewidth=0.9 * sc,
                           zorder=3, **kw))                                                  # puerta
    ax.plot([X0 + 10.2] * 2, [S0 + 1, S0 + 18.6], color=TINTA, linewidth=0.7 * sc, zorder=4, **kw)
    for j in range(6):                                                                      # ventanas
        ax.add_patch(Rectangle((X0 + 15 + j * 6.4, S0 + 9.5), 5.4, 8, facecolor=TENUE, alpha=0.55,
                               edgecolor=TINTA, linewidth=0.8 * sc, zorder=3, **kw))
    xa = X1 - 2.6                                                                           # altura interior
    ax.plot([xa, xa], [S0 + 1.4, S0 + ALTO - 1.2], color=PIZARRA, linewidth=0.8 * sc, zorder=4, **kw)
    for y, d in ((S0 + 1.4, 1), (S0 + ALTO - 1.2, -1)):
        ax.plot([xa - 0.6, xa, xa + 0.6], [y + d * 0.9, y, y + d * 0.9], color=PIZARRA, linewidth=0.8 * sc,
                zorder=4, **kw)
    ax.add_patch(Rectangle((X1 - 0.2, S0 - 2.4), 3.2, 1.0, facecolor=PIZARRA, zorder=2, **kw))   # escape
    for dx, dy, rr in ((4, -1.6, 0.8), (6.2, -0.8, 1.0), (8.8, 0.2, 1.2)):
        ax.add_patch(Circle((X1 + dx, S0 - 2 + dy), rr, facecolor="none", edgecolor=TENUE, linewidth=0.8 * sc,
                            zorder=2, **kw))
    for xr in (64, 101):                                                                    # ruedas
        ax.add_patch(Circle((xr, S0), 4.3, facecolor=TINTA, zorder=3, **kw))
        ax.add_patch(Circle((xr, S0), 1.7, facecolor=GRIS, zorder=4, **kw))


def micro():
    F = "informe_cuadrado"
    W, H, sc = ps._spec(F)
    CI = be.comp_items()
    por = {it["corto"]: it for it in CI}
    en_micro = [c for lista in (LLAMADAS_IZQ, LLAMADAS_DER) for cs, _, _ in lista for c in cs]
    borrados = [it for it in CI if it["cls"] == "derog"]
    servicio = sorted((it for it in CI if it["corto"] not in en_micro and it["cls"] != "derog"),
                      key=lambda it: it["t"])
    todos = en_micro + [it["corto"] for it in servicio + borrados]
    assert sorted(todos) == sorted(por), "el micro tiene que nombrar cada compromiso de compromisos.csv una vez"

    vig = sum(1 for it in CI if it["cls"] == "vig")
    meta = ficha("blog-tarifas-micro", "El micro que exigen las normas en 2026",
                 "Santa Cruz de la Sierra: cada exigencia, con la norma que la impone y su estado. Es lo que "
                 "piden las normas, no lo que se cumple: no hay datos públicos de fiscalización",
                 f"Si se juntan las exigencias vigentes ({vig}), este es el micro que debería circular hoy. "
                 + cpc.NOTA_BUEN_ESTADO.lstrip("* ") + " El aire acondicionado solo aparece en un anexo de la "
                 "Ordenanza Municipal 020/2009, que no lo exige.",
                 "diagrama", F, ["compromisos", "micro", "gas natural", "Ordenanza Municipal 029/2013"])
    fig, ax = ps.nueva_figura(F)
    componer(fig, ax, meta)
    w, h, Y = lienzo(fig, ax, W, H, sc)
    rend = fig.canvas.get_renderer()

    def ancho(texto, fam, s_px):   # noqa: F811  — en este dibujo se mide con matplotlib, no con PIL
        return rend.get_text_width_height_descent(texto, ps.fp(fam, s_px), ismath=False)[0]

    s_ley = ps.SIZES["leyenda"] * sc
    s_t, s_n = ps.SIZES["dato"] * sc * 0.84, ps.SIZES["dato"] * sc * 0.7
    r_g = s_t * 0.34                                       # glifo de las llamadas y de la lista
    gap = r_g + 0.45 * s_t                                  # glifo → texto

    alto_ley = leyenda_glifos(ax, [("vig", "Exigido y vigente"), ("blando", "Sin plazo, sin cifra o solo incentivo"),
                                   ("prensa", "Solo en la prensa"), ("nada", "Ninguna norma lo exige")],
                              0, h, w, s_ley, sc, s_ley * 0.36)

    # --- la lista de abajo: el servicio y lo derogado, a dos columnas, nombre y norma en un renglón ---
    col_w = w / 2 - 40 * sc

    def textos(it, tachar):
        nombre = NOMBRE_LISTA.get(it["corto"], it["corto"]).rstrip("*")
        nr = norma_de(it) + (f" · derogado en {it['hasta'][:4]}" if tachar else "")
        return nombre, nr

    def en_un_renglon(lista, tachar):
        return all(2 * r_g + 0.45 * s_t + ancho(a, ps.BOLD, s_t) + 0.7 * s_t + ancho(b, ps.BODY, s_n) <= col_w
                   for a, b in (textos(it, tachar) for it in lista))

    secciones = [("En el servicio", servicio, False), ("Exigido y después borrado", borrados, True)]
    paso_1, paso_2 = s_t * 1.85, s_t * 1.25 + s_n * 1.3 + 26 * sc
    altos = []
    for _, lista, tachar in secciones:
        filas = -(-len(lista) // 2)
        altos.append(s_t * 1.9 + filas * (paso_1 if en_un_renglon(lista, tachar) else paso_2))
    y_lista = h - sum(altos) + 6 * sc                      # desde arriba
    ax.plot([0, w], [Y(y_lista)] * 2, color=TENUE, linewidth=0.8 * sc, solid_capstyle="butt")

    tachados = []
    y = y_lista
    for (titulo, lista, tachar), alto in zip(secciones, altos):
        ax.text(0, Y(y + s_t * 1.15), titulo, ha="left", va="center_baseline", color=TINTA,
                fontproperties=ps.fp(ps.BOLD, s_t))
        uno = en_un_renglon(lista, tachar)
        filas = -(-len(lista) // 2)
        for j, it in enumerate(lista):                     # en columnas: se lee de arriba abajo
            x = (j // filas) * w / 2
            yc = y + s_t * 1.9 + (j % filas + 0.5) * (paso_1 if uno else paso_2) - (0 if uno else s_n * 0.6)
            nombre, nr = textos(it, tachar)
            glifo(ax, x + r_g, Y(yc), it["cls"], r_g, sc)
            fam = ps.BOLD if it["cls"] == "vig" else ps.BODY
            base = Y(yc) - s_t * 0.36                       # nombre y norma, en la misma línea base
            t = ax.text(x + 2 * r_g + 0.45 * s_t, base, nombre, ha="left", va="baseline",
                        color=PIZARRA if tachar else TINTA, fontproperties=ps.fp(fam, s_t))
            if uno:
                ax.text(x + 2 * r_g + 1.15 * s_t + ancho(nombre, fam, s_t), base, nr, ha="left", va="baseline",
                        color=PIZARRA, fontproperties=ps.fp(ps.BODY, s_n))
            else:
                ax.text(x + 2 * r_g + 0.45 * s_t, Y(yc + s_t * 0.55 + 8 * sc), nr, ha="left", va="top",
                        color=PIZARRA, fontproperties=ps.fp(ps.BODY, s_n))
            if tachar:
                tachados.append(t)
        y += alto

    # --- el micro y sus llamadas, entre la leyenda y la lista ---
    def lineas(cs, txt):
        return [NORMA_LLAMADA[txt]] if len(cs) > 1 else [norma_de(por[c]) for c in cs]

    def ancho_llamada(lista):
        return max(max([ancho(t, ps.BOLD, s_t)] + [ancho(x, ps.BODY, s_n) for x in lineas(cs, t)])
                   for cs, t, _ in lista)

    xg_izq, xg_der = ancho_llamada(LLAMADAS_IZQ) + gap, w - ancho_llamada(LLAMADAS_DER) - gap
    holgura = 34 * sc                                      # entre los glifos y el micro, para las líneas
    arriba, abajo = alto_ley + 50 * sc, y_lista - 40 * sc
    sube, baja = s_t * 1.25, s_n * 1.3 + 6 * sc        # lo que ocupa una llamada sobre y bajo su glifo
    bx0, bx1, by0, by1 = X0 - 6, X1 + 10, S0 - 4.6, TECHO + 4.1   # caja del dibujo (suelo, humo, antena)
    k = min((xg_der - xg_izq - 2 * holgura - 2 * r_g) / (bx1 - bx0), (abajo - arriba) / (by1 - by0))
    A = Affine2D().translate(-(bx0 + bx1) / 2, -(by0 + by1) / 2).scale(k).translate(
        (xg_izq + xg_der) / 2, Y((arriba + abajo) / 2))
    dibujar_micro(ax, A + ax.transData, sc)

    n_ll = max(len(LLAMADAS_IZQ), len(LLAMADAS_DER))
    paso = (abajo - arriba - sube - baja) / (n_ll - 1)
    ys = [Y(arriba + sube + i * paso) for i in range(n_ll)]
    for lado, lista, xg in (("izq", LLAMADAS_IZQ, xg_izq), ("der", LLAMADAS_DER, xg_der)):
        yy = ys[(n_ll - len(lista)) // 2:][:len(lista)]
        anclas = [tuple(A.transform(a)) for _, _, a in lista]
        perm = cpc.sin_cruces(anclas, xg, yy)
        for j, i in enumerate(perm):
            cs, txt, _ = lista[i]
            its = [por[c] for c in cs]
            cls = its[0]["cls"]
            assert all(x["cls"] == cls for x in its), f"{cs}: estados distintos en una misma llamada"
            glifo(ax, xg, yy[j], cls, r_g, sc)
            ha, xt = ("right", xg - gap) if lado == "izq" else ("left", xg + gap)
            ax.text(xt, yy[j] + 4 * sc, txt, ha=ha, va="bottom", color=PIZARRA if cls == "nada" else TINTA,
                    fontproperties=ps.fp(ps.BOLD if cls == "vig" else ps.BODY, s_t))
            for m, nl in enumerate(lineas(cs, txt)):
                ax.text(xt, yy[j] - 6 * sc - m * s_n * 1.3, nl, ha=ha, va="top", color=PIZARRA,
                        fontproperties=ps.fp(ps.BODY, s_n))
            xl = xg + (r_g + 6 * sc) * (1 if lado == "izq" else -1)
            ax.plot([xl, anclas[i][0]], [yy[j], anclas[i][1]], color=PIZARRA, linewidth=0.6 * sc, zorder=5)
            ax.add_patch(Circle(anclas[i], 4.2 * sc, color=PIZARRA, zorder=7))

    # lo derogado, tachado (como en el embed)
    fig.canvas.draw()
    rend, inv = fig.canvas.get_renderer(), ax.transData.inverted()
    for t in tachados:
        b = t.get_window_extent(rend)
        (xa, ya), (xb, yb) = inv.transform((b.x0, b.y0)), inv.transform((b.x1, b.y1))
        ax.plot([xa, xb], [(ya + yb) / 2 - 2 * sc] * 2, color=GRIS, linewidth=0.8 * sc, solid_capstyle="butt")
    cerrar(fig, meta)


# --------------------------------------------------------------------------- #
def copiar_al_blog():
    """Los PNG que baja el botón «Descargar imagen» de la entrada (mismo origen que el embed)."""
    DESCARGAS.mkdir(parents=True, exist_ok=True)
    for slug in HECHAS:
        shutil.copy2(CAT.GRAFICAS / f"{slug}.png", DESCARGAS / f"{slug}.png")
    print(f"→ {len(HECHAS)} PNG copiados a {DESCARGAS}")


LAMINAS = {"pasaje": pasaje, "motivos": motivos, "compromisos": compromisos, "micro": micro}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo", default="", help="coma: " + ",".join(LAMINAS))
    ap.add_argument("--blog", action="store_true", help="copia los PNG a blog-graficos/descargas")
    ap.add_argument("--sin-contrato", action="store_true", help="no corre verificar.py (iterar el diseño)")
    args = ap.parse_args()
    # la verificación de la entrada (montos y citas contra cada norma): si no pasa, no hay lámina
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        be.verificar()
    print(f"Entrada verificada: {len(be.motivos)} decisiones, citas contra el texto de su norma")
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

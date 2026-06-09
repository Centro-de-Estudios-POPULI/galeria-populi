"""
barras.py — Barras verticales (serie/tiempo) y ranking horizontal.

  grafico_barras          : barras verticales por categoría/periodo, con
                            resaltado opcional de barras clave y etiqueta directa.
  grafico_barras_ranking  : barras horizontales ordenadas (ranking), nombres a la
                            izquierda y valor al final de cada barra; colorea por
                            signo o resalta el Top-N.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import populi_style as ps


def _titlecase_es(s):
    menores = {"y", "e", "o", "u", "de", "del", "la", "el", "los", "las",
               "en", "a", "por", "con", "para", "al", "sin"}
    out = []
    for i, w in enumerate(s.split()):
        lw = w.lower()
        out.append(lw if (i > 0 and lw in menores) else lw[:1].upper() + lw[1:])
    return " ".join(out)


def _wrap(s, n=22, maxl=2):
    words, lines, cur = s.split(), [], ""
    for w in words:
        if len(f"{cur} {w}".strip()) <= n or not cur:
            cur = f"{cur} {w}".strip()
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    if len(lines) > maxl:
        lines = lines[:maxl]; lines[-1] = lines[-1].rstrip(".,") + "…"
    return "\n".join(lines)


def grafico_barras(x, valores, titulo="", subtitulo="", fuente="", nota="",
                   color="rojo", resaltar=None, etiqueta_fmt="{:.1f}",
                   formato="red_vertical", archivo=None, titulo_familia=None,
                   y_decimales=0, y_sufijo=""):
    """Barras verticales. `resaltar` = índices a destacar (el resto va atenuado)."""
    fig, ax = ps.nueva_figura(formato)
    _, _, sc = ps._spec(formato)
    n = len(valores)
    resaltar = set(resaltar) if resaltar is not None else set(range(n))
    base = ps.col(color)
    palido = ps.aclarar(base, 0.68)
    colores = [base if i in resaltar else palido for i in range(n)]
    ax.bar(range(n), valores, color=colores, width=0.78, zorder=3)
    for i in resaltar:
        ax.annotate(ps.es_num(valores[i], _dec(etiqueta_fmt)) + y_sufijo,
                    (i, valores[i]), xytext=(0, 5 * sc), textcoords="offset points",
                    ha="center", va="bottom", color=ps.COLORS["cafe_oscuro"],
                    fontproperties=ps.fp(ps.MONO, ps.SIZES["dato"] * sc, weight="bold"))
    ps.aplicar_estilo_ejes(ax)
    ax.yaxis.set_major_formatter(ps.formateador_es(y_decimales, y_sufijo))
    # marcas X: enteros terminados en 0/5 si son años, o todas si son pocas
    etiquetas = [str(v) for v in x]
    if n <= 12:
        ticks = list(range(n))
    else:
        ticks = [i for i, v in enumerate(etiquetas) if v[-1:] in ("0", "5")] or list(range(0, n, max(1, n // 8)))
    ax.set_xticks(ticks)
    ax.set_xticklabels([etiquetas[i] for i in ticks], fontfamily=ps.MONO)
    ax.margins(x=0.02, y=0.02)
    ps.componer(fig, ax, titulo, subtitulo, fuente, nota, formato, titulo_familia)
    if archivo:
        ps.guardar(fig, archivo, formato=formato)
    return fig, ax


def grafico_barras_ranking(etiquetas, valores, titulo="", subtitulo="", fuente="",
                           nota="", color="rojo", color_neg="azul", resaltar_top=0,
                           etiqueta_fmt="{:+.1f}", sufijo="%", formato="red_vertical",
                           archivo=None, titulo_familia=None, gutter=330):
    """Ranking horizontal ordenado. Sin resaltar_top: colorea por signo
    (rojo positivo / azul negativo). Con resaltar_top=N: destaca las N mayores."""
    fig, ax = ps.nueva_figura(formato)
    _, _, sc = ps._spec(formato)
    orden = np.argsort(valores)
    etiquetas = [etiquetas[i] for i in orden]
    valores = [valores[i] for i in orden]
    n = len(valores)
    base, neg = ps.col(color), ps.col(color_neg)
    if resaltar_top > 0:
        palido = ps.aclarar(base, 0.6)
        colores = [base if (n - 1 - i) < resaltar_top else palido for i in range(n)]
    else:
        colores = [base if v >= 0 else neg for v in valores]
    ax.barh(range(n), valores, color=colores, height=0.72, zorder=3)
    vmax = max(abs(v) for v in valores) or 1
    for i, v in enumerate(valores):
        ax.annotate(ps.es_num(v, _dec(etiqueta_fmt)) + sufijo,
                    (v, i), xytext=((6 if v >= 0 else -6) * sc, 0),
                    textcoords="offset points", va="center",
                    ha="left" if v >= 0 else "right", color=ps.COLORS["cafe_oscuro"],
                    fontproperties=ps.fp(ps.MONO, ps.SIZES["dato"] * sc, weight="bold"))
    ax.set_yticks(range(n))
    ax.set_yticklabels([_wrap(_titlecase_es(l)) for l in etiquetas],
                       color=ps.COLORS["tinta"],
                       fontproperties=ps.fp(ps.BODY, ps.SIZES["dato"] * sc))
    ax.axvline(0, color=ps.COLORS["borde"], linewidth=1.2 * sc, zorder=2)
    ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
    ax.tick_params(left=False, bottom=False, labelbottom=False)
    ax.margins(x=0.18, y=0.03)
    ps.componer(fig, ax, titulo, subtitulo, fuente, nota, formato, titulo_familia,
                gutter_izq=gutter)
    if archivo:
        ps.guardar(fig, archivo, formato=formato)
    return fig, ax


def _dec(fmt):
    """Extrae el nº de decimales de un format spec tipo '{:+.1f}'."""
    import re
    m = re.search(r"\.(\d+)f", fmt)
    return int(m.group(1)) if m else 1

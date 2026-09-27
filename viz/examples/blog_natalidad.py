"""
Láminas del Banco desde la entrada del blog «Algunas consecuencias demográficas del declive de
la natalidad en Bolivia» (Carlos Aranda, 2026-09-22).

    python viz/examples/blog_natalidad.py                     # las cinco + manifiesto + contrato
    python viz/examples/blog_natalidad.py --solo=region,poblacion

Los datos se leen de la carpeta de la entrada (Escritorio/entradas_nuevas/caida-natalidad-bolivia),
los MISMOS CSV que alimentan los gráficos del blog. Los parámetros de los escenarios salen de su
`escenarios.py`, que se ejecuta sin dejarlo escribir y se comprueba que reproduce los CSV: si
alguien rehace la proyección y no los CSV (o al revés), esto se detiene. Nada de datos al repo: el
Banco publica la imagen.

Las dos tablas del blog pasan a gráfico: la aritmética de 2026 como cascada y la composición
menonita como dos paneles (participación y fecundidad del país).
"""
import argparse
import contextlib
import io
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

VIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(VIZ))
import populi_style as ps   # noqa: E402
import catalogo as CAT      # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

ENTRADA = Path.home() / "OneDrive" / "Desktop" / "entradas_nuevas" / "caida-natalidad-bolivia"
FICHA = json.loads((ENTRADA / "ficha.json").read_text(encoding="utf-8"))
SPEC = {c["id"]: c for c in FICHA["charts"]}
URL = f"https://populi.org.bo/blog/{FICHA['slug']}/"

FECHA = "2026-09-26"
AUTOR = "Elaboración: Centro de Estudios POPULI · Carlos Aranda."
GRUPO = "Blog · Declive de la natalidad"
TAGS = ["Blog", "Bolivia", "demografía", "fecundidad", "natalidad"]

P = ps._pal
ROJO, TINTA, PIZARRA, TENUE = P.BRAND, P.INK, P.MUTED, P.HIGHLIGHT_MUTED
MENOS = "−"


# --------------------------------------------------------------------------- #
# Datos
# --------------------------------------------------------------------------- #
def escenarios():
    """Ejecuta escenarios.py de la entrada SIN dejarlo escribir sus CSV auxiliares."""
    g = {"__file__": str(ENTRADA / "escenarios.py"), "__name__": "escenarios"}
    guardar = pd.DataFrame.to_csv
    pd.DataFrame.to_csv = lambda *a, **k: None
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile((ENTRADA / "escenarios.py").read_text(encoding="utf-8"), "escenarios.py", "exec"), g)
    finally:
        pd.DataFrame.to_csv = guardar
    return g


def llega(fn):
    """(valor final, año en que lo alcanza) de una senda de fecundidad."""
    fin = fn(3000)
    return fin, next(a for a in range(2026, 3001) if abs(fn(a) - fin) < 1e-12)


def oraciones(texto):
    return [o.strip().rstrip(".") + "." for o in texto.split(". ") if o.strip()]


def num(v, d=1, miles=False):
    s = ps.es_num(abs(v), d, miles)
    return (MENOS + s) if v < 0 else s


ESC = escenarios()
ESC_A, ESC_B = ESC["ESC_A"], ESC["ESC_B"]
A, B = ESC["A"], ESC["B"]

# columnas de los CSV ↔ claves de escenarios.py (los mismos nombres de build_datos.py)
COL_A = {"INE (se estabiliza en 1,47)": "Supuestos del INE",
         "sin rebote (baja a 1,20 en 2045)": "Sin rebote (TGF 1,20)",
         "INE, sin emigracion": "Supuestos del INE, sin emigración"}
COL_B = {"A": "Parámetros de Fernández-Villaverde", "B": "Medido en el censo",
         "C": "Subregistro alto y fecundidad alta", "D": "Medido, sin rebote del resto"}
CLAVE_B = {k.split(" ")[0]: k for k in ESC_B}


def comprobar():
    """La proyección que se ejecuta reproduce los CSV del blog."""
    g4 = pd.read_csv(ENTRADA / "g4_poblacion.csv").set_index("anio")
    for k, c in COL_A.items():
        v = A[k][A[k].anio <= 2101].set_index("anio").pob / 1e6
        if (v.round(3) - g4[c]).abs().max() > 1e-9:
            raise SystemExit(f"⛔ g4_poblacion.csv no coincide con escenarios.py ({c})")
    g7 = pd.read_csv(ENTRADA / "g7_menonitas_pob.csv").set_index("anio")
    for letra, c in COL_B.items():
        v = B[CLAVE_B[letra]].set_index("anio").pct_pob
        if (v.round(2) - g7[c]).abs().max() > 1e-9:
            raise SystemExit(f"⛔ g7_menonitas_pob.csv no coincide con escenarios.py ({c})")
    t5 = pd.read_csv(ENTRADA / "t5_composicion.csv")
    b = B[CLAVE_B["B"]].set_index("anio")
    for _, r in t5.iterrows():
        a = int(r["Año"])
        if (f"{b.pct_pob[a]:.1f} %".replace(".", ",") != r["Población"]
                or f"{b.pct_nac[a]:.1f} %".replace(".", ",") != r["Nacimientos"]
                or f"{b.tgf_nac[a]:.2f}".replace(".", ",") != r["TGF del país"]):
            raise SystemExit(f"⛔ t5_composicion.csv no coincide con escenarios.py ({a})")
    print("✓ escenarios.py reproduce g4, g7 y t5")


# --------------------------------------------------------------------------- #
# Piezas de estilo
# --------------------------------------------------------------------------- #
def estilo(ax, sc, eje="y"):
    ps.aplicar_estilo_ejes(ax, grid_y=False)
    ax.grid(axis=eje, color=ps.COLORS["borde"], linewidth=1.0 * sc,
            linestyle=(0, (1.6, 2.6)), zorder=0)
    ax.set_axisbelow(True)


def umbral(ax, sc, y, texto, x_texto, s_px, arriba=True):
    """Línea de referencia (reemplazo, mitad) en pizarra, punteada, rotulada a la izquierda."""
    ax.axhline(y, color=PIZARRA, linewidth=1.1 * sc, linestyle=(0, (4, 3)), zorder=1)
    ax.annotate(texto, (x_texto, y), xytext=(0, (4 if arriba else -4) * sc), textcoords="offset points",
                ha="left", va="bottom" if arriba else "top", color=PIZARRA,
                fontproperties=ps.fp(ps.BODY, s_px), zorder=6)


def rotular_fin(fig, ax, items, sc, x_ancla, s_px):
    """«nombre  valor» a la derecha de x_ancla, sin encimarse. Si el rótulo se aleja de la
    punta de su línea (o la línea termina antes), una guía fina lo une a ella."""
    fig.canvas.draw()
    T = ax.transData
    x_disp = T.transform((x_ancla, 0))[0]
    alto = s_px * 1.32
    ys = [T.transform((x_ancla, it["y"]))[1] for it in items]
    orden = sorted(range(len(items)), key=lambda i: ys[i])
    pos = [ys[i] for i in orden]
    for _ in range(800):
        mov = False
        for k in range(len(pos) - 1):
            d = pos[k + 1] - pos[k]
            if d < alto - 0.5:
                e = (alto - d) / 2
                pos[k] -= e
                pos[k + 1] += e
                mov = True
        if not mov:
            break
    inv = T.inverted()
    textos = []
    for k, i in enumerate(orden):
        it = items[i]
        y_lab = inv.transform((x_disp, pos[k]))[1]
        if it["x"] < x_ancla or abs(pos[k] - ys[i]) > alto * 0.25:
            ax.plot([it["x"], x_ancla], [it["y"], y_lab], color=it.get("guia", TENUE),
                    linewidth=0.9 * sc, linestyle=(0, (1, 1.6)), zorder=3, clip_on=False)
        nom = ax.annotate(it["nombre"], xy=(x_ancla, y_lab), xytext=(7 * sc, 0),
                          textcoords="offset points", ha="left", va="center",
                          color=it["color"], fontproperties=ps.fp(ps.BOLD, s_px),
                          annotation_clip=False, zorder=6)
        val = ax.annotate(it["valor"], xy=(1, 0.5), xycoords=nom, xytext=(5 * sc, 0),
                          textcoords="offset points", ha="left", va="center",
                          color=it["color"], fontproperties=ps.fp(ps.MONO_BOLD, s_px),
                          annotation_clip=False, zorder=6)
        textos += [nom, val]
    return textos


def encajar(fig, ax, textos, limite_px):
    """Encoge el ancho del eje hasta que ningún rótulo pase de limite_px (el borde W − M)."""
    W = fig.bbox.width
    for _ in range(8):
        fig.canvas.draw()
        r = fig.canvas.get_renderer()
        over = max(t.get_window_extent(r).x1 for t in textos) - limite_px
        if over <= 1:
            return
        p = ax.get_position()
        ax.set_position([p.x0, p.y0, p.width - over / W, p.height])


def fuentes_ejes(ax, sc, s_px=None):
    fpn = ps.fp(ps.MONO, (s_px or ps.SIZES["eje"]) * sc)
    for lbl in ax.get_xticklabels() + ax.get_yticklabels():
        lbl.set_fontproperties(fpn)


def ficha(slug, titulo, subtitulo, fuente, nota, tipo, formato, tags):
    return {"slug": slug, "titulo": titulo, "subtitulo": subtitulo, "categoria": "censo",
            "fuente": fuente, "nota": nota, "tags": TAGS + tags, "fecha": FECHA, "datos": None,
            "grupo": GRUPO, "enlace": URL, "enlace_etiqueta": "Ver en el blog",
            "documento": {"titulo": FICHA["title"], "url": URL, "fecha": FICHA["date"]},
            "tipo": tipo, "formato": formato}


def cerrar(fig, meta):
    ps.guardar(fig, CAT.GRAFICAS / f"{meta['slug']}.png", formato=meta["formato"])
    CAT.registrar(meta, meta["tipo"], meta["formato"])


# --------------------------------------------------------------------------- #
# 1 · Bolivia y la región
# --------------------------------------------------------------------------- #
def region():
    F = "informe_horizontal"
    W, H, sc = ps._spec(F)
    spec = SPEC["nb-dem-region"]
    df = pd.read_csv(ENTRADA / spec["dataset"])
    bol = df[["anio", "Bolivia"]].dropna()
    paises = [s["col"] for s in spec["series"] if s["col"] != "Bolivia"]
    x0, x1 = int(df.anio.min()), int(bol.anio.max())
    s_dato = ps.SIZES["dato"] * sc

    fig, ax = ps.nueva_figura(F)
    items = []
    for p in paises:
        d = df[["anio", p]].dropna()
        ax.plot(d.anio, d[p], color=TENUE, linewidth=1.7 * sc, zorder=2, solid_capstyle="round")
        items.append(dict(x=d.anio.iloc[-1], y=d[p].iloc[-1], nombre=p, valor=num(d[p].iloc[-1], 2),
                          color=PIZARRA))
    ax.plot(bol.anio, bol.Bolivia, color=ROJO, linewidth=2.7 * sc, zorder=4,
            solid_capstyle="round", solid_joinstyle="round")
    ax.scatter(bol.anio, bol.Bolivia, s=(3.4 * sc) ** 2, color=ROJO, zorder=5,
               edgecolors=ps.COLORS["fondo"], linewidths=0.9 * sc)
    items.append(dict(x=bol.anio.iloc[-1], y=bol.Bolivia.iloc[-1], nombre="Bolivia",
                      valor=num(bol.Bolivia.iloc[-1], 2), color=ROJO))
    # cifra de cada medición de Bolivia, salvo las pegadas al último dato (ése va en su rótulo)
    for a, v in zip(bol.anio, bol.Bolivia):
        if a <= x1 - 3:
            ax.annotate(num(v, 1), (a, v), xytext=(0, -6 * sc), textcoords="offset points",
                        ha="center", va="top", color=ROJO, zorder=6,
                        fontproperties=ps.fp(ps.MONO_BOLD, s_dato))

    estilo(ax, sc)
    umbral(ax, sc, spec["refline"], f"Nivel de reemplazo: {num(spec['refline'], 1)}", x0, s_dato,
           arriba=False)
    ax.set_xlim(x0 - 0.8, x1 + 0.6)
    ax.set_ylim(0.8, 5.7)
    ax.set_yticks(range(1, 6))
    ax.yaxis.set_major_formatter(ps.formateador_es(0))
    ax.set_xticks([a for a in range(1995, x1 + 1, 5)])

    o_sub, o_src = oraciones(spec["sub"]), oraciones(spec["source"])
    meta = ficha("blog-natalidad-fecundidad-region",
                 "Bolivia y la región: tasa global de fecundidad",
                 f"Hijos por mujer, {x0}–{x1}",
                 "Fuente: encuestas de demografía y salud (ENDSA/EDSA) e INE, Revisión 2025, para "
                 "Bolivia; Banco Mundial para los demás países. " + AUTOR,
                 " ".join([o_sub[2], o_src[2]]),
                 "lineas", F, ["tasa global de fecundidad", "América Latina", "reemplazo", "INE"])
    ps.componer(fig, ax, titulo=meta["titulo"], subtitulo=meta["subtitulo"], fuente=meta["fuente"],
                nota=meta["nota"], formato=F)
    textos = rotular_fin(fig, ax, items, sc, x1, ps.SIZES["fin_linea"] * sc * 0.9)
    encajar(fig, ax, textos, W - ps.MARGIN * sc)
    cerrar(fig, meta)


# --------------------------------------------------------------------------- #
# 2 · La aritmética de 2026, en cascada
# --------------------------------------------------------------------------- #
def aritmetica():
    F = "informe_horizontal"
    W, H, sc = ps._spec(F)
    spec = SPEC["nb-dem-aritmetica-2026"]
    t = pd.read_csv(ENTRADA / spec["dataset"], dtype=str)
    fila = {r.Componente: (int(r.Personas.replace(MENOS, "-").replace(".", "")),
                           float(r["Por mil"].replace(",", "."))) for _, r in t.iterrows()}
    nac, emi = fila["Nacimientos"], fila["Emigración neta"]
    net, dfn = fila["Nacimientos netos de emigración"], fila["Defunciones"]
    crec = fila["Crecimiento de la población"]
    if nac[0] + emi[0] != net[0] or net[0] + dfn[0] != crec[0]:
        raise SystemExit("⛔ la tabla de la aritmética no cierra")

    # (rótulo, personas, por mil, ¿total?)
    pasos = [("Nacimientos", *nac, False), ("Emigración\nneta", *emi, False),
             ("Nacimientos netos\nde emigración", *net, True), ("Defunciones", *dfn, False),
             ("Crecimiento de\nla población", *crec, True)]
    s_dato = ps.SIZES["dato"] * sc
    s_pt = ps._px2pt(s_dato)

    fig, ax = ps.nueva_figura(F)
    nivel, x = 0, np.arange(len(pasos))
    tramos = []
    for i, (_, v, _pm, total) in enumerate(pasos):
        a, b = (0, v) if total else (nivel, nivel + v)
        tramos.append((min(a, b), max(a, b), b))
        nivel = b
    for i, (lo, hi, _) in enumerate(tramos):
        ax.bar(i, hi - lo, bottom=lo, width=0.6, color=ROJO, linewidth=0, zorder=2)
        if i < len(tramos) - 1:
            ax.plot([i + 0.3, i + 0.7], [tramos[i][2]] * 2, color=PIZARRA, linewidth=1.0 * sc,
                    linestyle=(0, (1, 1.6)), zorder=3)
    for i, ((_, v, pm, total), (lo, hi, _)) in enumerate(zip(pasos, tramos)):
        cifra = num(v, 0, miles=True) if total else (("+" if v > 0 else "") + num(v, 0, miles=True))
        tasa = f"{num(pm, 1)} por mil"
        arriba = v > 0
        y, sg, va = (hi, 1, "bottom") if arriba else (lo, -1, "top")
        d1, d2 = (5 * sc + s_pt * 1.3, 5 * sc) if arriba else (5 * sc, 5 * sc + s_pt * 1.35)
        ax.annotate(cifra, (i, y), xytext=(0, sg * d1), textcoords="offset points", ha="center",
                    va=va, color=TINTA, fontproperties=ps.fp(ps.MONO_BOLD, s_dato * 1.1), zorder=6)
        ax.annotate(tasa, (i, y), xytext=(0, sg * d2), textcoords="offset points", ha="center",
                    va=va, color=PIZARRA, fontproperties=ps.fp(ps.BODY, s_dato * 0.92), zorder=6)

    estilo(ax, sc)
    ax.set_xlim(-0.6, len(pasos) - 0.4)
    ax.set_ylim(0, 185_000)
    ax.set_yticks(range(0, 150_001, 50_000))
    ax.yaxis.set_major_formatter(ps.formateador_es(0, miles=True))
    ax.set_xticks(x)
    ax.set_xticklabels([p[0] for p in pasos])
    ax.tick_params(axis="x", length=0)

    o_sub = oraciones(spec["sub"])
    meta = ficha("blog-natalidad-componentes-2026",
                 "Bolivia: componentes del cambio de la población",
                 "Personas y tasa por cada mil habitantes, 2026",
                 f"Fuente: {spec['source']}. " + AUTOR,
                 "Proyección del INE para 2026. " + o_sub[1],
                 "cascada", F, ["nacimientos", "defunciones", "emigración", "crecimiento de la población",
                                "INE"])
    ps.componer(fig, ax, titulo=meta["titulo"], subtitulo=meta["subtitulo"], fuente=meta["fuente"],
                nota=meta["nota"], formato=F)
    # los rótulos del eje X son TEXTO (componer los pasa a cifras) y ocupan dos renglones
    for lbl, p in zip(ax.get_xticklabels(), pasos):
        lbl.set_fontproperties(ps.fp(ps.BOLD if p[3] else ps.BODY, ps.SIZES["eje"] * sc * 0.92))
        lbl.set_color(TINTA if p[3] else ps.COLORS["cafe"])
        lbl.set_linespacing(1.15)
    extra = ps.SIZES["eje"] * sc * 1.2
    pos = ax.get_position()
    # el eje llega justo a W − M y el grosor de su línea base asomaba 4 px por fuera
    asoma = 1.2 * sc * ps.DPI / 72.0
    ax.set_position([pos.x0, pos.y0 + extra / H, pos.width - asoma / W, pos.height - extra / H])
    cerrar(fig, meta)


# --------------------------------------------------------------------------- #
# 3 · La población bajo tres supuestos
# --------------------------------------------------------------------------- #
def poblacion():
    F = "informe_horizontal"
    W, H, sc = ps._spec(F)
    spec = SPEC["nb-dem-poblacion"]
    df = pd.read_csv(ENTRADA / spec["dataset"])
    series = spec["series"]
    colores = P.rampa(len(series))
    texto = {P.GOLD: P.GOLD_INK}
    x0, x1 = int(df.anio.min()), int(df.anio.max())

    fig, ax = ps.nueva_figura(F)
    items = []
    for s, c in zip(series, colores):
        prota = s["col"] in spec.get("highlight", [])
        ax.plot(df.anio, df[s["col"]], color=c, linewidth=(2.7 if prota else 2.0) * sc,
                zorder=5 if prota else 4, solid_capstyle="round", solid_joinstyle="round")
        items.append(dict(x=x1, y=df[s["col"]].iloc[-1], nombre=s["name"],
                          valor=num(df[s["col"]].iloc[-1], 1), color=texto.get(c, c)))
    estilo(ax, sc)
    ax.set_xlim(x0 - 1.5, x1 + 1)
    ax.set_ylim(0, 14.6)
    ax.set_yticks(range(0, 15, 2))
    ax.yaxis.set_major_formatter(ps.formateador_es(0))
    ax.set_xticks([x0] + list(range(2040, x1 - 10, 20)) + [x1])

    (k_ine, (f_ine, em_ine)), (k_reb, (f_reb, _)), (k_sin, (_, em_sin)) = ESC_A.items()
    tgf_ine, a_ine = llega(f_ine)
    tgf_reb, a_reb = llega(f_reb)
    nota = (f"Proyección propia de cohorte-componentes con insumos del Censo 2024. Supuestos del INE: "
            f"la fecundidad baja a {num(tgf_ine, 2)} hasta {a_ine} y la emigración neta es de "
            f"{num(em_ine, 1)} por mil. Sin rebote: la fecundidad baja a {num(tgf_reb, 2)} hasta {a_reb}. "
            f"Sin emigración: supuestos del INE con emigración neta de {num(em_sin, 0)}.")
    meta = ficha("blog-natalidad-poblacion-escenarios",
                 "Bolivia: población proyectada bajo tres supuestos",
                 f"Millones de personas, {x0}–{x1}",
                 f"Fuente: {spec['source']}. " + AUTOR, nota,
                 "lineas", F, ["población", "proyecciones", "emigración", "Censo 2024"])
    ps.componer(fig, ax, titulo=meta["titulo"], subtitulo=meta["subtitulo"], fuente=meta["fuente"],
                nota=meta["nota"], formato=F)
    textos = rotular_fin(fig, ax, items, sc, x1, ps.SIZES["fin_linea"] * sc * 0.9)
    encajar(fig, ax, textos, W - ps.MARGIN * sc)
    cerrar(fig, meta)


# --------------------------------------------------------------------------- #
# 4 · Participación menonita, cuatro escenarios (modo Foco)
# --------------------------------------------------------------------------- #
CORTO = {"Parámetros de Fernández-Villaverde": "Fernández-Villaverde",
         "Medido en el censo": "Medido en el censo",
         "Subregistro alto y fecundidad alta": "Subregistro alto",
         "Medido, sin rebote del resto": "Sin rebote del resto"}


def menonitas():
    F = "informe_horizontal"
    W, H, sc = ps._spec(F)
    spec = SPEC["nb-dem-menonitas"]
    df = pd.read_csv(ENTRADA / spec["dataset"])
    x0, x1 = int(df.anio.min()), int(df.anio.max())
    prota = spec["highlight"][0]
    refe = COL_B["A"]            # el contraste del texto: los parámetros de Fernández-Villaverde
    s_dato = ps.SIZES["dato"] * sc

    fig, ax = ps.nueva_figura(F)
    items = []
    for s in spec["series"]:
        c = s["col"]
        if c == prota:
            kw, txt = dict(color=ROJO, linewidth=2.7 * sc, zorder=5), ROJO
        elif c == refe:
            kw, txt = dict(color=TINTA, linewidth=1.8 * sc, zorder=4, linestyle=(0, (3.2, 2.2))), TINTA
        else:
            kw, txt = dict(color=TENUE, linewidth=1.9 * sc, zorder=3), PIZARRA
        ax.plot(df.anio, df[c], solid_capstyle="round", **kw)
        items.append(dict(x=x1, y=df[c].iloc[-1], nombre=CORTO[c], valor=num(df[c].iloc[-1], 1) + "%",
                          color=txt))
    estilo(ax, sc)
    umbral(ax, sc, 50, "Mitad de la población", x0, s_dato)
    ax.set_xlim(x0 - 1.5, x1 + 1)
    ax.set_ylim(0, 75)
    ax.set_yticks(range(0, 71, 10))
    ax.yaxis.set_major_formatter(ps.formateador_es(0, "%"))
    ax.set_xticks([x0] + list(range(2050, x1 - 10, 25)) + [x1])

    def p(letra):
        e = ESC_B[CLAVE_B[letra]]
        return e, llega(e["tgf_res"])
    (ea, (ra, _)), (eb, (rb, ab)), (ec, _), (ed, (rd, ad)) = p("A"), p("B"), p("C"), p("D")
    nota = (f"Medido en el censo: {num(eb['men0'], 0, True)} menonitas en {x0}, fecundidad de "
            f"{num(eb['tgf_men'], 1)} y emigración de {num(eb['em_men'], 1)} por mil; el resto del país "
            f"baja a {num(rb, 2)} hasta {ab}. Fernández-Villaverde: {num(ea['men0'], 0, True)}, fecundidad "
            f"de {num(ea['tgf_men'], 1)} y sin emigración; el resto, {num(ra, 2)}. Subregistro alto: "
            f"{num(ec['men0'], 0, True)}, fecundidad de {num(ec['tgf_men'], 1)} y emigración de "
            f"{num(ec['em_men'], 1)} por mil. Sin rebote del resto: como el medido, pero el resto del "
            f"país baja a {num(rd, 2)} hasta {ad}.")
    meta = ficha("blog-natalidad-menonitas-escenarios",
                 "Bolivia: participación menonita en la población",
                 f"Porcentaje de la población del país en cuatro escenarios, {x0}–{x1}",
                 f"Fuente: {spec['source']}. " + AUTOR, nota,
                 "lineas", F, ["menonitas", "proyecciones", "composición", "Censo 2024",
                               "Fernández-Villaverde"])
    ps.componer(fig, ax, titulo=meta["titulo"], subtitulo=meta["subtitulo"], fuente=meta["fuente"],
                nota=meta["nota"], formato=F)
    textos = rotular_fin(fig, ax, items, sc, x1, ps.SIZES["fin_linea"] * sc * 0.9)
    encajar(fig, ax, textos, W - ps.MARGIN * sc)
    cerrar(fig, meta)


# --------------------------------------------------------------------------- #
# 5 · Composición: participación y fecundidad del país (dos paneles)
# --------------------------------------------------------------------------- #
def composicion():
    F = "informe_panorama"
    W, H, sc = ps._spec(F)
    spec = SPEC["nb-dem-composicion"]
    e = ESC_B[CLAVE_B["B"]]
    b = B[CLAVE_B["B"]]
    x = b.anio.to_numpy()
    x0, x1 = int(x.min()), int(x.max())
    resto = np.array([e["tgf_res"](a) for a in x])
    tgf_res, a_res = llega(e["tgf_res"])
    ref = SPEC["nb-dem-region"]["refline"]
    S_EJE, S_ROT, S_FIN, S_DATO = 20, 25, 21, 19

    fig, axd = ps.nueva_figura(F)
    axd.set_xticks([])
    axd.set_yticks([])
    meta = ficha("blog-natalidad-menonitas-composicion",
                 f"Bolivia: peso menonita y fecundidad del país, {x0}–{x1}",
                 "Escenario con los parámetros medidos en el Censo 2024",
                 f"Fuente: {spec['source']}. " + AUTOR,
                 f"Los menonitas mantienen una fecundidad de {num(e['tgf_men'], 1)} y la del resto del "
                 f"país baja a {num(tgf_res, 2)} hasta {a_res}: la fecundidad del país sube por composición.",
                 "lineas_paneles", F, ["menonitas", "composición", "tasa global de fecundidad",
                                       "nacimientos", "Censo 2024"])
    ps.componer(fig, axd, titulo=meta["titulo"], subtitulo=meta["subtitulo"], fuente=meta["fuente"],
                nota=meta["nota"], formato=F)
    pos = axd.get_position()
    axd.set_visible(False)

    head_h = 62 * sc / H
    gap = 150 * sc / W
    colW = (pos.width - gap) / 2
    ix0, dx0 = pos.x0, pos.x0 + colW + gap
    ax_i = fig.add_axes([ix0, pos.y0, colW, pos.height - head_h])
    ax_d = fig.add_axes([dx0, pos.y0, colW, pos.height - head_h])

    # izquierda: participación en la población y en los nacimientos
    c_nac, c_pob = P.rampa(2)
    ax_i.plot(x, b.pct_nac, color=c_nac, linewidth=2.5 * sc, zorder=5, solid_capstyle="round")
    ax_i.plot(x, b.pct_pob, color=c_pob, linewidth=2.5 * sc, zorder=4, solid_capstyle="round")
    estilo(ax_i, sc)
    ax_i.set_ylim(0, 70)
    ax_i.set_yticks(range(0, 71, 10))
    ax_i.yaxis.set_major_formatter(ps.formateador_es(0, "%"))
    items_i = [dict(x=x1, y=b.pct_nac.iloc[-1], nombre="Nacimientos", valor=num(b.pct_nac.iloc[-1], 1) + "%",
                    color=c_nac),
               dict(x=x1, y=b.pct_pob.iloc[-1], nombre="Población", valor=num(b.pct_pob.iloc[-1], 1) + "%",
                    color=c_pob)]

    # derecha: la fecundidad del país contra la del resto
    ax_d.plot(x, resto, color=TENUE, linewidth=2.0 * sc, zorder=3, solid_capstyle="round")
    ax_d.plot(x, b.tgf_nac, color=ROJO, linewidth=2.5 * sc, zorder=5, solid_capstyle="round")
    estilo(ax_d, sc)
    umbral(ax_d, sc, ref, f"Nivel de reemplazo: {num(ref, 1)}", x0, S_DATO * sc)
    ax_d.set_ylim(1.0, 2.8)
    ax_d.set_yticks(np.arange(1.0, 2.51, 0.5))
    ax_d.yaxis.set_major_formatter(ps.formateador_es(1))
    items_d = [dict(x=x1, y=b.tgf_nac.iloc[-1], nombre="País", valor=num(b.tgf_nac.iloc[-1], 2), color=ROJO),
               dict(x=x1, y=resto[-1], nombre="Resto del país", valor=num(resto[-1], 2), color=PIZARRA)]

    for ax in (ax_i, ax_d):
        ax.set_xlim(x0 - 2, x1 + 1)
        ax.set_xticks([x0] + list(range(2050, x1 - 10, 25)) + [x1])
        fuentes_ejes(ax, sc, S_EJE)

    # bloque de cifras Y al borde izquierdo de SU columna (el de la izquierda = margen del título)
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    for ax, c0, c1 in ((ax_i, ix0, ix0 + colW), (ax_d, dx0, dx0 + colW)):
        lw = max(l.get_window_extent(r).width for l in ax.get_yticklabels() if l.get_text())
        spine = c0 * W + lw + 6 * sc * ps.DPI / 72.0
        p = ax.get_position()
        ax.set_position([spine / W, p.y0, c1 - spine / W, p.height])

    ti = rotular_fin(fig, ax_i, items_i, sc, x1, S_FIN * sc)
    encajar(fig, ax_i, ti, (ix0 + colW) * W)
    td = rotular_fin(fig, ax_d, items_d, sc, x1, S_FIN * sc)
    encajar(fig, ax_d, td, (dx0 + colW) * W)

    fp_rot = ps.fp(ps.BOLD, S_ROT * sc)
    y_rot = pos.y0 + pos.height - 8 * sc / H
    fig.text(ix0, y_rot, "Participación Menonita",
             fontproperties=fp_rot, color=ps.COLORS["cafe_oscuro"], va="top", ha="left")
    fig.text(dx0, y_rot, "Tasa Global de Fecundidad",
             fontproperties=fp_rot, color=ps.COLORS["cafe_oscuro"], va="top", ha="left")
    cerrar(fig, meta)


LAMINAS = {"region": region, "aritmetica": aritmetica, "poblacion": poblacion,
           "menonitas": menonitas, "composicion": composicion}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo", default="", help="coma: " + ",".join(LAMINAS))
    args = ap.parse_args()
    comprobar()
    solo = [s for s in args.solo.split(",") if s] or list(LAMINAS)
    for s in solo:
        LAMINAS[s]()
    CAT.build_manifest()
    r = subprocess.run([sys.executable, str(VIZ / "verificar.py")], cwd=VIZ.parent,
                       capture_output=True, text=True, encoding="utf-8")
    print("\n".join(r.stdout.strip().splitlines()[-3:]))
    if r.returncode:
        raise SystemExit("⛔ el contrato del Banco no pasa:\n" + r.stdout[-1500:] + r.stderr[-800:])


if __name__ == "__main__":
    main()

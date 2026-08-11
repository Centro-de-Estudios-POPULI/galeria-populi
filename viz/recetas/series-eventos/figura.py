"""
Figura de publicación — Reservas Internacionales del BCB y el oro pignorado.
Caso de referencia del estilo «series-eventos» (ver README.md de esta carpeta).

Figura única de marca (formato 'informe_horizontal', ~3:2) con 2 paneles LADO A
LADO, cada uno en su escala:
  · izquierda: Oro · derecha: Divisas
  · cada hito = punto sobre la línea + guía fina + etiqueta de 2 líneas (nombre
    en negrita + detalle), sin banda sombreada.

El estilo (eje de fechas + anotación de eventos) viene de
`viz/charts/series_eventos.py`; el marco/marca/tipografía de `viz/populi_style.py`.
Aquí solo viven los datos, la composición de paneles y el layout de los callouts.

Salida: output/reservas_oro_pignorado.png  (formato 'informe_horizontal', 2x).
"""
import sys
import json
from pathlib import Path
import datetime as dt
import numpy as np
import matplotlib
matplotlib.use("Agg")
from matplotlib.dates import date2num

VIZ = Path(__file__).resolve().parents[2]          # …/galeria-populi/viz
sys.path.insert(0, str(VIZ))                        # populi_style
sys.path.insert(0, str(VIZ / "charts"))             # series_eventos
import populi_style as ps          # noqa: E402
import series_eventos as se        # noqa: E402

PUB = Path(__file__).parent
S = json.loads((PUB / "data" / "serie_final.json").read_text(encoding="utf-8"))["serie"]
EVENTS = json.loads((PUB / "data" / "events.json").read_text(encoding="utf-8"))

FORMATO = "informe_horizontal"   # 3:2 horizontal, fuentes fijas (SC_REF)
W, H, sc = ps._spec(FORMATO)

# ── Datos ──────────────────────────────────────────────────────────────────
dates = [dt.date.fromisoformat(p["date"]) for p in S]
fechas = [p["date"] for p in S]                     # ISO, alineado con x (para eventos)
x = np.array(date2num(dates))
oro = np.array([p["oro"] for p in S], float)
div = np.array([p["divisas"] for p in S], float)
otros = np.array([p["deg"] + p["fmi"] for p in S], float)
rin = np.array([p["rin"] for p in S], float)
EST_I = next(i for i, p in enumerate(S) if p["tipo"] == "estimado")

# Colores de las series (paleta de marca: oro + navy = 2ª serie oficial)
C_ORO   = ps.COLORS["oro"]        # #D4A017
C_DIV   = ps.COLORS["azul"]       # #0D1B2A (navy, --color-navy 2ª serie)

# Nombre (1ª línea, negrita) por evento/panel
ABBR = {
    ("oro", "2026-03-20"): "Precio del oro",
    ("oro", "2026-06-15"): "Oro pignorado",
    ("divisas", "2025-12-24"): "Desembolso CAF",
    ("divisas", "2026-03-20"): "Deuda externa",
    ("divisas", "2026-05-15"): "Bonos soberanos",
}
# Detalle (2ª línea, gris) — la "información extra" de cada llamada
DET = {
    ("oro", "2026-03-20"): "Caída de la cotización",
    ("oro", "2026-06-15"): "−586 MM US$ · est.",
    ("divisas", "2025-12-24"): "Crédito multilateral",
    ("divisas", "2026-03-20"): "Pago de vencimientos",
    ("divisas", "2026-05-15"): "Emisión externa",
}
# Posición de cada etiqueta: ly (altura 0-1 de su base) · dx (corrimiento
# horizontal del bloque centrado, fracción del rango X; <0 izquierda)
LAYOUT = {
    ("oro", "2026-03-20"): dict(ly=0.82, dx=0.0),
    ("oro", "2026-06-15"): dict(ly=0.575, dx=-0.11),   # bloque entre 3800 y 4000
    ("divisas", "2025-12-24"): dict(ly=0.60, dx=0.10),
    ("divisas", "2026-03-20"): dict(ly=0.44, dx=0.0),
    ("divisas", "2026-05-15"): dict(ly=0.845, dx=-0.05),  # bloque entre 1200 y 1400
}


def style_axis(ax):
    se.estilo_eje(ax, dates, sc)


def add_events(ax, panel, serie_y, lo, top):
    se.marcar_eventos(ax, EVENTS, x=x, fechas=fechas, panel=panel, ymin=lo, ymax=top,
                      sc=sc, serie_y=serie_y, layout=LAYOUT, abbr=ABBR, detalle=DET,
                      banda_alpha=0.0)   # sin bandas: el punto ya fija el evento


EV_EST = se.colores_evento()["est"]

# ── Marco de marca con componer() (eje dummy) ───────────────────────────────
fig, axd = ps.nueva_figura(FORMATO)
axd.set_xticks([]); axd.set_yticks([])
ps.componer(
    fig, axd,
    titulo="Bolivia: evolución de los componentes de las RIN",
    subtitulo="Componentes principales —oro y divisas—, evolución semanal · millones de USD",
    fuente="Fuente: Banco Central de Bolivia (BCB), Estadísticas Semanales; Nota de Prensa NP10/2026. "
           "Elaboración: Centro de Estudios POPULI.",
    nota="El punto del 15-jun-2026 estima el impacto de la entrega de 4,3 t de oro pignorado (−USD 586 MM en oro); "
         "el BCB aún no publica esa semana.",
    formato=FORMATO,
)
pos = axd.get_position()
axd.set_visible(False)

# ── Dos paneles lado a lado: Oro (izq) · Divisas (der) ──────────────────────
# Encuadre: el conjunto respeta los márgenes del título (izq = M, der = W-M);
# cada panel inserta su bloque de números Y al borde izquierdo de SU columna.
M = ps.MARGIN * sc
Hb = pos.height
head_h = 46 * sc / H              # franja del rótulo (Oro / Divisas) sobre los paneles
col_gap = 80 * sc / W             # separación entre las dos columnas
colW = (pos.width - col_gap) / 2.0
panelH = Hb - head_h
xpad = (x.max() - x.min()) * 0.03

ox0 = pos.x0                       # borde izquierdo de la columna Oro (= M)
dx0 = pos.x0 + colW + col_gap      # borde izquierdo de la columna Divisas
ax_oro = fig.add_axes([ox0, pos.y0, colW, panelH])
ax_div = fig.add_axes([dx0, pos.y0, colW, panelH])


def panel_simple(ax, serie, color, panel, lo, top):
    ax.fill_between(x[:EST_I+1], 0, serie[:EST_I+1], color=color, alpha=0.26, linewidth=0, zorder=2)
    ax.plot(x[:EST_I+1], serie[:EST_I+1], color=color, linewidth=0.76 * sc, zorder=4, solid_capstyle="round")
    ax.plot(x[EST_I-1:EST_I+1], serie[EST_I-1:EST_I+1], color=color, linewidth=0.76 * sc,
            linestyle=(0, (2, 2)), zorder=4)
    style_axis(ax)
    ax.set_ylim(lo, top)
    ax.set_xlim(x.min() - xpad, x.max() + xpad)
    add_events(ax, panel, serie, lo, top)


panel_simple(ax_oro, oro, C_ORO, "oro", oro.min() * 0.92, oro.max() * 1.20)
panel_simple(ax_div, div, C_DIV, "divisas", 0, div.max() * 1.40)

# Encuadre: insertar el bloque de números Y al borde izquierdo de cada columna
# (el de Oro coincide con M, como el título); el borde derecho de Divisas = W-M.
fig.canvas.draw()
_rend = fig.canvas.get_renderer()


def _inset_y(ax, col_left, col_right):
    ws = [l.get_window_extent(_rend).width for l in ax.get_yticklabels() if l.get_text()]
    lw = max(ws) if ws else 0.0
    spine = col_left * W + lw + 6 * sc * ps.DPI / 72.0
    p = ax.get_position()
    ax.set_position([spine / W, p.y0, col_right - spine / W, p.height])


_inset_y(ax_oro, ox0, ox0 + colW)
_inset_y(ax_div, dx0, dx0 + colW)

# Rótulo de cada panel: SEPARADO arriba (un poco más), negrita REAL, al borde de su columna
f_rot = ps.fp(se.BOLD, ps.SIZES["subtitulo"] * 0.86 * sc)
_y_rot = pos.y0 + panelH + 18 * sc / H
fig.text(ox0, _y_rot, "Oro · millones de USD", fontproperties=f_rot, color=C_ORO, va="bottom", ha="left")
fig.text(dx0, _y_rot, "Divisas · millones de USD", fontproperties=f_rot, color=C_DIV, va="bottom", ha="left")

ps.guardar(fig, str(PUB / "output" / "reservas_oro_pignorado.png"), formato=FORMATO, thumb=False)
print("OK render")

"""
Renderizador de charts de EJEMPLO con estilo POPULI (matplotlib).

Su único rol es producir PNGs de chart que luego make_card.py enmarca.
En producción, este paso lo reemplaza la exportación de cada repo
(ECharts/Plotly -> PNG). Aquí sirve para generar muestras reales.
"""
from __future__ import annotations
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import brand_kit as bk

ROOT = bk.ROOT
C = bk.C
OUT = ROOT / "data" / "charts"
OUT.mkdir(parents=True, exist_ok=True)

# registrar tipografías de marca en matplotlib
for fp in (ROOT / "assets" / "fonts").glob("*.ttf"):
    font_manager.fontManager.addfont(str(fp))
plt.rcParams["font.family"] = "Inter"
plt.rcParams["axes.edgecolor"] = C["grid"]
plt.rcParams["axes.linewidth"] = 1.0
plt.rcParams["svg.fonttype"] = "none"


def style_axes(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(C["grid"])
    ax.tick_params(colors=C["inkSoft"], labelsize=15)
    ax.grid(axis="y", color=C["grid"], linewidth=0.8, alpha=0.7)
    ax.set_axisbelow(True)


def save(fig, name):
    p = OUT / name
    fig.savefig(p, dpi=200, bbox_inches="tight", transparent=True, pad_inches=0.1)
    plt.close(fig)
    print(f"chart OK  {name}")
    return p


def chart_ipc_interanual():
    """Inflación interanual general — línea."""
    data = json.loads((ROOT.parent / "populi-inflacion" / "data" / "ipc_general.json").read_text(encoding="utf-8"))
    serie = data["indice"]
    # inflación interanual = variación contra 12 meses atrás
    fechas = [d["fecha"] for d in serie]
    vals = [d["valor"] for d in serie]
    yoy_x, yoy_y = [], []
    for i in range(12, len(vals)):
        yoy_x.append(fechas[i])
        yoy_y.append((vals[i] / vals[i - 12] - 1) * 100)
    yoy_x, yoy_y = yoy_x[-60:], yoy_y[-60:]

    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.plot(range(len(yoy_y)), yoy_y, color=C["red"], linewidth=3.2, solid_capstyle="round")
    ax.fill_between(range(len(yoy_y)), yoy_y, min(yoy_y) - 0.5, color=C["red"], alpha=0.08)
    ax.scatter([len(yoy_y) - 1], [yoy_y[-1]], color=C["red"], s=80, zorder=5)
    ax.annotate(f"{yoy_y[-1]:.1f}%", (len(yoy_y) - 1, yoy_y[-1]),
                textcoords="offset points", xytext=(-12, 12),
                fontsize=22, fontweight="bold", color=C["red"], ha="right")
    step = max(1, len(yoy_x) // 6)
    ax.set_xticks(range(0, len(yoy_x), step))
    ax.set_xticklabels([yoy_x[i] for i in range(0, len(yoy_x), step)], rotation=0)
    ax.set_ylabel("Variación interanual (%)", fontsize=15, color=C["inkSoft"])
    style_axes(ax)
    return save(fig, "ipc_interanual.png")


def chart_divisiones():
    """Top divisiones del IPC por variación interanual — barras horizontales."""
    data = json.loads((ROOT.parent / "populi-inflacion" / "data" / "ipc_divisiones.json").read_text(encoding="utf-8"))
    rows = []
    for nombre, serie in data.items():
        if nombre == "ÍNDICE GENERAL" or len(serie) < 13:
            continue
        yoy = (serie[-1]["valor"] / serie[-13]["valor"] - 1) * 100
        rows.append((nombre.title(), yoy))
    rows.sort(key=lambda r: r[1])
    rows = rows[-8:]
    labels = [r[0] if len(r[0]) <= 28 else r[0][:26] + "…" for r in rows]
    vals = [r[1] for r in rows]
    colors = [C["red"] if v >= 0 else C["teal"] for v in vals]

    fig, ax = plt.subplots(figsize=(9, 5.4))
    bars = ax.barh(range(len(vals)), vals, color=colors, height=0.68)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=14)
    for b, v in zip(bars, vals):
        ax.text(b.get_width() + (0.05 if v >= 0 else -0.05), b.get_y() + b.get_height() / 2,
                f"{v:+.1f}%", va="center", ha="left" if v >= 0 else "right",
                fontsize=14, fontweight="bold", color=C["inkSoft"])
    ax.axvline(0, color=C["grid"], linewidth=1)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(left=False, colors=C["inkSoft"])
    ax.set_xticks([])
    ax.margins(x=0.12)
    return save(fig, "ipc_divisiones.png")


if __name__ == "__main__":
    chart_ipc_interanual()
    chart_divisiones()

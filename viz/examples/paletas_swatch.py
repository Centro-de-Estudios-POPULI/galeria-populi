"""Muestrario de paletas junto al rojo de marca, para evaluar la armonía."""
import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

VIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VIZ))
import populi_style as ps

orden = ["calido", "rojo", "verde", "azul", "divergente"]
fig = plt.figure(figsize=(5.4, 4.4), dpi=200)
fig.patch.set_facecolor(ps.COLORS["fondo"])
grad = np.linspace(0, 1, 256).reshape(1, -1)

n = len(orden) + 1
# fila de marca (rojo sólido)
axb = fig.add_axes([0.28, 0.86, 0.66, 0.07])
axb.imshow(np.ones((1, 256, 3)) * np.array(ps._rgb(ps.COLORS["rojo"])) / 255, aspect="auto")
axb.set_xticks([]); axb.set_yticks([])
for s in axb.spines.values():
    s.set_visible(False)
fig.text(0.26, 0.895, "Rojo de marca", ha="right", va="center",
         fontproperties=ps.fp("Zilla Slab", 18), color=ps.COLORS["tinta"])

for i, nombre in enumerate(orden):
    y = 0.72 - i * 0.135
    ax = fig.add_axes([0.28, y, 0.66, 0.085])
    ax.imshow(grad, aspect="auto", cmap=ps.colormap(nombre))
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    fig.text(0.26, y + 0.042, nombre, ha="right", va="center",
             fontproperties=ps.fp("Public Sans", 17), color=ps.COLORS["cafe"])

fig.text(0.06, 0.965, "Paletas de mapa POPULI", fontproperties=ps.fp("Zilla Slab", 26),
         color=ps.COLORS["tinta"], va="center")
fig.savefig(VIZ / "output" / "paletas_swatch.png", facecolor=ps.COLORS["fondo"])
print("OK paletas_swatch.png")

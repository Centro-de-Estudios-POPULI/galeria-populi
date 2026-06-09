"""
lineas.py — Series de tiempo simples (sin bandas).

Reutiliza el motor de líneas con bandas (mismas reglas de estilo), pero pensado
para 1–4 series limpias con etiqueta al final y, opcionalmente, punto + valor
destacado en el último dato (número-héroe).

  grafico_lineas(df, series=[{"y","label","color"}], destacar_fin=False, ...)
"""
from __future__ import annotations
import sys
from pathlib import Path

VIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VIZ))
sys.path.insert(0, str(VIZ / "charts"))
import populi_style as ps
from lineas_bandas import grafico_lineas_bandas


def grafico_lineas(df, series, destacar_fin=False, **kw):
    """Series limpias. destacar_fin=True marca el último punto con un círculo y
    su valor (útil para una sola serie protagonista)."""
    archivo = kw.pop("archivo", None)
    fig, ax = grafico_lineas_bandas(df, series, archivo=None, **kw)
    if destacar_fin:
        _, _, sc = ps._spec(kw.get("formato", "red_vertical"))
        for s in series:
            color = ps.col(s.get("color", "rojo"))
            y = df[s["y"]].to_numpy()
            ax.scatter([df.index[-1]], [y[-1]], color=color, s=80 * sc, zorder=7)
    if archivo:
        ps.guardar(fig, archivo, formato=kw.get("formato", "red_vertical"))
    return fig, ax

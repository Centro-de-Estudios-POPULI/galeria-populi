"""
catalogo.py — Publicar gráficas al Banco de Gráficos y Datos.

`publicar(meta, df, **opts)` hace TODO de una sola vez:
  1. Renderiza la gráfica branded (motor populi_style).
  2. Exporta los DATOS detrás de la gráfica a CSV descargable.
  3. Registra la FICHA (metadata) en el catálogo.

Así, para crear una gráfica solo necesitas pasar: los datos, el título y qué
tipo es. El resto (marca, estilo, descargas, catálogo) sale solo.

    from catalogo import publicar, build_manifest
    publicar(
        meta={"slug": "ipc-interanual", "titulo": "...", "tipo": "lineas_bandas",
              "subtitulo": "...", "fuente": "Fuente: INE.", "categoria": "inflacion",
              "tags": ["ipc"], "fecha": "2026-06-09"},
        df=mi_dataframe,
        series=[{"y": "valor", "label": "IPC", "color": "rojo"}],
    )
    build_manifest()   # consolida todas las fichas -> src/manifest.json (para Astro)

Salidas por gráfica:
    public/graficas/<slug>.png    (imagen branded, formato elegido)
    public/thumbs/<slug>.png      (miniatura cuadrada)
    public/datos/<slug>.csv       (datos descargables)
    data/catalogo/<slug>.json     (ficha de metadata)
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

VIZ = Path(__file__).resolve().parent
ROOT = VIZ.parent
sys.path.insert(0, str(VIZ))
sys.path.insert(0, str(VIZ / "charts"))
import populi_style as ps
from lineas_bandas import grafico_lineas_bandas
from lineas import grafico_lineas
from barras import grafico_barras, grafico_barras_ranking
from areas import grafico_areas
from mapas import grafico_mapa
from mapa_mundial import grafico_mapa_mundial

GRAFICAS = ROOT / "public" / "graficas"
DATOS = ROOT / "public" / "datos"
CATALOGO = ROOT / "data" / "catalogo"

# Categorías del Banco: etiqueta visible + color de acento (nombre de paleta).
CATEGORIAS = {
    "inflacion":  {"label": "Inflación",            "color": "rojo"},
    "fiscal":     {"label": "Fiscal y presupuesto", "color": "azul"},
    "monetario":  {"label": "Monetario",            "color": "azul"},
    "actividad":  {"label": "Actividad económica",  "color": "oro"},
    "censo":      {"label": "Censo y social",       "color": "rojo"},
    "empleo":     {"label": "Empleo",               "color": "azul"},
    "mundo":      {"label": "Mundo",                "color": "rojo"},
    "general":    {"label": "General",              "color": "rojo"},
}

# tipo -> (función constructora, ¿recibe DataFrame como 1er argumento?)
_BUILDERS = {
    "lineas_bandas": (grafico_lineas_bandas, True),
    "lineas":        (grafico_lineas,        True),
    "areas":         (grafico_areas,         True),
    "barras":        (grafico_barras,        False),
    "ranking":       (grafico_barras_ranking, False),
    "mapa":          (grafico_mapa,          False),  # datos vía gdf en chart_kwargs
    "mapa_mundial":  (grafico_mapa_mundial,  False),  # mundial (ISO3) vía gdf
}


def publicar(meta: dict, df=None, **chart_kwargs):
    """Renderiza + exporta datos + registra la ficha. Devuelve la ficha (dict).

    meta (obligatorio: slug, titulo, tipo): identidad y metadata de la gráfica.
    df: DataFrame con los datos a exportar (CSV). Para líneas/áreas también es la
        fuente del gráfico; para barras/ranking los datos van en chart_kwargs.
    chart_kwargs: argumentos del tipo (series=, color=, x=, valores=, etiquetas=,
        y_sufijo=, eje_x=, etc.).
    """
    for req in ("slug", "titulo", "tipo"):
        if req not in meta:
            raise ValueError(f"meta requiere '{req}'")
    slug, tipo = meta["slug"], meta["tipo"]
    if tipo not in _BUILDERS:
        raise ValueError(f"tipo '{tipo}' no válido. Opciones: {list(_BUILDERS)}")
    fn, usa_df = _BUILDERS[tipo]
    formato = meta.get("formato", "red_vertical")

    for d in (GRAFICAS, CATALOGO):
        d.mkdir(parents=True, exist_ok=True)

    comun = dict(titulo=meta["titulo"], subtitulo=meta.get("subtitulo", ""),
                 fuente=meta.get("fuente", ""), nota=meta.get("nota", ""),
                 formato=formato)
    if usa_df:
        if df is None:
            raise ValueError(f"el tipo '{tipo}' requiere df")
        fig, _ = fn(df, **chart_kwargs, **comun, archivo=None)
    else:
        fig, _ = fn(**chart_kwargs, **comun, archivo=None)

    ps.guardar(fig, GRAFICAS / f"{slug}.png", formato=formato)

    # Política del Banco: solo se publica la IMAGEN, no los datos crudos. La idea
    # es que se usen y compartan nuestros gráficos, no que se repliquen los datos.
    datos_rel = None

    ficha = {
        "slug": slug,
        "titulo": meta["titulo"],
        "subtitulo": meta.get("subtitulo", ""),
        "categoria": meta.get("categoria", "general"),
        "fuente": meta.get("fuente", ""),
        "tags": meta.get("tags", []),
        "fecha": meta.get("fecha", ""),
        "tipo": tipo,
        "formato": formato,
        "imagen": f"graficas/{slug}.png",
        "thumb": f"thumbs/{slug}.png",
        "datos": datos_rel,
    }
    (CATALOGO / f"{slug}.json").write_text(
        json.dumps(ficha, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"PUBLICADA  {slug}  [{tipo}]  datos={'sí' if datos_rel else 'no'}")
    return ficha


def build_manifest():
    """Consolida todas las fichas del catálogo en src/manifest.json (para Astro)."""
    fichas = [json.loads(p.read_text(encoding="utf-8"))
              for p in sorted(CATALOGO.glob("*.json"))]
    fichas.sort(key=lambda e: e.get("fecha", ""), reverse=True)
    cats = {k: {"label": v["label"], "color": ps.col(v["color"])}
            for k, v in CATEGORIAS.items()}
    manifest = {"categorias": cats, "graficas": fichas}
    out = ROOT / "src" / "manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"manifest.json  ({len(fichas)} gráficas)")
    return fichas


if __name__ == "__main__":
    build_manifest()

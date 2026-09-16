"""
catalogo.py — Publicar gráficas al Banco de Gráficos.

`publicar(meta, df, **opts)` hace TODO de una sola vez:
  1. Renderiza la gráfica branded (motor populi_style).
  2. Registra la FICHA (metadata) en el catálogo.

Política del Banco: se publica la IMAGEN, no los datos crudos.

    from catalogo import publicar, build_manifest
    publicar(
        meta={"slug": "ipc-interanual", "titulo": "...", "tipo": "lineas_bandas",
              "subtitulo": "...", "fuente": "Fuente: INE.", "categoria": "inflacion",
              "tags": ["ipc"], "fecha": "2026-06-09"},
        df=mi_dataframe,
        series=[{"y": "valor", "label": "IPC", "color": "rojo"}],
    )
    build_manifest()   # consolida las fichas -> src/manifest.json + public/indice_laminas.json

Salidas por gráfica:
    public/graficas/<slug>.png    (imagen branded, formato elegido)
    public/thumbs/<slug>.webp     (miniatura cuadrada, letterbox)
    data/catalogo/<slug>.json     (ficha de metadata)

★ LA FICHA DECLARA SU VÍNCULO CON EL ATLAS (2026-09-16). Además de los doce
  campos de siempre, una lámina municipal lleva `clave` (la del catálogo del
  atlas), `atlas` («censo» | «fiscal»), `anio`, `modo` y `enlace` (la URL del
  indicador en el tablero interactivo). Antes el vínculo sobrevivía como un tag
  suelto y el atlas lo reconstruía por coincidencia de tags: cambiar un tag
  rompía 215 enlaces en silencio. Ahora se declara y `build_manifest()` lo
  publica en `public/indice_laminas.json`, que los atlas leen al arrancar para
  ofrecer SÓLO las láminas que existen.
"""
from __future__ import annotations
import json
import sys
from datetime import date
from pathlib import Path

VIZ = Path(__file__).resolve().parent
ROOT = VIZ.parent
sys.path.insert(0, str(VIZ))
sys.path.insert(0, str(VIZ / "charts"))
import populi_style as ps
from lineas_bandas import grafico_lineas_bandas
from lineas import grafico_lineas
from barras import grafico_barras, grafico_barras_ranking
from barras_apiladas import grafico_barras_apiladas
from areas import grafico_areas
from mapas import grafico_mapa
from mapa_mundial import grafico_mapa_mundial

GRAFICAS = ROOT / "public" / "graficas"
THUMBS = ROOT / "public" / "thumbs"
CATALOGO = ROOT / "data" / "catalogo"
INDICE = ROOT / "public" / "indice_laminas.json"

# Categorías del Banco: etiqueta visible + color de acento, tomado del reparto
# por sección del sitio (el monitor de ese tema, o la sección que lo aloja).
CATEGORIAS = {
    "inflacion":  {"label": "Inflación",            "color": "rojo"},
    "fiscal":     {"label": "Fiscal y presupuesto", "color": "#E57D22"},   # = M. Fiscal
    "monetario":  {"label": "Monetario",            "color": "oro_tinta"}, # = M. Monetario
    "actividad":  {"label": "Actividad económica",  "color": "oro"},       # = M. Actividad
    "censo":      {"label": "Censo y social",       "color": "serie_teal"},# = Herramientas
    "empleo":     {"label": "Empleo",               "color": "serie_azul"},
    "mundo":      {"label": "Mundo",                "color": "serie_rosa"},
    "general":    {"label": "General",              "color": "rojo_oscuro"},
}

# Campos fijos de la ficha. Cualquier otro campo de `meta` se copia tal cual
# (clave, atlas, anio, modo, enlace, universo, unidad, escala…).
CAMPOS_FIJOS = ("slug", "titulo", "subtitulo", "categoria", "fuente", "tags", "fecha",
                "tipo", "formato", "imagen", "thumb", "datos")

# tipo -> (función constructora, ¿recibe DataFrame como 1er argumento?)
_BUILDERS = {
    "lineas_bandas": (grafico_lineas_bandas, True),
    "lineas":        (grafico_lineas,        True),
    "areas":         (grafico_areas,         True),
    "barras_apiladas": (grafico_barras_apiladas, True),
    "barras":        (grafico_barras,        False),
    "ranking":       (grafico_barras_ranking, False),
    "mapa":          (grafico_mapa,          False),  # datos vía gdf en chart_kwargs
    "mapa_mundial":  (grafico_mapa_mundial,  False),  # mundial (ISO3) vía gdf
}


def ficha_de(meta: dict, tipo: str, formato: str) -> dict:
    """Arma la ficha: los doce campos fijos + los declarados por el generador."""
    slug = meta["slug"]
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
        "thumb": f"thumbs/{slug}.webp",
        "datos": None,
    }
    for k, v in meta.items():
        if k not in ficha and k not in ("tipo", "formato"):
            ficha[k] = v
    return ficha


def registrar(meta: dict, tipo: str, formato: str) -> dict:
    """Escribe la ficha sin renderizar (para gráficas compuestas con `componer()`
    directo, que ya escribieron su PNG con ps.guardar)."""
    CATALOGO.mkdir(parents=True, exist_ok=True)
    ficha = ficha_de(meta, tipo, formato)
    (CATALOGO / f"{meta['slug']}.json").write_text(
        json.dumps(ficha, ensure_ascii=False, indent=2), encoding="utf-8")
    return ficha


def publicar(meta: dict, df=None, **chart_kwargs):
    """Renderiza + registra la ficha. Devuelve la ficha (dict).

    meta (obligatorio: slug, titulo, tipo): identidad y metadata de la gráfica.
    df: DataFrame con los datos; para líneas/áreas es la fuente del gráfico,
        para barras/ranking/mapas los datos van en chart_kwargs.
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
    ficha = registrar(meta, tipo, formato)
    print(f"PUBLICADA  {slug}  [{tipo}]")
    return ficha


def build_manifest():
    """Consolida las fichas en src/manifest.json (para Astro) y publica el
    índice de láminas municipales que leen los atlas."""
    fichas = [json.loads(p.read_text(encoding="utf-8"))
              for p in sorted(CATALOGO.glob("*.json"))]
    fichas.sort(key=lambda e: (e.get("fecha", ""), e.get("titulo", "")), reverse=True)

    # ⚠️ sólo se publica lo que EXISTE en disco: una ficha sin PNG o sin
    #    miniatura es un enlace roto con nombre de gráfica
    rotas = [f["slug"] for f in fichas
             if not (ROOT / "public" / f["imagen"]).exists()
             or not (ROOT / "public" / f["thumb"]).exists()]
    if rotas:
        raise SystemExit(f"⛔ {len(rotas)} fichas sin PNG o sin miniatura: {rotas[:8]}")

    usadas = {f.get("categoria") for f in fichas}
    cats = {k: {"label": v["label"], "color": ps.col(v["color"])}
            for k, v in CATEGORIAS.items() if k in usadas}
    manifest = {
        "meta": {"generado": date.today().isoformat(), "n": len(fichas),
                 "municipios": 343},
        "categorias": cats, "graficas": fichas,
    }
    out = ROOT / "src" / "manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # índice de láminas por atlas → clave → modo → slug
    indice = {}
    for f in fichas:
        if f.get("atlas") and f.get("clave") and f.get("modo"):
            indice.setdefault(f["atlas"], {}).setdefault(f["clave"], {})[f["modo"]] = f["slug"]
    INDICE.write_text(json.dumps({"generado": manifest["meta"]["generado"], "laminas": indice},
                                 ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    n_ind = sum(len(v) for v in indice.values())
    print(f"manifest.json  ({len(fichas)} gráficas, {len(cats)} categorías) · "
          f"indice_laminas.json ({n_ind} claves)")
    return fichas


if __name__ == "__main__":
    build_manifest()

# Motor de visualización POPULI — `viz/`

Sistema para producir gráficas con la identidad del Centro de Estudios POPULI
(estética editorial tipo FMI) y publicarlas al **Banco de Gráficos y Datos**.

## Identidad (decidida 2026-06-09)

- **Titular:** Zilla Slab (Bold, slab serif robusta).
- **Cuerpo, ejes y números:** Public Sans (sans humanista — alternativa libre a
  Whitney, la fuente del FMI). Una sola familia en todo, look FMI.
- **Paleta:** tokens reales del sitio populi.org.bo (rojo `#8B1A1A`, fondo
  `#FAF8F3`, navy `#0D1B2A`, café, oro, grilla `#E2DDD3`).
- Todo el estilo vive en `populi_style.py`. Ningún gráfico define color/fuente por su cuenta.

## Estructura

```
viz/
├── populi_style.py     # NÚCLEO: paleta, fuentes, formatos, estilo de ejes,
│                       #   alineación, pie de marca, guardar(). set_tema() y fp().
├── charts/
│   ├── lineas_bandas.py  # líneas + bandas de confianza (estrella, IRF/FMI)
│   ├── lineas.py         # series simples (con punto final opcional)
│   ├── barras.py         # barras verticales + ranking horizontal
│   └── areas.py          # áreas apiladas (100%)
├── catalogo.py         # publicar() + build_manifest() -> Banco
└── examples/           # demos y ejemplos de autoría
```

Salidas del Banco:
```
public/graficas/<slug>.png   imagen branded
public/thumbs/<slug>.png     miniatura
public/datos/<slug>.csv      datos descargables
data/catalogo/<slug>.json    ficha (metadata)
src/manifest.json            catálogo consolidado (para Astro)
```

## Cómo crear una gráfica (autoría)

Pasas **datos + metadata**; el resto (marca, estilo, descargas, catálogo) sale solo:

```python
from catalogo import publicar, build_manifest
import pandas as pd

df = pd.DataFrame({"ipc": [...], "ipc_lo": [...], "ipc_hi": [...]}, index=anios)

publicar(
    meta={
        "slug": "ipc-anual-bolivia",          # id único (archivo)
        "tipo": "lineas_bandas",              # lineas_bandas | lineas | barras | ranking | areas
        "titulo": "…",
        "subtitulo": "…",
        "fuente": "Fuente: INE Bolivia. Elaboración: Centro de Estudios POPULI.",
        "categoria": "inflacion",             # ver CATEGORIAS en catalogo.py
        "tags": ["ipc", "inflacion"],
        "fecha": "2026-06-09",
        # "formato": "red_vertical" (def.) | red_cuadrada | red_historia | informe…
    },
    df=df,                                    # se exporta a CSV
    series=[{"y": "ipc", "lo": "ipc_lo", "hi": "ipc_hi", "label": "IPC", "color": "rojo"}],
    eje_x="Año", y_decimales=1, y_sufijo="%",
)
build_manifest()
```

Argumentos por tipo (`chart_kwargs`):
- **lineas_bandas / lineas:** `series=[{"y","lo","hi","label","color"}]`, `eje_x`, `y_decimales`, `y_sufijo`.
- **areas:** `series=["colA","colB",…]`, `colores=[…]`, `normalizar=True`.
- **barras:** `x=[…]`, `valores=[…]`, `color`, `resaltar=[idx]`, `y_decimales`, `y_sufijo`.
- **ranking:** `etiquetas=[…]`, `valores=[…]`, `resaltar_top=N`.

### En lote (ej. mapas/municipios del censo)

Como `publicar()` es una función, se itera sobre cualquier base:

```python
for muni, sub in datos.groupby("municipio"):
    publicar(meta={"slug": f"censo-{muni}", "tipo": "barras", "titulo": f"…{muni}…",
                   "categoria": "censo", "fecha": HOY},
             df=sub, x=list(sub["grupo"]), valores=list(sub["valor"]))
build_manifest()
```

## Previsualizar y publicar la galería (Astro)

La vitrina es la página Astro `src/pages/index.astro` (lee `src/manifest.json` y
los assets de `public/`). Banco standalone, desplegado a `datos.populi.org.bo`.

```bash
npm run dev      # vitrina en vivo con recarga -> http://localhost:4321
npm run build    # genera dist/ (lo que se publica en GitHub Pages)
```

Flujo completo para añadir gráficas:
1. `python viz/examples/...` o tu script con `publicar(...)` + `build_manifest()`.
2. Commit de `public/graficas`, `public/datos`, `public/thumbs`, `data/catalogo`,
   `src/manifest.json`.
3. Push → el workflow `deploy.yml` construye Astro y publica en Pages.

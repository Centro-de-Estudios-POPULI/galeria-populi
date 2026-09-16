# Motor de visualización POPULI — `viz/`

Todo el estilo vive en `populi_style.py`. Ningún gráfico define color ni fuente
por su cuenta, y `populi_style.py` tampoco: los lee de `paleta.py`, que es una
copia byte a byte de `Proyectos/populi-marca/paleta.py`.

## Identidad (cerrada 2026-08-10; rampa de mapas oficializada 2026-09-16)

- **Colores:** rampa editorial de 10 tonos, rojo de marca `BRAND`, oro `GOLD`,
  categórica de 12, ordinal de 4, y `DIVERGING_MAPA` (9 tonos) para los mapas
  municipales: la MISMA lista en el motor y en los dos atlas.
- **Tipografía:** Playfair Display (`TITLE_SERIF`) · Inter (`BODY`) · JetBrains
  Mono (`MONO`). Negritas por FAMILIA: `BOLD` («Inter Bold»), `MONO_BOLD`.
  El titular de las láminas va en Zilla Slab (`TITLE_REDES`).
- **Formatos:** `red_vertical` (1080×1350, el de los mapas municipales),
  `red_cuadrada`, `mundo`, `informe_*`. Render a 2× y cuantización a 256 colores.

## Estructura

```
viz/
  paleta.py, paleta.json     copia de populi-marca (NO editar acá)
  populi_style.py            colores, fuentes, formatos, componer(), guardar(),
                             escala_atlas() y miniatura()
  catalogo.py                publicar(), registrar(), build_manifest()
  verificar.py               el contrato (ver README raíz)
  regenerar_miniaturas.py    rehace los WebP sin volver a renderizar
  og_portada.py              la tarjeta OG del sitio (public/og.png)
  charts/                    mapas · mapa_mundial · lineas · lineas_bandas ·
                             areas · barras · barras_apiladas · series_eventos
  examples/                  generadores en lote (mapas_censo_todos, mapas_atlas_fiscal,
                             mapas_mundo, monetario_*) + demo_tipos + paletas_swatch
  recetas/                   figuras compuestas (series-eventos, serie-y-ranking,
                             small-multiples) con su README
  geo/                       atlas_muni_343.topojson (respaldo del mapa maestro),
                             world_110m.topojson + crosswalk
```

## La escala de los atlas: `escala_atlas()`

Divergente de ancla real, idéntica a la de la web:

- `dominio=` → el `dom` declarado en el catálogo (p02/p98 sobre la unión de
  censos). Con dominio declarado la leyenda rotula ≤ y ≥ siempre.
- `pivote=` + `piv_tipo=` → el ancla YA calculada por el generador con la regla
  del atlas («país 2024», «promedio nacional», «mediana») y su nombre. Es la
  forma correcta: cada atlas pondera distinto y replicar cada regla adentro del
  motor es cómo las láminas se desviaron de la web.
- `con_signo=True` → pivote en cero, dominio simétrico (mapas de cambio y
  resultado fiscal).
- `direccion=` → `dir` del catálogo; +1 invierte la rampa.
- El pivote se recorta a ±8 % del rango para que la rampa no se degenere, y la
  leyenda rotula el REAL con asterisco cuando eso pasa.

## Cómo crear una gráfica

```python
from catalogo import publicar, build_manifest
publicar(meta={"slug": "...", "tipo": "lineas", "titulo": "...", "subtitulo": "...",
               "fuente": "...", "categoria": "monetario", "tags": [...], "fecha": "AAAA-MM-DD"},
         df=df, series=[...])
build_manifest()
```

`meta` admite campos extra (`clave`, `atlas`, `modo`, `anio`, `enlace`,
`universo`, `unidad`, `escala`…) que van tal cual a la ficha. Las figuras
compuestas que dibujan con `componer()` directo registran su ficha con
`registrar(meta, tipo, formato)` después de `ps.guardar(...)`.

## Previsualizar y publicar

```bash
npm run dev          # http://localhost:4321/galeria-populi/
python viz/verificar.py
git add -A && git commit && git push   # la Action construye y despliega
```

# Banco de Gráficos POPULI

Galería buscable de gráficas e indicadores de Bolivia con la identidad del Centro
de Estudios POPULI, en alta resolución y listas para compartir. Publicada en
GitHub Pages: <https://centro-de-estudios-populi.github.io/galeria-populi/>

**Se publica la IMAGEN, no el dato crudo.** Cada mapa municipal enlaza al atlas
interactivo del que sale, y cada atlas enlaza de vuelta a su lámina.

## Cómo está armado

```
Proyectos/populi-marca/paleta.py  ─── fuente única de colores y tipografía
        │  (copia byte a byte)            exportar.py → paleta.json
        ▼
viz/populi_style.py  ── motor matplotlib: formatos, tipografía, escala de los atlas
viz/charts/*.py      ── tipos de gráfica (mapas, líneas, barras, apiladas, mundial…)
viz/examples/*.py    ── generadores en lote (los que publican al Banco)
viz/recetas/*        ── figuras compuestas de publicación
        │
        ▼  publicar(meta, …)  →  public/graficas/<slug>.png
        │                        public/thumbs/<slug>.webp   (letterbox, 600 px)
        │                        data/catalogo/<slug>.json   (la ficha)
        ▼
viz/catalogo.py build_manifest()  →  src/manifest.json          (lo que lee Astro)
                                     public/indice_laminas.json  (lo que leen los atlas)
        ▼
Astro (src/)  →  portada con buscador, visor y una página por gráfica  →  Pages
```

### Los generadores que publican

| Comando | Produce |
|---|---|
| `python viz/examples/mapas_censo_todos.py` | los mapas del Censo en TRES modos: 2024, 2012 y cambio 2012→2024. Título, definición, universo, dirección, dominio y denominador salen del `catalogo.json` del Atlas Socioeconómico |
| `python viz/examples/mapas_atlas_fiscal.py` | los 30 mapas del Atlas Fiscal (gestión de referencia). Título de lámina y definición salen de `fiscal_catalogo.json` |
| `python viz/examples/mapas_mundo.py todos` | los 222 mapas mundiales (OJO: sin `todos` hace sólo 9) |
| `viz/examples/monetario_*.py`, `viz/recetas/*/publicar.py` | las series del monitor monetario y las figuras compuestas |

Cada lámina municipal declara en su ficha `clave`, `atlas`, `modo`, `anio` y
`enlace`. Con eso `build_manifest()` escribe `public/indice_laminas.json`, y los
atlas ofrecen el botón «Descargar este mapa» sólo donde la lámina existe.

### El contrato

```bash
python viz/verificar.py          # aborta si algo del contrato dejó de ser cierto
python viz/verificar.py --rapido # sin recomputar los pivotes
```

Comprueba que la paleta es una (copia idéntica, misma rampa en el motor y en los
dos atlas), que cada ficha tiene su PNG y su WebP, que cada indicador de los dos
catálogos tiene lámina y el índice la nombra, que el pivote de cada lámina
censal coincide con la regla del Atlas recomputada aparte, que el sitio no tiene
colores fuera de paleta ni esquinas redondeadas ni fuentes derogadas, y que el
motor no pide negrita con `weight="bold"`.

## Uso local

```bash
pip install matplotlib geopandas pillow antimeridian   # motor
npm install                                              # sitio

python viz/examples/mapas_censo_todos.py --solo=pct_urbano   # una lámina, para mirar
python viz/verificar.py
npm run dev        # http://localhost:4321/galeria-populi/
npm run build      # dist/
```

Publicar = dos ramas. `main` lleva el código, las fichas (`data/catalogo`) y
`src/manifest.json`; las IMÁGENES (`public/graficas`, `public/thumbs`) viven en
la rama huérfana `laminas`, de un solo commit, que recrea
`scripts/publicar_laminas.py`. La Action hace checkout de las dos, copia las
imágenes a `public/` y construye el sitio Astro.

```
python viz/examples/<generador>.py --solo=<clave>   # genera PNG + WebP + ficha
python viz/verificar.py                              # contrato
git add -A && git commit                             # fichas + manifiesto (main)
git push origin main
python scripts/publicar_laminas.py                   # rama laminas (push forzado) + dispara la Action
```

Un push a `laminas` no dispara la Action (la huérfana no lleva `.github/`), así que
`publicar_laminas.py` la lanza con `gh workflow run` al terminar. Sin `gh`, lanzarla
desde la pestaña Actions; si no, el sitio queda con las imágenes anteriores.

Por qué: cada regeneración completa de los 606 mapas sumaba ~170 MB a `.git`.
Con la rama de un commit el repo pesa lo que pesa la última versión, siempre.

## Reglas que no se negocian

- **Ningún hexadecimal a mano.** Todo color se lee de `viz/paleta.py` (copia de
  `populi-marca`). Si hace falta un color nuevo, se declara ALLÁ y se recopia.
- **La lámina dice lo mismo que el tablero.** Mismo dominio, mismo pivote, mismo
  rótulo del pivote, misma rampa. El generador calcula el ancla con la misma
  regla que el Atlas y se la pasa a `escala_atlas(pivote=…)`.
- **La lámina es el mapa, no el tablero:** 343 municipios con borde fino y
  blanco, sin malla departamental.
- **Los slugs no cambian.** Salen de `lam` en el catálogo del Atlas; los de 2012
  y cambio se derivan (`<lam>-2012`, `<lam>-cambio`).
- **Negrita por familia** (`ps.BOLD`, `ps.MONO_BOLD`), nunca `weight="bold"`:
  matplotlib lo ignora al resolver por archivo.
- **`border-radius: 0` en todo.**

## Tipografía

Playfair Display (titulares del sitio) · Inter (texto) · JetBrains Mono (cifras).
La única excepción: el TITULAR de cada lámina va en **Zilla Slab**, porque un
título de gráfico se lee en miniatura y la slab sostiene el peso donde la didona
se adelgaza. Es una decisión del Banco, no del sitio.

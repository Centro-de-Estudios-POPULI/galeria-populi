# Sistema de Visualización Institucional — Centro de Estudios POPULI

Guía para que **Claude Code** construya y mantenga la librería de gráficos de POPULI,
aplicable a todas nuestras bases de datos (series económicas, fiscales, electorales y mapas).

---

## 1. Objetivo

Crear un módulo de visualización **reutilizable y con identidad visual consistente**, de modo que
cualquier gráfico de POPULI —para informes o para redes sociales— comparta paleta, tipografía,
elementos de marca y estilo editorial, cambiando los colores/fuentes en **un solo lugar**.

Regla de oro: **la paleta, las fuentes y los elementos de marca viven en `populi_style.py`.
Ningún gráfico define colores o fuentes por su cuenta.**

---

## 2. Estructura de carpetas sugerida

```
populi_viz/
├── populi_style.py        # paleta, carga de fuentes, marca, helpers (núcleo)
├── charts/
│   ├── lineas_bandas.py   # líneas con bandas de confianza (estilo IRF/FMI)
│   ├── lineas.py          # series de tiempo simples
│   ├── barras.py          # barras / barras agrupadas
│   ├── areas.py           # áreas apiladas
│   └── mapas.py           # coropléticos (GeoPandas)
├── assets/
│   └── fonts/             # .ttf institucionales (ver sección 5)
├── examples/              # un script demo por tipo de gráfico
├── output/                # PNG/SVG generados
└── README.md
```

---

## 3. Identidad visual

### Paleta (definir como diccionario en `populi_style.py`)

| Nombre        | HEX       | Uso                                   |
|---------------|-----------|---------------------------------------|
| beige_claro   | `#FBF8F2` | Fondo de figura y ejes                |
| beige         | `#F5F0E6` | Fondo alternativo / cajas             |
| rojo          | `#B5322E` | Serie principal, marca, énfasis       |
| cafe          | `#5C4433` | Texto, ejes, serie secundaria         |
| azul          | `#1F4E66` | Segunda serie (contraste sobrio)      |
| gris          | `#8C8378` | Notas de fuente, texto terciario      |
| gris_claro    | `#D8D2C7` | Líneas de grilla                      |
| negro         | `#2B2420` | Títulos, línea de cero                |

### Tipografía (parametrizable)

- **Informes:** Playfair Display (títulos) + Source Sans 3 (cuerpo).
- **Redes sociales:** Fraunces (títulos, más peso/impacto) + Source Sans 3 (cuerpo).
- Debe poder cambiarse pasando un argumento o cambiando una constante. **No** hardcodear
  el nombre de la fuente dentro de cada gráfico.

### Estilo editorial (tipo FMI / The Economist)

- Sin bordes (`spines`) superior, derecho ni izquierdo. Solo eje inferior, en color café.
- Grilla **solo horizontal**, tenue (`gris_claro`).
- **Etiquetas de serie al final de cada línea**, no leyenda. (`ax.annotate` en el último punto,
  ampliando `xlim` ~14% a la derecha para que quepan.)
- Bandas de confianza con `fill_between(..., alpha≈0.16)` dibujadas **debajo** de las líneas.
- Línea horizontal en y=0 cuando aplique (`axhline`).
- Al pie: nota de **fuente** (gris, pequeña) + **marca POPULI** + franja roja de firma.

---

## 4. Arquitectura de la API

Cada tipo de gráfico es **una función** que:

1. Recibe un **DataFrame genérico** (nunca datos fijos). El índice = eje X.
2. Recibe una lista `series` describiendo qué columna es cada línea y, opcionalmente, sus bandas.
3. Importa todo lo visual desde `populi_style.py`.
4. Acepta `titulo`, `subtitulo`, `eje_x`, `eje_y`, `fuente`, `archivo`.
5. Devuelve `(fig, ax)` para permitir ajustes finos.

Firma de referencia (líneas con bandas):

```python
grafico_lineas_bandas(
    df,
    series=[
        {"y": "col", "lo": "col_lo", "hi": "col_hi",
         "label": "Etiqueta", "color": "rojo"},  # color por nombre de paleta o HEX
        ...
    ],
    titulo=..., subtitulo=..., eje_x=..., fuente=...,
    formato="informe" | "red_cuadrada" | "red_vertical",
    archivo="output/grafico.png",
)
```

### Formatos de salida (clave para redes)

| Formato        | Tamaño        | Uso                          |
|----------------|---------------|------------------------------|
| `informe`      | ~9×9 in, 200 dpi | PDF/HTML, presentaciones  |
| `red_cuadrada` | 1080×1080 px  | Instagram / X feed           |
| `red_vertical` | 1080×1350 px  | Instagram retrato / stories  |

La función ajusta tamaños de fuente y márgenes según el formato.

---

## 5. Fuentes

Descargar los `.ttf` a `assets/fonts/` desde Google Fonts y cargarlos con
`matplotlib.font_manager.addfont()`, con **fallback** a una serif/sans del sistema si faltan
(para que nunca se rompa). Fuentes a incluir:

- `PlayfairDisplay.ttf`, `SourceSans3.ttf` (informes)
- `Fraunces.ttf` (títulos para redes)
- Opcionales evaluadas: `Archivo.ttf`, `Sora.ttf`, `LibreFranklin.ttf`

> En entornos sin las fuentes instaladas, matplotlib cae a una fuente por defecto y el
> gráfico pierde identidad. Por eso van versionadas en el repo, no asumidas del sistema.

---

## 6. Mapas (caso aparte)

Los coropléticos **no** son matplotlib puro:

- **Estáticos:** `GeoPandas` + matplotlib → hereda el mismo `populi_style.py` (paleta, marca, fuentes).
  Usar shapefiles/GeoJSON de municipios, TIOC y gobernaciones de Bolivia.
- **Interactivos (dashboards):** Folium/Leaflet o Plotly. Replicar la paleta como escala de color.
- Para datos fiscales/socioeconómicos por municipio, usar escalas secuenciales derivadas del
  rojo/café institucional; reservar divergentes (rojo↔azul) para variables con signo.

---

## 7. Orden de trabajo sugerido para Claude Code

1. Crear estructura de carpetas + `populi_style.py` (paleta, carga de fuentes con fallback, marca).
2. Implementar `charts/lineas_bandas.py` (tomar como base el script `populi_irf_chart.py` adjunto).
3. Refactorizar para que el estilo salga 100% de `populi_style.py`.
4. Añadir soporte de `formato` (informe / red_cuadrada / red_vertical).
5. Replicar el patrón para `lineas.py`, `barras.py`, `areas.py`.
6. Revisar nuestras bases de datos existentes y crear un `examples/` por tipo.
7. Último: `mapas.py` con GeoPandas.

---

## 8. Convenciones

- Salida en PNG (≥200 dpi para informes) y **SVG** cuando se necesite editar después.
- Idioma de todo lo visible: español. Decimales con coma (`0,30`) vía formatter de matplotlib.
- Nunca incrustar credenciales ni rutas absolutas de máquina; usar rutas relativas al repo.
- Cada función con docstring y un ejemplo mínimo ejecutable.

---

*Punto de partida: el script `populi_irf_chart.py` ya implementa el estilo de líneas con bandas
y la marca. Úsalo como semilla y conviértelo en el módulo `charts/lineas_bandas.py`.*
